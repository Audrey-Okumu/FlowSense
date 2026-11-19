# controller/

| File | What it does |
|---|---|
| `rule_based.py` | The FlowSense brain. `choose()` is the decision rule; `Flow` applies it to the SUMO signal |
| `tuned_fixed.py` | Fair baseline: a fixed timer whose N/S vs E/W green split is set from the scenario's average demand |
| `vision_input.py` | Camera-fed mode: runs the same `choose()` rule on the Vision Lead's counts file |

## Run (from the `simulation` folder)
    python run_flowsense.py all --seeds 3        fixed vs tuned fixed vs FlowSense, all scenarios -> results/compare.csv
    python run_flowsense.py rush_hour --seeds 3  one scenario
    python run_flowsense.py rush_hour --only flowsense --gui   watch FlowSense live in SUMO

## Run (from the `controller` folder)
    python vision_input.py ..\data\lane_counts.json          camera counts -> decisions -> ..\evaluation\vision_replay_decisions.csv

## Rules (settings at the top of rule_based.py)
- Minimum green 8 s, maximum green 60 s, yellow always kept
- Any vehicle waiting more than 90 s forces its phase next
- Switch early when the served road empties and another has cars waiting
- Switch when another road's demand >= 2 x current demand + 3

## Status
- Done: adaptive controller, tuned fixed-time baseline, camera-input replay
- To do: sensitivity table (vary min/max green and the switch threshold), ambulance priority, RL (stretch)
