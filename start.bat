@echo off
title Deck - Browser Stream Deck
cd /d "%~dp0"

echo Checking port 8765...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Installing dependencies...
pip install -r requirements.txt -q

echo.
python run.py
pause