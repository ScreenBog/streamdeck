@echo off
cd /d "%~dp0"
pip install -r requirements.txt -q >nul 2>&1
python run.py