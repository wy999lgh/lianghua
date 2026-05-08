#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新回测结果表结构，支持完整报告数据存储"""

import sys
sys.path.insert(0, 'd:/AI量化999')
from core.data.database import get_db

def update_backtest_table():
    db = get_db()
    conn = db._pg_connect()
    try:
        cur = conn.cursor()
        
        # 添加策略名称和类型字段
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS strategy_name TEXT DEFAULT ''")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS strategy_type TEXT DEFAULT 'grid'")
        
        # 添加初始和最终资金字段
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS initial_cash DOUBLE PRECISION DEFAULT 1000000")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS final_cash DOUBLE PRECISION DEFAULT 1000000")
        
        # 添加更多绩效指标字段
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS annual_return DOUBLE PRECISION DEFAULT 0")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS sortino_ratio DOUBLE PRECISION DEFAULT 0")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS calmar_ratio DOUBLE PRECISION DEFAULT 0")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS win_rate DOUBLE PRECISION DEFAULT 0")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS volatility DOUBLE PRECISION DEFAULT 0")
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS benchmark_return DOUBLE PRECISION DEFAULT 0")
        
        # 添加JSONB字段存储完整报告数据
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS full_report JSONB DEFAULT '{}'::jsonb")
        
        # 添加存储图表数据的JSONB字段
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS chart_data JSONB DEFAULT '{}'::jsonb")
        
        # 添加标的代码字段
        cur.execute("ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS symbol TEXT DEFAULT ''")
        
        conn.commit()
        print("回测结果表结构更新成功！")
        
    finally:
        db._pg_release(conn)

if __name__ == "__main__":
    update_backtest_table()
