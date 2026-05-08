# -*- coding: utf-8 -*-
"""
网格交易系统 - 绩效报告生成器
Performance report generator module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from .bias_checker import BiasChecker


class ReportGenerator:
    """
    回测绩效报告生成器

    提供完整的回测绩效分析和报告生成功能，包括：
    - 收益指标（总收益、年化收益、波动率等）
    - 风险指标（最大回撤、夏普比率、卡尔玛比率等）
    - 交易统计（胜率、盈利因子、连续盈亏等）
    - 基准对比（Alpha、Beta、信息比率等）
    - 偏差检查
    """

    # 默认配置
    DEFAULT_CONFIG = {
        'risk_free_rate': 0.03,      # 无风险利率 3%
        'trading_days': 252,          # 年交易日数量
        'benchmark_name': '基准',     # 基准名称
    }

    def __init__(self, config: Dict = None):
        """
        初始化报告生成器

        Args:
            config: 自定义配置，可覆盖默认值
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        self.bias_checker = BiasChecker()

    def generate_report(self, portfolio_returns: pd.Series,
                        trade_records: List[Dict] = None,
                        benchmark_returns: pd.Series = None,
                        equity_curve: pd.Series = None,
                        initial_capital: float = 100000.0,
                        include_bias_check: bool = False,
                        market_data: pd.DataFrame = None,
                        strategy_params: Dict = None) -> Dict[str, Any]:
        """
        生成完整的绩效报告

        Args:
            portfolio_returns: 策略日收益率序列，索引为日期
            trade_records: 交易记录列表，每条记录可包含:
                - datetime: 交易时间
                - signal: 'buy' 或 'sell'
                - price: 成交价格
                - amount/quantity: 成交数量
                - pnl/profit: 盈亏（如已计算）
                - commission: 手续费
                - slippage: 滑点
            benchmark_returns: 基准收益率序列（可选）
            equity_curve: 权益曲线（可选，如未提供则从收益率计算）
            initial_capital: 初始资金
            include_bias_check: 是否包含偏差检查
            market_data: 市场数据（用于偏差检查）
            strategy_params: 策略参数（用于过拟合检查）

        Returns:
            Dict: 完整的绩效报告字典
        """
        report = {}

        # 确保收益率序列有效
        if portfolio_returns is None or len(portfolio_returns) == 0:
            return self._empty_report()

        # 清理数据
        portfolio_returns = portfolio_returns.dropna()
        if len(portfolio_returns) == 0:
            return self._empty_report()

        # 如果没有提供权益曲线，从收益率计算
        if equity_curve is None:
            equity_curve = self._returns_to_equity(
                portfolio_returns, initial_capital)

        # 基础绩效指标
        report['total_return'] = self._calculate_total_return(
            portfolio_returns)
        report['annual_return'] = self._calculate_annual_return(
            portfolio_returns)
        report['sharpe_ratio'] = self._calculate_sharpe_ratio(
            portfolio_returns)
        report['sortino_ratio'] = self._calculate_sortino_ratio(
            portfolio_returns)
        report['max_drawdown'] = self._calculate_max_drawdown(
            portfolio_returns)
        report['max_drawdown_duration'] = self._calculate_max_drawdown_duration(
            equity_curve)
        report['volatility'] = self._calculate_volatility(portfolio_returns)
        report['calmar_ratio'] = self._calculate_calmar_ratio(
            portfolio_returns)
        report['downside_deviation'] = self._calculate_downside_deviation(
            portfolio_returns)

        # 收益分布统计
        report['skewness'] = self._calculate_skewness(portfolio_returns)
        report['kurtosis'] = self._calculate_kurtosis(portfolio_returns)
        report['var_95'] = self._calculate_var(portfolio_returns, 0.95)
        report['cvar_95'] = self._calculate_cvar(portfolio_returns, 0.95)

        # 资金相关
        report['initial_capital'] = initial_capital
        report['final_capital'] = float(
            equity_curve.iloc[-1]) if len(equity_curve) > 0 else initial_capital
        report['total_profit'] = report['final_capital'] - initial_capital

        # 交易统计
        if trade_records:
            report['trade_count'] = len(trade_records)
            report['win_rate'] = self._calculate_win_rate(trade_records)
            report['profit_factor'] = self._calculate_profit_factor(
                trade_records)
            report['avg_profit'] = self._calculate_avg_profit(trade_records)
            report['avg_win'] = self._calculate_avg_win(trade_records)
            report['avg_loss'] = self._calculate_avg_loss(trade_records)
            avg_win = float(report.get("avg_win", 0.0) or 0.0)
            avg_loss = float(report.get("avg_loss", 0.0) or 0.0)
            if avg_loss < 0:
                report["profit_loss_ratio"] = float(avg_win / abs(avg_loss)) if abs(avg_loss) > 0 else float("inf")
            else:
                report["profit_loss_ratio"] = float("inf") if avg_win > 0 else 0.0
            report['max_consecutive_wins'] = self._calculate_max_consecutive(
                trade_records, True)
            report['max_consecutive_losses'] = self._calculate_max_consecutive(
                trade_records, False)
            report['total_commission'] = self._calculate_total_commission(
                trade_records)
            report['avg_holding_period'] = self._calculate_avg_holding_period(
                trade_records)
            report['trade_frequency'] = self._calculate_trade_frequency(
                trade_records, portfolio_returns)

        # 基准对比
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            # 对齐日期
            aligned = self._align_series(portfolio_returns, benchmark_returns)
            if len(aligned[0]) > 0:
                report['alpha'] = self._calculate_alpha(aligned[0], aligned[1])
                report['beta'] = self._calculate_beta(aligned[0], aligned[1])
                report['information_ratio'] = self._calculate_information_ratio(
                    aligned[0], aligned[1])
                report['tracking_error'] = self._calculate_tracking_error(
                    aligned[0], aligned[1])
                report['correlation'] = self._calculate_correlation(
                    aligned[0], aligned[1])
                report['benchmark_return'] = self._calculate_total_return(
                    aligned[1])
                report['benchmark_volatility'] = self._calculate_volatility(
                    aligned[1])
                report['excess_return'] = report['total_return'] - \
                    report['benchmark_return']

        # 时间信息
        report['start_date'] = str(portfolio_returns.index[0])
        report['end_date'] = str(portfolio_returns.index[-1])
        report['trading_days'] = len(portfolio_returns)
        report['years'] = len(portfolio_returns) / self.config['trading_days']
        report['generated_at'] = datetime.now().isoformat()

        # 月度收益
        report['monthly_returns'] = self._calculate_monthly_returns(
            portfolio_returns)
        
        # 滚动收益（1个月、3个月、6个月、12个月）
        rolling_df = self._calculate_rolling_returns(portfolio_returns)
        if not rolling_df.empty:
            rolling_data = []
            for idx, row in rolling_df.iterrows():
                rolling_data.append({
                    'date': idx.strftime('%Y-%m'),
                    '1_month': row.get('window_30d'),
                    '3_month': row.get('window_90d'),
                    '6_month': row.get('window_180d'),
                    '12_month': row.get('window_365d')
                })
            report['rolling_returns'] = rolling_data

        # 偏差检查
        if include_bias_check:
            report['bias_check'] = self.bias_checker.check_all(
                data=market_data,
                trade_records=trade_records,
                strategy_params=strategy_params
            )

        return report

    def _empty_report(self) -> Dict[str, Any]:
        """返回空报告"""
        return {
            'error': '无有效数据',
            'total_return': 0.0,
            'annual_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trading_days': 0,
            'generated_at': datetime.now().isoformat()
        }

    def _returns_to_equity(self, returns: pd.Series,
                           initial_capital: float) -> pd.Series:
        """从收益率序列计算权益曲线"""
        equity = initial_capital * (1 + returns).cumprod()
        # 在前面插入初始资金
        equity = pd.concat([
            pd.Series([initial_capital], index=[
                      returns.index[0] - pd.Timedelta(days=1)]),
            equity
        ])
        return equity

    def _align_series(self, series1: pd.Series,
                      series2: pd.Series) -> tuple:
        """对齐两个时间序列"""
        common_idx = series1.index.intersection(series2.index)
        return series1.loc[common_idx], series2.loc[common_idx]

    def _calculate_total_return(self, returns: pd.Series) -> float:
        """
        计算总收益率

        Args:
            returns: 日收益率序列

        Returns:
            float: 总收益率（如 0.5 表示 50%）
        """
        if len(returns) == 0:
            return 0.0
        return float((1 + returns).prod() - 1)

    def _calculate_annual_return(self, returns: pd.Series) -> float:
        """
        计算年化收益率

        使用几何平均方法：(1 + total_return) ^ (252 / n) - 1

        Args:
            returns: 日收益率序列

        Returns:
            float: 年化收益率
        """
        if len(returns) == 0:
            return 0.0

        total_return = self._calculate_total_return(returns)
        n_days = len(returns)
        trading_days = self.config['trading_days']

        if n_days == 0:
            return 0.0

        # 处理负收益的情况
        if total_return <= -1:
            return -1.0

        return float((1 + total_return) ** (trading_days / n_days) - 1)

    def _calculate_sharpe_ratio(self, returns: pd.Series,
                                risk_free_rate: float = None) -> float:
        """
        计算夏普比率

        Sharpe = (年化收益 - 无风险利率) / 年化波动率
               = sqrt(252) * (平均超额日收益) / 日收益标准差

        Args:
            returns: 日收益率序列
            risk_free_rate: 无风险利率，默认使用配置值

        Returns:
            float: 夏普比率
        """
        if len(returns) < 2:
            return 0.0

        if risk_free_rate is None:
            risk_free_rate = self.config['risk_free_rate']

        trading_days = self.config['trading_days']
        daily_rf = risk_free_rate / trading_days

        excess_returns = returns - daily_rf
        std = returns.std()

        if std == 0 or np.isnan(std):
            return 0.0

        return float(np.sqrt(trading_days) * excess_returns.mean() / std)

    def _calculate_sortino_ratio(self, returns: pd.Series,
                                 risk_free_rate: float = None) -> float:
        """
        计算索提诺比率

        只考虑下行风险（负收益的标准差）
        Sortino = (年化收益 - 无风险利率) / 下行标准差

        Args:
            returns: 日收益率序列
            risk_free_rate: 无风险利率

        Returns:
            float: 索提诺比率
        """
        if len(returns) < 2:
            return 0.0

        if risk_free_rate is None:
            risk_free_rate = self.config['risk_free_rate']

        trading_days = self.config['trading_days']
        daily_rf = risk_free_rate / trading_days

        excess_returns = returns - daily_rf
        negative_returns = returns[returns < 0]

        if len(negative_returns) == 0:
            return float('inf') if excess_returns.mean() > 0 else 0.0

        downside_std = negative_returns.std()

        if downside_std == 0 or np.isnan(downside_std):
            return 0.0

        return float(np.sqrt(trading_days) * excess_returns.mean() / downside_std)

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            returns: 日收益率序列

        Returns:
            float: 最大回撤（负数，如 -0.2 表示 -20%）
        """
        if len(returns) < 2:
            return 0.0

        # 计算累计收益
        cumulative = (1 + returns).cumprod()
        # 历史最高点
        peak = cumulative.expanding(min_periods=1).max()
        # 回撤
        drawdown = (cumulative - peak) / peak

        return float(drawdown.min())

    def _calculate_max_drawdown_duration(self, equity_curve: pd.Series) -> int:
        """
        计算最大回撤持续天数

        Args:
            equity_curve: 权益曲线

        Returns:
            int: 最大回撤持续天数
        """
        if len(equity_curve) < 2:
            return 0

        peak = equity_curve.expanding(min_periods=1).max()
        drawdown = (equity_curve - peak) / peak

        max_duration = 0
        current_duration = 0

        for dd in drawdown:
            if dd < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    def _calculate_volatility(self, returns: pd.Series) -> float:
        """
        计算年化波动率

        Args:
            returns: 日收益率序列

        Returns:
            float: 年化波动率
        """
        if len(returns) < 2:
            return 0.0

        trading_days = self.config['trading_days']
        return float(returns.std() * np.sqrt(trading_days))

    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """
        计算卡尔玛比率

        Calmar = 年化收益率 / |最大回撤|

        Args:
            returns: 日收益率序列

        Returns:
            float: 卡尔玛比率
        """
        annual_return = self._calculate_annual_return(returns)
        max_dd = self._calculate_max_drawdown(returns)

        if max_dd == 0:
            return float('inf') if annual_return > 0 else 0.0

        return float(annual_return / abs(max_dd))

    def _calculate_downside_deviation(self, returns: pd.Series,
                                      mar: float = 0.0) -> float:
        """
        计算下行偏差

        Args:
            returns: 日收益率序列
            mar: 最低可接受收益率 (Minimum Acceptable Return)

        Returns:
            float: 年化下行偏差
        """
        if len(returns) < 2:
            return 0.0

        trading_days = self.config['trading_days']
        downside = returns[returns < mar] - mar

        if len(downside) == 0:
            return 0.0

        return float(np.sqrt((downside ** 2).mean()) * np.sqrt(trading_days))

    def _calculate_skewness(self, returns: pd.Series) -> float:
        """
        计算收益率偏度

        Args:
            returns: 日收益率序列

        Returns:
            float: 偏度（正值右偏，负值左偏）
        """
        if len(returns) < 3:
            return 0.0
        return float(returns.skew())

    def _calculate_kurtosis(self, returns: pd.Series) -> float:
        """
        计算收益率峰度

        Args:
            returns: 日收益率序列

        Returns:
            float: 超额峰度（正值尖峰，负值扁平）
        """
        if len(returns) < 4:
            return 0.0
        return float(returns.kurtosis())

    def _calculate_var(self, returns: pd.Series,
                       confidence: float = 0.95) -> float:
        """
        计算风险价值 (Value at Risk)

        Args:
            returns: 日收益率序列
            confidence: 置信水平

        Returns:
            float: VaR（负数，表示在置信水平下的最大损失）
        """
        if len(returns) == 0:
            return 0.0
        return float(returns.quantile(1 - confidence))

    def _calculate_cvar(self, returns: pd.Series,
                        confidence: float = 0.95) -> float:
        """
        计算条件风险价值 (Conditional VaR / Expected Shortfall)

        Args:
            returns: 日收益率序列
            confidence: 置信水平

        Returns:
            float: CVaR（负数，表示超出VaR的平均损失）
        """
        if len(returns) == 0:
            return 0.0

        var = self._calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]

        if len(tail_returns) == 0:
            return var

        return float(tail_returns.mean())

    def _calculate_monthly_returns(self, returns: pd.Series) -> Dict[str, float]:
        """
        计算月度收益率

        Args:
            returns: 日收益率序列

        Returns:
            Dict: 月度收益率字典 {'YYYY-MM': return}
        """
        if len(returns) == 0:
            return {}

        # 按月分组计算累计收益
        monthly = returns.groupby(returns.index.to_period('M')).apply(
            lambda x: (1 + x).prod() - 1
        )

        return {str(k): float(v) for k, v in monthly.items()}

    def _calculate_rolling_returns(self, returns: pd.Series, windows: List[int] = None) -> pd.DataFrame:
        """
        计算滚动收益率

        Args:
            returns: 日收益率序列
            windows: 滚动窗口大小列表（天数），默认[30, 90, 180, 365]

        Returns:
            pd.DataFrame: 包含各窗口滚动收益率的DataFrame
        """
        if len(returns) == 0:
            return pd.DataFrame()

        if windows is None:
            windows = [30, 90, 180, 365]

        result = pd.DataFrame(index=returns.index)
        
        for window in windows:
            result[f'window_{window}d'] = (1 + returns).rolling(window=window).apply(
                lambda x: x.prod() - 1, raw=True
            )
        
        return result

    def _extract_profits(self, trade_records: List[Dict]) -> List[float]:
        """
        从交易记录中提取盈亏列表

        Args:
            trade_records: 交易记录列表

        Returns:
            List[float]: 每笔交易的盈亏
        """
        profits = []
        buy_records = []

        for record in trade_records:
            # 如果记录中已有pnl/profit字段，直接使用
            if 'pnl' in record:
                profits.append(record['pnl'])
            elif 'profit' in record:
                profits.append(record['profit'])
            else:
                # 需要配对计算
                signal = record.get('signal', record.get('direction', ''))
                if signal.lower() in ['buy', 'long', '买入']:
                    buy_records.append(record)
                elif signal.lower() in ['sell', 'short', '卖出'] and buy_records:
                    buy_record = buy_records.pop(0)
                    buy_price = buy_record.get('price', 0)
                    sell_price = record.get('price', 0)
                    quantity = min(
                        buy_record.get(
                            'amount', buy_record.get('quantity', 0)),
                        record.get('amount', record.get('quantity', 0))
                    )
                    pnl = (sell_price - buy_price) * quantity
                    # 扣除手续费
                    pnl -= buy_record.get('commission', 0)
                    pnl -= record.get('commission', 0)
                    profits.append(pnl)

        return profits

    def _calculate_win_rate(self, trade_records: List[Dict]) -> float:
        """
        计算胜率

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 胜率 (0-1)
        """
        profits = self._extract_profits(trade_records)

        if not profits:
            return 0.0

        winning_trades = sum(1 for p in profits if p > 0)
        return float(winning_trades / len(profits))

    def _calculate_profit_factor(self, trade_records: List[Dict]) -> float:
        """
        计算盈利因子

        盈利因子 = 总盈利 / 总亏损

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 盈利因子
        """
        profits = self._extract_profits(trade_records)

        if not profits:
            return 0.0

        total_profit = sum(p for p in profits if p > 0)
        total_loss = abs(sum(p for p in profits if p < 0))

        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0

        return float(total_profit / total_loss)

    def _calculate_avg_profit(self, trade_records: List[Dict]) -> float:
        """
        计算平均每笔交易盈亏

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 平均盈亏
        """
        profits = self._extract_profits(trade_records)

        if not profits:
            return 0.0

        return float(np.mean(profits))

    def _calculate_avg_win(self, trade_records: List[Dict]) -> float:
        """
        计算平均盈利金额

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 平均盈利
        """
        profits = self._extract_profits(trade_records)
        wins = [p for p in profits if p > 0]

        if not wins:
            return 0.0

        return float(np.mean(wins))

    def _calculate_avg_loss(self, trade_records: List[Dict]) -> float:
        """
        计算平均亏损金额

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 平均亏损（负数）
        """
        profits = self._extract_profits(trade_records)
        losses = [p for p in profits if p < 0]

        if not losses:
            return 0.0

        return float(np.mean(losses))

    def _calculate_max_consecutive(self, trade_records: List[Dict],
                                   is_win: bool) -> int:
        """
        计算最大连续盈利/亏损次数

        Args:
            trade_records: 交易记录列表
            is_win: True计算连续盈利，False计算连续亏损

        Returns:
            int: 最大连续次数
        """
        profits = self._extract_profits(trade_records)

        if not profits:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for p in profits:
            if (is_win and p > 0) or (not is_win and p < 0):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_total_commission(self, trade_records: List[Dict]) -> float:
        """
        计算总手续费

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 总手续费
        """
        return float(sum(
            record.get('commission', 0)
            for record in trade_records
        ))

    def _calculate_avg_holding_period(self, trade_records: List[Dict]) -> float:
        """
        计算平均持仓周期（天）

        Args:
            trade_records: 交易记录列表

        Returns:
            float: 平均持仓天数
        """
        holding_periods = []
        buy_records = []

        for record in trade_records:
            signal = record.get('signal', record.get('direction', ''))

            if signal.lower() in ['buy', 'long', '买入']:
                buy_records.append(record)
            elif signal.lower() in ['sell', 'short', '卖出'] and buy_records:
                buy_record = buy_records.pop(0)

                buy_time = buy_record.get('datetime', buy_record.get('date'))
                sell_time = record.get('datetime', record.get('date'))

                if buy_time and sell_time:
                    try:
                        if isinstance(buy_time, str):
                            buy_time = pd.to_datetime(buy_time)
                        if isinstance(sell_time, str):
                            sell_time = pd.to_datetime(sell_time)

                        holding_days = (sell_time - buy_time).days
                        if holding_days >= 0:
                            holding_periods.append(holding_days)
                    except:
                        pass

        if not holding_periods:
            return 0.0

        return float(np.mean(holding_periods))

    def _calculate_trade_frequency(self, trade_records: List[Dict],
                                   returns: pd.Series) -> float:
        """
        计算交易频率（每月平均交易次数）

        Args:
            trade_records: 交易记录列表
            returns: 日收益率序列

        Returns:
            float: 每月平均交易次数
        """
        if not trade_records or len(returns) == 0:
            return 0.0

        # 计算总月数
        months = len(returns) / 21  # 约21个交易日为一个月

        if months == 0:
            return 0.0

        return float(len(trade_records) / months)

    def _calculate_alpha(self, portfolio_returns: pd.Series,
                         benchmark_returns: pd.Series) -> float:
        """
        计算Alpha（超额收益）

        使用CAPM模型: Alpha = Rp - (Rf + Beta * (Rm - Rf))

        Args:
            portfolio_returns: 策略收益率序列
            benchmark_returns: 基准收益率序列

        Returns:
            float: 年化Alpha
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        trading_days = self.config['trading_days']
        risk_free_rate = self.config['risk_free_rate']
        daily_rf = risk_free_rate / trading_days

        # 计算Beta
        beta = self._calculate_beta(portfolio_returns, benchmark_returns)

        # 计算Alpha
        portfolio_excess = portfolio_returns.mean() - daily_rf
        benchmark_excess = benchmark_returns.mean() - daily_rf

        daily_alpha = portfolio_excess - beta * benchmark_excess

        # 年化
        return float(daily_alpha * trading_days)

    def _calculate_beta(self, portfolio_returns: pd.Series,
                        benchmark_returns: pd.Series) -> float:
        """
        计算Beta（市场敏感度）

        Beta = Cov(Rp, Rm) / Var(Rm)

        Args:
            portfolio_returns: 策略收益率序列
            benchmark_returns: 基准收益率序列

        Returns:
            float: Beta系数
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        covariance = portfolio_returns.cov(benchmark_returns)
        benchmark_var = benchmark_returns.var()

        if benchmark_var == 0 or np.isnan(benchmark_var):
            return 0.0

        return float(covariance / benchmark_var)

    def _calculate_information_ratio(self, portfolio_returns: pd.Series,
                                     benchmark_returns: pd.Series) -> float:
        """
        计算信息比率

        IR = (Rp - Rb) / TrackingError

        Args:
            portfolio_returns: 策略收益率序列
            benchmark_returns: 基准收益率序列

        Returns:
            float: 信息比率
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        trading_days = self.config['trading_days']

        # 计算超额收益
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = active_returns.std()

        if tracking_error == 0 or np.isnan(tracking_error):
            return 0.0

        return float(np.sqrt(trading_days) * active_returns.mean() / tracking_error)

    def _calculate_tracking_error(self, portfolio_returns: pd.Series,
                                  benchmark_returns: pd.Series) -> float:
        """
        计算跟踪误差

        Args:
            portfolio_returns: 策略收益率序列
            benchmark_returns: 基准收益率序列

        Returns:
            float: 年化跟踪误差
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        trading_days = self.config['trading_days']
        active_returns = portfolio_returns - benchmark_returns

        return float(active_returns.std() * np.sqrt(trading_days))

    def _calculate_correlation(self, portfolio_returns: pd.Series,
                               benchmark_returns: pd.Series) -> float:
        """
        计算与基准的相关系数

        Args:
            portfolio_returns: 策略收益率序列
            benchmark_returns: 基准收益率序列

        Returns:
            float: 相关系数 (-1 到 1)
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        correlation = portfolio_returns.corr(benchmark_returns)

        if np.isnan(correlation):
            return 0.0

        return float(correlation)

    def format_report(self, report: Dict) -> str:
        """
        格式化报告为可读文本

        Args:
            report: generate_report()返回的报告字典

        Returns:
            str: 格式化的文本报告
        """
        lines = [
            "=" * 60,
            "回测绩效报告",
            "=" * 60,
            "",
            f"生成时间: {report.get('generated_at', 'N/A')}",
            f"回测区间: {report.get('start_date', 'N/A')} 至 {report.get('end_date', 'N/A')}",
            f"交易天数: {report.get('trading_days', 0)} 天 ({report.get('years', 0):.2f} 年)",
            "",
            "-" * 60,
            "【收益指标】",
            "-" * 60,
            f"  初始资金: {report.get('initial_capital', 0):,.2f}",
            f"  最终资金: {report.get('final_capital', 0):,.2f}",
            f"  总盈亏: {report.get('total_profit', 0):,.2f}",
            f"  总收益率: {report.get('total_return', 0) * 100:.2f}%",
            f"  年化收益率: {report.get('annual_return', 0) * 100:.2f}%",
        ]

        # 基准对比
        if 'benchmark_return' in report:
            lines.extend([
                "",
                f"  基准收益率: {report.get('benchmark_return', 0) * 100:.2f}%",
                f"  超额收益: {report.get('excess_return', 0) * 100:.2f}%",
            ])

        lines.extend([
            "",
            "-" * 60,
            "【风险指标】",
            "-" * 60,
            f"  最大回撤: {report.get('max_drawdown', 0) * 100:.2f}%",
            f"  最大回撤持续: {report.get('max_drawdown_duration', 0)} 天",
            f"  年化波动率: {report.get('volatility', 0) * 100:.2f}%",
            f"  下行偏差: {report.get('downside_deviation', 0) * 100:.2f}%",
            f"  VaR (95%): {report.get('var_95', 0) * 100:.2f}%",
            f"  CVaR (95%): {report.get('cvar_95', 0) * 100:.2f}%",
            "",
            "-" * 60,
            "【风险调整收益】",
            "-" * 60,
            f"  夏普比率: {report.get('sharpe_ratio', 0):.2f}",
            f"  索提诺比率: {report.get('sortino_ratio', 0):.2f}",
            f"  卡尔玛比率: {report.get('calmar_ratio', 0):.2f}",
        ])

        # Alpha/Beta
        if 'alpha' in report:
            lines.extend([
                f"  Alpha: {report.get('alpha', 0) * 100:.2f}%",
                f"  Beta: {report.get('beta', 0):.2f}",
                f"  信息比率: {report.get('information_ratio', 0):.2f}",
                f"  跟踪误差: {report.get('tracking_error', 0) * 100:.2f}%",
                f"  相关系数: {report.get('correlation', 0):.2f}",
            ])

        lines.extend([
            "",
            "-" * 60,
            "【收益分布】",
            "-" * 60,
            f"  偏度: {report.get('skewness', 0):.2f}",
            f"  峰度: {report.get('kurtosis', 0):.2f}",
        ])

        # 交易统计
        if 'trade_count' in report:
            lines.extend([
                "",
                "-" * 60,
                "【交易统计】",
                "-" * 60,
                f"  总交易次数: {report.get('trade_count', 0)}",
                f"  胜率: {report.get('win_rate', 0) * 100:.2f}%",
                f"  盈利因子: {report.get('profit_factor', 0):.2f}",
                f"  平均盈亏: {report.get('avg_profit', 0):.2f}",
                f"  平均盈利: {report.get('avg_win', 0):.2f}",
                f"  平均亏损: {report.get('avg_loss', 0):.2f}",
                f"  最大连续盈利: {report.get('max_consecutive_wins', 0)} 次",
                f"  最大连续亏损: {report.get('max_consecutive_losses', 0)} 次",
                f"  总手续费: {report.get('total_commission', 0):.2f}",
                f"  平均持仓周期: {report.get('avg_holding_period', 0):.1f} 天",
                f"  月均交易次数: {report.get('trade_frequency', 0):.1f}",
            ])

        lines.extend([
            "",
            "=" * 60,
        ])

        return "\n".join(lines)

    def to_dataframe(self, report: Dict) -> pd.DataFrame:
        """
        将报告转换为DataFrame

        Args:
            report: 报告字典

        Returns:
            pd.DataFrame: 包含指标名称和值的DataFrame
        """
        # 定义指标分组
        groups = {
            '收益指标': ['total_return', 'annual_return', 'total_profit',
                     'benchmark_return', 'excess_return'],
            '风险指标': ['max_drawdown', 'max_drawdown_duration', 'volatility',
                     'downside_deviation', 'var_95', 'cvar_95'],
            '风险调整收益': ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
                       'alpha', 'beta', 'information_ratio'],
            '交易统计': ['trade_count', 'win_rate', 'profit_factor',
                     'avg_profit', 'max_consecutive_wins', 'max_consecutive_losses'],
        }

        rows = []
        for group, metrics in groups.items():
            for metric in metrics:
                if metric in report:
                    value = report[metric]
                    if isinstance(value, float):
                        if metric in ['total_return', 'annual_return', 'max_drawdown',
                                      'volatility', 'win_rate', 'alpha', 'var_95', 'cvar_95',
                                      'benchmark_return', 'excess_return', 'tracking_error',
                                      'downside_deviation']:
                            value = f"{value * 100:.2f}%"
                        else:
                            value = f"{value:.2f}"
                    rows.append({
                        '分组': group,
                        '指标': metric,
                        '值': value
                    })

        return pd.DataFrame(rows)

    def compare_reports(self, reports: Dict[str, Dict]) -> pd.DataFrame:
        """
        对比多个策略的报告

        Args:
            reports: 策略名称到报告的映射 {'策略1': report1, '策略2': report2}

        Returns:
            pd.DataFrame: 对比表格
        """
        metrics = [
            ('总收益率', 'total_return', True),
            ('年化收益率', 'annual_return', True),
            ('最大回撤', 'max_drawdown', True),
            ('夏普比率', 'sharpe_ratio', False),
            ('索提诺比率', 'sortino_ratio', False),
            ('卡尔玛比率', 'calmar_ratio', False),
            ('胜率', 'win_rate', True),
            ('盈利因子', 'profit_factor', False),
            ('年化波动率', 'volatility', True),
        ]

        data = {}
        for strategy_name, report in reports.items():
            values = []
            for display_name, key, is_percent in metrics:
                value = report.get(key, 0)
                if isinstance(value, float):
                    if is_percent:
                        values.append(f"{value * 100:.2f}%")
                    else:
                        values.append(f"{value:.2f}")
                else:
                    values.append(str(value))
            data[strategy_name] = values

        index = [m[0] for m in metrics]
        return pd.DataFrame(data, index=index)
