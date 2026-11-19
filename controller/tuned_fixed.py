"""Tuned fixed-time baseline: still a fixed timer (no sensing), but the green split between the
north-south and east-west through phases is set in proportion to that scenario's average demand.
This is the fair "best a fixed timer can do" comparison. Cycle length stays 90 s."""
import xml.etree.ElementTree as ET
import traci


def tune(tls, routes_file, min_g=15):
    ns = ew = 0.0
    for f in ET.parse(routes_file).getroot().findall("flow"):
        v = float(f.get("probability")) * (float(f.get("end")) - float(f.get("begin")))
        if f.get("route")[0] in "NS": ns += v
        else: ew += v
    share = ns / (ns + ew)
    logic = traci.trafficlight.getAllProgramLogics(tls)[0]
    lanes = traci.trafficlight.getControlledLanes(tls)
    big = [k for k, p in enumerate(logic.phases) if p.duration >= 20]          # the two through phases
    axis = lambda k: {lanes[i][0] for i, c in enumerate(logic.phases[k].state) if c in "Gg" and not lanes[i].startswith(":")}
    ns_k = next(k for k in big if axis(k) <= {"N", "S"}); ew_k = next(k for k in big if k != ns_k)
    total = logic.phases[ns_k].duration + logic.phases[ew_k].duration
    a = int(min(max(round(total * share), min_g), total - min_g))
    logic.phases[ns_k].duration, logic.phases[ew_k].duration = a, total - a
    traci.trafficlight.setProgramLogic(tls, logic)
    return a, total - a
