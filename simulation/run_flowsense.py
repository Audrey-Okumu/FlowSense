"""FlowSense adaptive controller vs the fixed timer, same junction, traffic and seeds.
  python run_flowsense.py all --seeds 3          -> results/compare.csv + compare.json
  python run_flowsense.py rush_hour --replay 1000 1300   -> replay files for the demo page
Rules: min green 8 s, max green 60 s, yellow always kept, any vehicle waiting >90 s forces its phase next,
switch early when the served road empties or another road's demand is clearly bigger."""
import argparse, csv, json, os, statistics
import sys
import traci, sumolib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "controller"))
from rule_based import Flow, YELLOW
from tuned_fixed import tune  # controller logic lives in ../controller/rule_based.py
import run_baseline as rb

def run(name, seed, mode, win=None, end=3600, gui=False, delay=0, params=None):
    os.makedirs("results", exist_ok=True)
    ti = f"results/tripinfo_{mode}_{name}_s{seed}.xml"
    cmd = ["sumo-gui" if gui else "sumo", "-c", "flowsense.sumocfg", "-r", f"routes_{name}.rou.xml",
           "--tripinfo-output", ti, "--seed", str(seed), "--no-step-log", "true", "--no-warnings", "true", "--end", str(end)]
    if gui:
        cmd += ["--start", "true", "--quit-on-end", "true", "--delay", str(delay), "--window-size", "680,720",
                "--window-pos", {"fixed": "0,30", "tuned": "345,30", "flowsense": "690,30"}.get(mode, "0,30")]
    traci.start(cmd)
    tls = rb.pick_tls(); edges = rb.approach_edges(tls)
    cx, cy = traci.junction.getPosition(tls)
    if gui:
        try:
            traci.gui.setSchema("View #0", "real world"); traci.gui.setBoundary("View #0", cx - 160, cy - 90, cx + 160, cy + 90)
        except traci.TraCIException:
            pass
    ctl = Flow(tls, **(params or {})) if mode == "flowsense" else None
    if mode == "tuned": print("tuned split (N/S, E/W green s):", tune(tls, f"routes_{name}.rou.xml"))
    rows, frames, types = [], [], {}
    while traci.simulation.getTime() < end:
        traci.simulationStep(); now = traci.simulation.getTime()
        if ctl: ctl.step(now)
        row = {"time": now}
        for e in edges: row[f"{e}_queue"] = traci.edge.getLastStepHaltingNumber(e); row[f"{e}_wait"] = 0
        rows.append(row)
        if win and win[0] <= now < win[1]:
            vs = []
            for v in traci.vehicle.getIDList():
                x, y = traci.vehicle.getPosition(v); x -= cx; y -= cy
                if abs(x) < 170 and abs(y) < 130:
                    t = traci.vehicle.getTypeID(v)
                    if t not in types: types[t] = [t, traci.vehicletype.getColor(t)[:3], traci.vehicle.getLength(v), traci.vehicle.getWidth(v)]
                    vs.append([int(v) if v.isdigit() else abs(hash(v)) % 10**7, round(x, 1), round(y, 1), round(traci.vehicle.getAngle(v)), list(types).index(t)])
            frames.append(dict(t=now, v=vs, s=traci.trafficlight.getRedYellowGreenState(tls),
                               q=[traci.edge.getLastStepHaltingNumber(e) for e in sorted(edges)]))
    traci.close()
    s = rb.summarize(ti, rows, name, mode, tls, seed)
    return s, frames, list(types.values()), tls

def net_view(tls):
    net = sumolib.net.readNet("intersection.net.xml", withInternal=True)
    c = net.getNode(tls).getCoord()
    r = lambda sh: [[round(a - c[0], 1), round(b - c[1], 1)] for a, b in sh]
    road, side, cross = [], [], []
    for e in net.getEdges(withInternal=True):
        for l in e.getLanes():
            it = dict(p=r(l.getShape()), w=round(l.getWidth(), 1))
            f = e.getFunction()
            if f == "crossing": cross.append(it)
            elif f == "walkingarea" or (l.allows("pedestrian") and not l.allows("passenger")): side.append(it)
            elif l.allows("passenger"): road.append(it)
    return dict(road=road, side=side, cross=cross, c=[c[0], c[1]])

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=rb.BUILT_IN + ["all"]); p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--replay", nargs=2, type=int)
    p.add_argument("--gui", action="store_true", help="watch it in SUMO (use with --only)")
    p.add_argument("--only", choices=["fixed", "tuned", "flowsense"], help="run just one controller")
    p.add_argument("--delay", type=int, default=50, help="ms per step in the GUI (bigger = slower)")
    p.add_argument("--end", type=int, default=3600, help="simulated seconds"); a = p.parse_args()
    modes = (a.only,) if a.only else ("fixed", "tuned", "flowsense")
    names = rb.BUILT_IN if a.scenario == "all" else [a.scenario]
    if a.replay:
        out = {}
        for mode in ("fixed", "flowsense"):
            s, fr, ty, tls = run(names[0], 42, mode, tuple(a.replay)); out[mode] = fr; out["types"] = ty
            print(s)
        nv = net_view(tls); traci.start(["sumo", "-c", "flowsense.sumocfg", "--no-step-log", "true"])
        ctl = Flow(tls); links = []
        net = sumolib.net.readNet("intersection.net.xml", withInternal=True)
        for i in ctl.vi:
            sh = net.getLane(ctl.lanes[i]).getShape(); links.append([round(sh[-1][0] - nv['c'][0], 1), round(sh[-1][1] - nv['c'][1], 1)])
        traci.close(); nv["links"] = links; nv["vi"] = ctl.vi; out["net"] = nv
        json.dump(out, open("results/replay.json", "w"), separators=(",", ":")); print("replay written")
    else:
        res = [run(n, 42 + k, m, end=a.end, gui=a.gui, delay=a.delay)[0] for n in names for k in range(a.seeds) for m in modes]
        cols = ["vehicles_finished", "avg_wait_s", "max_wait_s", "avg_time_loss_s", "avg_total_queue", "max_single_road_queue"]
        comp = []
        for n in names:
            for m in modes:
                rs = [r for r in res if r["scenario"] == n and r["controller"] == m]
                comp.append(dict(scenario=n, controller=m, seeds=len(rs), **{c: round(statistics.mean(r[c] for r in rs), 2) for c in cols}))
        with open("results/compare.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=comp[0].keys()); w.writeheader(); w.writerows(comp)
        json.dump(comp, open("results/compare.json", "w")); print("\nCOMPARE (avg of seeds)")
        for c in comp: print(c)
