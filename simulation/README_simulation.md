# simulation/ - FlowSense SUMO setup

| File | Purpose |
|---|---|
| intersection.nod.xml / .edg.xml | Source of the road network: 4-way junction, 3 lanes in / 2 out per approach, 300 m arms |
| intersection.net.xml | Built network (left-hand traffic, 4-phase signal, 90 s cycle) |
| generate_demand.py | Creates traffic for 3 scenarios (normal, rush_hour, uneven) with a mixed fleet: cars in several colours, matatus, boda-bodas, trucks, buses |
| generate_scenery.py / scenery.add.xml | Visual only: buildings and trees around the junction (python generate_scenery.py) |
| routes_*.rou.xml | Generated traffic files |
| flowsense.sumocfg | SUMO config (1 simulated hour) |
| run_baseline.py | Fixed-time baseline only: logs queues and waiting time, prints a summary |
| run_flowsense.py | Runs the controller modes (fixed, tuned, flowsense) on the scenarios and compares them. Controller logic lives in ../controller/ |
| run_side_by_side.bat | Opens two SUMO windows on identical traffic: fixed timer (left) vs FlowSense (right) |
| make_demo.bat, build_demo.py, demo_template.html | Rebuild the results and the demo page (../demo/flowsense_demo.html) |
| results/ | CSV + tripinfo outputs (do not commit) |

## Scenarios and controller modes
| Scenarios | What it is |
|---|---|
| normal | steady traffic on every road |
| rush_hour | demand ramps up, peaks, then eases |
| uneven | north and south busy, east and west quiet |

| Controller modes | What it is |
|---|---|
| fixed | today's light: 90 s cycle, equal split, never changes |
| tuned | still a fixed timer, but the N/S vs E/W split is set from the scenario's average demand (fair rival) |
| flowsense | adaptive: reads queues each second and adjusts green time |

## Run (all commands from this folder, SUMO and `pip install -r ../requirements.txt` done)
**Everything: all scenarios x all controller modes, 3 seeds, writes results/compare.csv (a few minutes)**

    python run_flowsense.py all --seeds 3

**One scenario, all controller modes** (normal | rush_hour | uneven)

    python run_flowsense.py rush_hour --seeds 3

**One scenario, one controller mode** (fixed | tuned | flowsense)

    python run_flowsense.py uneven --only flowsense --seeds 3

**Watch it live in SUMO**

    python run_flowsense.py uneven --only fixed --gui
    python run_flowsense.py uneven --only flowsense --gui
    run_side_by_side.bat uneven          (both windows at once, same traffic)

In the SUMO window, "real world" colours are set automatically; press Play if it is paused. "Retrying in 1 seconds" is normal while SUMO starts.

**Fixed-timer baseline only**

    python run_baseline.py all --seeds 3

**Camera-fed mode** (from ../controller): `python vision_input.py ..\data\lane_counts.json`

## Rebuild the map, traffic and demo page
    netconvert --node-files=intersection.nod.xml --edge-files=intersection.edg.xml -o intersection.net.xml --lefthand --tls.layout=opposites --tls.left-green.time=8 --tls.cycle.time=90 --sidewalks.guess --sidewalks.guess.max-speed 15 --crossings.guess true --crossings.guess.speed-threshold 15
    python generate_demand.py
    python generate_scenery.py
    make_demo.bat                        (results + 3 replays + ../demo/flowsense_demo.html)
