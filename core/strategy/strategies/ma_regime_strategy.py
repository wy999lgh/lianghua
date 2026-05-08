#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线牛熊策略
功能：基于均线交叉判断市场牛熊市
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

import pandas as pd

from core.strategy.base_strategy import BaseStrategy


class MARegimeStrategy(BaseStrategy):
    """
    均线牛熊策略类
    
    使用短期均线和长期均线交叉来判断市场状态：
    - 短期均线上穿长期均线：牛市信号
    - 短期均线下穿长期均线：熊市信号
    """

    DEFAULT_CONFIG = {
        'symbol': '',              # 交易标的
        'short_window': 50,        # 短期均线窗口
        'long_window': 200,        # 长期均线窗口
        'signal_threshold': 0.001, # 信号阈值
    }
    
    PARAM_DESCRIPTIONS = {
        'symbol': {'name': '交易标的', 'desc': '要交易的股票或ETF代码，如 159633'},
        'short_window': {'name': '短期均线窗口', 'desc': '短期均线计算周期，默认50日均线'},
        'long_window': {'name': '长期均线窗口', 'desc': '长期均线计算周期，默认200日均线'},
        'signal_threshold': {'name': '信号阈值', 'desc': '均线交叉信号的阈值，避免频繁切换'}
    }

    def __init__(self, name: str = "ma_regime", description: str = ""):
        if not description:
            description = "均线牛熊策略：基于50/200日均线交叉判断市场牛熊状态"
        if name == "temp":
            name = "ma_regime"
        super().__init__(name=name, description=description)
        
        self.config = self.DEFAULT_CONFIG.copy()
        self.version = "1.0.0"
        
        # 价格缓冲区
        self.price_buffer: List[float] = []
        self.last_regime = "neutral"

    def update_price(self, price: float, datetime: Optional[datetime] = None) -> Dict:
        """更新价格并生成交易信号"""
        self.price_buffer.append(price)
        
        short_window = self.config['short_window']
        long_window = self.config['long_window']
        
        # 确保有足够的数据
        if len(self.price_buffer) < long_window:
            return {
                'signal': 'neutral',
                'regime': 'neutral',
                'reason': f'样本不足，需要{long_window}条数据',
                'price': price,
                'timestamp': datetime or datetime.now()
            }
        
        # 计算均线
        prices = pd.Series(self.price_buffer)
        short_ma = prices.rolling(window=short_window).mean().iloc[-1]
        long_ma = prices.rolling(window=long_window).mean().iloc[-1]
        
        # 判断状态
        if short_ma > long_ma * (1 + self.config['signal_threshold']):
            regime = 'bull'
            signal = 'buy'
        elif short_ma < long_ma * (1 - self.config['signal_threshold']):
            regime = 'bear'
            signal = 'sell'
        else:
            regime = 'neutral'
            signal = 'hold'
            
        self.last_regime = regime
        
        return {
            'signal': signal,
            'regime': regime,
            'price': price,
            'short_ma': float(short_ma),
            'long_ma': float(long_ma),
            'timestamp': datetime or datetime.now()
        }

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if isinstance(config, dict):
            self.config.update(config)
