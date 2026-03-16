import pandas as pd
import numpy as np
from datetime import datetime
from grid_trading.strategy.position_manager import PositionManager, BasePriceManager


class GridStrategy:
    """
    网格交易策略核心逻辑类

    功能：
    - 网格价格计算：基于基准价和涨跌幅计算上下网格线
    - 信号生成：检测价格突破网格线并生成交易信号
    - 交易触发逻辑：上涨卖出、下跌买入、回落卖出、反弹买入
    - 委托价格计算：根据触发价格计算委托价
    - 数量计算：根据上涨卖出量和下跌买入量执行
    - 手续费估算：千分之三手续费计算
    """

    def __init__(self, config=None):
        """
        初始化网格策略

        参数：
        config: dict - 策略配置参数
        """
        # 默认配置
        default_config = {
            'initial_base_price': 10.0,       # 初始基准价
            'buy_percent': 0.01,               # 每下跌1%买入
            'sell_percent': 0.01,              # 每上涨1%卖出
            'buy_amount': 100,                # 下跌买入量
            'sell_amount': 100,               # 上涨卖出量
            'max_position': 10000,             # 最大持仓10000股
            'min_position': 1000,              # 最小底仓1000股
            'price_range': [8.0, 12.0],        # 价格区间
            'update_method': 'trigger_price',  # 基准价更新方式
            'commission_rate': 0.0001          # 手续费率0.10‰（ETF佣金）
        }

        # 更新配置
        self.config = default_config.copy()
        if config:
            self.config.update(config)

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
        self.trades = []  # 交易记录
        self.last_signal = None  # 上次交易信号
        self.last_trade_price = None  # 上次交易价格
        self.last_trade_time = None  # 上次交易时间

    def calculate_grid_lines(self):
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
        # 最多生成1000条网格线，避免性能问题
        max_lines = min(self.config.get('lower_count', 100), 1000)
        for _ in range(max_lines):
            current_price *= (1 - buy_percent)
            buy_lines.append(round(current_price, 4))

        # 计算卖出网格线（向上）- 限制数量
        sell_lines = []
        current_price = base_price
        # 最多生成1000条网格线，避免性能问题
        max_lines = min(self.config.get('upper_count', 100), 1000)
        for _ in range(max_lines):
            current_price *= (1 + sell_percent)
            sell_lines.append(round(current_price, 4))

        return {
            'buy_lines': sorted(buy_lines, reverse=True),  # 从高到低排序
            'sell_lines': sorted(sell_lines)  # 从低到高排序
        }

    def generate_signal(self, current_price, timestamp=None):
        """
        生成交易信号

        参数：
        current_price: float - 当前价格
        timestamp: datetime - 当前时间戳

        返回：
        dict - 交易信号，包含信号类型、价格、数量等信息
        """
        # 计算网格线
        grid_lines = self.calculate_grid_lines()
        buy_lines = grid_lines['buy_lines']
        sell_lines = grid_lines['sell_lines']

        # 检查价格区间
        if current_price < self.config['price_range'][0] or current_price > self.config['price_range'][1]:
            return {'signal': 'out_of_range', 'price': current_price}

        # 检查持仓限制
        if self.position_manager.is_max_position_reached():
            # 达到最大持仓，暂停买入
            if current_price <= min(buy_lines):
                return {'signal': 'max_position_reached', 'price': current_price}

        if self.position_manager.is_min_position_reached():
            # 达到最小持仓，暂停卖出
            if current_price >= max(sell_lines):
                return {'signal': 'min_position_reached', 'price': current_price}

        # 检测买入信号
        for buy_line in buy_lines:
            if current_price <= buy_line:
                # 检查是否为新的买入信号
                if self.last_signal != 'buy' or (self.last_trade_price and current_price < self.last_trade_price):
                    signal = {
                        'signal': 'buy',
                        'price': current_price,
                        'buy_line': buy_line,
                        'amount': self.config['buy_amount'],
                        'timestamp': timestamp or datetime.now()
                    }
                    return signal
                break

        # 检测卖出信号
        for sell_line in sell_lines:
            if current_price >= sell_line:
                # 检查是否为新的卖出信号
                if self.last_signal != 'sell' or (self.last_trade_price and current_price > self.last_trade_price):
                    signal = {
                        'signal': 'sell',
                        'price': current_price,
                        'sell_line': sell_line,
                        'amount': self.config['sell_amount'],
                        'timestamp': timestamp or datetime.now()
                    }
                    return signal
                break

        # 无信号
        return {'signal': 'hold', 'price': current_price}

    def execute_trade(self, signal, current_price, timestamp=None):
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

        # 计算交易数量
        if signal['signal'] == 'buy':
            amount = signal['amount']
            # 使用持仓管理器检查持仓限制
            if not self.position_manager.check_position('buy', amount):
                return {'status': 'rejected', 'reason': 'max_position_exceeded'}
        else:  # sell
            amount = signal['amount']
            # 使用持仓管理器检查持仓限制
            if not self.position_manager.check_position('sell', amount):
                return {'status': 'rejected', 'reason': 'min_position_violation'}

        # 计算委托价格
        if signal['signal'] == 'buy':
            # 买入委托价，略低于当前价格
            order_price = round(current_price * 0.999, 4)
        else:
            # 卖出委托价，略高于当前价格
            order_price = round(current_price * 1.001, 4)

        # 计算手续费（ETF佣金：0.10‰，不足0.1元按0.1元收取）
        commission = order_price * amount * 0.0001  # 0.10‰
        commission = max(commission, 0.1)  # 不足0.1元按0.1元收取
        commission = round(commission, 2)

        # 使用持仓管理器更新持仓
        position_update = self.position_manager.update_position(
            amount, signal['signal'])
        if not position_update['success']:
            return {'status': 'rejected', 'reason': position_update['reason']}

        # 交易成功执行后，更新基准价（完全成交，非部分成交）
        base_price_update = self.base_price_manager.update_base_price(order_price, is_partial=False)

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

        return {
            'status': 'executed',
            'trade': trade_record,
            'base_price_update': base_price_update
        }

    def update_price(self, current_price, timestamp=None):
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

    def get_trades(self):
        """
        获取交易记录

        返回：
        list - 交易记录列表
        """
        return self.trades

    def get_performance(self):
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
                'total_profit': 0
            }

        # 计算总交易量和手续费
        total_trades = len(self.trades)
        total_commission = sum(trade['commission'] for trade in self.trades)

        # 计算盈利交易数
        profitable_trades = 0
        total_profit = 0
        total_loss = 0
        trade_pairs = 0

        # 正确计算交易对和利润
        i = 0
        while i < len(self.trades) - 1:
            current_trade = self.trades[i]
            next_trade = self.trades[i + 1]

            # 检查是否为有效的交易对（买卖或卖买）
            if current_trade['signal'] != next_trade['signal']:
                trade_pairs += 1

                if next_trade['signal'] == 'sell':
                    # 先买后卖
                    profit = (
                        next_trade['price'] - current_trade['price']) * next_trade['amount']
                    profit -= next_trade['commission'] + \
                        current_trade['commission']
                    if profit > 0:
                        profitable_trades += 1
                        total_profit += profit
                    else:
                        total_loss += abs(profit)
                elif next_trade['signal'] == 'buy':
                    # 先卖后买
                    profit = (
                        current_trade['price'] - next_trade['price']) * next_trade['amount']
                    profit -= next_trade['commission'] + \
                        current_trade['commission']
                    if profit > 0:
                        profitable_trades += 1
                        total_profit += profit
                    else:
                        total_loss += abs(profit)

                # 跳过下一个交易，因为已经配对
                i += 2
            else:
                # 相同信号，移动到下一个交易
                i += 1

        # 计算胜率
        win_rate = profitable_trades / trade_pairs if trade_pairs > 0 else 0
        # 确保胜率不超过100%
        win_rate = min(win_rate, 1.0)

        # 计算盈利因子
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        return {
            'total_trades': total_trades,
            'total_commission': round(total_commission, 2),
            'win_rate': round(win_rate, 4),
            'profit_factor': round(profit_factor, 4),
            'total_profit': round(total_profit - total_loss, 2),
            'trade_pairs': trade_pairs
        }

    def reset(self):
        """
        重置策略状态
        """
        self.base_price = self.config['initial_base_price']
        self.current_position = self.config['min_position']
        self.trades = []
        self.last_signal = None
        self.last_trade_price = None
        self.last_trade_time = None

    def update_config(self, config):
        """
        更新策略配置

        参数：
        config: dict - 新的配置参数
        """
        self.config.update(config)
        # 如果更新了初始基准价，同时更新当前基准价
        if 'initial_base_price' in config:
            self.base_price = config['initial_base_price']
        # 如果更新了最小持仓，同时更新当前持仓
        if 'min_position' in config:
            self.current_position = max(
                self.current_position, config['min_position'])


