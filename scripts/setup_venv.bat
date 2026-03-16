@echo off

rem 创建并设置虚拟环境

echo ===============================
echo 网格交易量化策略系统 - 虚拟环境设置
echo ===============================
echo.

rem 切换到项目根目录
cd /d "%~dp0.."

rem 检查Python是否安装
echo 检查Python安装状态...
python --version
if %errorlevel% neq 0 (
    echo 错误：Python未安装，请先安装Python 3.8+
    pause
    exit /b 1
)
echo Python安装正常！
echo.

rem 删除旧的虚拟环境（如果存在）
if exist .venv (
    echo 检测到旧的虚拟环境，正在删除...
    rd /s /q .venv
    if %errorlevel% neq 0 (
        echo 警告：删除旧虚拟环境失败，可能正在使用中
        echo 将尝试在现有环境中安装依赖
    ) else (
        echo 旧虚拟环境删除成功！
    )
    echo.
)

rem 创建新的虚拟环境
echo 创建新的虚拟环境...
python -m venv .venv
if %errorlevel% neq 0 (
    echo 错误：创建虚拟环境失败
    pause
    exit /b 1
)
echo 虚拟环境创建成功！
echo.

rem 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo 错误：激活虚拟环境失败
    pause
    exit /b 1
)
echo 虚拟环境激活成功！
echo.

rem 升级pip
echo 升级pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo 警告：升级pip失败，但将继续安装依赖
)
echo.

rem 安装项目依赖
echo 安装项目依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误：安装依赖失败
    pause
    exit /b 1
)
echo 依赖安装成功！
echo.

rem 显示完成信息
echo ===============================
echo 虚拟环境设置完成！
echo ===============================
echo 可用命令：
echo 1. 启动后端API服务: python scripts/run_api.py
echo 2. 启动前端服务: scripts\run_frontend.bat
echo 3. 测试API: python test_api.py
echo.
echo 注意：请在激活的虚拟环境中运行以上命令

echo 按任意键退出...
pause
