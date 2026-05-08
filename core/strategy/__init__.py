#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略模块
包含网格交易策略、持仓管理、风险控制等核心组件
"""

from core.strategy.base_strategy import BaseStrategy
from core.strategy.grid_strategy import GridStrategy, DynamicGridStrategy, TrendGridStrategy
from core.strategy.position_manager import PositionManager, BasePriceManager
from core.strategy.strategy_manager import StrategyManager, get_strategy_manager
from core.strategy.risk_control import RiskControl
from core.strategy.strategies import TrendResonanceRegimeStrategy

__all__ = [
    'BaseStrategy',
    'GridStrategy',
    'DynamicGridStrategy',
    'TrendGridStrategy',
    'PositionManager',
    'BasePriceManager',
    'StrategyManager',
    'get_strategy_manager',
    'RiskControl',
    'TrendResonanceRegimeStrategy',
]
