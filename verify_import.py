#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 A 股列表是否成功导入到数据库中

此脚本检查 a_stock_list 表的结构和数据
"""

import sqlite3

def verify_import(db_path, table_name="a_stock_list"):
    """
    验证数据库中的表结构和数据
    
    参数:
        db_path: 数据库文件路径
        table_name: 表名，默认为 a_stock_list
    """
    print(f"验证 {table_name} 表的数据...")
    print(f"数据库文件: {db_path}")
    print("-" * 60)
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
        )
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print(f"错误: {table_name} 表不存在")
            return False
        
        # 查看表结构
        print(f"{table_name} 表结构:")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            pk_str = "(PK)" if pk else ""
            not_null_str = "(NOT NULL)" if not_null else ""
            default_str = f"DEFAULT {default}" if default else ""
            print(f"  {col_name} {col_type} {pk_str} {not_null_str} {default_str}")
        
        # 查看数据量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        total_count = cursor.fetchone()[0]
        print(f"\n表中共有 {total_count} 条数据")
        
        # 查看前 10 条数据
        print("\n前 10 条数据:")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  ID: {row[0]}, 股票代码: {row[1]}, 股票名称: {row[2]}")
        
        # 关闭连接
        conn.close()
        
        print("-" * 60)
        print("验证完成！")
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
    
    # 执行验证
    success = verify_import(db_file, table_name)
    
    if success:
        print("\n验证成功！A 股列表已正确导入到数据库中。")
    else:
        print("\n验证失败，请检查错误信息。")