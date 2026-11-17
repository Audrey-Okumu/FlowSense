# simulation/ - FlowSense SUMO setup

| File | Purpose |
|---|---|
| intersection.nod.xml / .edg.xml | Source of the road network: 4-way junction, 3 lanes in / 2 out per approach, 300 m arms |
| intersection.net.xml | Built network (left-hand traffic, 4-phase signal, 90 s cycle) |
| generate_demand.py | Creates traffic for 3 scenarios (normal, rush_hour, uneven) with a mixed fleet: cars in several colours, matatus, boda-bodas, trucks, buses |
| generate_scenery.py / scenery.add.xml | Visual only: buildings and trees around the junction (python generate_scenery.py) |
| routes_*.rou.xml | Generated traffic files |
| flowsense.sumocfg | SUMO config (1 simulated hour) |
| run_baseline.py | Runs the fixed-time baseline, logs queues and waiting time, prints a summary |
| results/ | CSV + tripinfo outputs (do not commit) |

## Run
    netconvert --node-files=intersection.nod.xml --edge-files=intersection.edg.xml -o intersection.net.xml --lefthand --tls.layout=opposites --tls.left-green.time=8 --tls.cycle.time=90 --sidewalks.guess --sidewalks.guess.max-speed 15 --crossings.guess true --crossings.guess.speed-threshold 15
    python generate_demand.py
    python run_baseline.py rush_hour --gui     (watch it)
    python run_baseline.py all                 (all scenarios, headless, writes results/summary_fixed.csv)
    python run_baseline.py all --seeds 3       (3 random seeds + averaged table in results/summary_fixed_avg.csv)

"Retrying in 1 seconds" messages are normal: TraCI is waiting for SUMO to start.

## FlowSense controller and demo
| File | Purpose |
|---|---|
| run_flowsense.py | Adaptive controller (rules: min green 8 s, max 60 s, yellow kept, anyone waiting >90 s served next). `python run_flowsense.py all --seeds 3` runs fixed timer vs FlowSense and writes results/compare.csv |
| demo_template.html, build_demo.py | Side-by-side replay page. Run `python run_flowsense.py uneven --replay 1000 1300` then `python build_demo.py` |
