@echo off
REM Launch the JobHunter web cockpit and open it in the browser.
cd /d "%~dp0.."
start "" http://127.0.0.1:5001
py serve.py
