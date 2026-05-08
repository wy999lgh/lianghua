#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动后端服务"""
from api.app import create_app
import uvicorn

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("后端服务已启动！")
    print("地址: http://localhost:8003")
    print("API文档: http://localhost:8003/docs")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
