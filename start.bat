@echo off
chcp 65001 >nul
title AI量化交易系统启动脚本

echo ================================================
echo          AI量化交易系统 - 启动脚本
echo ================================================
echo.

set "VENV_PATH=.venv"
set "VENV_ACTIVATE=%VENV_PATH%\Scripts\Activate.ps1"

:: 检查虚拟环境是否存在
if not exist "%VENV_ACTIVATE%" (
    echo [1/4] 创建Python虚拟环境...
    rmdir /s /q "%VENV_PATH%" 2>nul
    python -m venv "%VENV_PATH%"
    
    if not exist "%VENV_ACTIVATE%" (
        echo [警告] 虚拟环境创建失败，使用系统Python启动...
        set "USE_SYSTEM_PYTHON=1"
    ) else (
        echo [成功] 虚拟环境创建完成
        set "USE_SYSTEM_PYTHON=0"
    )
) else (
    echo [1/4] 虚拟环境已存在
    set "USE_SYSTEM_PYTHON=0"
)

:: 安装依赖
if "%USE_SYSTEM_PYTHON%"=="0" (
    echo [2/4] 安装/更新依赖包...
    call "%VENV_PATH%\Scripts\activate.bat"
    pip install -q fastapi uvicorn psycopg2-binary pandas numpy scipy
    echo [成功] 依赖安装完成
)

:: 启动后端服务
echo [3/4] 启动后端服务...
if "%USE_SYSTEM_PYTHON%"=="1" (
    start "后端服务" cmd /k "cd /d d:\AI量化999 && python start_server.py"
) else (
    start "后端服务" cmd /k "cd /d d:\AI量化999 && call .venv\Scripts\activate.bat && python start_server.py"
)

:: 等待后端启动
echo [4/4] 等待后端服务启动...
timeout /t 3 /nobreak >nul

:: 启动前端服务
echo [5/5] 启动前端服务...
start "前端服务" cmd /k "cd /d d:\AI量化999\frontend && npm run dev"

echo.
echo ================================================
echo          服务启动完成！
echo ================================================
echo.
echo 后端服务: http://localhost:8001
echo 前端服务: http://localhost:3000
echo.
echo 按任意键退出...
pause