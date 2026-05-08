# -*- coding: utf-8 -*-
"""
网格交易系统 - 回测引擎
Backtest engine for the grid trading system

重构自 grid_trading/backtest/backtest_engine.py
主要改动：移除 sys.path 操作，统一使用 core.* 和 config.* 导入
"""

import backtrader as bt
import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# 使用重构后的模块导入路径
from core.data_module.legacy_loader import DataLoader
from core.strategy_module import GridStrategy
from config import get_database_config, get_trading_config


class GridBacktraderStrategy(bt.Strategy):
    """
    backtrader网格交易策略类

    用于在backtrader框架中运行网格交易策略
    """

    params = (
        ('grid_config', None),  # 网格策略配置
    )

    def __init__(self):
        """
        初始化策略
        """
        # 从配置中提取参数
        grid_config = self.params.grid_config

        # 计算价格上下限
        base_price = grid_config.get('initial_base_price', 10.0)
        buy_percent = grid_config.get('buy_percent', 0.01)
        sell_percent = grid_config.get('sell_percent', 0.01)
        lower_count = grid_config.get('lower_count', 100)
        upper_count = grid_config.get('upper_count', 100)

        lower_price = base_price * (1 - buy_percent) ** lower_count
        upper_price = base_price * (1 + sell_percent) ** upper_count

        # 初始化网格策略
        self.grid_strategy = GridStrategy(
            symbol='',  # 暂时为空
            base_price=base_price,
            upper_price=upper_price,
            lower_price=lower_price,
            max_position=grid_config.get('max_position', 10000),
            min_position=grid_config.get('min_position', 0),
            step_percent=buy_percent * 100,  # 转换为百分比
            buy_quantity=grid_config.get('buy_quantity'),
            sell_quantity=grid_config.get('sell_quantity'),
        )

        # 计算网格
        self.grid_strategy.calculate_grid()

        # 保存交易记录
        self.trade_records = []

        # 保存持仓明细记录
        self.position_records = []

        # 跟踪订单
        self.order = None

        # 跟踪价格
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

    def next(self):
        """
        每个时间步执行的逻辑
        """
        # 检查是否有未完成的订单
        if self.order:
            return

        # 获取当前价格（使用收盘价）
        current_price = self.dataclose[0]

        # 使用网格策略生成订单
        order = self.grid_strategy.generate_order(current_price)

        # 执行交易
        if order:
            # 记录交易
            trade_record = {
                'datetime': self.datas[0].datetime.datetime(),
                'signal': order['type'],
                'price': order['price'],
                'amount': order['quantity'],  # 使用quantity作为交易数量
                'position': self.grid_strategy.current_holding,
                # 计算手续费
                'commission': order['price'] * order['quantity'] * 0.0001
            }

            self.trade_records.append(trade_record)

            # 在backtrader中执行交易
            if order['type'] == 'buy':
                # 买入
                self.order = self.buy(
                    size=order['quantity'], price=order['price'])
            elif order['type'] == 'sell':
                # 卖出
                self.order = self.sell(
                    size=order['quantity'], price=order['price'])

        # 记录每天的持仓明细
        self.position_records.append({
            'datetime': self.datas[0].datetime.datetime(),
            'position': self.grid_strategy.current_holding,
            'price': current_price
        })

    def notify_order(self, order):
        """
        订单通知
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或接受，不做处理
            return

        if order.status in [order.Completed]:
            # 订单已完成，更新网格策略的持仓
            executed_price = order.executed.price
            executed_quantity = order.executed.size

            # 构建订单对象
            trade_order = {
                'type': 'buy' if order.isbuy() else 'sell',
                'price': executed_price,
                'quantity': executed_quantity,
                'amount': executed_price * executed_quantity
            }

            # 更新网格策略的持仓
            self.grid_strategy.update_position(trade_order, executed=True,
                                               executed_price=executed_price,
                                               executed_quantity=executed_quantity)

            self.order = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # 订单已取消、保证金不足或被拒绝
            self.order = None

    def notify_trade(self, trade):
        """
        交易通知
        """
        if not trade.isclosed:
            return

    def get_trade_records(self) -> List[Dict]:
        """
        获取交易记录

        返回：
        list - 交易记录列表
        """
        return self.trade_records

    def get_strategy(self) -> GridStrategy:
        """
        获取网格策略实例

        返回：
        GridStrategy - 网格策略实例
        """
        return self.grid_strategy

    def get_position_records(self) -> List[Dict]:
        """
        获取持仓明细记录

        返回：
        list - 持仓明细记录列表
        """
        return self.position_records


class BacktestEngine:
    """
    回测引擎类

    功能：
    - 加载历史数据
    - 执行回测
    - 生成性能报告
    - 支持参数优化
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化回测引擎

        参数：
        db_path: str - 可选，数据库路径。如果不提供，使用配置中的路径
        """
        self.data_loader = DataLoader()
        self.results = None
        self.strategy = None

        # 使用配置获取数据库路径
        if db_path:
            self.db_path = db_path
        else:
            db_config = get_database_config()
            self.db_path = db_config.get_stock_data_db_path()

    def load_data(self, file_name: str, start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> bt.feeds.PandasData:
        """
        加载历史数据

        参数：
        file_name: str - CSV文件名
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"

        返回：
        bt.feeds.PandasData - backtrader数据源
        """
        # 使用数据加载器加载数据
        df = self.data_loader.load_csv_data(file_name, start_date, end_date)

        if df.empty:
            raise ValueError("数据加载失败！")

        # 转换为backtrader数据源
        data = bt.feeds.PandasData(
            dataname=df,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )

        return data

    def load_data_from_db(self, symbol: str, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> bt.feeds.PandasData:
        """
        从数据库加载历史数据

        参数：
        symbol: str - 股票代码
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"

        返回：
        bt.feeds.PandasData - backtrader数据源
        """
        db_path = self.db_path
        print(f"使用的数据库路径: {db_path}")
        print(f"数据库文件是否存在: {os.path.exists(db_path)}")

        # 检查文件权限
        print(f"数据库文件是否可读: {os.access(db_path, os.R_OK)}")
        print(f"数据库文件是否可写: {os.access(db_path, os.W_OK)}")

        conn = sqlite3.connect(db_path)

        # 打印所有表名
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库中的表: {tables}")

        # 简单的表名映射逻辑
        if symbol.startswith("stock_") or symbol.startswith("etf_"):
            table_name = symbol
        elif len(symbol) == 6 and (symbol.startswith("5") or symbol.startswith("1")):
            table_name = f"etf_{symbol}"
        else:
            table_name = f"stock_{symbol}"

        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            raise ValueError(f"数据库中未找到表: {table_name}，请先导入数据")

        # 构建查询
        query = f"SELECT date, open_price as open, close_price as close, high_price as high, low_price as low, volume FROM {table_name}"
        print(f"构建的SQL查询: {query}")

        where_conditions = []
        if start_date:
            where_conditions.append(f"date >= '{start_date}'")
        if end_date:
            where_conditions.append(f"date <= '{end_date}'")

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
            print(f"添加WHERE条件后的查询: {query}")

        query += " ORDER BY date ASC"
        print(f"最终SQL查询: {query}")

        try:
            print("开始执行SQL查询...")
            df = pd.read_sql_query(query, conn)
            print(f"查询成功，返回 {len(df)} 行数据")
            print(f"数据列: {list(df.columns)}")

            if df.empty:
                raise ValueError(f"指定日期范围内没有数据: {start_date} 到 {end_date}")

            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            # 确保数据类型正确
            df = df.astype({
                'open': 'float64',
                'close': 'float64',
                'high': 'float64',
                'low': 'float64',
                'volume': 'float64'
            })

            # 创建backtrader数据源
            data = bt.feeds.PandasData(
                dataname=df,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=None
            )
            return data

        except Exception as e:
            raise ValueError(f"从数据库加载数据失败: {e}")
        finally:
            conn.close()

    def run_backtest(self, symbol_or_file: str, grid_config: Dict,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        运行回测

        参数：
        symbol_or_file: str - 股票代码或CSV文件名
        grid_config: dict - 网格策略配置
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"

        返回：
        dict - 回测结果
        """
        # 创建cerebro实例
        cerebro = bt.Cerebro()

        # 设置手续费（ETF佣金：0.10‰）
        commission_rate = grid_config.get('commission_rate', 0.0001)
        cerebro.broker.setcommission(commission=commission_rate)

        # 设置初始资金
        initial_cash = grid_config.get('initial_cash', 100000.0)  # 默认10万初始资金
        cerebro.broker.setcash(initial_cash)

        # 加载数据
        if symbol_or_file.endswith('.csv'):
            data = self.load_data(symbol_or_file, start_date, end_date)
        else:
            data = self.load_data_from_db(symbol_or_file, start_date, end_date)

        cerebro.adddata(data)

        # 添加策略
        cerebro.addstrategy(GridBacktraderStrategy, grid_config=grid_config)

        # 运行回测
        print('开始回测...')
        print(f'初始资金: {cerebro.broker.getvalue():.2f}')

        # 运行回测
        self.results = cerebro.run()

        # 获取策略实例
        self.strategy = self.results[0]

        # 计算最终资金
        final_value = cerebro.broker.getvalue()
        print(f'最终资金: {final_value:.2f}')
        print(f'总收益: {(final_value - initial_cash):.2f}')

        # 生成权益曲线数据
        equity_curve = []

        # 使用交易记录来生成简单的权益曲线
        current_equity = initial_cash
        for trade in self.strategy.get_trade_records():
            # 根据交易计算权益变化
            if trade['signal'] == 'buy':
                # 买入会减少现金，增加持仓
                current_equity -= trade['price'] * \
                    trade['amount'] + trade['commission']
            elif trade['signal'] == 'sell':
                # 卖出会增加现金，减少持仓
                current_equity += trade['price'] * \
                    trade['amount'] - trade['commission']

            # 添加权益曲线数据点
            equity_curve.append({
                'datetime': trade['datetime'],
                'equity': current_equity,
                'return': ((current_equity - initial_cash) / initial_cash) * 100
            })

        # 确保最后一个数据点是最终权益
        if equity_curve:
            equity_curve[-1]['equity'] = final_value
            equity_curve[-1]['return'] = ((final_value -
                                          initial_cash) / initial_cash) * 100
        else:
            # 如果没有交易，添加一个初始和最终的数据点
            equity_curve.append({
                'datetime': datetime.now(),
                'equity': final_value,
                'return': ((final_value - initial_cash) / initial_cash) * 100
            })

        # 生成回测结果
        backtest_result = {
            'initial_value': initial_cash,
            'final_value': final_value,
            'total_return': final_value - initial_cash,
            'total_return_percent': ((final_value - initial_cash) / initial_cash) * 100,
            'trade_records': self.strategy.get_trade_records(),
            'position_records': self.strategy.get_position_records(),
            'strategy_performance': {
                'total_trades': len(self.strategy.get_trade_records()),
                'trade_pairs': len(self.strategy.get_trade_records()) // 2,
                'total_commission': sum(trade['commission'] for trade in self.strategy.get_trade_records()),
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_profit': final_value - initial_cash
            },
            'equity_curve': equity_curve
        }

        return backtest_result

    def get_analyzer_results(self) -> Dict:
        """
        获取分析器结果

        返回：
        dict - 分析器结果
        """
        if not self.results:
            return {}

        # 这里可以添加各种分析器的结果
        # 例如：年化收益率、最大回撤、夏普比率等

        return {}

    def optimize_parameters(self, file_name: str, param_ranges: Dict,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> Dict:
        """
        参数优化

        参数：
        file_name: str - CSV文件名
        param_ranges: dict - 参数范围字典
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"

        返回：
        dict - 最佳参数和结果
        """
        # 简单实现：返回默认参数
        trading_config = get_trading_config()

        default_config = {
            'initial_base_price': 10.0,
            'buy_percent': trading_config.buy_percent,
            'sell_percent': trading_config.sell_percent,
            'buy_amount': trading_config.buy_quantity,
            'sell_amount': trading_config.sell_quantity,
            'max_position': trading_config.max_position,
            'min_position': trading_config.min_position,
            'price_range': [8.0, 12.0],
            'update_method': 'trigger_price'
        }

        # 运行默认参数的回测
        result = self.run_backtest(
            file_name, default_config, start_date, end_date)

        return {
            'best_params': default_config,
            'best_result': result
        }

    def generate_report(self, backtest_result: Dict) -> str:
        """
        生成回测报告

        参数：
        backtest_result: dict - 回测结果

        返回：
        str - 回测报告
        """
        report = """# 网格交易策略回测报告

## 回测概览
- 初始资金: {initial_value:.2f}
- 最终资金: {final_value:.2f}
- 总收益: {total_return:.2f}
- 总收益率: {total_return_percent:.2f}%

## 交易统计
- 总交易次数: {total_trades}
- 交易对数量: {trade_pairs}
- 总手续费: {total_commission:.2f}
- 胜率: {win_rate:.2f}%
- 盈利因子: {profit_factor:.2f}
- 策略总利润: {strategy_profit:.2f}

## 交易明细
""".format(
            initial_value=backtest_result['initial_value'],
            final_value=backtest_result['final_value'],
            total_return=backtest_result['total_return'],
            total_return_percent=backtest_result['total_return_percent'],
            total_trades=backtest_result['strategy_performance'].get(
                'total_trades', 0),
            trade_pairs=backtest_result['strategy_performance'].get(
                'trade_pairs', 0),
            total_commission=backtest_result['strategy_performance'].get(
                'total_commission', 0),
            win_rate=backtest_result['strategy_performance'].get(
                'win_rate', 0) * 100,
            profit_factor=backtest_result['strategy_performance'].get(
                'profit_factor', 0),
            strategy_profit=backtest_result['strategy_performance'].get(
                'total_profit', 0)
        )

        # 添加交易明细
        if backtest_result['trade_records']:
            report += "| 日期 | 信号 | 价格 | 数量 | 持仓 | 手续费 |\n"
            report += "|------|------|------|------|------|--------|\n"

            for trade in backtest_result['trade_records'][:20]:  # 只显示前20条
                report += f"| {trade['datetime']} | {trade['signal']} | {trade['price']:.4f} | {trade['amount']} | {trade['position']} | {trade['commission']:.2f} |\n"

            if len(backtest_result['trade_records']) > 20:
                report += f"... 还有 {len(backtest_result['trade_records']) - 20} 条交易记录\n"

        return report


# 测试代码
if __name__ == "__main__":
    # 创建回测引擎实例
    engine = BacktestEngine()

    # 配置参数
    grid_config = {
        'initial_base_price': 2.8,
        'buy_percent': 0.01,
        'sell_percent': 0.01,
        'buy_amount': 100,
        'sell_amount': 100,
        'max_position': 10000,
        'min_position': 1000,
        'price_range': [2.0, 3.5],
        'update_method': 'trigger_price',
        'commission_rate': 0.0001  # ETF佣金：0.10‰
    }

    # 运行回测
    try:
        result = engine.run_backtest(
            '19900101-20251014_159633_日线_前复权.csv',
            grid_config,
            '2023-01-01',
            '2023-12-31'
        )

        # 生成报告
        report = engine.generate_report(result)
        print(report)

    except Exception as e:
        print(f"回测失败: {e}")
