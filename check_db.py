#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库文件类型和结构

此脚本用于检查指定的数据库文件是否为 SQLite 数据库，并查看其表结构
"""

import sqlite3
import os

def check_sqlite_db(db_path):
    """
    检查指定路径的文件是否为 SQLite 数据库，并查看其表结构
    
    参数:
        db_path: 数据库文件路径
    """
    print(f"\n检查数据库: {db_path}")
    print("-" * 50)
    
    # 检查文件是否存在
    if not os.path.exists(db_path):
        print(f"错误: 文件不存在 - {db_path}")
        return
    
    # 检查文件大小
    file_size = os.path.getsize(db_path)
    print(f"文件大小: {file_size} 字节")
    
    # 尝试连接到数据库
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否为有效的 SQLite 数据库
        # SQLite 数据库文件头部应该是 "SQLite format 3"
        with open(db_path, 'rb') as f:
            header = f.read(16)
            if header == b'SQLite format 3\x00':
                print("类型: SQLite 数据库")
            else:
                print(f"类型: 未知 (头部: {header})")
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n发现 {len(tables)} 个表:")
            for table in tables:
                table_name = table[0]
                print(f"\n表: {table_name}")
                
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                print("  列结构:")
                for col in columns:
                    col_id, col_name, col_type, not_null, default, pk = col
                    pk_str = "(PK)" if pk else ""
                    print(f"    {col_name} {col_type} {pk_str}")
        else:
            print("\n未发现表")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

if __name__ == "__main__":
    # 检查两个数据库文件
    db_files = [
        "d:\\AI量化999\\data\\grid_trading_system.db",
        "d:\\AI量化999\\data\\stock_data.db"
    ]
    
    for db_file in db_files:
        check_sqlite_db(db_file)