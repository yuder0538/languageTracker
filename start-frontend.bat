@echo off
cd /d "%~dp0frontend"
call npm run dev -- --port 5173 --strictPort
echo.
echo Frontend stopped (closed, or an error happened above - scroll up to check).
pause
