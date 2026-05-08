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

    @staticmethod
    def cmo(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Chande Momentum Oscillator (CMO)

        CMO = (Sum(Up) - Sum(Down)) / (Sum(Up) + Sum(Down)) * 100

        Args:
            data: 价格序列（通常为收盘价）
            period: 计算周期，默认 20

        Returns:
            pd.Series: CMO 序列，范围约为 [-100, 100]
        """
        diff = data.diff()
        up = diff.clip(lower=0)
        down = (-diff).clip(lower=0)
        sum_up = up.rolling(window=period).sum()
        sum_down = down.rolling(window=period).sum()
        denominator = sum_up + sum_down
        cmo = (sum_up - sum_down) / denominator.replace(0, np.nan) * 100
        return cmo.fillna(0.0)

    @staticmethod
    def bollinger_bands_ema(
        data: pd.Series,
        period: int = 20,
        std_mult: float = 2.0
    ) -> pd.DataFrame:
        """
        基于 EMA 中轨的布林带

        Args:
            data: 价格序列（通常为收盘价）
            period: 中轨 EMA 周期，默认 20
            std_mult: 标准差倍数，默认 2.0

        Returns:
            pd.DataFrame: 包含以下列
                - bb_mid: EMA 中轨
                - bb_upper: 上轨
                - bb_lower: 下轨
                - bb_width: 带宽 (upper-lower)/mid
                - bb_pos: 价格在通道中的相对位置 [0,1]，越大越靠近上轨
        """
        bb_mid = data.ewm(span=period, adjust=False).mean()
        rolling_std = data.rolling(window=period).std()
        bb_upper = bb_mid + std_mult * rolling_std
        bb_lower = bb_mid - std_mult * rolling_std
        band_range = (bb_upper - bb_lower).replace(0, np.nan)
        bb_pos = (data - bb_lower) / band_range
        bb_width = (bb_upper - bb_lower) / bb_mid.replace(0, np.nan)

        result = pd.DataFrame(index=data.index)
        result["bb_mid"] = bb_mid
        result["bb_upper"] = bb_upper
        result["bb_lower"] = bb_lower
        result["bb_width"] = bb_width
        result["bb_pos"] = bb_pos.clip(lower=0, upper=1)
        return result

    @staticmethod
    def rolling_beta(
        y_ret: pd.Series,
        x_ret: pd.Series,
        window: int = 60
    ) -> pd.Series:
        """
        计算滚动 Beta（OLS 斜率）

        Args:
            y_ret: 目标资产收益率序列
            x_ret: 基准资产收益率序列
            window: 滚动窗口，默认 60

        Returns:
            pd.Series: beta 序列
        """
        cov = y_ret.rolling(window=window).cov(x_ret)
        var = x_ret.rolling(window=window).var()
        beta = cov / var.replace(0, np.nan)
        return beta

    @staticmethod
    def residual_momentum(
        y_ret: pd.Series,
        x_ret: pd.Series,
        beta_window: int = 60
    ) -> pd.Series:
        """
        计算残差动量 RM

        RM_t = y_ret_t - beta_t * x_ret_t

        Args:
            y_ret: 目标资产收益率
            x_ret: 基准资产收益率
            beta_window: beta 滚动窗口，默认 60

        Returns:
            pd.Series: RM 序列
        """
        beta = FactorLibrary.rolling_beta(y_ret, x_ret, window=beta_window)
        return y_ret - beta * x_ret

    @staticmethod
    def rolling_zscore(series: pd.Series, window: int = 60) -> pd.Series:
        """
        滚动 ZScore 标准化

        Args:
            series: 原始序列
            window: 滚动窗口，默认 60

        Returns:
            pd.Series: ZScore 序列
        """
        mean = series.rolling(window=window).mean()
        std = series.rolling(window=window).std().replace(0, np.nan)
        z = (series - mean) / std
        return z.replace([np.inf, -np.inf], np.nan)

    @staticmethod
    def rolling_slope(series: pd.Series, window: int = 10) -> pd.Series:
        """
        计算滚动线性斜率

        Args:
            series: 原始序列
            window: 滚动窗口，默认 10

        Returns:
            pd.Series: 斜率序列
        """
        def _slope(values: np.ndarray) -> float:
            x = np.arange(len(values), dtype=float)
            if len(values) < 2 or np.all(np.isnan(values)):
                return np.nan
            y = np.asarray(values, dtype=float)
            mask = ~np.isnan(y)
            if mask.sum() < 2:
                return np.nan
            x = x[mask]
            y = y[mask]
            x_mean = x.mean()
            y_mean = y.mean()
            denominator = ((x - x_mean) ** 2).sum()
            if denominator == 0:
                return np.nan
            return ((x - x_mean) * (y - y_mean)).sum() / denominator

        return series.rolling(window=window).apply(_slope, raw=True)

    @staticmethod
    def rolling_percentile_rank(series: pd.Series, window: int = 60) -> pd.Series:
        """
        计算滚动窗口内“当前值”的分位排名（0~1）

        Args:
            series: 原始序列
            window: 滚动窗口，默认 60

        Returns:
            pd.Series: 分位排名序列
        """
        def _rank_last(values: np.ndarray) -> float:
            if len(values) == 0:
                return np.nan
            s = pd.Series(values)
            last = s.iloc[-1]
            if pd.isna(last):
                return np.nan
            return (s <= last).sum() / len(s)

        return series.rolling(window=window).apply(_rank_last, raw=True)
