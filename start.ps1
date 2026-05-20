# AI量化交易系统启动脚本
Write-Host "=========================================="
Write-Host "      AI量化交易系统 - 启动脚本"
Write-Host "=========================================="
Write-Host ""

# 创建并激活虚拟环境
$venvPath = ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "[1/4] 创建Python虚拟环境..."
    if (Test-Path $venvPath) {
        Remove-Item -Recurse -Force $venvPath
    }
    python -m venv $venvPath
    Write-Host "[成功] 虚拟环境创建完成"
} else {
    Write-Host "[1/4] 虚拟环境已存在"
}

Write-Host "[2/4] 安装依赖..."
& $activateScript
pip install -q fastapi uvicorn psycopg2-binary pandas numpy scipy
Write-Host "[成功] 依赖安装完成"

# 启动后端服务
Write-Host "[3/4] 启动后端服务..."
$backendCmd = "cd d:\AI量化999; .venv\Scripts\Activate.ps1; python app.py"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $backendCmd

Start-Sleep -Seconds 3

# 启动前端服务
Write-Host "[4/4] 启动前端服务..."
$frontendCmd = "cd d:\AI量化999\frontend; npm run dev"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $frontendCmd

Write-Host ""
Write-Host "=========================================="
Write-Host "          服务启动完成！"
Write-Host "=========================================="
Write-Host ""
Write-Host "后端服务: http://localhost:8000"
Write-Host "前端服务: http://localhost:3000"
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")