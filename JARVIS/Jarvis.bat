@echo off
cd /d "%~dp0"
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "Start-Process python3 -ArgumentList 'main.py' -Verb RunAs"