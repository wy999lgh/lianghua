import sqlite3
import os
import pandas as pd

# 数据库路径
db_path = r"d:\AI量化999\data\stock_data.db"

def list_tables():
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    
    print(f"数据库路径: {db_path}")
    print(f"共有 {len(table_names)} 个表:")
    
    for table in table_names:
        # 查询数据条数
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"- {table}: {count} 条记录")
        except Exception as e:
             print(f"- {table}: 查询失败 ({e})")

    conn.close()

if __name__ == "__main__":
    list_tables()
