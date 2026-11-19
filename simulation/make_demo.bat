@echo off
rem Rebuilds results and the demo page: all scenarios, all controller modes, 3 replays, demo page.
python run_flowsense.py all --seeds 3
python run_flowsense.py normal --replay 1000 1300
copy /y results\replay.json results\replay_normal.json >nul
python run_flowsense.py rush_hour --replay 1200 1500
copy /y results\replay.json results\replay_rush_hour.json >nul
python run_flowsense.py uneven --replay 1000 1300
copy /y results\replay.json results\replay_uneven.json >nul
python build_demo.py
