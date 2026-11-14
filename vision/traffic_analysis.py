import json
import numpy as np
import supervision as sv
from ultralytics import YOLO
import cv2
from typing import Dict, Iterable, List, Set
from tqdm import tqdm
import gc

COLORS = sv.ColorPalette.from_hex(["#E6194B", "#3CB44B", "#FFE119", "#3C76D1"])
LANE_NAMES = ["north", "south", "west", "east"]

ZONE_IN_POLYGONS = [
    np.array([[592, 282], [900, 282], [900, 82], [592, 82]]),
    np.array([[950, 860], [1250, 860], [1250, 1060], [950, 1060]]),
    np.array([[592, 582], [592, 860], [392, 860], [392, 582]]),
    np.array([[1250, 282], [1250, 530], [1450, 530], [1450, 282]]),
]

ZONE_OUT_POLYGONS = [
    np.array([[950, 282], [1250, 282], [1250, 82], [950, 82]]),
    np.array([[592, 860], [900, 860], [900, 1060], [592, 1060]]),
    np.array([[592, 282], [592, 550], [392, 550], [392, 282]]),
    np.array([[1250, 860], [1250, 560], [1450, 560], [1450, 860]]),
]



class DetectionsManager:
    def __init__(self) -> None:
        self.tracker_id_to_zone_id: Dict[int, int] = {}
        self.counts: Dict[int, Dict[int, Set[int]]] = {}

    def update(
        self,
        detections_all: sv.Detections,
        detections_in_zones: List[sv.Detections],
        detections_out_zones: List[sv.Detections],
    ) -> sv.Detections:
        for zone_in_id, detections_in_zone in enumerate(detections_in_zones):
            for tracker_id in detections_in_zone.tracker_id:
                self.tracker_id_to_zone_id.setdefault(tracker_id, zone_in_id)

        for zone_out_id, detections_out_zone in enumerate(detections_out_zones):
            for tracker_id in detections_out_zone.tracker_id:
                if tracker_id in self.tracker_id_to_zone_id:
                    zone_in_id = self.tracker_id_to_zone_id[tracker_id]
                    self.counts.setdefault(zone_out_id, {})
                    self.counts[zone_out_id].setdefault(zone_in_id, set())
                    self.counts[zone_out_id][zone_in_id].add(tracker_id)

        if len(detections_all) > 0:
            detections_all.class_id = np.vectorize(
                lambda x: self.tracker_id_to_zone_id.get(x, -1)
            )(detections_all.tracker_id)
        else:
            detections_all.class_id = np.array([], dtype=int)

        return detections_all[detections_all.class_id != -1]


def initiate_polygon_zones(
    polygons: List[np.ndarray],
    triggering_anchors: Iterable[sv.Position] = [sv.Position.CENTER],
) -> List[sv.PolygonZone]:
    return [
        sv.PolygonZone(polygon=polygon, triggering_anchors=triggering_anchors)
        for polygon in polygons
    ]


