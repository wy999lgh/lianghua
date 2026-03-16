import akshare as ak
import pandas as pd
import time
from typing import Optional
from .config import RETRY_COUNT, RETRY_DELAY


class Fetcher:
    """数据获取类，封装 AKShare 接口"""

    def fetch_stock_daily(self, symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
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
        for i in range(RETRY_COUNT):
            try:
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"Fetch stock {symbol} failed (attempt {i+1}/{RETRY_COUNT}): {e}")
                time.sleep(RETRY_DELAY)
        return pd.DataFrame()

    def fetch_etf_daily(self, symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
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
        for i in range(RETRY_COUNT):
            try:
                # AKShare 的 ETF 接口可能不需要 adjust 参数，或者参数名不同
                # fund_etf_hist_em 默认返回不复权数据，复权可能需要自行处理或使用其他接口
                # 这里假设 akshare 提供了复权参数，如果报错则需要调整
                df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"Fetch ETF {symbol} failed (attempt {i+1}/{RETRY_COUNT}): {e}")
                time.sleep(RETRY_DELAY)
        return pd.DataFrame()

    def fetch_index_daily(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取指数日线数据 (支持中证指数、上证指数等)
        
        Args:
            symbol: 指数代码 (如 "sh000985" 或 "399001")
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            pd.DataFrame: 原始数据
        """
        for i in range(RETRY_COUNT):
            try:
                # 优先使用新浪财经接口 (ak.stock_zh_index_daily)
                # 该接口通常需要带前缀 (sh/sz)，但也支持部分纯数字
                # 注意: 该接口返回所有历史数据，不支持按日期过滤，需要在获取后过滤
                df = ak.stock_zh_index_daily(symbol=symbol)
                
                if not df.empty:
                    # 标准化列名以匹配后续处理
                    # 新浪接口返回: date, open, high, low, close, volume
                    # 我们需要将其转换为 clean_stock_data 能处理的格式，或者直接返回
                    # 这里保持原始返回，让 Cleaner 处理
                    
                    # 简单过滤日期
                    if start_date:
                        # 将 start_date (YYYYMMDD) 转换为 YYYY-MM-DD
                        s_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
                        df['date'] = pd.to_datetime(df['date'])
                        df = df[df['date'] >= pd.to_datetime(s_date)]
                        
                    if end_date:
                        e_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
                        df['date'] = pd.to_datetime(df['date'])
                        df = df[df['date'] <= pd.to_datetime(e_date)]
                        
                    # 转回字符串日期，保持一致性
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                    
                    return df
            except Exception as e:
                print(f"Fetch Index (Sina) {symbol} failed (attempt {i+1}/{RETRY_COUNT}): {e}")
                
                # 如果新浪接口失败，尝试东方财富接口
                try:
                    # 东方财富接口不需要前缀 sh/sz，或者使用 sz/sh + code
                    # ak.stock_zh_index_daily_em(symbol="sz000985")
                    print(f"Trying EastMoney interface for {symbol}...")
                    df = ak.stock_zh_index_daily_em(symbol=symbol)
                    
                    if not df.empty:
                        # 东方财富接口返回列名可能不同，这里假设 AKShare 已经标准化或者后续 Cleaner 能处理
                        # 同样进行日期过滤
                        if start_date:
                             s_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
                             df['date'] = pd.to_datetime(df['date'])
                             df = df[df['date'] >= pd.to_datetime(s_date)]
                        
                        if end_date:
                             e_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
                             df['date'] = pd.to_datetime(df['date'])
                             df = df[df['date'] <= pd.to_datetime(e_date)]
                             
                        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                        return df
                except Exception as em_e:
                     print(f"Fetch Index (EastMoney) {symbol} failed: {em_e}")
                
                time.sleep(RETRY_DELAY)
        return pd.DataFrame()
