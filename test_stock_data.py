#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试股票数据获取功能

本脚本演示如何使用 tqcenter 获取股票历史数据
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from user.tqcenter import tq

def test_stock_data():
    """测试股票数据获取"""
    print("=" * 80)
    print("测试股票数据获取功能 - 获取所有字段")
    print("=" * 80)
    
    try:
        # 初始化连接
        tq.initialize(__file__)
        print("初始化连接成功")
        
        # 测试获取股票数据 - 空field_list表示获取所有字段
        print("\n获取浦发银行(600000.SH)的所有字段数据")
        result = tq.get_market_data(
            field_list=[],  # 空列表表示获取所有字段
            stock_list=['600000.SH'],  # 浦发银行
            start_time='20250101',  # 开始日期
            end_time='20250105',    # 结束日期
            count=-1,               # -1表示不限制数量
            dividend_type='none',   # 不复权
            period='1d',            # 日K线
            fill_data=True          # 填充缺失数据
        )
        
        print(f"\n返回的数据类型: {type(result)}")
        print(f"返回的字段数量: {len(result)}")
        print(f"所有可用字段: {list(result.keys())}")
        
        # 检查是否获取到数据
        if result:
            # 打印每个字段的数据
            for field, data in result.items():
                print(f"\n{field} 数据:")
                print(data)
        else:
            print("未获取到数据")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        tq.close()
        print("\n连接已关闭")

if __name__ == "__main__":
    test_stock_data()
