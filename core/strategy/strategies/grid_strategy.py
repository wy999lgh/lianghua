#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网格交易策略
功能：基于网格交易算法实现自动买卖
"""

from datetime import datetime
from typing import Dict, Any, Optional

from core.strategy.base_strategy import BaseStrategy


class GridTradingStrategy(BaseStrategy):
    """
    网格交易策略类
    
    基于基准价和涨跌幅计算上下网格线，当价格突破网格线时生成交易信号。
    """

    DEFAULT_CONFIG = {
        'symbol': '',                      # 交易标的
        'initial_base_price': 10.0,        # 初始基准价
        'buy_percent': 0.01,               # 下跌买入百分比
        'sell_percent': 0.01,              # 上涨卖出百分比
        'buy_amount': 100,                 # 下跌买入量
        'sell_amount': 100,                # 上涨卖出量
        'max_position': 10000,             # 最大持仓数量
        'min_position': 1000,              # 最小底仓数量
        'price_range': [8.0, 12.0],        # 价格区间
        'commission_rate': 0.0001,         # 手续费率
        'slippage': 0.001,                 # 滑点
    }
    
    PARAM_DESCRIPTIONS = {
        'symbol': {'name': '交易标的', 'desc': '要交易的股票或ETF代码，如 159633'},
        'initial_base_price': {'name': '初始基准价', 'desc': '网格的基准价格，作为计算上下网格线的基础'},
        'buy_percent': {'name': '下跌买入百分比', 'desc': '价格下跌该百分比时触发买入信号，默认0.01表示1%'},
        'sell_percent': {'name': '上涨卖出百分比', 'desc': '价格上涨该百分比时触发卖出信号，默认0.01表示1%'},
        'buy_amount': {'name': '下跌买入量', 'desc': '每次下跌买入的数量'},
        'sell_amount': {'name': '上涨卖出量', 'desc': '每次上涨卖出的数量'},
        'max_position': {'name': '最大持仓数量', 'desc': '允许持有的最大数量上限'},
        'min_position': {'name': '最小底仓数量', 'desc': '必须持有的最小底仓数量'},
        'price_range': {'name': '价格区间', 'desc': '交易价格区间，超出此范围策略暂停', 'format': 'array'},
        'commission_rate': {'name': '手续费率', 'desc': '交易手续费率，默认0.0001表示万分之一'},
        'slippage': {'name': '滑点', 'desc': '预计的买卖滑点，默认0.001表示0.1%'}
    }

    def __init__(self, name: str = "grid_trading", description: str = ""):
        if not description:
            description = "网格交易策略：基于基准价和涨跌幅计算网格线，自动买卖"
        if name == "temp":
            name = "grid_trading"
        super().__init__(name=name, description=description)
        
        self.config = self.DEFAULT_CONFIG.copy()
        self.version = "1.0.0"
        
        # 状态变量
        self.last_signal = None
        self.last_trade_price = None
        self.highest_price = self.config['initial_base_price']
        self.lowest_price = self.config['initial_base_price']

    def update_price(self, price: float, datetime: Optional[datetime] = None) -> Dict:
        """更新价格并生成交易信号"""
        base_price = self.config['initial_base_price']
        buy_percent = self.config['buy_percent']
        sell_percent = self.config['sell_percent']
        
        signal = 'hold'
        
        # 检测买入信号
        if price <= base_price * (1 - buy_percent):
            signal = 'buy'
            self.last_signal = 'buy'
            self.last_trade_price = price
            
        # 检测卖出信号
        elif price >= base_price * (1 + sell_percent):
            signal = 'sell'
            self.last_signal = 'sell'
            self.last_trade_price = price
            
        return {
            'signal': signal,
            'price': price,
            'base_price': base_price,
            'timestamp': datetime or datetime.now()
        }

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if isinstance(config, dict):
            self.config.update(config)
