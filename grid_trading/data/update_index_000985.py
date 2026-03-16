import sys
import os
import pandas as pd
import akshare as ak

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from grid_trading.data.fetcher import Fetcher
from grid_trading.data.cleaner import Cleaner
from grid_trading.data.storage import DBManager

def test_akshare_direct():
    print("测试直接调用 akshare 接口...")
    # 东方财富接口 - 获取所有历史数据
    symbols = ["sz000985", "000985", "sh000985"]
    
    import time
    
    # 增加 headers 模拟浏览器
    import akshare as ak
    
    for symbol in symbols:
        try:
            print(f"尝试 ak.stock_zh_index_daily_em(symbol='{symbol}')...")
            # 增加重试机制
            for i in range(5):
                try:
                    df = ak.stock_zh_index_daily_em(symbol=symbol)
                    break
                except Exception as retry_e:
                    print(f"  重试 {i+1}/5: {retry_e}")
                    time.sleep(3) # 增加等待时间
            else:
                 raise Exception("重试5次均失败")

            if not df.empty:
                print(f"成功! 获取到 {len(df)} 条数据")
                # 确保日期列存在并转换为 datetime
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    print(f"原始数据日期范围: {df['date'].min()} 到 {df['date'].max()}")
                    
                    # 过滤日期范围 20000101 - 20260307
                    start_date = pd.to_datetime("2000-01-01")
                    end_date = pd.to_datetime("2026-03-07")
                    
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df_filtered = df.loc[mask].copy()
                    
                    print(f"过滤后数据 ({start_date.date()} - {end_date.date()}): {len(df_filtered)} 条")
                    
                    # 转回字符串格式以便后续处理
                    df_filtered['date'] = df_filtered['date'].dt.strftime('%Y-%m-%d')
                    return symbol, df_filtered
                else:
                    print("未找到 date 列")
                    
        except Exception as e:
            print(f"获取失败 ({symbol}): {e}")

    return None, None

def update_index_data(symbol_code, table_name_suffix):
    """
    获取并保存指数数据
    """
    # 1. 获取数据
    valid_symbol, df = test_akshare_direct()
    
    if df is None or df.empty:
        print(f"所有尝试均失败，无法获取 000985 数据。")
        return False
        
    print(f"使用 symbol: {valid_symbol} 获取到 {len(df)} 条数据。")
    print("原始列名:", df.columns.tolist())
    if 'date' in df.columns:
        print(f"数据日期范围: {df['date'].min()} 到 {df['date'].max()}")
    
    # 2. 清洗
    cleaner = Cleaner()
    
    # 确保日期格式正确
    if 'date' in df.columns:
         df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    df_clean = cleaner.clean_stock_data(df, table_name_suffix)
    
    if df_clean.empty:
        print("清洗后数据为空。")
        return False
        
    print(f"清洗后 {len(df_clean)} 条数据。")
    
    # 3. 保存
    db_manager = DBManager()
    table_name = f"index_{table_name_suffix}"
    
    # 强制清空旧数据，确保完全是新获取的
    print(f"清空旧表 {table_name} ...")
    conn = sqlite3.connect(db_manager.db_path)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    conn.close()
    
    print(f"准备保存到表 {table_name} ...")
    db_manager.save_data(df_clean, table_name)
    print("保存成功。")
    
    # 验证
    check_saved_data(table_name)
    return True

def check_saved_data(table_name):
    db_manager = DBManager()
    df = db_manager.get_data(table_name)
    print(f"数据库验证: 表 {table_name} 当前共有 {len(df)} 条记录")
    if not df.empty:
        print("最后 5 条记录:")
        print(df.tail())

if __name__ == "__main__":
    import sqlite3 # 确保导入
    update_index_data("000985", "000985")
