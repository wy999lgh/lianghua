import pandas as pd
from typing import Optional
from .fetcher import Fetcher
from .cleaner import Cleaner
from .storage import DBManager

class DataFetcher:
    """数据获取模块主类"""

    def __init__(self, db_path: str = None):
        self.fetcher = Fetcher()
        self.cleaner = Cleaner()
        self.storage = DBManager(db_path) if db_path else DBManager()

    def update_stock(self, symbol: str, start_date: str, end_date: str, adjust: str = "qfq"):
        """
        获取并保存股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型
        """
        # 1. Fetch
        raw_df = self.fetcher.fetch_stock_daily(symbol, start_date, end_date, adjust)
        
        if raw_df.empty:
            print(f"Fetch stock {symbol} failed or no data found.")
            return

        # 2. Clean
        cleaned_df = self.cleaner.clean_stock_data(raw_df, symbol, adjust)
        
        # 3. Save
        table_name = f"stock_{symbol}"
        self.storage.save_data(cleaned_df, table_name=table_name)
        print(f"Updated stock {symbol} data from {start_date} to {end_date} into {table_name}.")

    def update_etf(self, symbol: str, start_date: str, end_date: str, adjust: str = "qfq"):
        """
        获取并保存 ETF 数据
        
        Args:
            symbol: ETF 代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型
        """
        # 1. Fetch
        raw_df = self.fetcher.fetch_etf_daily(symbol, start_date, end_date, adjust)
        
        if raw_df.empty:
            print(f"Fetch ETF {symbol} failed or no data found.")
            return

        # 2. Clean
        cleaned_df = self.cleaner.clean_stock_data(raw_df, symbol, adjust)
        
        # 3. Save
        table_name = f"etf_{symbol}"
        self.storage.save_data(cleaned_df, table_name=table_name)
        print(f"Updated ETF {symbol} data from {start_date} to {end_date} into {table_name}.")

    def get_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
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
        # 如果 symbol 已经包含 stock_ 或 etf_ 前缀，直接使用
        if symbol.startswith("stock_") or symbol.startswith("etf_"):
            return self.storage.get_data(symbol, start_date, end_date)
            
        # 否则尝试 stock_{symbol} 和 etf_{symbol}
        # 优先尝试 stock
        table_name = f"stock_{symbol}"
        df = self.storage.get_data(table_name, start_date, end_date)
        if not df.empty:
            return df
            
        # 尝试 etf
        table_name = f"etf_{symbol}"
        return self.storage.get_data(table_name, start_date, end_date)