# 测试代码
if __name__ == "__main__":
    # 创建策略实例
    config = {
        'initial_base_price': 2.8,
        'buy_percent': 0.01,
        'sell_percent': 0.01,
        'buy_amount': 100,
        'sell_amount': 100,
        'max_position': 10000,
        'min_position': 1000,
        'price_range': [2.0, 3.5],
        'update_method': 'trigger_price'
    }

    strategy = GridStrategy(config)

    # 测试网格线计算
    grid_lines = strategy.calculate_grid_lines()
    print("买入网格线:", grid_lines['buy_lines'][:5])  # 显示前5条
    print("卖出网格线:", grid_lines['sell_lines'][:5])  # 显示前5条

    # 测试信号生成
    test_prices = [2.75, 2.85, 2.70, 2.90]
    for price in test_prices:
        signal = strategy.generate_signal(price)
        print(f"价格 {price}: 信号 {signal['signal']}")

    # 测试交易执行
    print("\n测试交易执行:")
    for price in test_prices:
        result = strategy.update_price(price)
        print(
            f"价格 {price}: 信号 {result['signal']['signal']}, 交易状态 {result['trade_result']['status']}")

    # 查看交易记录
    print("\n交易记录:")
    for trade in strategy.get_trades():
        print(
            f"时间: {trade['timestamp']}, 信号: {trade['signal']}, 价格: {trade['price']}, 数量: {trade['amount']}, 持仓: {trade['position']}")

    # 查看性能指标
    performance = strategy.get_performance()
    print("\n性能指标:")
    print(f"总交易次数: {performance['total_trades']}")
    print(f"交易对数量: {performance.get('trade_pairs', 0)}")
    print(f"总手续费: {performance['total_commission']}")
    print(f"胜率: {performance['win_rate']:.2%}")
    print(f"盈利因子: {performance['profit_factor']:.2f}")
    print(f"总利润: {performance['total_profit']:.2f}")
