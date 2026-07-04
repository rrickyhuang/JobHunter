@echo off
cd /d "%~dp0"
"C:\Users\Ricky\AppData\Local\Programs\Python\Python311\python.exe" scrape.py --all --digest >> "%~dp0logs\daily_run.log" 2>&1
