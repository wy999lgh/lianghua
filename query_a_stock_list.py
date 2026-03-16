#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询 a_stock_list 表的数据

此脚本用于查询 a_stock_list 表的结构、数据量和具体数据
"""

import sqlite3

def query_a_stock_list(db_path, table_name="a_stock_list"):
    """
    查询 a_stock_list 表的数据
    
    参数:
        db_path: 数据库文件路径
        table_name: 表名，默认为 a_stock_list
    """
    print(f"查询 {table_name} 表的数据...")
    print(f"数据库文件: {db_path}")
    print("-" * 60)
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        )
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print(f"错误: {table_name} 表不存在")
            return False
        
        # 查看表结构
        print(f"{table_name} 表结构:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            pk_str = "(PK)" if pk else ""
            not_null_str = "(NOT NULL)" if not_null else ""
            default_str = f"DEFAULT {default}" if default else ""
            print(f"  {col_name} {col_type} {pk_str} {not_null_str} {default_str}")
        
        # 查看数据量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        print(f"\n表中共有 {total_count} 条数据")
        
        # 查看前 20 条数据
        print("\n前 20 条数据:")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 20")
        rows = cursor.fetchall()
        
        # 打印表头
        print(f"  {'ID':<5} {'股票代码':<10} {'股票名称':<10}")
        print("  " + "-" * 30)
        
        # 打印数据
        for row in rows:
            print(f"  {row[0]:<5} {row[1]:<10} {row[2]:<10}")
        
        # 查看股票代码类型分布
        print("\n股票代码类型分布:")
        cursor.execute(
            "SELECT SUBSTR(stock_code, -2) AS suffix, COUNT(*) AS count "
            f"FROM {table_name} GROUP BY suffix ORDER BY count DESC"
        )
        suffix_stats = cursor.fetchall()
        for suffix, count in suffix_stats:
            print(f"  {suffix}: {count} 只股票")
        
        # 关闭连接
        conn.close()
        
        print("-" * 60)
        print("查询完成！")
        return True
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False

if __name__ == "__main__":
    # 定义文件路径
    db_file = "d:\\AI量化999\\data\\stock_data.db"
    table_name = "a_stock_list"
    
    # 执行查询
    query_a_stock_list(db_file, table_name)