#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数数据验证脚本
功能：验证指数数据是否正确导入到数据库中
"""

import sqlite3

def verify_index_data(db_path, table_name="index_data"):
    """
    验证指数数据
    
    参数：
    - db_path: 数据库文件路径
    - table_name: 表名，默认为index_data
    """
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    print("表结构:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for column in columns:
        print(f"{column[1]} ({column[2]})")
    
    # 检查数据总量
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_count = cursor.fetchone()[0]
    print(f"\n总数据量: {total_count}")
    
    # 检查每个指数的数据量
    indexes = ["创业板", "沪深300", "中证500"]
    print("\n各指数数据量:")
    for index_name in indexes:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE index_name = ?", (index_name,))
        count = cursor.fetchone()[0]
        print(f"{index_name}: {count}")
    
    # 检查最新数据
    print("\n最新数据:")
    for index_name in indexes:
        cursor.execute(f"""
            SELECT date, open, high, low, close, volume, amount 
            FROM {table_name} 
            WHERE index_name = ? 
            ORDER BY date DESC 
            LIMIT 5
        """, (index_name,))
        rows = cursor.fetchall()
        print(f"\n{index_name} 最新5条数据:")
        for row in rows:
            print(f"日期: {row[0]}, 开盘: {row[1]}, 最高: {row[2]}, 最低: {row[3]}, 收盘: {row[4]}, 成交量: {row[5]}, 成交额: {row[6]}")
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    db_path = "d:\\AI量化999\\data\\stock_data.db"
    verify_index_data(db_path)
