"""FastAPI后端API服务

此模块创建并配置FastAPI应用，设置CORS策略，并包含所有API路由。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web.backend.routes import router

# 创建FastAPI应用实例
app = FastAPI(
    title="网格交易量化策略系统API",
    description="提供网格交易策略的配置、回测和监控功能",
    version="1.0.0"
)

# 配置CORS策略，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(router)

# 根路径
@app.get("/")
def read_root():
    """根路径，返回API信息"""
    return {
        "message": "网格交易量化策略系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 健康检查端点
@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "healthy"}
