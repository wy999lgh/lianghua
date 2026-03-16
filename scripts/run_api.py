"""启动后端API服务

此脚本用于启动FastAPI后端服务，提供网格交易策略的API接口。
"""

import uvicorn
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # 启动Uvicorn服务器
    uvicorn.run(
        "web.backend.api:app",
        host="0.0.0.0",  # 允许所有IP访问
        port=8000,       # 服务端口
        reload=True,     # 开发模式下启用热重载
        log_level="info"  # 日志级别
    )
