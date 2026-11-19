# FlowSense simulation specification

Everything below is what every controller (fixed-time, rule-based, RL) is tested on. Same map, same traffic, same seeds.

## Junction
- One 4-way signalised junction (SUMO node `center`), arms 300 m long, speed limit 50 km/h (13.9 m/s)
- Each approach: 3 lanes in, 2 lanes out. Left-hand traffic (Kenya)
- Pavements and zebra crossings are drawn for realism. **No pedestrians are simulated**, so crossings have no effect on traffic
- Built from `intersection.nod.xml` + `intersection.edg.xml` with the `netconvert` command in `simulation/README_simulation.md`

## Baseline signal (fixed-time)
- 90 s cycle, equal split, never changes: N/S through (26 s + 5 s clearance), N/S turning (8 s), E/W through (26 s + 5 s), E/W turning (8 s), 3 s yellow after each green
- This is a representative fixed-timer plan. It is not copied from a real Nairobi signal plan

## Traffic
| Vehicle | Share | Length | Top speed | Notes |
|---|---|---|---|---|
| Cars (5 colours/body shapes) | 55% | 4.3-4.8 m | 50 km/h | |
| Matatu | 15% | 6.0 m | 45 km/h | slower acceleration |
| Boda-boda | 15% | 2.2 m | 50 km/h | quickest acceleration |
| Truck | 10% | 7.5 m | 40 km/h | slow |
| Bus | 5% | 12 m | 40 km/h | slowest |

Each driver's speed also varies about +/-12% around the type's top speed. Arrivals are random (Poisson-style). Turning: 60% straight, 20% left, 20% right.

## Scenarios (1 simulated hour each; vehicles per hour per approach)
| Scenario | Demand |
|---|---|
| normal | steady 500 on every approach |
| rush_hour | 250 for 10 min, then 850 (x1.7) for 30 min, then 300; N and S 20% heavier than E and W |
| uneven | N about 950, S about 750, E and W about 150 each |

## Fairness rules
- Same random seeds for every controller: 42, 43, 44 (`--seeds 3`)
- Results are reported as the average over the seeds
- Safety limits for any adaptive controller: minimum green 8 s, maximum green 60 s, yellow always kept, no approach waits more than about 90 s

## Metrics
- **avg_wait_s**: average seconds a vehicle spends nearly stopped (waitingTime)
- **max_wait_s**: longest wait of any single vehicle
- **avg_time_loss_s**: extra trip time versus driving at full speed
- **avg_total_queue**: average number of stopped vehicles on all four approaches
- **max_single_road_queue**: biggest queue on any one approach

## Baseline results (fixed-time, average of 3 seeds)
| Scenario | Avg wait (s) | Longest wait (s) | Avg time loss (s) | Avg total queue | Longest queue on one road |
|---|---|---|---|---|---|
| normal | 18.8 | 66.3 | 27.4 | 9.9 | 15.3 |
| rush_hour | 27.8 | 262.3 | 40.0 | 18.5 | 38.7 |
| uneven | 22.9 | 134.3 | 33.3 | 12.3 | 25.7 |

## Not covered (be honest in the pitch)
- Simulation results will not transfer perfectly to real roads
- No pedestrians, cyclists or emergency vehicles
- One junction only. Coordinating several junctions is future work
