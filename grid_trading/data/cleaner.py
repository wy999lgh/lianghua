import pandas as pd
import numpy as np
from typing import Optional
from .config import COLUMN_MAPPING

class Cleaner:
    """数据清洗与处理类"""

    def clean_stock_data(self, df: pd.DataFrame, symbol: str, adjust: str = "") -> pd.DataFrame:
        """
        清洗股票/ETF数据
        
        Args:
            df: 原始数据 DataFrame
            symbol: 标的代码
            adjust: 复权类型
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if df.empty:
            return pd.DataFrame()

        # 1. 重命名列
        df = df.rename(columns=COLUMN_MAPPING)
        
        # 2. 保留需要的列
        required_cols = list(COLUMN_MAPPING.values())
        # 确保只保留存在的列
        cols_to_keep = [col for col in required_cols if col in df.columns]
        df = df[cols_to_keep]

        # 3. 添加额外字段
        # df['symbol'] = symbol  # 移除 symbol，因为已经分表
        df['adjust_type'] = adjust
        df['period'] = 'daily'

        # 4. 数据类型转换
        numeric_cols = ['open', 'close', 'high', 'low', 
                        'volume', 'amount', 'change', 'pct_chg', 
                        'amplitude', 'turnover']
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
        """计算 ATR 指标"""
        if len(df) < period:
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
        
        # 计算 ATR (使用简单移动平均 SMA，也可以用 EMA)
        # 这里使用 Wilder's Smoothing (类似于 EMA) 或者简单 SMA
        # 为了简单且符合常见定义，使用 SMA
        # df['atr14'] = tr.rolling(window=period).mean()

        # 或者使用 Wilder's Smoothing (更常用)
        # ATR = (Prev ATR * (n-1) + TR) / n
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        
        df['atr14'] = atr
        
        return df
