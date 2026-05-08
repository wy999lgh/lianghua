#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准策略接口定义
功能：定义策略脚本的标准接口和生命周期钩子，确保策略能够无缝集成到回测引擎
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Signal:
    """
    交易信号数据类
    """
    type: Literal['buy', 'sell', 'hold']
    price: float
    amount: float = 0.0
    timestamp: Optional[datetime] = None
    reason: Optional[str] = None
    confidence: float = 1.0


@dataclass
class StrategyState:
    """
    策略状态数据类
    """
    position: float = 0.0
    base_price: float = 0.0
    cash: float = 0.0
    equity: float = 0.0
    margin: float = 0.0


@dataclass
class StrategyConfig:
    """
    策略配置数据类
    """
    symbol: str = ""
    initial_capital: float = 100000.0
    commission_rate: float = 0.0001
    slippage_rate: float = 0.001
    params: Dict[str, Any] = field(default_factory=dict)


class IStandardStrategy(ABC):
    """
    标准策略接口

    所有策略必须实现此接口，以确保能够无缝集成到回测引擎。
    策略生命周期：
    1. __init__() - 初始化
    2. on_init() - 策略初始化钩子（在数据开始前调用）
    3. on_start() - 策略开始钩子（在第一次数据更新前调用）
    4. next() - 每根K线调用一次，生成交易信号
    5. update() - 更新策略状态（在信号执行后调用）
    6. on_stop() - 策略结束钩子
    7. stop() - 清理资源
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
        self.version = "2.0.0"
        self.created_at = datetime.now()
        
        # 策略配置
        self.config: StrategyConfig = StrategyConfig()
        
        # 策略状态
        self.state: StrategyState = StrategyState()
        
        # 交易记录
        self.trade_records: List[Dict] = []
        
        # 信号历史
        self.signal_history: List[Signal] = []
        
        # 是否已初始化
        self._initialized = False
        
        # 是否已启动
        self._started = False
        
        # 是否已停止
        self._stopped = False

    def on_init(self) -> None:
        """
        策略初始化钩子（可选）
        
        在数据开始前调用，用于初始化内部状态、加载预计算数据等
        """
        self._initialized = True

    def on_start(self) -> None:
        """
        策略开始钩子（可选）
        
        在第一次数据更新前调用，用于设置初始状态
        """
        self._started = True
        self.state.cash = self.config.initial_capital
        self.state.equity = self.config.initial_capital

    @abstractmethod
    def next(self, data: Dict[str, Any]) -> Optional[Signal]:
        """
        生成交易信号
        
        每根K线调用一次，基于输入数据生成交易信号
        
        参数：
        - data: 当前K线数据，包含：
                - datetime: 时间戳
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - amount: 成交额
                - factors: 因子数据（可选）
        
        返回：
        Optional[Signal] - 交易信号（买入/卖出/持有），None表示持有
        """
        pass

    def update(self, signal: Optional[Signal], executed_price: float, 
               executed_amount: float, commission: float) -> None:
        """
        更新策略状态（在信号执行后调用）
        
        参数：
        - signal: 原始信号
        - executed_price: 实际执行价格
        - executed_amount: 实际执行数量
        - commission: 手续费
        """
        if signal is None:
            return
        
        # 更新持仓
        if signal.type == 'buy':
            self.state.position += executed_amount
            self.state.cash -= executed_price * executed_amount + commission
        elif signal.type == 'sell':
            self.state.position -= executed_amount
            self.state.cash += executed_price * executed_amount - commission
        
        # 更新权益
        self.state.equity = self.state.cash + self.state.position * executed_price
        
        # 记录交易
        self._record_trade(
            signal=signal.type,
            price=executed_price,
            amount=executed_amount,
            position=self.state.position,
            commission=commission,
            timestamp=signal.timestamp
        )

    def on_stop(self) -> None:
        """
        策略结束钩子（可选）
        
        在回测结束后调用，用于清理资源、生成总结报告等
        """
        self._stopped = True

    def stop(self) -> None:
        """
        停止策略，清理资源
        """
        self.on_stop()

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
        self.state = StrategyState()
        self.trade_records = []
        self.signal_history = []
        self._initialized = False
        self._started = False
        self._stopped = False

    def get_trade_records(self) -> List[Dict]:
        """
        获取交易记录
        
        返回：
        List[Dict] - 交易记录列表
        """
        return self.trade_records

    def get_signal_history(self) -> List[Signal]:
        """
        获取信号历史
        
        返回：
        List[Signal] - 信号历史列表
        """
        return self.signal_history

    def get_state(self) -> StrategyState:
        """
        获取当前策略状态
        
        返回：
        StrategyState - 当前策略状态
        """
        return self.state

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
            'initialized': self._initialized,
            'started': self._started,
            'stopped': self._stopped,
            'config': self.get_config(),
            'state': {
                'position': self.state.position,
                'cash': self.state.cash,
                'equity': self.state.equity,
                'base_price': self.state.base_price
            }
        }

    def get_performance(self) -> Dict[str, Any]:
        """
        获取策略性能统计
        
        返回：
        Dict[str, Any] - 性能统计字典
        """
        total_trades = len(self.trade_records)
        winning_trades = sum(1 for t in self.trade_records if t.get('profit', 0) > 0)
        losing_trades = total_trades - winning_trades
        total_profit = sum(t.get('profit', 0) for t in self.trade_records)
        total_commission = sum(t.get('commission', 0) for t in self.trade_records)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_profit': total_profit,
            'total_commission': total_commission,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0.0,
            'profit_factor': abs(total_profit) / (abs(total_profit) + 1e-10) if total_profit != 0 else float('inf')
        }

    def _record_trade(self, signal: str, price: float, amount: float,
                      position: float, commission: float = 0.0,
                      timestamp: Optional[datetime] = None) -> None:
        """
        记录一笔交易
        
        参数：
        - signal: 交易信号 ('buy' 或 'sell')
        - price: 交易价格
        - amount: 交易数量
        - position: 交易后持仓
        - commission: 手续费
        - timestamp: 时间戳
        """
        trade = {
            'datetime': timestamp or datetime.now(),
            'signal': signal,
            'price': price,
            'amount': amount,
            'position': position,
            'commission': commission,
            'profit': 0.0  # 由回测引擎计算并填充
        }
        self.trade_records.append(trade)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} version={self.version!r}>"

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
