"""
指数数据导入脚本

功能：
- 从本地 CSV（制表符分隔）读取指数日线数据
- 写入 PostgreSQL（默认按环境变量 PGPASSWORD 取密码）
"""

import os
import csv
from datetime import datetime
import psycopg2

# 数据库连接参数
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': os.environ.get("PGPASSWORD", "")
}


def load_index_data(csv_file, index_code, index_name):
    """
    加载指数数据到数据库

    使用复合主键 (index_code, trade_date) 确保数据唯一性
    ON CONFLICT 处理重复数据插入
    """
    if not DB_PARAMS.get("password"):
        raise RuntimeError("未检测到 PostgreSQL 密码，请先设置环境变量 PGPASSWORD")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # 插入指数基础信息
    cur.execute('''
        INSERT INTO index_basic (index_code, index_name, market, period, adjust_type)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (index_code) DO UPDATE
        SET index_name = %s, last_update = CURRENT_TIMESTAMP
    ''', (index_code, index_name, '沪市', '日线', '后复权', index_name))

    # 读取并插入日线数据
    inserted_count = 0
    skipped_count = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # 跳过表头
        next(reader)  # 跳过字段名行

        for row in reader:
            if not row or len(row) < 7:
                continue

            try:
                trade_date = datetime.strptime(
                    row[0].strip(), '%Y-%m-%d').date()
                open_price = float(row[1].strip())
                high = float(row[2].strip())
                low = float(row[3].strip())
                close = float(row[4].strip())
                volume = int(row[5].strip())
                amount = float(row[6].strip())

                # 插入数据（复合主键冲突时跳过）
                cur.execute('''
                    INSERT INTO index_daily (index_code, trade_date, open, high, low, close, volume, amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (index_code, trade_date) DO NOTHING
                ''', (index_code, trade_date, open_price, high, low, close, volume, amount))

                if cur.rowcount > 0:
                    inserted_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                print(f"处理行失败: {row}, 错误: {e}")
                continue

    conn.commit()
    cur.close()
    conn.close()
    print(f"数据加载完成: {csv_file}")
    print(f"  插入: {inserted_count} 条")
    print(f"  跳过（已存在）: {skipped_count} 条")


if __name__ == '__main__':
    csv_file = 'd:\\AI量化999\\data\\300\\SH\\SH#999999_utf8.csv'
    load_index_data(csv_file, '999999', '上证指数')
