"""Generate realistic traffic demand for FlowSense.

Writes one routes_<scenario>.rou.xml per scenario with:
  - a mixed fleet (cars, matatus, buses, trucks, boda-bodas)
  - time-varying arrival rates (Poisson-style arrivals)
  - turning movements (60% straight, 20% each side turn)

Usage:  python generate_demand.py
"""

# ---- Vehicle mix (probabilities should sum to 1) ----
VTYPES = [
    # id,        class,        shape,                 len, maxSpeed, accel, decel, color,         prob
    ("car_blue",   "passenger",  "passenger/hatchback", 4.3, 13.9, 2.6, 4.5, "40,110,200",  0.14),
    ("car_white",  "passenger",  "passenger/sedan",     4.6, 13.9, 2.6, 4.5, "235,235,235", 0.15),
    ("car_silver", "passenger",  "passenger/hatchback", 4.3, 13.9, 2.6, 4.5, "175,178,185", 0.13),
    ("car_red",    "passenger",  "passenger/sedan",     4.6, 13.9, 2.6, 4.5, "190,40,40",   0.07),
    ("car_black",  "passenger",  "passenger/wagon",     4.8, 13.9, 2.6, 4.5, "35,35,40",    0.06),
    ("matatu",     "bus",        "passenger/van",       6.0, 12.5, 2.0, 4.0, "245,200,20",  0.15),
    ("boda",       "motorcycle", "motorcycle",          2.2, 13.9, 3.5, 5.0, "220,60,120",  0.15),
    ("truck",      "truck",      "delivery",            7.5, 11.0, 1.6, 3.5, "130,90,60",   0.10),
    ("bus",        "bus",        "bus",           12.0, 11.0, 1.4, 3.5, "30,150,90",   0.05),
]

# ---- Scenarios ----
# base_vph = vehicles/hour entering from each approach at multiplier 1.0
# profile  = (start_s, end_s, multiplier)   -> demand changes over time
# weights  = per-approach multiplier (uneven demand)
SIM_END = 3600
SCENARIOS = {
    "normal": {
        "base_vph": 500,
        "profile": [(0, SIM_END, 1.0)],
        "weights": {"N": 1.0, "S": 1.0, "E": 1.0, "W": 1.0},
    },
    "rush_hour": {
        "base_vph": 500,
        "profile": [(0, 600, 0.5), (600, 2400, 1.7), (2400, SIM_END, 0.6)],
        "weights": {"N": 1.2, "S": 1.2, "E": 1.0, "W": 1.0},
    },
    "uneven": {
        "base_vph": 500,
        "profile": [(0, SIM_END, 1.0)],
        "weights": {"N": 1.9, "S": 1.5, "E": 0.3, "W": 0.3},
    },
}

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}
TURN_SPLIT = {"straight": 0.6, "side_a": 0.2, "side_b": 0.2}


def destinations(origin):
    straight = OPPOSITE[origin]
    others = [d for d in "NSEW" if d not in (origin, straight)]
    return [(straight, TURN_SPLIT["straight"]),
            (others[0], TURN_SPLIT["side_a"]),
            (others[1], TURN_SPLIT["side_b"])]


def write_scenario(name, cfg):
    lines = ['<routes>']
    lines.append('  <vTypeDistribution id="mix">')
    for vid, vcls, shape, ln, ms, ac, dc, col, p in VTYPES:
        lines.append(
            f'    <vType id="{vid}" vClass="{vcls}" guiShape="{shape}" length="{ln}" '
            f'maxSpeed="{ms}" speedFactor="normc(1.0,0.12,0.7,1.3)" accel="{ac}" decel="{dc}" '
            f'sigma="0.5" color="{col}" probability="{p}"/>')
    lines.append('  </vTypeDistribution>')

    for o in "NSEW":
        for d, _ in destinations(o):
            lines.append(f'  <route id="{o}_{d}" edges="{o}_in {d}_out"/>')

    # flows sorted by start time (SUMO requirement)
    for (t0, t1, mult) in cfg["profile"]:
        for o in "NSEW":
            vph_origin = cfg["base_vph"] * mult * cfg["weights"][o]
            for d, share in destinations(o):
                prob = vph_origin * share / 3600.0
                lines.append(
                    f'  <flow id="f_{o}_{d}_{t0}" route="{o}_{d}" type="mix" '
                    f'begin="{t0}" end="{t1}" probability="{prob:.5f}" '
                    f'departLane="best" departSpeed="max"/>')
    lines.append('</routes>')
    with open(f"routes_{name}.rou.xml", "w") as f:
        f.write("\n".join(lines))
    print(f"wrote routes_{name}.rou.xml")


if __name__ == "__main__":
    for n, c in SCENARIOS.items():
        write_scenario(n, c)
