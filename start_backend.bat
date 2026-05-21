@echo off
title FairHire AI Backend
cd /d "c:\Users\arpit.jain1\Downloads\fairhire-ai\fairhire-ai\backend"
echo ================================================
echo  FairHire AI Backend
echo  Running on http://127.0.0.1:8000
echo  Keep this window open. Press CTRL+C to stop.
echo ================================================
echo.
venv312\Scripts\python.exe run_server.py
pause
