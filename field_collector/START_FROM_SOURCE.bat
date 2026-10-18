@echo off
cd /d "%~dp0"
py -3 run_collector.py 2>nul || python run_collector.py
