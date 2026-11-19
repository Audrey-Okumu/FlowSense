"""Rebuild demo/flowsense_demo.html (3 scenario tabs). Easiest: run make_demo.bat"""
import json
S = ["normal", "rush_hour", "uneven"]
r = {s: json.load(open(f"results/replay_{s}.json")) for s in S}
d = {"net": r["uneven"]["net"], "stats": json.load(open("results/compare.json")),
     "scen": {s: {"fixed": r[s]["fixed"], "flowsense": r[s]["flowsense"], "types": r[s]["types"]} for s in S}}
html = open("demo_template.html").read().replace("/*DATA*/null", json.dumps(d, separators=(",", ":")))
open("../demo/flowsense_demo.html", "w").write(html); print("wrote ../demo/flowsense_demo.html")
