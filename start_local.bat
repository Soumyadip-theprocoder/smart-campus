@echo off
title Launching Smart Campus Local Environment...
echo =========================================
echo   Starting Smart Campus Local Environment
echo =========================================
echo.

cd /d "%~dp0"

echo [1/4] Ensuring PostgreSQL Database container is running...
docker compose up -d db

echo Waiting for database...
ping 127.0.0.1 -n 3 >nul

echo [2/4] Starting Django Backend Web Server...
start "Smart Campus - Backend" "%~dp0scripts\run_backend.bat"

echo [3/4] Starting Django Q Background Worker...
start "Smart Campus - Worker" "%~dp0scripts\run_worker.bat"

echo [4/4] Starting React Frontend...
start "Smart Campus - Frontend" "%~dp0scripts\run_frontend.bat"

echo.
echo =========================================
echo All services launched in separate windows!
echo Backend API:  http://127.0.0.1:8000
echo Frontend UI:  http://localhost:5173
echo.
echo Optional: To run the Face Recognition webcam engine, run:
echo   scripts\run_face_recognition.bat
echo =========================================
echo.
