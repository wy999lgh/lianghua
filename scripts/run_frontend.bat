@echo off

rem 启动前端开发服务器

echo 正在启动前端开发服务器...
echo 请稍候，正在加载依赖...

cd /d "%~dp0..\web\frontend"

rem 检查是否安装了依赖
if not exist node_modules (  
    echo 未检测到依赖，正在安装...
    npm install
    if %errorlevel% neq 0 (
        echo 依赖安装失败，请检查网络连接和package.json文件
        pause
        exit /b 1
    )
    echo 依赖安装成功！
)

rem 启动开发服务器
echo 启动前端开发服务器...
npm run dev

pause
