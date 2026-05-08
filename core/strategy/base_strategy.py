#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略基类
功能：定义所有交易策略的统一接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseStrategy(ABC):
    """
    交易策略基类

    所有交易策略都应该继承此类并实现抽象方法
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化策略

        参数：
        - name: 策略名称
        - description: 策略描述
        """
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.version = "1.0.0"

        # 策略配置
        self.config: Dict[str, Any] = {}

        # 交易记录
        self.trade_records: List[Dict] = []

        # 当前持仓
        self.current_position = 0.0

        # 当前基准价格
        self.base_price = 0.0

        # 性能统计
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_commission': 0.0
        }

    @abstractmethod
    def update_price(self, price: float, datetime: Optional[datetime] = None) -> Dict:
        """
        更新价格并生成交易信号

        参数：
        - price: 当前价格
        - datetime: 日期时间（可选）

        返回：
        Dict - 包含交易结果和当前状态的字典
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        获取策略配置

        返回：
        Dict[str, Any] - 策略配置字典
        """
        pass

    @abstractmethod
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        设置策略配置

        参数：
        - config: 策略配置字典
        """
        pass

    def reset(self) -> None:
        """
        重置策略状态
        """
        self.trade_records = []
        self.current_position = 0.0
        self.base_price = 0.0
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_commission': 0.0
        }

    def get_trade_records(self) -> List[Dict]:
        """
        获取交易记录

        返回：
        List[Dict] - 交易记录列表
        """
        return self.trade_records

    def get_performance(self) -> Dict[str, Any]:
        """
        获取策略性能统计

        返回：
        Dict[str, Any] - 性能统计字典
        """
        perf = self.performance.copy()

        # 计算胜率
        if perf['total_trades'] > 0:
            perf['win_rate'] = perf['winning_trades'] / perf['total_trades']
        else:
            perf['win_rate'] = 0.0

        # 计算盈亏比
        if perf['losing_trades'] > 0:
            perf['profit_factor'] = abs(
                perf['total_profit']) / max(1, abs(perf['total_profit'] - perf['winning_trades'] * 10))
        else:
            perf['profit_factor'] = float('inf')

        return perf

    def get_info(self) -> Dict[str, Any]:
        """
        获取策略信息

        返回：
        Dict[str, Any] - 策略信息字典
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'config': self.get_config(),
            'current_position': self.current_position,
            'base_price': self.base_price
        }

    def _record_trade(self, signal: str, price: float, amount: float,
                      position: float, commission: float = 0.0,
                      profit: float = 0.0) -> None:
        """
        记录一笔交易

        参数：
        - signal: 交易信号 ('buy' 或 'sell')
        - price: 交易价格
        - amount: 交易数量
        - position: 交易后持仓
        - commission: 手续费
        - profit: 利润（仅卖出时）
        """
        trade = {
            'datetime': datetime.now(),
            'signal': signal,
            'price': price,
            'amount': amount,
            'position': position,
            'commission': commission
        }

        self.trade_records.append(trade)

        # 更新性能统计
        self.performance['total_trades'] += 1
        self.performance['total_commission'] += commission

        if signal == 'sell' and profit > 0:
            self.performance['winning_trades'] += 1
            self.performance['total_profit'] += profit
        elif signal == 'sell' and profit <= 0:
            self.performance['losing_trades'] += 1
            self.performance['total_profit'] += profit
