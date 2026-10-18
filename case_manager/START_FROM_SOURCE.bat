@echo off
cd /d "%~dp0"
py -3 run_case_manager.py 2>nul || python run_case_manager.py
