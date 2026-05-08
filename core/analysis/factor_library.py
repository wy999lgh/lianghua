# -*- coding: utf-8 -*-
"""
技术指标因子库
Technical Indicator Factor Library

提供各类移动平均线（MA）技术指标的计算方法
"""

import pandas as pd
import numpy as np
from typing import List, Optional


class FactorLibrary:
    """
    技术指标因子库

    提供常用的技术分析指标计算方法，当前版本专注于移动平均线系列指标。
    所有方法均为静态方法，可直接通过类名调用。

    Example:
        >>> import pandas as pd
        >>> close_prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        >>> ma5 = FactorLibrary.ma(close_prices, period=5)
        >>> ema5 = FactorLibrary.ema(close_prices, period=5)
    """

    @staticmethod
    def ma(data: pd.Series, period: int = 20) -> pd.Series:
        """
        简单移动平均线 (Simple Moving Average, SMA)

        计算给定周期内数据的算术平均值。

        Args:
            data: 价格序列数据（通常为收盘价）
            period: 移动平均周期，默认20

        Returns:
            pd.Series: 移动平均线序列，前 period-1 个值为 NaN

        Example:
            >>> close = pd.Series([10, 11, 12, 13, 14])
            >>> FactorLibrary.ma(close, period=3)
            0          NaN
            1          NaN
            2    11.000000
            3    12.000000
            4    13.000000
            dtype: float64
        """
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int = 20) -> pd.Series:
        """
        指数移动平均线 (Exponential Moving Average, EMA)

        对近期数据赋予更高权重的移动平均线，对价格变化更为敏感。
        EMA = 当前价格 * K + 前日EMA * (1-K)，其中 K = 2/(period+1)

        Args:
            data: 价格序列数据（通常为收盘价）
            period: 移动平均周期，默认20

        Returns:
            pd.Series: 指数移动平均线序列

        Example:
            >>> close = pd.Series([10, 11, 12, 13, 14])
            >>> FactorLibrary.ema(close, period=3)
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def wma(data: pd.Series, period: int = 20) -> pd.Series:
        """
        加权移动平均线 (Weighted Moving Average, WMA)

        对近期数据赋予线性递增的权重。
        WMA = (P1*1 + P2*2 + ... + Pn*n) / (1+2+...+n)

        Args:
            data: 价格序列数据（通常为收盘价）
            period: 移动平均周期，默认20

        Returns:
            pd.Series: 加权移动平均线序列，前 period-1 个值为 NaN

        Example:
            >>> close = pd.Series([10, 11, 12, 13, 14])
            >>> FactorLibrary.wma(close, period=3)
        """
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

    @staticmethod
    def ma_cross_signal(
        data: pd.Series,
        fast_period: int = 5,
        slow_period: int = 20
    ) -> pd.Series:
        """
        均线交叉信号

        通过快速均线与慢速均线的相对位置判断趋势方向。
        - 金叉（Golden Cross）: 快线上穿慢线，看涨信号
        - 死叉（Death Cross）: 快线下穿慢线，看跌信号

        Args:
            data: 价格序列数据（通常为收盘价）
            fast_period: 快速均线周期，默认5
            slow_period: 慢速均线周期，默认20

        Returns:
            pd.Series: 信号序列
                - 1: 金叉（快线在慢线上方）
                - -1: 死叉（快线在慢线下方）
                - 0: 无信号或数据不足

        Example:
            >>> close = pd.Series([10, 11, 12, 13, 14, 15, 14, 13, 12, 11])
            >>> signals = FactorLibrary.ma_cross_signal(close, fast_period=3, slow_period=5)
        """
        fast_ma = data.rolling(window=fast_period).mean()
        slow_ma = data.rolling(window=slow_period).mean()

        signals = pd.Series(0, index=data.index)
        signals[fast_ma > slow_ma] = 1   # 金叉信号
        signals[fast_ma < slow_ma] = -1  # 死叉信号

        return signals

    @staticmethod
    def multi_ma(
        data: pd.Series,
        periods: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        多周期移动平均线

        同时计算多个周期的简单移动平均线，便于多周期趋势分析。

        Args:
            data: 价格序列数据（通常为收盘价）
            periods: 周期列表，默认 [5, 10, 20, 60]

        Returns:
            pd.DataFrame: 包含多个周期MA的DataFrame
                - 列名格式: MA{period}，如 MA5, MA10, MA20, MA60

        Example:
            >>> close = pd.Series(range(100))
            >>> mas = FactorLibrary.multi_ma(close, periods=[5, 10, 20])
            >>> mas.columns.tolist()
            ['MA5', 'MA10', 'MA20']
        """
        if periods is None:
            periods = [5, 10, 20, 60]

        result = pd.DataFrame(index=data.index)
        for period in periods:
            result[f'MA{period}'] = data.rolling(window=period).mean()

        return result
