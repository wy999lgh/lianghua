# -*- coding: utf-8 -*-
"""
网格交易系统 - 数据获取模块
Data fetcher for the grid trading system

合并自:
- grid_trading/data/api.py (DataFetcher 门面类)
- grid_trading/data/fetcher.py (Fetcher, AKShare 数据获取接口)
"""

import time
import pandas as pd
from typing import Optional

try:
    import akshare as ak
except ImportError:
    ak = None
    print("Warning: akshare not installed. Data fetching will not work.")

from config.database_config import get_database_config

from .data_cleaner import DataCleaner
from .database import Database


# 数据源重试配置
RETRY_COUNT = 3
RETRY_DELAY = 1  # 秒


class DataFetcher:
    """
    数据获取模块主类 (统一门面)

    功能:
    - 获取股票日线数据 (fetch_stock_daily)
    - 获取 ETF 日线数据 (fetch_etf_daily)
    - 获取指数日线数据 (fetch_index_daily)
    - 获取并保存股票数据 (update_stock)
    - 获取并保存 ETF 数据 (update_etf)
    - 获取并保存指数数据 (update_index)
    - 从本地数据库获取数据 (get_data)
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        retry_count: int = RETRY_COUNT,
        retry_delay: int = RETRY_DELAY
    ):
        """
        初始化数据获取器

        Args:
            db_path: 数据库路径，默认从配置获取
            retry_count: 重试次数
            retry_delay: 重试间隔 (秒)
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.cleaner = DataCleaner()

        # 获取数据库路径
        if db_path is None:
            config = get_database_config()
            db_path = config.get_stock_data_db_path()

        self.storage = Database(stock_db_path=db_path)

    # ==================== 原始数据获取 (来自 Fetcher) ====================

    def fetch_stock_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码 (如 "600519")
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ("qfq", "hfq", "")

        Returns:
            pd.DataFrame: 原始数据
        """
        if ak is None:
            print("Error: akshare not installed.")
            return pd.DataFrame()

        for i in range(self.retry_count):
            try:
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
                if not df.empty:
                    return df
            except Exception as e:
                print(
                    f"Fetch stock {symbol} failed (attempt {i+1}/{self.retry_count}): {e}")
                time.sleep(self.retry_delay)
        return pd.DataFrame()

    def fetch_etf_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取 ETF 日线数据

        Args:
            symbol: ETF 代码 (如 "510300")
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ("qfq", "hfq", "")

        Returns:
            pd.DataFrame: 原始数据
        """
        if ak is None:
            print("Error: akshare not installed.")
            return pd.DataFrame()

        for i in range(self.retry_count):
            try:
                df = ak.fund_etf_hist_em(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
                if not df.empty:
                    return df
            except Exception as e:
                print(
                    f"Fetch ETF {symbol} failed (attempt {i+1}/{self.retry_count}): {e}")
                time.sleep(self.retry_delay)
        return pd.DataFrame()

    def fetch_index_daily(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取指数日线数据 (支持中证指数、上证指数等)

        Args:
            symbol: 指数代码 (如 "sh000985" 或 "399001")
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            pd.DataFrame: 原始数据
        """
        if ak is None:
            print("Error: akshare not installed.")
            return pd.DataFrame()

        for i in range(self.retry_count):
            try:
                # 优先使用新浪财经接口 (ak.stock_zh_index_daily)
                df = ak.stock_zh_index_daily(symbol=symbol)

                if not df.empty:
                    # 日期过滤
                    df = self._filter_by_date(df, start_date, end_date)
                    return df

            except Exception as e:
                print(
                    f"Fetch Index (Sina) {symbol} failed (attempt {i+1}/{self.retry_count}): {e}")

                # 如果新浪接口失败，尝试东方财富接口
                try:
                    print(f"Trying EastMoney interface for {symbol}...")
                    df = ak.stock_zh_index_daily_em(symbol=symbol)

                    if not df.empty:
                        df = self._filter_by_date(df, start_date, end_date)
                        return df
                except Exception as em_e:
                    print(f"Fetch Index (EastMoney) {symbol} failed: {em_e}")

                time.sleep(self.retry_delay)
        return pd.DataFrame()

    def _filter_by_date(
        self,
        df: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """
        按日期过滤数据

        Args:
            df: 数据 DataFrame
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            pd.DataFrame: 过滤后的数据
        """
        if 'date' not in df.columns:
            return df

        df['date'] = pd.to_datetime(df['date'])

        if start_date:
            s_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            df = df[df['date'] >= pd.to_datetime(s_date)]

        if end_date:
            e_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            df = df[df['date'] <= pd.to_datetime(e_date)]

        # 转回字符串日期，保持一致性
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        return df

    # ==================== 获取并保存数据 (来自 DataFetcher) ====================

    def update_stock(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ):
        """
        获取并保存股票数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型
        """
        # 1. Fetch
        raw_df = self.fetch_stock_daily(symbol, start_date, end_date, adjust)

        if raw_df.empty:
            print(f"Fetch stock {symbol} failed or no data found.")
            return

        # 2. Clean
        cleaned_df = self.cleaner.clean_stock_data(raw_df, symbol, adjust)

        # 3. Save
        table_name = f"stock_{symbol}"
        self.storage.save_data(cleaned_df, table_name=table_name)
        print(
            f"Updated stock {symbol} data from {start_date} to {end_date} into {table_name}.")

    def update_etf(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ):
        """
        获取并保存 ETF 数据

        Args:
            symbol: ETF 代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型
        """
        # 1. Fetch
        raw_df = self.fetch_etf_daily(symbol, start_date, end_date, adjust)

        if raw_df.empty:
            print(f"Fetch ETF {symbol} failed or no data found.")
            return

        # 2. Clean
        cleaned_df = self.cleaner.clean_stock_data(raw_df, symbol, adjust)

        # 3. Save
        table_name = f"etf_{symbol}"
        self.storage.save_data(cleaned_df, table_name=table_name)
        print(
            f"Updated ETF {symbol} data from {start_date} to {end_date} into {table_name}.")

    def update_index(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        获取并保存指数数据

        Args:
            symbol: 指数代码 (如 "sh000985")
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        """
        # 1. Fetch
        raw_df = self.fetch_index_daily(symbol, start_date, end_date)

        if raw_df.empty:
            print(f"Fetch index {symbol} failed or no data found.")
            return

        # 2. Clean
        cleaned_df = self.cleaner.clean_index_data(raw_df, symbol)

        # 3. Save
        # 移除可能的前缀 (sh/sz)
        clean_symbol = symbol.lstrip('shsz')
        table_name = f"index_{clean_symbol}"
        self.storage.save_data(cleaned_df, table_name=table_name)
        print(f"Updated index {symbol} data into {table_name}.")

    def get_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        从本地数据库获取数据

        Args:
            symbol: 标的代码 (如 600519 或 stock_600519)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            pd.DataFrame: 数据
        """
        # 自动尝试推断表名
        # 如果 symbol 已经包含 stock_, etf_, index_ 前缀，直接使用
        if symbol.startswith("stock_") or symbol.startswith("etf_") or symbol.startswith("index_"):
            return self.storage.get_data(symbol, start_date, end_date)

        # 否则按顺序尝试 stock_{symbol}, etf_{symbol}, index_{symbol}
        for prefix in ['stock_', 'etf_', 'index_']:
            table_name = f"{prefix}{symbol}"
            df = self.storage.get_data(table_name, start_date, end_date)
            if not df.empty:
                return df

        return pd.DataFrame()

    def get_available_symbols(self, prefix: str = 'stock_') -> list:
        """
        获取可用的标的列表

        Args:
            prefix: 表名前缀 ('stock_', 'etf_', 'index_')

        Returns:
            list: 标的代码列表
        """
        tables = self.storage.list_tables(db_type='stock')
        symbols = []
        for table in tables:
            if table.startswith(prefix):
                symbol = table[len(prefix):]
                symbols.append(symbol)
        return symbols


# 保持向后兼容的别名
Fetcher = DataFetcher
