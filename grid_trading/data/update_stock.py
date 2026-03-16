import sys
import os

# 添加项目根目录到 sys.path，确保能导入 grid_trading 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from grid_trading.data.fetcher import Fetcher
from grid_trading.data.cleaner import Cleaner
from grid_trading.data.storage import DBManager

def update_stock_data(symbol: str, start_date: str, end_date: str):
    """
    获取、清洗并保存股票数据到数据库
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
    """
    print(f"开始更新股票 {symbol} 数据 ({start_date}-{end_date})...")
    
    # 1. 获取数据
    fetcher = Fetcher()
    df_raw = fetcher.fetch_stock_daily(symbol, start_date, end_date)
    
    if df_raw.empty:
        print(f"未获取到 {symbol} 的数据")
        return

    print(f"获取到 {len(df_raw)} 条原始数据")

    # 2. 清洗数据
    cleaner = Cleaner()
    df_clean = cleaner.clean_stock_data(df_raw, symbol)
    
    if df_clean.empty:
        print("数据清洗后为空")
        return
        
    print(f"清洗后剩余 {len(df_clean)} 条数据")
    print("清洗后数据示例:")
    print(df_clean.head())

    # 3. 保存到数据库
    db_manager = DBManager()
    table_name = f"stock_{symbol}"
    db_manager.save_data(df_clean, table_name)
    
    print(f"数据已保存到表 {table_name}")

    # 4. 验证保存结果
    df_saved = db_manager.get_data(table_name, start_date=start_date[:4]+"-"+start_date[4:6]+"-"+start_date[6:])
    print(f"从数据库读取验证: {len(df_saved)} 条记录")
    if not df_saved.empty:
        print(df_saved.head())

if __name__ == "__main__":
    # 示例: 更新贵州茅台 (600519) 的数据
    # 使用最近的时间段以确保有数据
    update_stock_data("600519", "20230101", "20231231")
