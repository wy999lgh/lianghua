import sqlite3
import pandas as pd
import sys
import os

# 数据库路径
db_path = r"d:\AI量化999\data\stock_data.db"

def view_data(table_name):
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    try:
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"表 {table_name} 不存在")
            return

        # 查询数据总数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"表: {table_name}")
        print(f"总记录数: {count}")

        # 读取前 5 行
        print("\n--- 前 5 行 ---")
        df_head = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY date ASC LIMIT 5", conn)
        print(df_head)

        # 读取后 5 行
        print("\n--- 后 5 行 ---")
        df_tail = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT 5", conn)
        # sort back for display
        df_tail = df_tail.sort_values(by='date') 
        print(df_tail)
        
        # 显示列信息
        print("\n--- 列信息 ---")
        print(df_head.columns.tolist())

    except Exception as e:
        print(f"查询出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
    else:
        table_name = "index_000985" # 默认值
    
    view_data(table_name)
