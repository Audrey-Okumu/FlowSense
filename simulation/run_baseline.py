"""Run the fixed-time baseline (the traffic light as cities run it today).

Our built-in junction:
    python run_baseline.py rush_hour --gui
    python run_baseline.py all

A real map (e.g. made with osmWebWizard):
    python run_baseline.py real --cfg osm_nairobi/osm.sumocfg
    python run_baseline.py real --cfg osm_nairobi/osm.sumocfg --tls <junction_id> --gui

For a real map the script automatically picks the busiest traffic light
(most signal links) unless you name one with --tls, and measures queues and
waiting time on the roads that feed it.
"""
import argparse, csv, os, statistics
import xml.etree.ElementTree as ET
import traci

BUILT_IN = ["normal", "rush_hour", "uneven"]


def pick_tls(tls_id=None):
    ids = traci.trafficlight.getIDList()
    if not ids:
        raise SystemExit("This network has no traffic lights.")
    if tls_id:
        if tls_id not in ids:
            raise SystemExit(f"Traffic light '{tls_id}' not found. Available: {list(ids)}")
        return tls_id
    return max(ids, key=lambda t: len(traci.trafficlight.getControlledLinks(t)))


def approach_edges(tls):
    edges = []
    for lane in traci.trafficlight.getControlledLanes(tls):
        e = traci.lane.getEdgeID(lane)
        if e not in edges and not e.startswith(":"):
            edges.append(e)
    return edges


def run(name, cfg="flowsense.sumocfg", routes=None, gui=False, seed=42,
        tag="fixed", tls_id=None, end=3600):
    os.makedirs("results", exist_ok=True)
    tripinfo = f"results/tripinfo_{tag}_{name}_s{seed}.xml"
    cmd = ["sumo-gui" if gui else "sumo", "-c", cfg]
    if routes:
        cmd += ["-r", routes]
    cmd += ["--tripinfo-output", tripinfo, "--seed", str(seed),
            "--no-step-log", "true", "--end", str(end)]
    if gui:
        cmd += ["--start", "true", "--quit-on-end", "true"]
    traci.start(cmd)

    if gui:  # nicer look: realistic colours, framed on our built-in junction
        try:
            traci.gui.setSchema("View #0", "real world")
            if name in BUILT_IN:
                traci.gui.setBoundary("View #0", -160, -90, 160, 90)
        except traci.TraCIException:
            pass

    tls = pick_tls(tls_id)
    edges = approach_edges(tls)
    print(f"[{name}] traffic light '{tls}' | approaches: {edges}")

    rows = []
    while traci.simulation.getTime() < end:
        traci.simulationStep()
        row = {"time": traci.simulation.getTime()}
        for e in edges:
            row[f"{e}_queue"] = traci.edge.getLastStepHaltingNumber(e)
            row[f"{e}_wait"] = round(traci.edge.getWaitingTime(e), 1)
        rows.append(row)
    traci.close()

    with open(f"results/timeseries_{tag}_{name}_s{seed}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    return summarize(tripinfo, rows, name, tag, tls, seed)


def summarize(tripinfo, rows, name, tag, tls, seed):
    trips = ET.parse(tripinfo).getroot().findall("tripinfo")
    wait = [float(t.get("waitingTime")) for t in trips]
    loss = [float(t.get("timeLoss")) for t in trips]
    qcols = [c for c in rows[0] if c.endswith("_queue")]
    s = {"controller": tag, "scenario": name, "seed": seed, "tls": tls,
         "vehicles_finished": len(trips),
         "avg_wait_s": round(statistics.mean(wait), 2),
         "max_wait_s": round(max(wait), 1),
         "avg_time_loss_s": round(statistics.mean(loss), 2),
         "avg_total_queue": round(statistics.mean(sum(r[c] for c in qcols) for r in rows), 2),
         "max_single_road_queue": max(max(r[c] for c in qcols) for r in rows)}
    print(s)
    return s


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=BUILT_IN + ["all", "real"])
    p.add_argument("--cfg", help="SUMO .sumocfg of a real map (use with 'real')")
    p.add_argument("--tls", help="traffic light id to measure (default: busiest)")
    p.add_argument("--end", type=int, default=3600, help="simulated seconds")
    p.add_argument("--seeds", type=int, default=1,
                   help="run N random seeds (42, 43, ...) and also write an averaged summary")
    p.add_argument("--gui", action="store_true")
    a = p.parse_args()
    seeds = [42 + k for k in range(a.seeds)]

    if a.scenario == "real":
        if not a.cfg:
            raise SystemExit("Use --cfg path/to/osm.sumocfg with 'real'")
        results = [run("real", cfg=a.cfg, gui=a.gui, tls_id=a.tls, end=a.end, seed=sd) for sd in seeds]
        out = "results/summary_fixed_real.csv"
    else:
        names = BUILT_IN if a.scenario == "all" else [a.scenario]
        results = [run(n, routes=f"routes_{n}.rou.xml", gui=a.gui, end=a.end, seed=sd)
                   for n in names for sd in seeds]
        out = "results/summary_fixed.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader(); w.writerows(results)
    if a.seeds > 1:   # average each scenario over its seeds
        avg = []
        for n in sorted({r["scenario"] for r in results}):
            rs = [r for r in results if r["scenario"] == n]
            row = {"controller": rs[0]["controller"], "scenario": n, "seeds": len(rs), "tls": rs[0]["tls"]}
            for k in ["vehicles_finished", "avg_wait_s", "max_wait_s", "avg_time_loss_s",
                      "avg_total_queue", "max_single_road_queue"]:
                row[k] = round(statistics.mean(r[k] for r in rs), 2)
            avg.append(row)
        with open(out.replace(".csv", "_avg.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=avg[0].keys())
            w.writeheader(); w.writerows(avg)
        print("\nAVERAGED OVER", a.seeds, "SEEDS")
        for r in avg:
            print(r)
