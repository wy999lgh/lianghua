"""
股票数据导入脚本
将CSV数据导入到SQLite数据库中
表名使用stock_159633（因为表名不能以数字开头）
"""

import sqlite3
import pandas as pd
import os

def import_stock_data():
    # 定义文件路径
    csv_file = 'd:/网格01/data/19900101-20251014_159633_日线_前复权.csv'
    db_name = 'stock_data.db'
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"错误: CSV文件不存在 - {csv_file}")
        return
    
    print("正在读取CSV文件...")
    df = pd.read_csv(csv_file)
    
    print(f"CSV文件包含 {len(df)} 行数据")
    print(f"CSV文件包含 {len(df.columns)} 列数据")
    print(f"列名: {list(df.columns)}")
    
    print("正在创建SQLite数据库...")
    conn = sqlite3.connect(db_name)
    
    # 将数据导入到名为 stock_159633 的表中
    df.to_sql('stock_159633', conn, if_exists='replace', index=False)
    
    # 获取表信息
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM stock_159633')
    row_count = cursor.fetchone()[0]
    
    # 获取表结构
    cursor.execute('PRAGMA table_info(stock_159633)')
    columns = cursor.fetchall()
    
    print()
    print(f"成功创建数据库: {db_name}")
    print(f"成功创建表: stock_159633")
    print(f"成功导入数据行数: {row_count}")
    print("表结构:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 显示前5行数据
    print("\n前5行数据:")
    preview_df = pd.read_sql_query('SELECT * FROM stock_159633 LIMIT 5', conn)
    print(preview_df)
    
    # 显示后5行数据
    print("\n后5行数据:")
    tail_df = pd.read_sql_query('SELECT * FROM stock_159633 ORDER BY ROWID DESC LIMIT 5', conn)
    print(tail_df)
    
    # 关闭连接
    conn.close()
    
    print(f"\n数据导入完成! 数据库文件: {db_name}")
    print("注意: 表名使用 'stock_159633'，因为SQLite表名不能以数字开头")

if __name__ == "__main__":
    import_stock_data()