#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险控制模块
功能：提供交易风险管理功能，包括止损、仓位限制、风险阈值检查等
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np


class RiskControl:
    """
    风险控制类

    功能：
    - 止损控制：当亏损达到阈值时触发止损
    - 仓位限制：限制单次交易和总仓位的比例
    - 风险阈值检查：综合评估交易风险
    - 信号过滤：根据风险规则过滤交易信号
    """

    def __init__(self, stop_loss: float = 0.05,
                 position_limit: float = 0.2,
                 risk_threshold: float = 0.1,
                 max_daily_trades: int = 10,
                 max_drawdown: float = 0.15):
        """
        初始化风险控制器

        参数：
        - stop_loss: 止损比例，默认5%
        - position_limit: 单次仓位限制，默认20%
        - risk_threshold: 风险阈值，默认10%
        - max_daily_trades: 每日最大交易次数，默认10次
        - max_drawdown: 最大回撤限制，默认15%
        """
        self.stop_loss = stop_loss
        self.position_limit = position_limit
        self.risk_threshold = risk_threshold
        self.max_daily_trades = max_daily_trades
        self.max_drawdown = max_drawdown

        # 交易统计
        self.daily_trades: Dict[str, int] = {}  # 按日期统计交易次数
        self.entry_prices: List[float] = []  # 入场价格记录
        self.peak_value: float = 0.0  # 峰值（用于计算回撤）
        self.current_value: float = 0.0  # 当前价值

        # 风险状态
        self.risk_status = {
            'stop_loss_triggered': False,
            'position_limit_exceeded': False,
            'risk_threshold_exceeded': False,
            'max_trades_reached': False,
            'max_drawdown_exceeded': False
        }

    def apply(self, signals: List[Dict[str, Any]],
              data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        应用所有风险控制规则

        参数：
        - signals: 交易信号列表
        - data: 市场数据和账户数据

        返回：
        List[Dict] - 过滤后的交易信号列表
        """
        # 依次应用各种风险控制
        signals = self.apply_stop_loss(signals, data)
        signals = self.apply_position_limit(signals, data)
        signals = self.check_risk_threshold(signals, data)
        signals = self.apply_daily_trade_limit(signals)
        signals = self.apply_drawdown_limit(signals, data)

        return signals

    def apply_stop_loss(self, signals: List[Dict[str, Any]],
                        data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        应用止损控制

        参数：
        - signals: 交易信号列表
        - data: 包含当前价格和持仓成本的数据

        返回：
        List[Dict] - 过滤后的信号列表
        """
        filtered_signals = []

        current_price = data.get('current_price', 0)
        avg_cost = data.get('avg_cost', 0)
        current_position = data.get('current_position', 0)

        for signal in signals:
            # 如果有持仓且当前价格低于止损价
            if current_position > 0 and avg_cost > 0:
                loss_ratio = (avg_cost - current_price) / avg_cost

                if loss_ratio >= self.stop_loss:
                    # 触发止损，强制卖出
                    self.risk_status['stop_loss_triggered'] = True
                    stop_loss_signal = {
                        'signal': 'sell',
                        'price': current_price,
                        'amount': current_position,
                        'reason': 'stop_loss',
                        'timestamp': datetime.now()
                    }
                    filtered_signals.append(stop_loss_signal)
                    continue

            # 如果是买入信号，检查是否在止损恢复期
            if signal.get('signal') == 'buy' and self.risk_status['stop_loss_triggered']:
                # 止损后暂停买入
                continue

            filtered_signals.append(signal)

        return filtered_signals

    def apply_position_limit(self, signals: List[Dict[str, Any]],
                             data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        应用仓位限制

        参数：
        - signals: 交易信号列表
        - data: 包含账户总值和当前仓位的数据

        返回：
        List[Dict] - 调整后的信号列表
        """
        if data is None:
            return signals

        filtered_signals = []

        total_value = data.get('total_value', 0)
        current_position_value = data.get('current_position_value', 0)

        for signal in signals:
            if signal.get('signal') == 'buy' and total_value > 0:
                # 计算买入后的仓位比例
                buy_amount = signal.get('amount', 0)
                buy_price = signal.get('price', 0)
                buy_value = buy_amount * buy_price

                new_position_ratio = (
                    current_position_value + buy_value) / total_value

                if new_position_ratio > self.position_limit:
                    # 调整买入数量以符合仓位限制
                    max_buy_value = total_value * self.position_limit - current_position_value
                    if max_buy_value > 0 and buy_price > 0:
                        adjusted_amount = int(max_buy_value / buy_price)
                        if adjusted_amount > 0:
                            signal = signal.copy()
                            signal['amount'] = adjusted_amount
                            signal['adjusted'] = True
                            signal['original_amount'] = buy_amount
                            filtered_signals.append(signal)
                    self.risk_status['position_limit_exceeded'] = True
                    continue

            filtered_signals.append(signal)

        return filtered_signals

    def check_risk_threshold(self, signals: List[Dict[str, Any]],
                             data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查风险阈值

        参数：
        - signals: 交易信号列表
        - data: 市场数据

        返回：
        List[Dict] - 过滤后的信号列表
        """
        filtered_signals = []

        # 获取市场波动率数据
        volatility = data.get('volatility', 0)

        for signal in signals:
            # 如果市场波动率超过风险阈值，暂停交易
            if volatility > self.risk_threshold:
                self.risk_status['risk_threshold_exceeded'] = True
                # 仅保留卖出信号（允许减仓）
                if signal.get('signal') == 'sell':
                    filtered_signals.append(signal)
                continue

            filtered_signals.append(signal)

        return filtered_signals

    def apply_daily_trade_limit(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用每日交易次数限制

        参数：
        - signals: 交易信号列表

        返回：
        List[Dict] - 过滤后的信号列表
        """
        today = datetime.now().strftime('%Y-%m-%d')
        current_trades = self.daily_trades.get(today, 0)

        if current_trades >= self.max_daily_trades:
            self.risk_status['max_trades_reached'] = True
            return []

        # 限制信号数量
        remaining_trades = self.max_daily_trades - current_trades
        return signals[:remaining_trades]

    def apply_drawdown_limit(self, signals: List[Dict[str, Any]],
                             data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        应用最大回撤限制

        参数：
        - signals: 交易信号列表
        - data: 账户数据

        返回：
        List[Dict] - 过滤后的信号列表
        """
        current_value = data.get('total_value', 0)

        # 更新峰值
        if current_value > self.peak_value:
            self.peak_value = current_value

        self.current_value = current_value

        # 计算当前回撤
        if self.peak_value > 0:
            drawdown = (self.peak_value - current_value) / self.peak_value

            if drawdown >= self.max_drawdown:
                self.risk_status['max_drawdown_exceeded'] = True
                # 回撤超限，仅保留卖出信号
                return [s for s in signals if s.get('signal') == 'sell']

        return signals

    def record_trade(self, trade: Dict[str, Any]) -> None:
        """
        记录交易（用于统计）

        参数：
        - trade: 交易记录
        """
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1

        if trade.get('signal') == 'buy':
            self.entry_prices.append(trade.get('price', 0))

    def get_risk_status(self) -> Dict[str, Any]:
        """
        获取当前风险状态

        返回：
        Dict - 风险状态字典
        """
        # 计算当前回撤
        current_drawdown = 0
        if self.peak_value > 0:
            current_drawdown = (
                self.peak_value - self.current_value) / self.peak_value

        return {
            **self.risk_status,
            'current_drawdown': round(current_drawdown, 4),
            'peak_value': self.peak_value,
            'current_value': self.current_value,
            'daily_trades_today': self.daily_trades.get(
                datetime.now().strftime('%Y-%m-%d'), 0
            )
        }

    def reset_status(self) -> None:
        """重置风险状态"""
        self.risk_status = {
            'stop_loss_triggered': False,
            'position_limit_exceeded': False,
            'risk_threshold_exceeded': False,
            'max_trades_reached': False,
            'max_drawdown_exceeded': False
        }

    def reset_daily(self) -> None:
        """重置每日统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = 0
        self.risk_status['max_trades_reached'] = False

    def reset_all(self) -> None:
        """完全重置"""
        self.daily_trades.clear()
        self.entry_prices.clear()
        self.peak_value = 0.0
        self.current_value = 0.0
        self.reset_status()

    def update_config(self, **kwargs) -> None:
        """
        更新风控配置

        参数：
        - stop_loss: 止损比例
        - position_limit: 仓位限制
        - risk_threshold: 风险阈值
        - max_daily_trades: 每日最大交易次数
        - max_drawdown: 最大回撤
        """
        if 'stop_loss' in kwargs:
            self.stop_loss = kwargs['stop_loss']
        if 'position_limit' in kwargs:
            self.position_limit = kwargs['position_limit']
        if 'risk_threshold' in kwargs:
            self.risk_threshold = kwargs['risk_threshold']
        if 'max_daily_trades' in kwargs:
            self.max_daily_trades = kwargs['max_daily_trades']
        if 'max_drawdown' in kwargs:
            self.max_drawdown = kwargs['max_drawdown']

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前风控配置

        返回：
        Dict - 配置字典
        """
        return {
            'stop_loss': self.stop_loss,
            'position_limit': self.position_limit,
            'risk_threshold': self.risk_threshold,
            'max_daily_trades': self.max_daily_trades,
            'max_drawdown': self.max_drawdown
        }

    def calculate_position_size(self, price: float, total_value: float,
                                risk_per_trade: float = 0.02) -> int:
        """
        计算建议的仓位大小

        参数：
        - price: 当前价格
        - total_value: 账户总值
        - risk_per_trade: 每笔交易风险比例，默认2%

        返回：
        int - 建议的交易数量
        """
        if price <= 0 or total_value <= 0:
            return 0

        # 基于风险的仓位计算
        risk_amount = total_value * risk_per_trade
        stop_loss_amount = price * self.stop_loss

        if stop_loss_amount > 0:
            position_size = int(risk_amount / stop_loss_amount)
        else:
            position_size = int(total_value * self.position_limit / price)

        # 确保不超过仓位限制
        max_position = int(total_value * self.position_limit / price)

        return min(position_size, max_position)
