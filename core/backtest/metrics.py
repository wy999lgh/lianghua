# -*- coding: utf-8 -*-
"""
网格交易系统 - 回测绩效指标计算
Backtest metrics calculation module
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime


class BacktestMetrics:
    """
    回测绩效指标计算类

    提供各种回测绩效指标的计算方法，包括：
    - 年化收益率
    - 最大回撤
    - 夏普比率
    - 胜率
    - 盈利因子
    - 索提诺比率
    - 卡尔玛比率
    等
    """

    @staticmethod
    def annual_return(equity_curve: pd.Series, trading_days: int = 252) -> float:
        """
        计算年化收益率

        参数：
        equity_curve: pd.Series - 权益曲线，索引为日期
        trading_days: int - 年交易日数量，默认252天

        返回：
        float - 年化收益率
        """
        if len(equity_curve) < 2:
            return 0.0

        total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
        n_days = len(equity_curve)

        if n_days <= 0:
            return 0.0

        return (1 + total_return) ** (trading_days / n_days) - 1

    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> float:
        """
        计算最大回撤

        参数：
        equity_curve: pd.Series - 权益曲线

        返回：
        float - 最大回撤（负数）
        """
        if len(equity_curve) < 2:
            return 0.0

        # 计算历史最高点
        peak = equity_curve.expanding(min_periods=1).max()
        # 计算回撤
        drawdown = (equity_curve - peak) / peak
        # 返回最大回撤
        return float(drawdown.min())

    @staticmethod
    def max_drawdown_duration(equity_curve: pd.Series) -> int:
        """
        计算最大回撤持续天数

        参数：
        equity_curve: pd.Series - 权益曲线

        返回：
        int - 最大回撤持续天数
        """
        if len(equity_curve) < 2:
            return 0

        peak = equity_curve.expanding(min_periods=1).max()
        drawdown = (equity_curve - peak) / peak

        # 找出回撤开始和结束的位置
        max_duration = 0
        current_duration = 0

        for i in range(len(drawdown)):
            if drawdown.iloc[i] < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.03,
                     trading_days: int = 252) -> float:
        """
        计算夏普比率

        参数：
        returns: pd.Series - 日收益率序列
        risk_free_rate: float - 无风险利率，默认3%
        trading_days: int - 年交易日数量，默认252天

        返回：
        float - 夏普比率
        """
        if len(returns) < 2:
            return 0.0

        # 计算超额收益
        daily_rf = risk_free_rate / trading_days
        excess_returns = returns - daily_rf

        # 计算标准差
        std = returns.std()

        if std == 0 or np.isnan(std):
            return 0.0

        # 年化夏普比率
        return float(np.sqrt(trading_days) * excess_returns.mean() / std)

    @staticmethod
    def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.03,
                      trading_days: int = 252) -> float:
        """
        计算索提诺比率
        只考虑下行风险

        参数：
        returns: pd.Series - 日收益率序列
        risk_free_rate: float - 无风险利率，默认3%
        trading_days: int - 年交易日数量，默认252天

        返回：
        float - 索提诺比率
        """
        if len(returns) < 2:
            return 0.0

        # 计算超额收益
        daily_rf = risk_free_rate / trading_days
        excess_returns = returns - daily_rf

        # 只计算负收益的标准差（下行风险）
        negative_returns = returns[returns < 0]

        if len(negative_returns) == 0:
            # 如果没有负收益，返回一个很大的值表示极好的表现
            return float('inf') if excess_returns.mean() > 0 else 0.0

        downside_std = negative_returns.std()

        if downside_std == 0 or np.isnan(downside_std):
            return 0.0

        return float(np.sqrt(trading_days) * excess_returns.mean() / downside_std)

    @staticmethod
    def calmar_ratio(equity_curve: pd.Series, trading_days: int = 252) -> float:
        """
        计算卡尔玛比率
        年化收益率 / |最大回撤|

        参数：
        equity_curve: pd.Series - 权益曲线
        trading_days: int - 年交易日数量，默认252天

        返回：
        float - 卡尔玛比率
        """
        annual_ret = BacktestMetrics.annual_return(equity_curve, trading_days)
        max_dd = BacktestMetrics.max_drawdown(equity_curve)

        if max_dd == 0:
            return float('inf') if annual_ret > 0 else 0.0

        return float(annual_ret / abs(max_dd))

    @staticmethod
    def win_rate(trade_records: List[Dict]) -> float:
        """
        计算胜率

        参数：
        trade_records: List[Dict] - 交易记录列表，每条记录需包含 'pnl' 或 'profit' 字段

        返回：
        float - 胜率 (0-1)
        """
        if not trade_records:
            return 0.0

        # 配对计算盈亏
        # 假设交易记录按时间顺序排列，买卖配对
        profits = []
        buy_records = []

        for record in trade_records:
            # 如果记录中已有pnl字段，直接使用
            if 'pnl' in record:
                profits.append(record['pnl'])
            elif 'profit' in record:
                profits.append(record['profit'])
            else:
                # 否则需要配对计算
                if record.get('signal') == 'buy':
                    buy_records.append(record)
                elif record.get('signal') == 'sell' and buy_records:
                    buy_record = buy_records.pop(0)
                    buy_price = buy_record.get('price', 0)
                    sell_price = record.get('price', 0)
                    quantity = min(buy_record.get('amount', 0),
                                   record.get('amount', 0))
                    pnl = (sell_price - buy_price) * quantity
                    profits.append(pnl)

        if not profits:
            return 0.0

        winning_trades = sum(1 for p in profits if p > 0)
        return float(winning_trades / len(profits))

    @staticmethod
    def profit_factor(trade_records: List[Dict]) -> float:
        """
        计算盈利因子
        总盈利 / 总亏损

        参数：
        trade_records: List[Dict] - 交易记录列表

        返回：
        float - 盈利因子
        """
        if not trade_records:
            return 0.0

        # 配对计算盈亏
        profits = []
        buy_records = []

        for record in trade_records:
            if 'pnl' in record:
                profits.append(record['pnl'])
            elif 'profit' in record:
                profits.append(record['profit'])
            else:
                if record.get('signal') == 'buy':
                    buy_records.append(record)
                elif record.get('signal') == 'sell' and buy_records:
                    buy_record = buy_records.pop(0)
                    buy_price = buy_record.get('price', 0)
                    sell_price = record.get('price', 0)
                    quantity = min(buy_record.get('amount', 0),
                                   record.get('amount', 0))
                    pnl = (sell_price - buy_price) * quantity
                    profits.append(pnl)

        if not profits:
            return 0.0

        total_profit = sum(p for p in profits if p > 0)
        total_loss = abs(sum(p for p in profits if p < 0))

        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0

        return float(total_profit / total_loss)

    @staticmethod
    def average_trade_pnl(trade_records: List[Dict]) -> float:
        """
        计算平均每笔交易盈亏

        参数：
        trade_records: List[Dict] - 交易记录列表

        返回：
        float - 平均每笔交易盈亏
        """
        if not trade_records:
            return 0.0

        profits = []
        buy_records = []

        for record in trade_records:
            if 'pnl' in record:
                profits.append(record['pnl'])
            elif 'profit' in record:
                profits.append(record['profit'])
            else:
                if record.get('signal') == 'buy':
                    buy_records.append(record)
                elif record.get('signal') == 'sell' and buy_records:
                    buy_record = buy_records.pop(0)
                    buy_price = buy_record.get('price', 0)
                    sell_price = record.get('price', 0)
                    quantity = min(buy_record.get('amount', 0),
                                   record.get('amount', 0))
                    pnl = (sell_price - buy_price) * quantity
                    profits.append(pnl)

        if not profits:
            return 0.0

        return float(np.mean(profits))

    @staticmethod
    def max_consecutive_wins(trade_records: List[Dict]) -> int:
        """
        计算最大连续盈利次数

        参数：
        trade_records: List[Dict] - 交易记录列表

        返回：
        int - 最大连续盈利次数
        """
        profits = BacktestMetrics._extract_profits(trade_records)

        if not profits:
            return 0

        max_wins = 0
        current_wins = 0

        for p in profits:
            if p > 0:
                current_wins += 1
                max_wins = max(max_wins, current_wins)
            else:
                current_wins = 0

        return max_wins

    @staticmethod
    def max_consecutive_losses(trade_records: List[Dict]) -> int:
        """
        计算最大连续亏损次数

        参数：
        trade_records: List[Dict] - 交易记录列表

        返回：
        int - 最大连续亏损次数
        """
        profits = BacktestMetrics._extract_profits(trade_records)

        if not profits:
            return 0

        max_losses = 0
        current_losses = 0

        for p in profits:
            if p < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0

        return max_losses

    @staticmethod
    def _extract_profits(trade_records: List[Dict]) -> List[float]:
        """
        从交易记录中提取盈亏列表

        参数：
        trade_records: List[Dict] - 交易记录列表

        返回：
        List[float] - 盈亏列表
        """
        profits = []
        buy_records = []

        for record in trade_records:
            if 'pnl' in record:
                profits.append(record['pnl'])
            elif 'profit' in record:
                profits.append(record['profit'])
            else:
                if record.get('signal') == 'buy':
                    buy_records.append(record)
                elif record.get('signal') == 'sell' and buy_records:
                    buy_record = buy_records.pop(0)
                    buy_price = buy_record.get('price', 0)
                    sell_price = record.get('price', 0)
                    quantity = min(buy_record.get('amount', 0),
                                   record.get('amount', 0))
                    pnl = (sell_price - buy_price) * quantity
                    profits.append(pnl)

        return profits

    @staticmethod
    def total_commission(trade_records: List[Dict]) -> float:
        """
        计算总手续费

        参数：
        trade_records: List[Dict] - 交易记录列表

        返回：
        float - 总手续费
        """
        if not trade_records:
            return 0.0

        return float(sum(record.get('commission', 0) for record in trade_records))

    @staticmethod
    def calculate_returns(equity_curve: pd.Series) -> pd.Series:
        """
        从权益曲线计算日收益率

        参数：
        equity_curve: pd.Series - 权益曲线

        返回：
        pd.Series - 日收益率序列
        """
        if len(equity_curve) < 2:
            return pd.Series(dtype=float)

        return equity_curve.pct_change().dropna()

    @staticmethod
    def volatility(returns: pd.Series, trading_days: int = 252) -> float:
        """
        计算年化波动率

        参数：
        returns: pd.Series - 日收益率序列
        trading_days: int - 年交易日数量，默认252天

        返回：
        float - 年化波动率
        """
        if len(returns) < 2:
            return 0.0

        return float(returns.std() * np.sqrt(trading_days))

    @staticmethod
    def calculate_all(equity_curve: Union[pd.Series, List[Dict]],
                      trade_records: List[Dict],
                      initial_value: float = 100000.0,
                      risk_free_rate: float = 0.03,
                      trading_days: int = 252) -> Dict:
        """
        计算所有指标并返回汇总

        参数：
        equity_curve: pd.Series 或 List[Dict] - 权益曲线
        trade_records: List[Dict] - 交易记录列表
        initial_value: float - 初始资金
        risk_free_rate: float - 无风险利率
        trading_days: int - 年交易日数量

        返回：
        Dict - 包含所有指标的字典
        """
        # 如果权益曲线是列表，转换为Series
        if isinstance(equity_curve, list):
            if not equity_curve:
                equity_series = pd.Series([initial_value], dtype=float)
            else:
                equity_series = pd.Series(
                    [e.get('equity', initial_value) for e in equity_curve],
                    index=[e.get('datetime', datetime.now())
                           for e in equity_curve]
                )
        else:
            equity_series = equity_curve

        # 计算日收益率
        returns = BacktestMetrics.calculate_returns(equity_series)

        # 计算各项指标
        metrics = {
            # 收益指标
            'total_return': float(equity_series.iloc[-1] / equity_series.iloc[0] - 1) if len(equity_series) > 0 else 0.0,
            'annual_return': BacktestMetrics.annual_return(equity_series, trading_days),
            'final_value': float(equity_series.iloc[-1]) if len(equity_series) > 0 else initial_value,

            # 风险指标
            'max_drawdown': BacktestMetrics.max_drawdown(equity_series),
            'max_drawdown_duration': BacktestMetrics.max_drawdown_duration(equity_series),
            'volatility': BacktestMetrics.volatility(returns, trading_days),

            # 风险调整后收益
            'sharpe_ratio': BacktestMetrics.sharpe_ratio(returns, risk_free_rate, trading_days),
            'sortino_ratio': BacktestMetrics.sortino_ratio(returns, risk_free_rate, trading_days),
            'calmar_ratio': BacktestMetrics.calmar_ratio(equity_series, trading_days),

            # 交易统计
            'total_trades': len(trade_records),
            'trade_pairs': len(trade_records) // 2,
            'win_rate': BacktestMetrics.win_rate(trade_records),
            'profit_factor': BacktestMetrics.profit_factor(trade_records),
            'average_trade_pnl': BacktestMetrics.average_trade_pnl(trade_records),
            'max_consecutive_wins': BacktestMetrics.max_consecutive_wins(trade_records),
            'max_consecutive_losses': BacktestMetrics.max_consecutive_losses(trade_records),
            'total_commission': BacktestMetrics.total_commission(trade_records),
        }

        return metrics

    @staticmethod
    def format_metrics(metrics: Dict) -> str:
        """
        格式化输出指标

        参数：
        metrics: Dict - 指标字典

        返回：
        str - 格式化的指标字符串
        """
        lines = [
            "=" * 50,
            "回测绩效指标汇总",
            "=" * 50,
            "",
            "【收益指标】",
            f"  总收益率: {metrics.get('total_return', 0) * 100:.2f}%",
            f"  年化收益率: {metrics.get('annual_return', 0) * 100:.2f}%",
            f"  最终资金: {metrics.get('final_value', 0):,.2f}",
            "",
            "【风险指标】",
            f"  最大回撤: {metrics.get('max_drawdown', 0) * 100:.2f}%",
            f"  最大回撤持续天数: {metrics.get('max_drawdown_duration', 0)}",
            f"  年化波动率: {metrics.get('volatility', 0) * 100:.2f}%",
            "",
            "【风险调整后收益】",
            f"  夏普比率: {metrics.get('sharpe_ratio', 0):.2f}",
            f"  索提诺比率: {metrics.get('sortino_ratio', 0):.2f}",
            f"  卡尔玛比率: {metrics.get('calmar_ratio', 0):.2f}",
            "",
            "【交易统计】",
            f"  总交易次数: {metrics.get('total_trades', 0)}",
            f"  交易对数量: {metrics.get('trade_pairs', 0)}",
            f"  胜率: {metrics.get('win_rate', 0) * 100:.2f}%",
            f"  盈利因子: {metrics.get('profit_factor', 0):.2f}",
            f"  平均每笔盈亏: {metrics.get('average_trade_pnl', 0):.2f}",
            f"  最大连续盈利: {metrics.get('max_consecutive_wins', 0)}",
            f"  最大连续亏损: {metrics.get('max_consecutive_losses', 0)}",
            f"  总手续费: {metrics.get('total_commission', 0):.2f}",
            "",
            "=" * 50,
        ]

        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    import numpy as np

    # 模拟权益曲线
    np.random.seed(42)
    n_days = 252
    returns = np.random.normal(0.001, 0.02, n_days)
    equity = [100000]
    for r in returns:
        equity.append(equity[-1] * (1 + r))

    equity_series = pd.Series(equity, index=pd.date_range(
        '2023-01-01', periods=len(equity)))
    returns_series = equity_series.pct_change().dropna()

    # 模拟交易记录
    trade_records = [
        {'datetime': '2023-01-01', 'signal': 'buy',
            'price': 10.0, 'amount': 100, 'commission': 1.0},
        {'datetime': '2023-01-05', 'signal': 'sell',
            'price': 10.5, 'amount': 100, 'commission': 1.05},
        {'datetime': '2023-01-10', 'signal': 'buy',
            'price': 10.2, 'amount': 100, 'commission': 1.02},
        {'datetime': '2023-01-15', 'signal': 'sell',
            'price': 9.8, 'amount': 100, 'commission': 0.98},
    ]

    # 计算所有指标
    metrics = BacktestMetrics.calculate_all(equity_series, trade_records)

    # 输出格式化结果
    print(BacktestMetrics.format_metrics(metrics))
