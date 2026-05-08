"""路由模块

包含所有分类的API路由。
"""

from api.routers import data, strategies, backtest, system, factors

__all__ = [
    'data',
    'strategies',
    'backtest',
    'system',
    'factors',
]
