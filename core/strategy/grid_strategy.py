#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网格交易策略核心实现

此模块根据网格交易策略规则实现了完整的网格交易功能，包括网格计算、订单管理、风险控制等。
合并了v1（grid_trading）和v2（skill）两个版本的最佳功能。
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from core.strategy.position_manager import PositionManager, BasePriceManager


class GridStrategy:
    """
    网格交易策略核心逻辑类

    功能：
    - 网格价格计算：基于基准价和涨跌幅计算上下网格线
    - 信号生成：检测价格突破网格线并生成交易信号
    - 交易触发逻辑：上涨卖出、下跌买入、回落卖出、反弹买入
    - 委托价格计算：根据触发价格计算委托价
    - 数量计算：根据上涨卖出量和下跌买入量执行
    - 手续费估算：支持自定义手续费率
    - 倍数委托：支持多倍数量委托
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        初始化网格策略

        参数：
        config: dict - 策略配置参数
        **kwargs: 直接参数（兼容v2版本的参数形式）
        """
        # 默认配置
        default_config = {
            'symbol': '',                      # 交易标的
            'initial_base_price': 10.0,        # 初始基准价
            'buy_percent': 0.01,               # 每下跌1%买入（step_percent）
            'sell_percent': 0.01,              # 每上涨1%卖出
            'buy_amount': 100,                 # 下跌买入量
            'sell_amount': 100,                # 上涨卖出量
            'max_position': 10000,             # 最大持仓数量
            'min_position': 1000,              # 最小底仓数量
            'price_range': [8.0, 12.0],        # 价格区间 [lower, upper]
            'update_method': 'trigger_price',  # 基准价更新方式
            'commission_rate': 0.0001,         # 手续费率0.10‰（ETF佣金）
            'slippage': 0.001,                 # 滑点（默认0.1%）
            # v2版本高级功能
            'multiple_order': False,           # 是否启用倍数委托
            'fallback_sell': False,            # 是否启用回落卖出
            'fallback_percent': None,          # 回落百分比
            'rebound_buy': False,              # 是否启用反弹买入
            'rebound_percent': None,           # 反弹百分比
            'upper_count': 100,                # 向上网格数量
            'lower_count': 100,                # 向下网格数量
        }

        # 更新配置
        self.config = default_config.copy()
        if config:
            self.config.update(config)
        # 支持kwargs直接传参（v2兼容）
        if kwargs:
            self._apply_kwargs(kwargs)

        # 初始化持仓管理器和基准价管理器
        self.position_manager = PositionManager(
            max_position=self.config['max_position'],
            min_position=self.config['min_position']
        )

        self.base_price_manager = BasePriceManager(
            initial_base_price=self.config['initial_base_price'],
            update_method=self.config['update_method']
        )

        # 初始化状态变量
        self.trades: List[Dict] = []  # 交易记录
        self.last_signal: Optional[str] = None  # 上次交易信号
        self.last_trade_price: Optional[float] = None  # 上次交易价格
        self.last_trade_time: Optional[datetime] = None  # 上次交易时间

        # v2版本功能：价格极值跟踪（用于回落卖出和反弹买入）
        self.highest_price: float = self.config['initial_base_price']
        self.lowest_price: float = self.config['initial_base_price']

        # 策略状态: active, sleeping, stopped
        self.status: str = "active"

    def _apply_kwargs(self, kwargs: Dict[str, Any]) -> None:
        """应用kwargs参数到config（v2兼容）"""
        mapping = {
            'symbol': 'symbol',
            'base_price': 'initial_base_price',
            'upper_price': 'price_range',  # 特殊处理
            'lower_price': 'price_range',  # 特殊处理
            'step_percent': 'buy_percent',  # 同时设置buy和sell
            'buy_quantity': 'buy_amount',
            'sell_quantity': 'sell_amount',
            'max_holding': 'max_position',
            'min_holding': 'min_position',
        }

        for k, v in kwargs.items():
            if k in mapping:
                if k == 'upper_price':
                    self.config['price_range'][1] = v
                elif k == 'lower_price':
                    self.config['price_range'][0] = v
                elif k == 'step_percent':
                    self.config['buy_percent'] = v / 100 if v > 1 else v
                    self.config['sell_percent'] = v / 100 if v > 1 else v
                else:
                    self.config[mapping[k]] = v
            elif k in self.config:
                self.config[k] = v

    def calculate_grid_lines(self) -> Dict[str, List[float]]:
        """
        计算网格线价格

        返回：
        dict - 包含买入和卖出网格线的字典
        """
        base_price = self.base_price_manager.get_base_price()
        buy_percent = self.config['buy_percent']
        sell_percent = self.config['sell_percent']

        # 计算买入网格线（向下）- 限制数量
        buy_lines = []
        current_price = base_price
        max_lines = min(self.config.get('lower_count', 100), 1000)
        for _ in range(max_lines):
            current_price *= (1 - buy_percent)
            buy_lines.append(round(current_price, 4))

        # 计算卖出网格线（向上）- 限制数量
        sell_lines = []
        current_price = base_price
        max_lines = min(self.config.get('upper_count', 100), 1000)
        for _ in range(max_lines):
            current_price *= (1 + sell_percent)
            sell_lines.append(round(current_price, 4))

        return {
            'buy_lines': sorted(buy_lines, reverse=True),  # 从高到低排序
            'sell_lines': sorted(sell_lines)  # 从低到高排序
        }

    def _update_price_extremes(self, current_price: float) -> None:
        """更新价格极值（用于回落卖出和反弹买入）"""
        if current_price > self.highest_price:
            self.highest_price = current_price
        if current_price < self.lowest_price:
            self.lowest_price = current_price

    def _check_price_range(self, current_price: float) -> bool:
        """检查价格是否在设定的价格区间内"""
        price_range = self.config['price_range']
        return price_range[0] <= current_price <= price_range[1]

    def generate_signal(self, current_price: float,
                        timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成交易信号

        参数：
        current_price: float - 当前价格
        timestamp: datetime - 当前时间戳

        返回：
        dict - 交易信号，包含信号类型、价格、数量等信息
        """
        # 检查策略状态
        if self.status != "active":
            if self.status == "sleeping" and self._check_price_range(current_price):
                self.status = "active"
            else:
                return {'signal': 'strategy_inactive', 'price': current_price}

        # 更新价格极值
        self._update_price_extremes(current_price)

        # 计算网格线
        grid_lines = self.calculate_grid_lines()
        buy_lines = grid_lines['buy_lines']
        sell_lines = grid_lines['sell_lines']

        # 检查价格区间
        if not self._check_price_range(current_price):
            self.status = "sleeping"
            return {'signal': 'out_of_range', 'price': current_price}

        # 检查持仓限制
        if self.position_manager.is_max_position_reached():
            if buy_lines and current_price <= min(buy_lines):
                return {'signal': 'max_position_reached', 'price': current_price}

        if self.position_manager.is_min_position_reached():
            if sell_lines and current_price >= max(sell_lines):
                return {'signal': 'min_position_reached', 'price': current_price}

        # 检测买入信号
        for buy_line in buy_lines:
            if current_price <= buy_line:
                # 检查反弹买入条件
                if self.config['rebound_buy'] and self.config['rebound_percent']:
                    rebound_threshold = self.lowest_price * \
                        (1 + self.config['rebound_percent'] / 100)
                    if current_price < rebound_threshold:
                        break  # 不满足反弹条件

                # 检查是否为新的买入信号
                if self.last_signal != 'buy' or (self.last_trade_price and current_price < self.last_trade_price):
                    amount = self.config['buy_amount']

                    # 倍数委托处理
                    if self.config['multiple_order'] and self.config['buy_percent']:
                        base_price = self.base_price_manager.get_base_price()
                        price_change = (
                            base_price - current_price) / base_price * 100
                        multiple = max(
                            1, int(price_change / (self.config['buy_percent'] * 100)))
                        amount *= multiple

                    return {
                        'signal': 'buy',
                        'price': current_price,
                        'buy_line': buy_line,
                        'amount': amount,
                        'timestamp': timestamp or datetime.now()
                    }
                break

        # 检测卖出信号
        for sell_line in sell_lines:
            if current_price >= sell_line:
                # 检查回落卖出条件
                if self.config['fallback_sell'] and self.config['fallback_percent']:
                    fallback_threshold = self.highest_price * \
                        (1 - self.config['fallback_percent'] / 100)
                    if current_price > fallback_threshold:
                        break  # 不满足回落条件

                # 检查是否为新的卖出信号
                if self.last_signal != 'sell' or (self.last_trade_price and current_price > self.last_trade_price):
                    amount = self.config['sell_amount']

                    # 倍数委托处理
                    if self.config['multiple_order'] and self.config['sell_percent']:
                        base_price = self.base_price_manager.get_base_price()
                        price_change = (
                            current_price - base_price) / base_price * 100
                        multiple = max(
                            1, int(price_change / (self.config['sell_percent'] * 100)))
                        amount *= multiple

                    return {
                        'signal': 'sell',
                        'price': current_price,
                        'sell_line': sell_line,
                        'amount': amount,
                        'timestamp': timestamp or datetime.now()
                    }
                break

        # 无信号
        return {'signal': 'hold', 'price': current_price}

    def execute_trade(self, signal: Dict[str, Any], current_price: float,
                      timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        执行交易

        参数：
        signal: dict - 交易信号
        current_price: float - 当前价格
        timestamp: datetime - 当前时间戳

        返回：
        dict - 交易结果
        """
        if signal['signal'] not in ['buy', 'sell']:
            return {'status': 'no_trade', 'signal': signal['signal']}

        amount = signal['amount']

        # 检查持仓限制
        if signal['signal'] == 'buy':
            if not self.position_manager.check_position('buy', amount):
                return {'status': 'rejected', 'reason': 'max_position_exceeded'}
        else:
            if not self.position_manager.check_position('sell', amount):
                return {'status': 'rejected', 'reason': 'min_position_violation'}

        # 计算委托价格（考虑滑点）
        slippage = self.config.get('slippage', 0.001)
        if signal['signal'] == 'buy':
            order_price = round(current_price * (1 - slippage), 4)
        else:
            order_price = round(current_price * (1 + slippage), 4)

        # 计算手续费
        commission_rate = self.config.get('commission_rate', 0.0001)
        commission = order_price * amount * commission_rate
        commission = max(commission, 0.1)  # 不足0.1元按0.1元收取
        commission = round(commission, 2)

        # 更新持仓
        position_update = self.position_manager.update_position(
            amount, signal['signal'])
        if not position_update['success']:
            return {'status': 'rejected', 'reason': position_update['reason']}

        # 更新基准价
        base_price_update = self.base_price_manager.update_base_price(
            order_price, is_partial=False)

        # 记录交易
        trade_record = {
            'timestamp': timestamp or datetime.now(),
            'signal': signal['signal'],
            'price': order_price,
            'amount': amount,
            'position': position_update['current_position'],
            'commission': commission,
            'base_price': self.base_price_manager.get_base_price(),
            'base_price_updated': base_price_update['success']
        }

        self.trades.append(trade_record)
        self.last_signal = signal['signal']
        self.last_trade_price = order_price
        self.last_trade_time = trade_record['timestamp']

        # 重置价格极值
        self.highest_price = self.base_price_manager.get_base_price()
        self.lowest_price = self.base_price_manager.get_base_price()

        return {
            'status': 'executed',
            'trade': trade_record,
            'base_price_update': base_price_update
        }

    def update_price(self, current_price: float,
                     timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        更新价格并处理交易

        参数：
        current_price: float - 当前价格
        timestamp: datetime - 当前时间戳

        返回：
        dict - 包含信号和交易结果的字典
        """
        # 生成信号
        signal = self.generate_signal(current_price, timestamp)

        # 执行交易
        if signal['signal'] in ['buy', 'sell']:
            trade_result = self.execute_trade(signal, current_price, timestamp)
        else:
            trade_result = {'status': 'no_trade', 'signal': signal['signal']}

        return {
            'signal': signal,
            'trade_result': trade_result,
            'current_position': self.position_manager.get_position(),
            'base_price': self.base_price_manager.get_base_price()
        }

    def get_trades(self) -> List[Dict]:
        """获取交易记录"""
        return self.trades

    def get_performance(self) -> Dict[str, Any]:
        """
        计算策略性能指标

        返回：
        dict - 性能指标字典
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'total_commission': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_profit': 0,
                'trade_pairs': 0
            }

        total_trades = len(self.trades)
        total_commission = sum(trade['commission'] for trade in self.trades)

        profitable_trades = 0
        total_profit = 0
        total_loss = 0
        trade_pairs = 0

        i = 0
        while i < len(self.trades) - 1:
            current_trade = self.trades[i]
            next_trade = self.trades[i + 1]

            if current_trade['signal'] != next_trade['signal']:
                trade_pairs += 1

                if next_trade['signal'] == 'sell':
                    profit = (
                        next_trade['price'] - current_trade['price']) * next_trade['amount']
                    profit -= next_trade['commission'] + \
                        current_trade['commission']
                else:
                    profit = (
                        current_trade['price'] - next_trade['price']) * next_trade['amount']
                    profit -= next_trade['commission'] + \
                        current_trade['commission']

                if profit > 0:
                    profitable_trades += 1
                    total_profit += profit
                else:
                    total_loss += abs(profit)

                i += 2
            else:
                i += 1

        win_rate = profitable_trades / trade_pairs if trade_pairs > 0 else 0
        win_rate = min(win_rate, 1.0)
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        return {
            'total_trades': total_trades,
            'total_commission': round(total_commission, 2),
            'win_rate': round(win_rate, 4),
            'profit_factor': round(profit_factor, 4),
            'total_profit': round(total_profit - total_loss, 2),
            'trade_pairs': trade_pairs
        }

    def reset(self) -> None:
        """重置策略状态"""
        self.trades = []
        self.last_signal = None
        self.last_trade_price = None
        self.last_trade_time = None
        self.highest_price = self.config['initial_base_price']
        self.lowest_price = self.config['initial_base_price']
        self.status = "active"
        self.position_manager.reset_position()
        self.base_price_manager.reset_base_price(
            self.config['initial_base_price'])

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新策略配置

        参数：
        config: dict - 新的配置参数
        """
        self.config.update(config)

        # 更新相关管理器
        if 'initial_base_price' in config:
            self.base_price_manager.reset_base_price(
                config['initial_base_price'])
            self.highest_price = config['initial_base_price']
            self.lowest_price = config['initial_base_price']

        if 'max_position' in config or 'min_position' in config:
            self.position_manager.update_limits(
                max_position=config.get('max_position'),
                min_position=config.get('min_position')
            )

    def get_status(self) -> Dict[str, Any]:
        """获取策略状态信息"""
        return {
            'symbol': self.config.get('symbol', ''),
            'base_price': self.base_price_manager.get_base_price(),
            'price_range': self.config['price_range'],
            'current_position': self.position_manager.get_position(),
            'position_status': self.position_manager.get_position_status(),
            'max_position': self.config['max_position'],
            'min_position': self.config['min_position'],
            'status': self.status,
            'highest_price': self.highest_price,
            'lowest_price': self.lowest_price,
            'total_trades': len(self.trades)
        }

    def stop_strategy(self, clear_position: bool = False) -> Optional[Dict[str, Any]]:
        """
        停止策略

        参数：
        clear_position: bool - 是否清仓

        返回：
        dict - 清仓订单信息（如果需要）
        """
        self.status = "stopped"

        if clear_position:
            current_holding = self.position_manager.get_position() - \
                self.config['min_position']
            if current_holding > 0:
                return {
                    'type': 'sell',
                    'price': self.base_price_manager.get_base_price(),
                    'amount': current_holding
                }

        return None

    def resume_strategy(self) -> None:
        """恢复策略"""
        self.status = "active"


class DynamicGridStrategy(GridStrategy):
    """
    动态网格策略类
    基于市场波动率自动调整网格间距
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 volatility_adjustment: float = 0.1, **kwargs):
        """
        初始化动态网格策略

        参数：
        config: 配置字典
        volatility_adjustment: float - 波动率调整系数
        """
        super().__init__(config, **kwargs)
        self.volatility_adjustment = volatility_adjustment
        self.historical_prices: List[float] = []

    def update_volatility(self, current_price: float) -> None:
        """
        更新波动率并调整网格

        参数：
        current_price: float - 当前市场价格
        """
        self.historical_prices.append(current_price)

        # 只保留最近的20个价格
        if len(self.historical_prices) > 20:
            self.historical_prices = self.historical_prices[-20:]

        # 计算波动率
        if len(self.historical_prices) >= 10:
            changes = []
            for i in range(1, len(self.historical_prices)):
                change = abs(
                    self.historical_prices[i] - self.historical_prices[i-1]) / self.historical_prices[i-1]
                changes.append(change)

            if changes:
                avg_volatility = sum(changes) / len(changes)
                volatility_factor = 1 + avg_volatility * self.volatility_adjustment

                # 调整价格区间
                price_range = self.config['price_range']
                original_range = price_range[1] - price_range[0]
                mid_price = (price_range[1] + price_range[0]) / 2

                new_range = original_range * volatility_factor
                self.config['price_range'] = [
                    mid_price - new_range / 2,
                    mid_price + new_range / 2
                ]

    def update_price(self, current_price: float,
                     timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """更新价格并调整波动率"""
        self.update_volatility(current_price)
        return super().update_price(current_price, timestamp)


class TrendGridStrategy(GridStrategy):
    """
    趋势网格策略类
    结合趋势指标调整网格密度
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 trend_indicator: Optional[Callable[[float], int]] = None, **kwargs):
        """
        初始化趋势网格策略

        参数：
        config: 配置字典
        trend_indicator: function - 趋势指标函数，返回 1 (上涨), 0 (横盘), -1 (下跌)
        """
        super().__init__(config, **kwargs)
        self.trend_indicator = trend_indicator
        self.current_trend = 0

    def calculate_grid_lines(self) -> Dict[str, List[float]]:
        """计算网格价格水平，考虑趋势因素"""
        base_lines = super().calculate_grid_lines()

        if self.trend_indicator is None:
            return base_lines

        # 根据趋势调整网格密度
        if self.current_trend == 1:  # 上涨趋势
            # 减少买入网格，增加卖出网格
            base_lines['buy_lines'] = base_lines['buy_lines'][:len(
                base_lines['buy_lines'])//2]
        elif self.current_trend == -1:  # 下跌趋势
            # 增加买入网格，减少卖出网格
            base_lines['sell_lines'] = base_lines['sell_lines'][:len(
                base_lines['sell_lines'])//2]

        return base_lines

    def update_price(self, current_price: float,
                     timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """更新价格并更新趋势"""
        if self.trend_indicator:
            self.current_trend = self.trend_indicator(current_price)
        return super().update_price(current_price, timestamp)
