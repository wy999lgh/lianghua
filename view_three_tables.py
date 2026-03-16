#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看三个表的数据脚本
功能：查看 a_stock_list、index_data 和 market_data 三个表的数据内容
"""

import sqlite3

def view_table_data(db_path, table_name, limit=10):
    """
    查看表数据
    
    参数：
    - db_path: 数据库文件路径
    - table_name: 表名
    - limit: 显示的记录数，默认为10
    """
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 获取数据
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        # 显示结果
        print(f"\n表: {table_name}")
        print("列名:", column_names)
        print(f"前 {limit} 条记录:")
        for row in rows:
            print(row)
        
        # 关闭数据库连接
        conn.close()
        
    except sqlite3.Error as e:
        print(f"查询表 {table_name} 时出错: {e}")

if __name__ == "__main__":
    # 查看 a_stock_list 表
    print("===== 查看 a_stock_list 表 =====")
    view_table_data("d:\\AI量化999\\data\\stock_data.db", "a_stock_list")
    
    # 查看 index_data 表
    print("\n===== 查看 index_data 表 =====")
    view_table_data("d:\\AI量化999\\data\\stock_data.db", "index_data")
    
    # 查看 market_data 表
    print("\n===== 查看 market_data 表 =====")
    view_table_data("d:\\AI量化999\\data\\grid_trading_system.db", "market_data")
