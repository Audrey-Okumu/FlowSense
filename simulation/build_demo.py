"""Rebuild demo/flowsense_demo.html from fresh simulation results.
  python run_flowsense.py all --seeds 3
  python run_flowsense.py uneven --replay 1000 1300
  python build_demo.py
"""
import json
d = json.load(open("results/replay.json"))
d["stats"] = json.load(open("results/compare.json")); d["flow"] = d["flowsense"]
html = open("demo_template.html").read().replace("/*DATA*/null", json.dumps(d, separators=(",", ":")))
open("../demo/flowsense_demo.html", "w").write(html); print("wrote ../demo/flowsense_demo.html")
