@echo off
setlocal

set "PROJECT_ROOT=D:\Desktop\Workspace\Automatic-Email-Responder"

echo [INFO] 启动后端...
start "AER Backend" cmd /k "call conda activate MIS && python %PROJECT_ROOT%\backend\app.py"

echo [INFO] 启动前端...
start "AER Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"

echo [DONE] 前后端已在新窗口启动。
