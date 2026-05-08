# -*- coding: utf-8 -*-
"""
网格交易系统 - 数据清洗模块
Data cleaner for the grid trading system

迁移自: grid_trading/data/cleaner.py
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict

# 数据字段映射 (AKShare -> 本地数据库)
COLUMN_MAPPING: Dict[str, str] = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_chg",
    "涨跌额": "change",
    "换手率": "turnover",
}


class DataCleaner:
    """
    数据清洗与处理类

    功能:
    - 列名标准化 (中文 -> 英文)
    - 数据类型转换
    - 计算技术指标 (ATR14)
    - 数据去重
    """

    def __init__(self, column_mapping: Optional[Dict[str, str]] = None):
        """
        初始化数据清洗器

        Args:
            column_mapping: 自定义列名映射，默认使用 COLUMN_MAPPING
        """
        self.column_mapping = column_mapping or COLUMN_MAPPING

    def clean_stock_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        adjust: str = ""
    ) -> pd.DataFrame:
        """
        清洗股票/ETF数据

        Args:
            df: 原始数据 DataFrame
            symbol: 标的代码
            adjust: 复权类型 ("qfq", "hfq", "")

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if df.empty:
            return pd.DataFrame()

        # 1. 重命名列
        df = df.rename(columns=self.column_mapping)

        # 2. 保留需要的列
        required_cols = list(self.column_mapping.values())
        # 确保只保留存在的列
        cols_to_keep = [col for col in required_cols if col in df.columns]
        df = df[cols_to_keep]

        # 3. 添加额外字段
        df['adjust_type'] = adjust
        df['period'] = 'daily'

        # 4. 数据类型转换
        numeric_cols = [
            'open', 'close', 'high', 'low',
            'volume', 'amount', 'change', 'pct_chg',
            'amplitude', 'turnover'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 5. 日期格式标准化 (假设原始日期已经是 YYYY-MM-DD 或 YYYYMMDD)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        # 6. 计算技术指标 (ATR14)
        df = self._calculate_atr(df, period=14)

        # 7. 去重 (按 date)
        df = df.drop_duplicates(subset=['date'])

        # 8. 处理缺失值 (根据需要，这里简单填充 0 或前值)
        # df = df.fillna(0)

        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算 ATR (Average True Range) 指标

        Args:
            df: 包含 high, low, close 列的 DataFrame
            period: ATR 周期，默认 14

        Returns:
            pd.DataFrame: 添加了 atr14 列的 DataFrame
        """
        if len(df) < period:
            df['atr14'] = np.nan
            return df

        # 确保必要的列存在
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            df['atr14'] = np.nan
            return df

        high = df['high']
        low = df['low']
        close = df['close']

        # 计算 TR (True Range)
        # TR = max(high-low, abs(high-close_prev), abs(low-close_prev))

        # Shift close to get previous close
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 使用 Wilder's Smoothing (更常用)
        # ATR = (Prev ATR * (n-1) + TR) / n
        atr = tr.ewm(alpha=1/period, adjust=False).mean()

        df['atr14'] = atr

        return df

    def clean_index_data(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> pd.DataFrame:
        """
        清洗指数数据

        Args:
            df: 原始数据 DataFrame
            symbol: 指数代码

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if df.empty:
            return pd.DataFrame()

        # 标准化列名
        df = df.rename(columns=self.column_mapping)

        # 保留基本列
        basic_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        cols_to_keep = [col for col in basic_cols if col in df.columns]
        df = df[cols_to_keep]

        # 数据类型转换
        numeric_cols = ['open', 'close', 'high', 'low', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 日期格式标准化
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        # 去重
        df = df.drop_duplicates(subset=['date'])

        return df

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化 DataFrame 列名

        Args:
            df: 原始 DataFrame

        Returns:
            pd.DataFrame: 列名标准化后的 DataFrame
        """
        return df.rename(columns=self.column_mapping)

    def add_calculated_fields(
        self,
        df: pd.DataFrame,
        fields: Optional[list] = None
    ) -> pd.DataFrame:
        """
        添加计算字段

        Args:
            df: 原始 DataFrame
            fields: 要添加的字段列表，默认 ['atr14']

        Returns:
            pd.DataFrame: 添加了计算字段的 DataFrame
        """
        if fields is None:
            fields = ['atr14']

        if 'atr14' in fields:
            df = self._calculate_atr(df, period=14)

        return df


# 保持向后兼容的别名
Cleaner = DataCleaner
