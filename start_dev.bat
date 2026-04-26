@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo   Automatic Email Responder - Dev Launcher
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found
  pause
  exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found
  pause
  exit /b 1
)

echo [INFO] Starting backend: http://127.0.0.1:5005
if exist "%ROOT%\backend\venv\Scripts\activate.bat" (
  start "AER Backend" cmd /k "cd /d "%ROOT%\backend" && call venv\Scripts\activate.bat && python app.py"
) else (
  start "AER Backend" cmd /k "cd /d "%ROOT%\backend" && python app.py"
)

timeout /t 2 /nobreak >nul

echo [INFO] Starting frontend: http://localhost:5173
start "AER Frontend" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"

echo.
echo [DONE] Services started in new windows
echo        Backend: http://127.0.0.1:5005
echo        Frontend: http://localhost:5173
echo.
endlocal
exit /b 0
