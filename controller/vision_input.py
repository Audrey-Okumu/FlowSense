"""Camera-fed mode: run FlowSense's decision rules on the Vision Lead's counts file.

  python vision_input.py ..\\data\\lane_counts.json

Each second of video: counts per approach -> demand for two signal groups (N/S and E/W) ->
rule_based.choose() decides keep or switch (3 s yellow modelled) -> we log who has green.
Same decision function the SUMO runs use. It proves camera counts can drive the controller;
it does NOT measure performance (the clip is a different scene, and only ~27 s long).
Mapping: north=N_in, south=S_in, east=E_in, west=W_in."""
import argparse, csv, json, os
from rule_based import choose, YELLOW

GROUPS = {"NS": ("north", "south"), "EW": ("east", "west")}


def load_per_second(path):
    d = json.load(open(path))
    recs = d["timeline"] if isinstance(d, dict) else d
    buckets = {}
    for r in recs:
        buckets.setdefault(int(r["timestamp"]), []).append(r["lanes"])
    return [(s, {k: sum(l[k] for l in ls) / len(ls) for k in ls[0]}) for s, ls in sorted(buckets.items())]


def replay(seconds, start="NS"):
    cur, t0, yellow, target = start, 0, 0, None
    last_green = {g: 0 for g in GROUPS}
    rows, switches, green = [], 0, {g: 0 for g in GROUPS}
    for t, (s, counts) in enumerate(seconds):
        demand = {g: sum(counts[a] for a in axes) for g, axes in GROUPS.items()}
        if yellow > 0:
            phase, decision, yellow = "yellow", "-", yellow - 1
            if yellow == 0:
                cur, t0 = target, t + 1
        else:
            wait = {g: (s - last_green[g]) if demand[g] > 0 else 0 for g in GROUPS if g != cur}
            nxt = choose(cur, t - t0, demand, wait)
            phase, decision = cur, "keep"
            green[cur] += 1; last_green[cur] = s
            if nxt:
                decision, target, yellow, switches = f"switch to {nxt}", nxt, YELLOW, switches + 1
        rows.append(dict(second=s, **{k: round(v, 1) for k, v in counts.items()},
                         demand_NS=round(demand["NS"], 1), demand_EW=round(demand["EW"], 1), green=phase, decision=decision))
    return rows, switches, green


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("counts", nargs="?", default="../data/lane_counts.json")
    p.add_argument("--out", default="../evaluation/vision_replay_decisions.csv")
    p.add_argument("--start", choices=list(GROUPS), default="NS")
    a = p.parse_args()
    sec = load_per_second(a.counts)
    rows, sw, green = replay(sec, a.start)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} seconds of camera counts -> {sw} switch(es). Green seconds: {green} (a fixed timer would split about evenly)")
    avg = {k: round(sum(r[k] for r in rows) / len(rows), 1) for k in ("demand_NS", "demand_EW")}
    print("average demand:", avg)
    for r in rows:
        if r["decision"].startswith("switch"):
            print(f"  t={r['second']} s: {r['decision']} (NS {r['demand_NS']} vs EW {r['demand_EW']})")
    print("Decisions written to", a.out)