class VideoProcessor:
    def __init__(
        self,
        source_weights_path: str = "data/traffic_analysis.pt",
        source_video_path: str = "data/traffic_analysis.mp4",
        target_video_path: str = "data/traffic_analysis_result.mp4",
        output_json_path: str = "data/lane_counts.json",
        confidence_threshold: float = 0.3,
        iou_threshold: float = 0.7,
    ) -> None:
        self.conf_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.source_video_path = source_video_path
        self.target_video_path = target_video_path
        self.output_json_path = output_json_path

        print("Loading YOLO model...")
        self.model = YOLO(source_weights_path)
        self.tracker = sv.ByteTrack()

        self.video_info = sv.VideoInfo.from_video_path(source_video_path)
        self.zones_in = initiate_polygon_zones(ZONE_IN_POLYGONS, [sv.Position.CENTER])
        self.zones_out = initiate_polygon_zones(ZONE_OUT_POLYGONS, [sv.Position.CENTER])

        self.box_annotator = sv.BoxAnnotator(color=COLORS)
        self.label_annotator = sv.LabelAnnotator(
            color=COLORS, text_color=sv.Color.BLACK
        )
        self.trace_annotator = sv.TraceAnnotator(
            color=COLORS, position=sv.Position.CENTER, trace_length=100, thickness=2
        )
        self.detections_manager = DetectionsManager()
        self.timeline_json = []

    def process_video(self):
        print(f"Processing video: {self.source_video_path}")
        frame_generator = sv.get_video_frames_generator(source_path=self.source_video_path)
        fps = self.video_info.fps or 30.0

        with sv.VideoSink(self.target_video_path, self.video_info) as sink:
            for frame_num, frame in enumerate(tqdm(frame_generator, total=self.video_info.total_frames)):
                if frame_num % 2 != 0:
                    continue
                annotated_frame = self.process_frame(frame, frame_num, fps)
                sink.write_frame(annotated_frame)
                if frame_num % 50 == 0:
                    gc.collect()

        payload = {
            "video_source": self.source_video_path,
            "fps": fps,
            "sample_interval_frames": 2,
            "total_snapshots": len(self.timeline_json),
            "timeline": self.timeline_json,
        }
        with open(self.output_json_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\nDONE! Saved video to {self.target_video_path} and JSON to {self.output_json_path}")

    def annotate_frame(self, frame: np.ndarray, detections: sv.Detections) -> np.ndarray:
        annotated_frame = frame.copy()
        for i, (zone_in, zone_out) in enumerate(zip(self.zones_in, self.zones_out)):
            annotated_frame = sv.draw_polygon(annotated_frame, zone_in.polygon, COLORS.colors[i])
            annotated_frame = sv.draw_polygon(annotated_frame, zone_out.polygon, COLORS.colors[i])

        labels = [f"#{tracker_id}" for tracker_id in detections.tracker_id]
        annotated_frame = self.trace_annotator.annotate(annotated_frame, detections)
        annotated_frame = self.box_annotator.annotate(annotated_frame, detections)
        annotated_frame = self.label_annotator.annotate(annotated_frame, detections, labels)

        for i, zone_out in enumerate(self.zones_out):
            zone_center = sv.get_polygon_center(polygon=zone_out.polygon)
            if i in self.detections_manager.counts:
                for j, zone_in_id in enumerate(self.detections_manager.counts[i]):
                    count = len(self.detections_manager.counts[i][zone_in_id])
                    text_anchor = sv.Point(x=zone_center.x, y=zone_center.y + 40 * j)
                    annotated_frame = sv.draw_text(
                        scene=annotated_frame,
                        text=str(count),
                        text_anchor=text_anchor,
                        background_color=COLORS.colors[zone_in_id],
                    )
        return annotated_frame

    def process_frame(self, frame: np.ndarray, frame_num: int = 0, fps: float = 30.0) -> np.ndarray:
        results = self.model(
            frame, verbose=False, conf=self.conf_threshold, iou=self.iou_threshold
        )[0]
        detections = sv.Detections.from_ultralytics(results)
        detections.class_id = np.zeros(len(detections))
        detections = self.tracker.update_with_detections(detections)

        detections_in_zones = []
        detections_out_zones = []
        lane_counts_snapshot = {}

        for idx, (zone_in, zone_out) in enumerate(zip(self.zones_in, self.zones_out)):
            detections_in_zone = detections[zone_in.trigger(detections=detections)]
            detections_in_zones.append(detections_in_zone)

            detections_out_zone = detections[zone_out.trigger(detections=detections)]
            detections_out_zones.append(detections_out_zone)

            lane_key = LANE_NAMES[idx] if idx < len(LANE_NAMES) else f"lane_{idx}"
            lane_counts_snapshot[lane_key] = len(detections_in_zone)

        self.timeline_json.append({
            "frame": frame_num,
            "timestamp": round(frame_num / fps, 2),
            "lanes": lane_counts_snapshot,
        })

        detections = self.detections_manager.update(
            detections, detections_in_zones, detections_out_zones
        )
        return self.annotate_frame(frame, detections)


if __name__ == "__main__":
    processor = VideoProcessor()
    processor.process_video()


if __name__ == '__main__':
    VideoProcessor().process_video()
