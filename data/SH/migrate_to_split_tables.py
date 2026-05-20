# -*- coding: utf-8 -*-
"""
指数日线数据分表迁移脚本

功能说明:
    将 index_daily 表中的数据按指数代码分表存储
    新表名格式: index_daily_{code}

作者: AI Assistant
创建日期: 2026-04-04
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import psycopg2
from psycopg2 import sql

# 数据库连接配置
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ninja_project',
    'user': 'postgres',
    'password': 'Wy@123456'
}

# 设置控制台编码
import os
os.system('chcp 65001 > nul')


def create_index_daily_table(conn, index_code, index_name):
    """
    创建指数日线数据分表
    
    参数:
        conn: 数据库连接对象
        index_code: 指数代码，如 '999999'
        index_name: 指数名称，如 '上证指数'
    
    返回:
        bool: 创建成功返回 True
    """
    table_name = f"index_daily_{index_code}"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        trade_date DATE PRIMARY KEY,
        open NUMERIC(10,2) NOT NULL,
        high NUMERIC(10,2) NOT NULL,
        low NUMERIC(10,2) NOT NULL,
        close NUMERIC(10,2) NOT NULL,
        volume BIGINT NOT NULL,
        amount NUMERIC(20,2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cur = conn.cursor()
    try:
        cur.execute(create_sql)
        
        # 添加表注释
        cur.execute(f"""
            COMMENT ON TABLE {table_name} IS '{index_name} {index_code} 日线数据';
        """)
        
        # 添加字段注释
        comments = [
            ("trade_date", "交易日期"),
            ("open", "开盘价"),
            ("high", "最高价"),
            ("low", "最低价"),
            ("close", "收盘价"),
            ("volume", "成交量"),
            ("amount", "成交额")
        ]
        
        for col, comment in comments:
            cur.execute(f"""
                COMMENT ON COLUMN {table_name}.{col} IS '{comment}';
            """)
        
        conn.commit()
        print(f"✓ 表 {table_name} 创建成功")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ 表 {table_name} 创建失败: {e}")
        return False
    finally:
        cur.close()


def migrate_data(conn, index_code, index_name):
    """
    迁移指定指数的数据到新分表
    
    参数:
        conn: 数据库连接对象
        index_code: 指数代码
        index_name: 指数名称
    
    返回:
        int: 迁移的记录数
    """
    table_name = f"index_daily_{index_code}"
    
    cur = conn.cursor()
    try:
        # 迁移数据
        cur.execute(f"""
            INSERT INTO {table_name} (trade_date, open, high, low, close, volume, amount, created_at)
            SELECT trade_date, open, high, low, close, volume, amount, created_at
            FROM index_daily
            WHERE index_code = %s
            ON CONFLICT (trade_date) DO NOTHING
        """, (index_code,))
        
        migrated_count = cur.rowcount
        conn.commit()
        
        print(f"✓ {index_name}({index_code}) 迁移完成: {migrated_count} 条记录")
        return migrated_count
        
    except Exception as e:
        conn.rollback()
        print(f"✗ {index_name}({index_code}) 迁移失败: {e}")
        return 0
    finally:
        cur.close()


def verify_migration(conn, index_code):
    """
    验证迁移结果
    
    参数:
        conn: 数据库连接对象
        index_code: 指数代码
    
    返回:
        dict: 验证结果统计
    """
    table_name = f"index_daily_{index_code}"
    
    cur = conn.cursor()
    try:
        # 查询新表统计
        cur.execute(f"""
            SELECT 
                COUNT(*) as total,
                MIN(trade_date) as start_date,
                MAX(trade_date) as end_date
            FROM {table_name}
        """)
        result = cur.fetchone()
        
        stats = {
            'table_name': table_name,
            'total_records': result[0],
            'start_date': result[1],
            'end_date': result[2]
        }
        
        return stats
        
    finally:
        cur.close()


def get_all_index_codes(conn):
    """
    获取所有指数代码列表
    
    参数:
        conn: 数据库连接对象
    
    返回:
        list: (index_code, index_name) 元组列表
    """
    cur = conn.cursor()
    try:
        cur.execute("SELECT index_code, index_name FROM index_basic ORDER BY index_code")
        return cur.fetchall()
    finally:
        cur.close()


def main():
    """主函数"""
    print("=" * 60)
    print("指数日线数据分表迁移工具")
    print("=" * 60)
    
    conn = None
    try:
        # 连接数据库
        print("\n[1/4] 连接数据库...")
        conn = psycopg2.connect(**DB_PARAMS)
        print("✓ 数据库连接成功")
        
        # 获取所有指数
        print("\n[2/4] 获取指数列表...")
        indexes = get_all_index_codes(conn)
        print(f"✓ 发现 {len(indexes)} 个指数")
        
        # 创建分表并迁移数据
        print("\n[3/4] 创建分表并迁移数据...")
        total_migrated = 0
        
        for index_code, index_name in indexes:
            # 创建表
            if create_index_daily_table(conn, index_code, index_name):
                # 迁移数据
                count = migrate_data(conn, index_code, index_name)
                total_migrated += count
        
        print(f"\n✓ 总共迁移 {total_migrated} 条记录")
        
        # 验证结果
        print("\n[4/4] 验证迁移结果...")
        for index_code, index_name in indexes:
            stats = verify_migration(conn, index_code)
            print(f"\n  表: {stats['table_name']}")
            print(f"  - 记录数: {stats['total_records']}")
            print(f"  - 日期范围: {stats['start_date']} ~ {stats['end_date']}")
        
        print("\n" + "=" * 60)
        print("分表迁移完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("\n数据库连接已关闭")


if __name__ == "__main__":
    main()
