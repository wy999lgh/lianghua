"""API路由注册中心

此模块提供统一的路由注册功能，使用 FastAPI 的 include_router 组织所有子路由。
"""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from api.routers import data, strategies, backtest, system, factors

# 创建主路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(system.router, tags=["系统"])
api_router.include_router(data.router, tags=["数据管理"])
api_router.include_router(strategies.router, tags=["策略配置"])
api_router.include_router(backtest.router, tags=["回测"])
api_router.include_router(factors.router, prefix="/factors", tags=["因子管理"])


def register_routes(app: FastAPI) -> None:
    """注册所有路由到 FastAPI app

    Args:
        app: FastAPI 应用实例
    """
    app.include_router(api_router, prefix="/api")


def setup_cors(app: FastAPI) -> None:
    """配置 CORS 策略

    Args:
        app: FastAPI 应用实例
    """
    origins = [
        "http://localhost:5173",
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ]
    allow_credentials = True
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Authorization", "Content-Type", "*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )


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

    # 配置 CORS
    setup_cors(app)

    # 注册路由
    register_routes(app)

    return app


app = create_app()
