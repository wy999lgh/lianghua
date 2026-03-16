#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数数据导入脚本
功能：读取指数数据目录中的CSV文件，整合创业板、沪深300、中证500的字段数据，
并创建保存到数据库中
"""

import os
import csv
import sqlite3
from datetime import datetime

def import_index_data(index_dir, db_path, table_name="index_data"):
    """
    导入指数数据到数据库
    
    参数：
    - index_dir: 指数数据目录路径
    - db_path: 数据库文件路径
    - table_name: 表名，默认为index_data
    """
    # 指数列表
    indexes = ["创业板", "沪深300", "中证500"]
    # 数据类型列表
    data_types = ["Open", "High", "Low", "Close", "Volume", "Amount"]
    
    # 存储所有数据
    all_data = []
    
    # 读取每个指数的数据
    for index_name in indexes:
        print(f"处理指数: {index_name}")
        
        # 存储当前指数的所有数据类型
        index_data = {}
        
        # 读取每种数据类型的文件
        for data_type in data_types:
            file_name = f"{index_name}_{data_type}.csv"
            file_path = os.path.join(index_dir, file_name)
            
            if not os.path.exists(file_path):
                print(f"警告: 文件 {file_path} 不存在")
                continue
            
            print(f"读取文件: {file_name}")
            
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # 读取CSV文件，处理没有列名的情况
                reader = csv.reader(f)
                # 跳过第一行（标题行）
                next(reader)
                
                for row in reader:
                    if len(row) >= 2:
                        date_str = row[0]
                        value = row[1]
                        if date_str not in index_data:
                            index_data[date_str] = {
                                'index_name': index_name,
                                'date': date_str
                            }
                        index_data[date_str][data_type.lower()] = value
        
        # 将当前指数的数据添加到总数据中
        for date_str, data in index_data.items():
            all_data.append(data)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建表
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_name TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        amount REAL,
        UNIQUE(index_name, date)
    )
    """
    cursor.execute(create_table_sql)
    
    # 批量插入数据
    insert_sql = f"""
    INSERT OR REPLACE INTO {table_name} 
    (index_name, date, open, high, low, close, volume, amount)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # 准备插入数据
    insert_data = []
    for data in all_data:
        row = (
            data.get('index_name'),
            data.get('date'),
            float(data.get('open', 0)) if data.get('open') else None,
            float(data.get('high', 0)) if data.get('high') else None,
            float(data.get('low', 0)) if data.get('low') else None,
            float(data.get('close', 0)) if data.get('close') else None,
            float(data.get('volume', 0)) if data.get('volume') else None,
            float(data.get('amount', 0)) if data.get('amount') else None
        )
        insert_data.append(row)
    
    # 执行批量插入
    if insert_data:
        cursor.executemany(insert_sql, insert_data)
        conn.commit()
        print(f"成功插入 {len(insert_data)} 条数据到 {table_name} 表")
    else:
        print("没有数据可插入")
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    index_dir = "d:\\AI量化999\\data\\index"
    db_path = "d:\\AI量化999\\data\\stock_data.db"
    
    import_index_data(index_dir, db_path)
