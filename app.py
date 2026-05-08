"""
AI量化交易系统 - FastAPI 主应用入口

此模块作为应用的统一入口点，创建并配置 FastAPI 应用实例。
"""
from fastapi import FastAPI

from api.app import register_routes, setup_cors


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用

    Returns:
        配置完成的 FastAPI 应用实例
    """
    app = FastAPI(
        title="网格交易量化策略系统API",
        description="提供网格交易策略的配置、回测和监控功能",
        version="1.0.0"
    )

    # 配置 CORS 策略
    setup_cors(app)

    # 注册所有路由
    register_routes(app)

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
