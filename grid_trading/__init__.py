"""
网格交易量化策略系统

主要模块:
- data: 数据加载和处理模块
- strategy: 网格策略实现模块
- backtest: 回测引擎模块
- db: 数据库管理模块
- web: Web API和服务模块
"""

__version__ = "1.0.0"
__author__ = "Grid Trading System"

# 导入主要模块
from . import data
from . import strategy
from . import backtest
from . import db
