@echo off
cd /d "%~dp0"
py scrape.py --all --digest >> "%~dp0logs\daily_run.log" 2>&1
