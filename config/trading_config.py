# -*- coding: utf-8 -*-
"""
网格交易系统 - 交易配置模块
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

import yaml


def _get_project_root() -> Path:
    return Path(__file__).parent.parent.resolve()


def _load_yaml_config() -> dict:
    config_path = _get_project_root() / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


@dataclass
class CommissionConfig:
    """手续费配置"""
    rate: float = 0.0001  # ETF: 0.10 permille
    min_fee: float = 0.1  # Min 0.1 yuan

    def calculate(self, trade_amount: float) -> float:
        fee = trade_amount * self.rate
        return max(fee, self.min_fee)


@dataclass
class SlippageConfig:
    """滑点配置"""
    rate: float = 0.001
    enabled: bool = True

    def apply(self, price: float, is_buy: bool) -> float:
        if not self.enabled:
            return price
        if is_buy:
            return round(price * (1 - self.rate), 4)
        else:
            return round(price * (1 + self.rate), 4)


@dataclass
class TradingConfig:
    """交易配置类"""
    commission: CommissionConfig = field(default_factory=CommissionConfig)
    slippage: SlippageConfig = field(default_factory=SlippageConfig)

    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "TradingConfig":
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = _load_yaml_config()

        trading_config = config.get('trading', {})
        commission_config = trading_config.get('commission', {})
        slippage_config = trading_config.get('slippage', {})

        return cls(
            commission=CommissionConfig(
                rate=commission_config.get('rate', 0.0001),
                min_fee=commission_config.get('min_fee', 0.1),
            ),
            slippage=SlippageConfig(
                rate=slippage_config.get('rate', 0.001),
                enabled=slippage_config.get('enabled', True),
            ),
        )

    def calculate_commission(self, price: float, quantity: float) -> float:
        trade_amount = price * quantity
        return self.commission.calculate(trade_amount)

    def apply_slippage(self, price: float, is_buy: bool) -> float:
        return self.slippage.apply(price, is_buy)


@dataclass
class GridDefaultConfig:
    """网格策略默认参数配置"""
    buy_percent: float = 0.01
    sell_percent: float = 0.01
    buy_amount: int = 100
    sell_amount: int = 100
    upper_count: int = 100
    lower_count: int = 100
    max_position: int = 10000
    min_position: int = 1000
    update_method: str = "trigger_price"

    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "GridDefaultConfig":
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = _load_yaml_config()

        grid_config = config.get('grid_default', {})

        return cls(
            buy_percent=grid_config.get('buy_percent', 0.01),
            sell_percent=grid_config.get('sell_percent', 0.01),
            buy_amount=grid_config.get('buy_amount', 100),
            sell_amount=grid_config.get('sell_amount', 100),
            upper_count=grid_config.get('upper_count', 100),
            lower_count=grid_config.get('lower_count', 100),
            max_position=grid_config.get('max_position', 10000),
            min_position=grid_config.get('min_position', 1000),
            update_method=grid_config.get('update_method', "trigger_price"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'buy_percent': self.buy_percent,
            'sell_percent': self.sell_percent,
            'buy_amount': self.buy_amount,
            'sell_amount': self.sell_amount,
            'upper_count': self.upper_count,
            'lower_count': self.lower_count,
            'max_position': self.max_position,
            'min_position': self.min_position,
            'update_method': self.update_method,
        }

    def create_strategy_config(
        self,
        initial_base_price: float,
        price_range: Optional[List[float]] = None,
        **overrides
    ) -> Dict[str, Any]:
        config = self.to_dict()
        config['initial_base_price'] = initial_base_price

        if price_range:
            config['price_range'] = price_range
        else:
            config['price_range'] = [
                initial_base_price * 0.5,
                initial_base_price * 1.5
            ]

        config.update(overrides)
        return config


_trading_config: Optional[TradingConfig] = None
_grid_default_config: Optional[GridDefaultConfig] = None


def get_trading_config(reload: bool = False) -> TradingConfig:
    global _trading_config
    if _trading_config is None or reload:
        _trading_config = TradingConfig.from_yaml()
    return _trading_config


def get_grid_default_config(reload: bool = False) -> GridDefaultConfig:
    global _grid_default_config
    if _grid_default_config is None or reload:
        _grid_default_config = GridDefaultConfig.from_yaml()
    return _grid_default_config


def get_commission_rate() -> float:
    return get_trading_config().commission.rate


def get_min_commission() -> float:
    return get_trading_config().commission.min_fee


if __name__ == "__main__":
    trading_config = get_trading_config()
    print(f"Commission rate: {trading_config.commission.rate}")
    print(f"Min commission: {trading_config.commission.min_fee}")

    grid_config = get_grid_default_config()
    print(f"Grid defaults: {grid_config.to_dict()}")
