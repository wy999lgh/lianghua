#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 A 股股票列表从 CSV 文件导入到 SQLite 数据库

此脚本读取 stocks_with_name.csv 文件，并将数据导入到 stock_data.db 数据库中，创建 a_stock_list 表
"""

import sqlite3
import csv
import os

def import_stocks_to_db(csv_path, db_path, table_name="a_stock_list"):
    """
    将 CSV 文件中的股票数据导入到 SQLite 数据库
    
    参数:
        csv_path: CSV 文件路径
        db_path: 数据库文件路径
        table_name: 表名，默认为 a_stock_list
    """
    print(f"开始导入股票数据到数据库...")
    print(f"CSV 文件: {csv_path}")
    print(f"数据库文件: {db_path}")
    print(f"表名: {table_name}")
    print("-" * 60)
    
    # 检查 CSV 文件是否存在
    if not os.path.exists(csv_path):
        print(f"错误: CSV 文件不存在 - {csv_path}")
        return False
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表（如果不存在）
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT UNIQUE NOT NULL,
            stock_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 清空表（如果需要）
        cursor.execute(f"DELETE FROM {table_name}")
        
        # 读取 CSV 文件并插入数据
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            # 先读取头部
            header = f.readline().strip()
            print(f"CSV 头部: {header}")
            
            # 重置文件指针
            f.seek(0)
            
            reader = csv.DictReader(f)
            count = 0
            
            # 打印列名
            if reader.fieldnames:
                print(f"列名: {reader.fieldnames}")
            
            for row in reader:
                try:
                    # 尝试获取列值，处理可能的列名差异
                    if 'StockCode' in row:
                        stock_code = row['StockCode'].strip()
                    elif 'stockcode' in row:
                        stock_code = row['stockcode'].strip()
                    else:
                        # 获取第一列
                        stock_code = list(row.values())[0].strip()
                    
                    if 'StockName' in row:
                        stock_name = row['StockName'].strip()
                    elif 'stockname' in row:
                        stock_name = row['stockname'].strip()
                    else:
                        # 获取第二列
                        stock_name = list(row.values())[1].strip()
                    
                    # 插入数据
                    cursor.execute(
                        f"INSERT INTO {table_name} (stock_code, stock_name) VALUES (?, ?)",
                        (stock_code, stock_name)
                    )
                    count += 1
                    
                    # 每插入 1000 条数据打印一次进度
                    if count % 1000 == 0:
                        print(f"已导入 {count} 条数据...")
                except Exception as e:
                    print(f"处理行时出错: {row}, 错误: {e}")
                    continue
        
        # 提交事务
        conn.commit()
        
        # 验证导入结果
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        print("-" * 60)
        print(f"导入完成！")
        print(f"共导入 {total_count} 条股票数据")
        
        # 关闭连接
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    except Exception as e:
        print(f"未知错误: {e}")
        return False

if __name__ == "__main__":
    # 定义文件路径
    csv_file = "d:\\AI量化999\\data\\stocks_with_name.csv"
    db_file = "d:\\AI量化999\\data\\stock_data.db"
    table_name = "a_stock_list"
    
    # 执行导入
    success = import_stocks_to_db(csv_file, db_file, table_name)
    
    if success:
        print("\n操作成功！A 股列表已成功导入到数据库中。")
    else:
        print("\n操作失败，请检查错误信息。")