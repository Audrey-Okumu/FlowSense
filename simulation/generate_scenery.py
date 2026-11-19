"""Generate background scenery (grass, pavement, buildings, trees) around the junction.

Writes scenery.add.xml, which flowsense.sumocfg loads. Purely visual: it does not
change traffic results. Run:  python generate_scenery.py
"""
import random

random.seed(7)
ARM = 300          # arm length (m), must match intersection.nod.xml
ROAD_HALF = 15     # pavement half-width around the road centre line
polys, pois = [], []


def rect(x1, y1, x2, y2):
    return f"{x1:.1f},{y1:.1f} {x2:.1f},{y1:.1f} {x2:.1f},{y2:.1f} {x1:.1f},{y2:.1f}"


def add_poly(pid, kind, color, layer, shape):
    polys.append(f'  <poly id="{pid}" type="{kind}" color="{color}" fill="1" layer="{layer}" shape="{shape}"/>')


# Ground and pavement
#add_poly("ground", "landuse", "126,160,98", -30, rect(-ARM - 150, -ARM - 150, ARM + 150, ARM + 150))
#add_poly("pave_ns", "pavement", "196,192,184", -20, rect(-ROAD_HALF, -ARM, ROAD_HALF, ARM))
#add_poly("pave_ew", "pavement", "196,192,184", -20, rect(-ARM, -ROAD_HALF, ARM, ROAD_HALF))

# Buildings: rows facing the roads in each quadrant
PALETTE = ["178,164,150", "196,178,160", "160,150,142", "205,190,170", "170,128,108",
           "150,160,170", "188,170,150", "214,200,182"]
n = 0
for sx in (-1, 1):
    for sy in (-1, 1):
        # rows along the east-west road (depth directions away from it)
        for row_y, depth in ((ROAD_HALF + 14, 26), (ROAD_HALF + 14 + 26 + 18, 30)):
            x = ROAD_HALF + 18
            while x < ARM - 20:
                w = random.uniform(22, 44)
                d = depth + random.uniform(-5, 8)
                x2 = min(x + w, ARM + 20)
                xa, xb = sorted((sx * x, sx * x2))
                ya, yb = sorted((sy * row_y, sy * (row_y + d)))
                n += 1
                add_poly(f"b{n}", "building", random.choice(PALETTE), -10, rect(xa, ya, xb, yb))
                x = x2 + random.uniform(5, 14)
        # rows along the north-south road
        for row_x, depth in ((ROAD_HALF + 14, 26),):
            y = ROAD_HALF + 18 + 60   # leave the first block to the other row
            while y < ARM - 20:
                w = random.uniform(22, 44)
                d = depth + random.uniform(-5, 8)
                y2 = min(y + w, ARM + 20)
                ya, yb = sorted((sy * y, sy * y2))
                xa, xb = sorted((sx * row_x, sx * (row_x + d)))
                n += 1
                add_poly(f"b{n}", "building", random.choice(PALETTE), -10, rect(xa, ya, xb, yb))
                y = y2 + random.uniform(5, 14)

# Trees along the pavement edges
t = 0
for side in (-1, 1):
    for pos in range(-ARM + 20, ARM - 10, 16):
        for axis in ("ns", "ew"):
            if abs(pos) < ROAD_HALF + 12:
                continue
            off = side * (ROAD_HALF + 4.5 + random.uniform(-1, 1))
            p = pos + random.uniform(-4, 4)
            x, y = (off, p) if axis == "ns" else (p, off)
            size = random.uniform(6, 9)
            t += 1
            g = random.choice(["52,118,56", "64,132,64", "44,104,50", "78,140,70"])
            pois.append(f'  <poi id="tree{t}" type="tree" color="{g}" x="{x:.1f}" y="{y:.1f}" '
                        f'width="{size:.1f}" height="{size:.1f}" layer="4"/>')

with open("scenery.add.xml", "w") as f:
    f.write("<additional>\n" + "\n".join(polys + pois) + "\n</additional>\n")
print(f"wrote scenery.add.xml ({n} buildings, {t} trees)")
