@echo off
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
uvicorn app.main:app --port 8000
echo.
echo Backend stopped (closed, or an error happened above - scroll up to check).
pause
