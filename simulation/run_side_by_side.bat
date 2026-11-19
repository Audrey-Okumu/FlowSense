@echo off
rem Opens two SUMO windows on identical traffic: fixed timer (left) vs FlowSense (right).
rem Usage: run_side_by_side.bat [normal|rush_hour|uneven]
set SC=%1
if "%SC%"=="" set SC=uneven
start "FIXED TIMER" python run_flowsense.py %SC% --only fixed --gui --end 900 --delay 50
start "FLOWSENSE" python run_flowsense.py %SC% --only flowsense --gui --end 900 --delay 50
