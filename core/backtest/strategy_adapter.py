#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略适配器框架
功能：将符合IStandardStrategy接口的自定义策略适配到Backtrader回测引擎
"""

import backtrader as bt
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import pandas as pd

from ..strategy.standard_strategy import IStandardStrategy, Signal, StrategyConfig


class StandardStrategyAdapter(bt.Strategy):
    """
    标准策略适配器
    
    将符合IStandardStrategy接口的自定义策略适配到Backtrader引擎
    """
    
    params = (
        ('strategy_class', None),
        ('strategy_config', {}),
    )

    def __init__(self):
        """
        初始化适配器
        """
        # 检查策略类是否提供
        if self.p.strategy_class is None:
            raise ValueError("strategy_class参数必须提供")
        
        if not issubclass(self.p.strategy_class, IStandardStrategy):
            raise TypeError("strategy_class必须继承自IStandardStrategy")
        
        # 创建策略实例
        self._strategy = self.p.strategy_class(
            name=self.p.strategy_class.__name__,
            description=f"Adapted {self.p.strategy_class.__name__}"
        )
        
        # 设置策略配置
        if self.p.strategy_config:
            self._strategy.set_config(self.p.strategy_config)
        
        # 初始化标志
        self._initialized = False
        self._started = False
        
        # 交易记录
        self.trade_records = []
        
        # 权益曲线
        self.equity_curve = []
        
        # 持仓记录
        self.position_records = []
        
        # 存储原始数据用于因子计算
        self._price_data = []
        
        # 最后交易价格
        self._last_price = 0.0

    def notify_order(self, order):
        """
        订单状态通知
        """
        if order.status in [order.Completed]:
            # 记录实际成交
            executed_price = order.executed.price
            executed_amount = order.executed.size
            commission = order.executed.comm
            
            # 更新策略状态
            signal = None
            if order.data:
                signal = Signal(
                    type='buy' if executed_amount > 0 else 'sell',
                    price=executed_price,
                    amount=abs(executed_amount),
                    timestamp=self.data.datetime.datetime()
                )
            
            self._strategy.update(
                signal=signal,
                executed_price=executed_price,
                executed_amount=abs(executed_amount),
                commission=commission
            )
            
            # 记录交易
            trade_record = {
                'datetime': self.data.datetime.datetime(),
                'signal': 'buy' if executed_amount > 0 else 'sell',
                'price': executed_price,
                'amount': abs(executed_amount),
                'position': self.position.size,
                'commission': commission,
                'cash': self.broker.get_cash(),
                'equity': self.broker.get_value()
            }
            self.trade_records.append(trade_record)

    def notify_trade(self, trade):
        """
        交易完成通知
        """
        if trade.isclosed:
            # 更新交易利润
            for record in reversed(self.trade_records):
                if record['signal'] == 'sell' and record['position'] == 0:
                    record['profit'] = trade.pnl
                    break

    def start(self):
        """
        Backtrader策略开始回调
        """
        # 调用策略的初始化钩子
        if not self._initialized:
            self._strategy.on_init()
            self._initialized = True
        
        # 调用策略的开始钩子
        if not self._started:
            self._strategy.on_start()
            self._started = True
            
            # 设置初始资金
            self._strategy.state.cash = self.broker.get_cash()
            self._strategy.state.equity = self.broker.get_value()

    def next(self):
        """
        每根K线执行一次
        """
        # 收集当前数据
        current_data = {
            'datetime': self.data.datetime.datetime(),
            'open': float(self.data.open[0]),
            'high': float(self.data.high[0]),
            'low': float(self.data.low[0]),
            'close': float(self.data.close[0]),
            'volume': float(self.data.volume[0]),
            'amount': float(self.data.close[0] * self.data.volume[0]),
            'factors': {}
        }
        
        # 存储价格数据用于因子计算
        self._price_data.append(current_data)
        self._last_price = current_data['close']
        
        # 生成信号
        signal = self._strategy.next(current_data)
        
        # 如果有信号，执行交易
        if signal is not None and signal.type != 'hold':
            self._execute_signal(signal)
        
        # 记录权益曲线
        self.equity_curve.append({
            'datetime': current_data['datetime'],
            'equity': self.broker.get_value(),
            'cash': self.broker.get_cash(),
            'position': self.position.size,
            'price': current_data['close']
        })
        
        # 记录持仓
        self.position_records.append({
            'datetime': current_data['datetime'],
            'position': self.position.size,
            'avg_cost': self.position.price
        })

    def _execute_signal(self, signal: Signal):
        """
        执行交易信号
        """
        current_price = signal.price or self._last_price
        commission_rate = self._strategy.config.commission_rate
        slippage_rate = self._strategy.config.slippage_rate
        
        # 计算滑点后的价格
        if signal.type == 'buy':
            executed_price = current_price * (1 + slippage_rate)
        else:
            executed_price = current_price * (1 - slippage_rate)
        
        # 计算可交易数量
        if signal.type == 'buy':
            max_amount = self.broker.get_cash() / (executed_price * (1 + commission_rate))
            amount = min(signal.amount, max_amount) if signal.amount > 0 else max_amount
            amount = int(amount)
        else:
            amount = min(signal.amount, abs(self.position.size)) if signal.amount > 0 else abs(self.position.size)
            amount = int(amount)
        
        if amount <= 0:
            return
        
        # 执行交易
        if signal.type == 'buy':
            self.buy(price=executed_price, size=amount)
        elif signal.type == 'sell':
            self.sell(price=executed_price, size=amount)

    def stop(self):
        """
        Backtrader策略停止回调
        """
        # 调用策略的停止钩子
        self._strategy.on_stop()
        
        # 更新最终状态
        self._strategy.state.cash = self.broker.get_cash()
        self._strategy.state.equity = self.broker.get_value()
        self._strategy.state.position = self.position.size

    def get_strategy(self) -> IStandardStrategy:
        """
        获取底层策略实例
        """
        return self._strategy

    def get_trade_records(self) -> List[Dict]:
        """
        获取交易记录
        """
        return self.trade_records

    def get_equity_curve(self) -> List[Dict]:
        """
        获取权益曲线
        """
        return self.equity_curve

    def get_position_records(self) -> List[Dict]:
        """
        获取持仓记录
        """
        return self.position_records

    def get_price_data(self) -> pd.DataFrame:
        """
        获取价格数据DataFrame
        """
        return pd.DataFrame(self._price_data)


class BacktestAdapter:
    """
    回测适配器
    
    提供统一的回测接口，简化回测流程
    """
    
    def __init__(self):
        self.cerebro = None
        self.adapter = None
    
    def run_backtest(
        self,
        strategy_class: Type[IStandardStrategy],
        data: pd.DataFrame,
        config: Optional[Dict[str, Any]] = None,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0001,
        slippage_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        运行回测
        
        参数：
        - strategy_class: 策略类（必须继承IStandardStrategy）
        - data: 行情数据DataFrame，必须包含datetime, open, high, low, close, volume列
        - config: 策略配置字典
        - initial_capital: 初始资金
        - commission_rate: 手续费率
        - slippage_rate: 滑点率
        
        返回：
        Dict[str, Any] - 回测结果
        """
        # 创建Cerebro实例
        self.cerebro = bt.Cerebro()
        
        # 设置初始资金
        self.cerebro.broker.setcash(initial_capital)
        
        # 设置手续费
        self.cerebro.broker.setcommission(commission=commission_rate)
        
        # 设置滑点
        self.cerebro.broker.set_slippage_perc(perc=slippage_rate)
        
        # 准备数据
        data_feed = self._prepare_datafeed(data)
        self.cerebro.adddata(data_feed)
        
        # 创建策略配置
        strategy_config = config or {}
        strategy_config['initial_capital'] = initial_capital
        strategy_config['commission_rate'] = commission_rate
        strategy_config['slippage_rate'] = slippage_rate
        
        # 添加策略适配器
        self.cerebro.addstrategy(
            StandardStrategyAdapter,
            strategy_class=strategy_class,
            strategy_config=strategy_config
        )
        
        # 运行回测
        self.cerebro.run()
        
        # 获取结果
        return self._collect_results()
    
    def _prepare_datafeed(self, data: pd.DataFrame) -> bt.feeds.PandasData:
        """
        将DataFrame转换为Backtrader数据feed
        """
        # 确保列名正确
        data = data.copy()
        if 'datetime' in data.columns:
            data['datetime'] = pd.to_datetime(data['datetime'])
            data.set_index('datetime', inplace=True)
        
        # 创建数据feed
        data_feed = bt.feeds.PandasData(
            dataname=data,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        
        return data_feed
    
    def _collect_results(self) -> Dict[str, Any]:
        """
        收集回测结果
        """
        # 获取策略实例
        strat = self.cerebro.runstrats[0][0]
        
        # 获取最终权益
        final_value = self.cerebro.broker.get_value()
        initial_value = self.cerebro.broker.startingcash
        
        # 计算收益
        total_return = (final_value - initial_value) / initial_value
        
        # 收集结果
        results = {
            'initial_capital': initial_value,
            'final_capital': final_value,
            'total_return': total_return,
            'trade_records': strat.get_trade_records(),
            'equity_curve': strat.get_equity_curve(),
            'position_records': strat.get_position_records(),
            'strategy_info': strat.get_strategy().get_info(),
            'strategy_performance': strat.get_strategy().get_performance()
        }
        
        return results
    
    def plot(self, **kwargs):
        """
        绘制回测结果
        """
        if self.cerebro:
            self.cerebro.plot(**kwargs)
