@echo off
echo Starting backend and frontend...
start "Backend (uvicorn)" "%~dp0start-backend.bat"
start "Frontend (vite dev)" "%~dp0start-frontend.bat"

echo Waiting for servers to start...
timeout /t 5 /nobreak > nul

start "" "http://localhost:5173"
