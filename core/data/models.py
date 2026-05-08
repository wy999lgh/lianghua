# -*- coding: utf-8 -*-
"""
网格交易系统 - 数据模型定义
Data models for the grid trading system
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List


@dataclass
class StockBasic:
    """股票基本信息"""
    symbol: str
    name: str
    market: str
    industry: str
    list_date: Optional[date] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'market': self.market,
            'industry': self.industry,
            'list_date': self.list_date.isoformat() if self.list_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StockBasic':
        """从字典创建实例"""
        list_date = data.get('list_date')
        if list_date and isinstance(list_date, str):
            list_date = date.fromisoformat(list_date)
        return cls(
            symbol=data['symbol'],
            name=data['name'],
            market=data['market'],
            industry=data['industry'],
            list_date=list_date,
        )


@dataclass
class DailyPrice:
    """日线行情数据"""
    symbol: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    adj_factor: Optional[float] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'trade_date': self.trade_date.isoformat() if isinstance(self.trade_date, date) else self.trade_date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'adj_factor': self.adj_factor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DailyPrice':
        """从字典创建实例"""
        trade_date = data.get('trade_date')
        if trade_date and isinstance(trade_date, str):
            trade_date = date.fromisoformat(trade_date)
        return cls(
            symbol=data['symbol'],
            trade_date=trade_date,
            open=float(data['open']),
            high=float(data['high']),
            low=float(data['low']),
            close=float(data['close']),
            volume=int(data['volume']),
            amount=float(data['amount']),
            adj_factor=data.get('adj_factor'),
        )


@dataclass
class FactorData:
    """因子数据"""
    symbol: str
    trade_date: date
    factor_name: str
    factor_value: float
    source: str = ''

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'trade_date': self.trade_date.isoformat() if isinstance(self.trade_date, date) else self.trade_date,
            'factor_name': self.factor_name,
            'factor_value': self.factor_value,
            'source': self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FactorData':
        """从字典创建实例"""
        trade_date = data.get('trade_date')
        if trade_date and isinstance(trade_date, str):
            trade_date = date.fromisoformat(trade_date)
        return cls(
            symbol=data['symbol'],
            trade_date=trade_date,
            factor_name=data['factor_name'],
            factor_value=float(data['factor_value']),
            source=data.get('source', ''),
        )


@dataclass
class StrategyConfig:
    """策略配置"""
    id: Optional[int] = None
    symbol: str = ''
    base_price: float = 0.0
    upper_step: float = 0.0
    lower_step: float = 0.0
    upper_count: int = 0
    lower_count: int = 0
    max_position: float = 0.0
    min_position: float = 0.0
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'base_price': self.base_price,
            'upper_step': self.upper_step,
            'lower_step': self.lower_step,
            'upper_count': self.upper_count,
            'lower_count': self.lower_count,
            'max_position': self.max_position,
            'min_position': self.min_position,
            'created_at': self.created_at,
        }


@dataclass
class BacktestResult:
    """回测结果"""
    id: Optional[int] = None
    config_id: Optional[int] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    trade_count: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: Optional[str] = None
    symbol: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'total_return': self.total_return,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'trade_count': self.trade_count,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at,
            'symbol': self.symbol,
        }


@dataclass
class TradeRecord:
    """交易记录"""
    id: Optional[int] = None
    config_id: Optional[int] = None
    datetime: str = ''
    signal: str = ''  # buy/sell
    price: float = 0.0
    amount: float = 0.0
    position: float = 0.0
    commission: float = 0.0
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'datetime': self.datetime,
            'signal': self.signal,
            'price': self.price,
            'amount': self.amount,
            'position': self.position,
            'commission': self.commission,
            'created_at': self.created_at,
        }
