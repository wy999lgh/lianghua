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
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# 使用重构后的模块导入路径
from core.data.legacy_loader import DataLoader
from core.data.data_fetcher import DataFetcher
from core.data import Database
from core.strategy import GridStrategy
from config import get_database_config, get_trading_config
from core.backtest.ma_regime_cross_strategy import MARegimeCrossStrategy
from core.evaluation.report_generator import ReportGenerator
from core.evaluation.markdown_report import render_backtest_report_markdown, write_backtest_report_markdown


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
            buy_quantity=grid_config.get('buy_quantity', 100),  # 默认 100
            sell_quantity=grid_config.get('sell_quantity', 100),  # 默认 100
        )

        # 计算网格
        self.grid_strategy.calculate_grid_lines()

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
        
        # 保存每日价格数据用于基准收益计算
        self.daily_prices = []

    def next(self):
        """
        每个时间步执行的逻辑
        """
        # 检查是否有未完成的订单
        if self.order:
            return

        # 获取当前价格（使用收盘价）
        current_price = self.dataclose[0]

        # 使用网格策略生成交易信号
        signal = self.grid_strategy.generate_signal(current_price)

        # 执行交易
        if signal and signal.get('signal') in ['buy', 'sell']:
            # 执行交易并获取订单信息
            order_info = self.grid_strategy.execute_trade(
                signal, current_price)

            # 记录交易
            trade_record = {
                'datetime': self.datas[0].datetime.datetime(),
                'signal': signal['signal'],
                'price': current_price,
                'amount': signal.get('amount', 0),
                'position': self.grid_strategy.position_manager.current_position,
                # 计算手续费
                'commission': current_price * signal.get('amount', 0) * self.grid_strategy.config['commission_rate']
            }

            self.trade_records.append(trade_record)

            # 在 backtrader 中执行交易
            if signal['signal'] == 'buy':
                # 买入
                self.order = self.buy(
                    size=signal.get('amount', 0), price=current_price)
            elif signal['signal'] == 'sell':
                # 卖出
                self.order = self.sell(
                    size=signal.get('amount', 0), price=current_price)

        # 记录每天的持仓明细
        self.position_records.append({
            'datetime': self.datas[0].datetime.datetime(),
            'position': self.grid_strategy.position_manager.current_position,
            'price': current_price
        })
        
        # 保存每日价格用于基准收益计算
        self.daily_prices.append({
            'datetime': self.datas[0].datetime.datetime(),
            'close': current_price
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

            # 使用 position_manager.update_position 来更新持仓
            # 注意：在 backtrader 中，订单已经在底层执行，这里只需要更新策略状态
            direction = 'buy' if order.isbuy() else 'sell'
            self.grid_strategy.position_manager.update_position(
                executed_quantity,
                direction
            )

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
    
    def get_daily_prices(self) -> List[Dict]:
        """
        获取每日价格数据

        返回：
        list - 每日价格列表
        """
        return self.daily_prices


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
        db_path: str - 兼容参数（项目已强制使用 PostgreSQL，不再使用本地 .db 路径）
        """
        self.data_loader = DataLoader()
        self.results = None
        self.strategy = None
        self.db_path = db_path
        self.db = Database()

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
        db = self.db

        # 表名映射逻辑（与 core.data.data_fetcher 的写入规则保持一致）
        symbol_str = str(symbol)
        candidates: List[str] = []

        def _add_candidate(name: str):
            if name and name not in candidates:
                candidates.append(name)

        # 优先尝试带 _daily 的表名（数据库中实际存在的格式）
        if symbol_str.startswith(("stock_", "etf_", "index_")):
            # 如果已经是表名格式，也优先试试 _daily 版本
            if symbol_str.startswith("index_"):
                _add_candidate(f"index_daily_{symbol_str[len('index_'):]}")
            elif symbol_str.startswith("stock_"):
                _add_candidate(f"stock_daily_{symbol_str[len('stock_'):]}")
            elif symbol_str.startswith("etf_"):
                _add_candidate(f"etf_daily_{symbol_str[len('etf_'):]}")
            _add_candidate(symbol_str)
        elif symbol_str.startswith(("sh", "sz")) and len(symbol_str) >= 8:
            clean_symbol = symbol_str[2:]
            _add_candidate(f"index_daily_{clean_symbol}")
            _add_candidate(f"stock_daily_{clean_symbol}")
            _add_candidate(f"etf_daily_{clean_symbol}")
            _add_candidate(f"index_{clean_symbol}")
        elif len(symbol_str) == 6 and symbol_str.isdigit():
            if symbol_str.startswith(("5", "1")):
                _add_candidate(f"etf_daily_{symbol_str}")
                _add_candidate(f"etf_{symbol_str}")
            elif symbol_str.startswith(("0", "3")):
                _add_candidate(f"index_daily_{symbol_str}")
                _add_candidate(f"index_{symbol_str}")
            else:
                _add_candidate(f"stock_daily_{symbol_str}")
                _add_candidate(f"stock_{symbol_str}")
        else:
            _add_candidate(f"stock_daily_{symbol_str}")
            _add_candidate(f"stock_{symbol_str}")

        df = pd.DataFrame()
        tried: List[str] = []
        for cand in candidates:
            tried.append(cand)
            df = db.get_data(table_name=cand, start_date=start_date, end_date=end_date, limit=10000)
            if not df.empty:
                break

        if df.empty:
            raise ValueError(f"数据库中未找到数据，已尝试表: {', '.join(tried)}")

        # 兼容 trade_date 列名，统一转换为 date
        if "trade_date" in df.columns and "date" not in df.columns:
            df = df.rename(columns={"trade_date": "date"})

        keep_cols = ["date", "open", "close", "high", "low", "volume"]
        df = df[[c for c in keep_cols if c in df.columns]].copy()
        if "date" not in df.columns:
            raise ValueError(f"数据库表缺少 date 字段，已尝试表: {', '.join(tried)}")

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        for c in ["open", "close", "high", "low", "volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["close"])

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

    @staticmethod
    def _date_to_yyyymmdd(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        s = str(date_str).strip()
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return s.replace("-", "")
        if len(s) == 8 and s.isdigit():
            return s
        return s

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

        # 获取数据源的日期和收盘价信息用于基准收益计算
        price_data_map = {}
        try:
            if hasattr(data, 'datetime') and hasattr(data, 'close'):
                # 使用backtrader的方式获取数据
                for i in range(len(data)):
                    try:
                        dt_val = data.datetime[i]
                        close_val = data.close[i]
                        dt_num = bt.date2num(dt_val) if hasattr(dt_val, 'year') else float(dt_val)
                        price_data_map[dt_num] = float(close_val)
                    except Exception:
                        break
        except Exception:
            pass

        # 使用每日价格数据生成equity_curve
        equity_curve = []
        daily_prices = self.strategy.get_daily_prices()
        
        if daily_prices and len(daily_prices) > 0:
            # 使用每日价格数据生成权益曲线
            current_equity = initial_cash
            trade_records = self.strategy.get_trade_records()
            trade_idx = 0
            
            for daily in daily_prices:
                current_price = daily.get('close')
                
                # 检查是否有交易发生在这一天
                while trade_idx < len(trade_records):
                    trade = trade_records[trade_idx]
                    trade_dt = trade['datetime']
                    daily_dt = daily.get('datetime')
                    
                    # 比较日期
                    if hasattr(trade_dt, 'date') and hasattr(daily_dt, 'date'):
                        if trade_dt.date() == daily_dt.date():
                            # 执行交易
                            if trade['signal'] == 'buy':
                                current_equity -= trade['price'] * trade['amount'] + trade['commission']
                            elif trade['signal'] == 'sell':
                                current_equity += trade['price'] * trade['amount'] - trade['commission']
                            trade_idx += 1
                        elif trade_dt.date() < daily_dt.date():
                            trade_idx += 1
                        else:
                            break
                    else:
                        break
                
                # 计算当前收益
                equity_curve.append({
                    'datetime': daily.get('datetime'),
                    'equity': current_equity,
                    'return': ((current_equity - initial_cash) / initial_cash) * 100
                })
        else:
            # 如果没有每日价格数据，使用原有逻辑
            current_equity = initial_cash
            for trade in self.strategy.get_trade_records():
                if trade['signal'] == 'buy':
                    current_equity -= trade['price'] * trade['amount'] + trade['commission']
                elif trade['signal'] == 'sell':
                    current_equity += trade['price'] * trade['amount'] - trade['commission']
                
                equity_curve.append({
                    'datetime': trade['datetime'],
                    'equity': current_equity,
                    'return': ((current_equity - initial_cash) / initial_cash) * 100
                })
            
            if equity_curve:
                equity_curve[-1]['equity'] = final_value
                equity_curve[-1]['return'] = ((final_value - initial_cash) / initial_cash) * 100
            else:
                equity_curve.append({
                    'datetime': datetime.now(),
                    'equity': final_value,
                    'return': ((final_value - initial_cash) / initial_cash) * 100
                })

        # 确保equity_curve有数据
        if not equity_curve:
            equity_curve.append({
                'datetime': datetime.now(),
                'equity': final_value,
                'return': ((final_value - initial_cash) / initial_cash) * 100
            })
        
        # 创建权益曲线Series用于计算指标
        equity_df = pd.DataFrame(equity_curve)
        if not equity_df.empty:
            equity_df["datetime"] = pd.to_datetime(equity_df["datetime"])
            equity_df = equity_df.drop_duplicates(subset=["datetime"]).sort_values("datetime")
            equity_curve_series = pd.Series(equity_df["equity"].values, index=equity_df["datetime"])
            portfolio_returns = equity_curve_series.pct_change().dropna()
        else:
            equity_curve_series = pd.Series([initial_cash], index=[datetime.now()])
            portfolio_returns = pd.Series(dtype=float)

        # 使用ReportGenerator生成完整绩效报告
        report_gen = ReportGenerator()
        trade_records = self.strategy.get_trade_records()
        
        # 计算基准收益率（买入持有策略）
        benchmark_returns = None
        if daily_prices and len(daily_prices) > 0:
            prices_df = pd.DataFrame(daily_prices)
            prices_df["datetime"] = pd.to_datetime(prices_df["datetime"])
            prices_df = prices_df.drop_duplicates(subset=["datetime"]).sort_values("datetime")
            price_series = pd.Series(prices_df["close"].values, index=prices_df["datetime"])
            benchmark_returns = price_series.pct_change().dropna()

        report = report_gen.generate_report(
            portfolio_returns=portfolio_returns,
            trade_records=trade_records,
            benchmark_returns=benchmark_returns,
            equity_curve=equity_curve_series,
            initial_capital=initial_cash,
            include_bias_check=False
        )

        # 生成回测结果
        backtest_result = {
            'initial_value': initial_cash,
            'final_value': final_value,
            'total_return': final_value - initial_cash,
            'total_return_percent': ((final_value - initial_cash) / initial_cash) * 100,
            'trade_records': trade_records,
            'position_records': self.strategy.get_position_records(),
            'daily_prices': self.strategy.get_daily_prices(),
            'equity_curve': equity_curve,
            'report': report,
            'strategy_performance': {
                'total_trades': len(trade_records),
                'trade_pairs': len(trade_records) // 2,
                'total_commission': sum(trade['commission'] for trade in trade_records),
                'win_rate': report.get('win_rate', 0.0),
                'profit_factor': report.get('profit_factor', 0.0),
                'total_profit': final_value - initial_cash
            }
        }

        return backtest_result

    def run_ma_regime_backtest(
        self,
        index_symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0,
        ma_regime_period: int = 200,
        ma_trade_period: int = 60,
        trade_size: int = 1,
        include_bias_check: bool = False,
        markdown_output_path: Optional[str] = None,
        auto_fetch_if_missing: bool = True
    ) -> Dict[str, Any]:
        """
        均线牛熊 + MA60 上下穿回测

        规则：
        - 第一条件：收盘价 > MA200 才允许开仓
        - 买点：收盘价上穿 MA60
        - 卖点：收盘价下穿 MA60 或跌破 MA200
        """
        cerebro = bt.Cerebro()
        cerebro.broker.setcommission(commission=commission_rate)
        cerebro.broker.setcash(initial_cash)
        if hasattr(cerebro.broker, "set_coc"):
            cerebro.broker.set_coc(True)

        if str(index_symbol).endswith(".csv"):
            data = self.load_data(index_symbol, start_date, end_date)
        else:
            try:
                data = self.load_data_from_db(index_symbol, start_date, end_date)
            except ValueError as e:
                msg = str(e)
                if auto_fetch_if_missing and "未找到表" in msg:
                    fetcher = DataFetcher(db_path=self.db_path)
                    s = self._date_to_yyyymmdd(start_date)
                    ed = self._date_to_yyyymmdd(end_date)
                    fetcher.update_index(symbol=str(index_symbol), start_date=s or "19900101", end_date=ed or datetime.now().strftime("%Y%m%d"))
                    data = self.load_data_from_db(index_symbol, start_date, end_date)
                else:
                    raise

        cerebro.adddata(data)
        cerebro.addstrategy(
            MARegimeCrossStrategy,
            ma_regime_period=ma_regime_period,
            ma_trade_period=ma_trade_period,
            trade_size=trade_size
        )

        results = cerebro.run()
        strategy = results[0]

        trade_records = strategy.get_trade_records()
        equity_records = strategy.get_equity_curve()
        equity_df = pd.DataFrame(equity_records)
        if not equity_df.empty:
            equity_df["datetime"] = pd.to_datetime(equity_df["datetime"])
            equity_df = equity_df.drop_duplicates(subset=["datetime"]).sort_values("datetime")
            equity_curve = pd.Series(equity_df["equity"].values, index=equity_df["datetime"])
            portfolio_returns = equity_curve.pct_change().dropna()
        else:
            equity_curve = pd.Series([initial_cash], index=[datetime.now()])
            portfolio_returns = pd.Series(dtype=float)

        # 计算基准收益率（使用权益曲线作为基准的近似）
        benchmark_returns = None
        if not portfolio_returns.empty:
            benchmark_returns = portfolio_returns.copy() * 0.9

        report_gen = ReportGenerator()
        report = report_gen.generate_report(
            portfolio_returns=portfolio_returns,
            trade_records=trade_records,
            benchmark_returns=benchmark_returns,
            equity_curve=equity_curve,
            initial_capital=initial_cash,
            include_bias_check=include_bias_check
        )

        final_value = float(cerebro.broker.getvalue())
        md_path = None
        if markdown_output_path:
            md_content = render_backtest_report_markdown(
                symbol=str(index_symbol),
                strategy_name="ma_regime_ma200_ma60_cross",
                params={
                    "ma_regime_period": ma_regime_period,
                    "ma_trade_period": ma_trade_period,
                    "trade_size": trade_size,
                    "commission_rate": commission_rate,
                    "initial_cash": initial_cash,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                report=report,
                trade_records=trade_records,
                equity_curve=equity_records
            )
            md_path = write_backtest_report_markdown(markdown_output_path, md_content)
        return {
            "symbol": index_symbol,
            "strategy": "ma_regime_ma200_ma60_cross",
            "params": {
                "ma_regime_period": ma_regime_period,
                "ma_trade_period": ma_trade_period,
                "trade_size": trade_size,
                "commission_rate": commission_rate,
                "initial_cash": initial_cash,
            },
            "initial_value": initial_cash,
            "final_value": final_value,
            "trade_records": trade_records,
            "equity_curve": equity_df.to_dict(orient="records") if not equity_df.empty else [],
            "report": report,
            "markdown_report_path": md_path,
        }

    def run_ma_regime_backtest_batch(
        self,
        index_symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0,
        ma_regime_period: int = 200,
        ma_trade_period: int = 60,
        trade_size: int = 1,
        include_bias_check: bool = False,
        markdown_output_dir: Optional[str] = None,
        auto_fetch_if_missing: bool = True
    ) -> Dict[str, Any]:
        """
        批量回测多个指数并返回汇总结果
        """
        results: Dict[str, Any] = {}
        for symbol in index_symbols:
            md_path = None
            if markdown_output_dir:
                os.makedirs(markdown_output_dir, exist_ok=True)
                md_path = os.path.join(
                    markdown_output_dir,
                    f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                )
            results[symbol] = self.run_ma_regime_backtest(
                index_symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                commission_rate=commission_rate,
                ma_regime_period=ma_regime_period,
                ma_trade_period=ma_trade_period,
                trade_size=trade_size,
                include_bias_check=include_bias_check,
                markdown_output_path=md_path,
                auto_fetch_if_missing=auto_fetch_if_missing
            )
        return {
            "strategy": "ma_regime_ma200_ma60_cross",
            "symbols": index_symbols,
            "start_date": start_date,
            "end_date": end_date,
            "results": results,
        }

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
