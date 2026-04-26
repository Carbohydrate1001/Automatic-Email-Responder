@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo   Debug Version - Testing Commands
echo ============================================================
echo.
echo ROOT directory: %ROOT%
echo.

echo Testing Python...
python --version
if errorlevel 1 (
  echo [ERROR] Python check failed
  pause
  exit /b 1
)

echo Testing npm...
npm --version
if errorlevel 1 (
  echo [ERROR] npm check failed
  pause
  exit /b 1
)

echo.
echo Checking paths...
echo Backend path: %ROOT%\backend
echo Frontend path: %ROOT%\frontend
echo.

if exist "%ROOT%\backend" (
  echo [OK] Backend directory exists
) else (
  echo [ERROR] Backend directory not found
)

if exist "%ROOT%\frontend" (
  echo [OK] Frontend directory exists
) else (
  echo [ERROR] Frontend directory not found
)

echo.
echo Testing start command...
echo About to open backend window...
start "Test Backend" cmd /k "echo Backend window opened && cd /d "%ROOT%\backend" && echo Current dir: && cd && pause"

timeout /t 3 /nobreak >nul

echo About to open frontend window...
start "Test Frontend" cmd /k "echo Frontend window opened && cd /d "%ROOT%\frontend" && echo Current dir: && cd && pause"

echo.
echo [DONE] Check if two new windows opened
pause
endlocal
