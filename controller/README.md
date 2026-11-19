# controller/

The FlowSense adaptive controller logic is in `rule_based.py` (class `Flow`, plus the settings MIN_G, MAX_G, YELLOW, STARVE at the top).
`simulation/run_flowsense.py` is the runner that loads the SUMO junction and calls this controller.

Run (from the simulation folder): `python run_flowsense.py all --seeds 3`

## Rules
- Minimum green 8 s, maximum green 60 s, yellow always kept
- Switch early when the served road empties and another has cars waiting
- Switch when another road's demand is at least 2x the current one + 3
- Any vehicle waiting more than 90 s forces its phase next

## Controller Lead to do
- Tune MIN_G, MAX_G and the switch threshold, and record a sensitivity table here
- Hook up camera input in the agreed JSON format
- Optional: tuned fixed-time baseline, ambulance priority, RL agent
