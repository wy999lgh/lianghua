"""Web API 模块

此模块提供Web API相关功能，包括路由定义、请求/响应模型等。
"""

from api.app import api_router, register_routes

__all__ = [
    'api_router',
    'register_routes',
]
