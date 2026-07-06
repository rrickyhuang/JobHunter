@echo off
REM Launch the JobHunter web cockpit, bound to all interfaces so phones and
REM other devices on the same Wi-Fi can reach it at http://<PC-LAN-IP>:5001.
REM Requires a one-time Windows Firewall rule allowing inbound TCP 5001
REM (see the phone-access note in the README / run the netsh command once).
cd /d "%~dp0.."
start "" http://127.0.0.1:5001
py serve.py --host 0.0.0.0
