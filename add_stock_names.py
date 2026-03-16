#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 all_a_stocks.csv 文件添加股票名称
"""

import sys
import pandas as pd
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from user.tqcenter import tq

def add_stock_names():
    """为股票代码添加名称"""
    print("=" * 80)
    print("为 all_a_stocks.csv 添加股票名称")
    print("=" * 80)
    
    try:
        # 初始化连接
        tq.initialize(__file__)
        print("初始化连接成功")
        
        # 读取股票代码文件
        input_file = Path(__file__).parent / 'data' / 'all_a_stocks.csv'
        output_file = Path(__file__).parent / 'data' / 'stocks_with_name.csv'
        
        print(f"读取文件: {input_file}")
        df = pd.read_csv(input_file)
        print(f"共 {len(df)} 只股票")
        
        # 添加股票名称列
        names = []
        error_count = 0
        
        for i, stock_code in enumerate(df['StockCode'], 1):
            if i % 100 == 0:
                print(f"处理中... {i}/{len(df)}")
            
            try:
                # 获取股票信息
                info = tq.get_stock_info(stock_code)
                if info and 'Name' in info:
                    names.append(info['Name'])
                else:
                    names.append('')
                    error_count += 1
            except Exception as e:
                names.append('')
                error_count += 1
                if i % 100 == 0:
                    print(f"错误: {stock_code} - {e}")
        
        # 添加名称列
        df['StockName'] = names
        
        # 保存结果
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n处理完成！")
        print(f"成功处理: {len(df) - error_count} 只股票")
        print(f"失败: {error_count} 只股票")
        print(f"结果保存到: {output_file}")
        
        # 显示前10条结果
        print("\n前10条结果:")
        print(df.head(10))
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        tq.close()
        print("\n连接已关闭")

if __name__ == "__main__":
    add_stock_names()
