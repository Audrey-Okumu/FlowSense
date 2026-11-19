# FlowSense: adaptive traffic signals for urban congestion

## Problem
Most urban traffic lights run on fixed, pre-programmed timers. They cannot tell a jammed road from an empty one, so green time is wasted while queues grow. This costs time, fuel and air quality.

## Solution
FlowSense is a signal controller that watches the queue on every approach and adapts the signal timing in real time. Cameras with a vehicle-detection model (YOLO) supply vehicle counts per approach; the controller uses them to decide which road gets green and for how long.

## How we tested it
- Simulator: SUMO, one signalised 4-way junction (3 lanes in, left-hand traffic, zebra crossings).
- Traffic: mixed fleet of cars, matatus, boda-bodas, trucks and buses, with random arrivals.
- Scenarios (one simulated hour each): normal, rush hour, uneven demand.
- Fair comparison: the fixed timer (90 s cycle, equal split) and FlowSense run on identical traffic and the same random seeds. Results are averages of 3 seeds.
- Safety limits: minimum green 8 s, maximum green 60 s, yellow always kept, any road waiting more than about 90 s is served next.

## Results (average of 3 seeds)
| Scenario | Avg wait, fixed | Avg wait, FlowSense | Longest wait, fixed | Longest wait, FlowSense |
|---|---|---|---|---|
| Normal | 18.8 s | 2.8 s | 66 s | 32 s |
| Rush hour | 27.8 s | 17.4 s | 262 s | 129 s |
| Uneven | 22.9 s | 3.6 s | 134 s | 74 s |

## Demo
Open `flowsense_demo.html` in any browser (it works offline). It replays two real simulation runs side by side on identical traffic: the fixed timer on the left, FlowSense on the right.

## Limits
- This is a simulation of one junction, not a field trial. Results will not transfer exactly to real roads.
- No pedestrians, cyclists or emergency vehicles are simulated yet.
- The vision demo uses sample footage, not Nairobi traffic.

## Next steps
Pilot with real camera data at one junction, add emergency-vehicle priority, coordinate several junctions, and compare against a demand-tuned fixed timer.
