# FlowSense

AI-powered adaptive traffic signal control. FlowSense uses computer vision (YOLO) and reinforcement learning to adjust traffic lights to real-time demand, and tests them against fixed-timer lights in the SUMO simulator.

## The idea
Camera sees traffic → software decides which road gets green and for how long → we measure the result against a fixed-timer light.

## Folder structure

| Folder | What goes here | Owner |
|---|---|---|
| `simulation/` | SUMO intersection, traffic scenarios, fixed-time baseline, metrics logging | Simulation Lead |
| `vision/` | YOLO vehicle detection and counting on traffic video | Vision Lead |
| `controller/` | Rule-based controller and RL agent, connected to SUMO via TraCI | Controller Lead |
| `evaluation/` | Comparison scripts, charts, results | Evaluation & Pitch Lead |
| `data/` | Small sample files only (large videos go on the shared Drive link) | Everyone |
| `docs/` | Data format spec, notes, pitch material | Everyone |

## How the parts connect
Vision outputs vehicle counts per lane → Controller reads them and picks the next signal phase → Simulation runs it → Evaluation compares results.

The agreed data format is in `docs/data_format.md`:
```json
{"timestamp": 12.5, "lanes": {"north": 12, "south": 3, "east": 7, "west": 2}}
```

## Getting started
1. Install Python 3.10+ and Git
2. Clone the repo: `git clone <repo-url>`
3. Install dependencies: `pip install -r requirements.txt`
4. Install SUMO from https://sumo.dlr.de/docs/Downloads.php and make sure `sumo` runs in your terminal
5. Work only in your own role's folder

## How to contribute
```bash
git checkout main
git pull
git checkout -b <role>/<task>     # e.g. vision/yolo-counting
# make your changes
git add .
git commit -m "Short clear message"
git push -u origin <role>/<task>
```
Then open a Pull Request on GitHub. A teammate reviews it and merges it. Never push directly to `main`.

## Rules
- Pull before you start work at any time
- Keep commits small, with clear messages
- Large files (videos, models) go on the shared Drive link, not in git
- Stuck? Ask in the group chat before running risky commands like `git push --force`

## Team
See `docs/team.md`.