#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股票列表数据导入脚本

功能：从CSV文件读取股票列表数据，并导入到PostgreSQL数据库中
"""

import os
import sys
import csv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data.database import Database

def create_table(db):
    """创建a_stock_list表"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS a_stock_list (
        id SERIAL PRIMARY KEY,
        stock_code VARCHAR(20) NOT NULL UNIQUE,
        stock_name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP
    );
    """
    
    conn = db._pg_connect()
    try:
        cur = conn.cursor()
        cur.execute(create_table_sql)
        conn.commit()
        print("表 a_stock_list 创建成功")
    finally:
        db._pg_release(conn)

def import_csv_data(db, csv_path):
    """从CSV文件导入数据"""
    # 清空表数据
    conn = db._pg_connect()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM a_stock_list;")
        conn.commit()
        print("已清空现有数据")
    finally:
        db._pg_release(conn)
    
    # 导入数据
    row_count = 0
    
    with open(csv_path, 'rb') as f:
        lines = f.readlines()
    
    conn = db._pg_connect()
    try:
        cur = conn.cursor()
        
        for i, line in enumerate(lines[1:], start=2):
            try:
                line_str = line.decode('utf-8', errors='replace').strip()
                
                if not line_str:
                    continue
                
                parts = []
                current = ''
                in_quotes = False
                
                for char in line_str:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        parts.append(current.strip('"'))
                        current = ''
                    else:
                        current += char
                parts.append(current.strip('"'))
                
                if len(parts) >= 4:
                    stock_code = parts[1]
                    stock_name = parts[2]
                    created_at = parts[3]
                    
                    cur.execute(
                        """INSERT INTO a_stock_list (stock_code, stock_name, created_at) VALUES (%s, %s, %s)""",
                        (stock_code, stock_name, created_at)
                    )
                    row_count += 1
                    
            except Exception as e:
                print(f"第 {i} 行导入失败: {e}")
        
        conn.commit()
        print(f"成功导入 {row_count} 条数据")
        
    finally:
        db._pg_release(conn)

def main():
    csv_path = r"d:\AI量化999\data\a_stock_list.csv"
    
    if not os.path.exists(csv_path):
        print(f"错误：文件不存在 - {csv_path}")
        return
    
    try:
        db = Database()
        print("数据库连接成功")
        
        create_table(db)
        import_csv_data(db, csv_path)
        
        print("数据导入完成")
        
    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()