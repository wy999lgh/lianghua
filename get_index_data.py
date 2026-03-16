#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取沪深300、中证500、创业板指数的日线数据
"""

import sys
import pandas as pd
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from user.tqcenter import tq

def get_index_data():
    """获取指数日线数据"""
    print("=" * 80)
    print("获取沪深300、中证500、创业板指数日线数据")
    print("=" * 80)
    
    try:
        # 初始化连接
        tq.initialize(__file__)
        print("初始化连接成功")
        
        # 指数代码
        index_codes = {
            "沪深300": "000300.SH",
            "中证500": "000905.SH",
            "创业板": "399006.SZ"
        }
        
        # 数据字段
        fields = ["Open", "High", "Low", "Close", "Volume", "Amount"]
        
        # 时间范围（获取全部数据）
        start_time = "20000101"  # 从2000年开始
        end_time = ""  # 空字符串表示当前时间
        
        # 数据周期
        period = "1d"  # 日线
        
        # 除权类型
        dividend_type = "none"  # 不复权
        
        # 创建数据目录
        data_dir = Path(__file__).parent / 'data' / 'index'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取每个指数的数据
        for index_name, index_code in index_codes.items():
            print(f"\n获取 {index_name} ({index_code}) 数据...")
            
            # 获取数据
            data = tq.get_market_data(
                field_list=fields,
                stock_list=[index_code],
                period=period,
                start_time=start_time,
                end_time=end_time,
                dividend_type=dividend_type
            )
            
            if not data:
                print(f"获取 {index_name} 数据失败")
                continue
            
            # 保存数据
            for field, df in data.items():
                # 重命名列
                df.columns = [index_name]
                
                # 保存为CSV文件
                file_path = data_dir / f"{index_name}_{field}.csv"
                df.to_csv(file_path, encoding='utf-8-sig')
                print(f"保存 {field} 数据到: {file_path}")
            
            # 显示数据基本信息
            if "Close" in data:
                close_df = data["Close"]
                print(f"数据时间范围: {close_df.index.min()} 到 {close_df.index.max()}")
                print(f"数据条数: {len(close_df)}")
                print(f"最新价格: {close_df.iloc[-1].values[0]:.2f}")
        
        print("\n" + "=" * 80)
        print("数据获取完成！")
        print(f"数据保存目录: {data_dir}")
        print("=" * 80)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        tq.close()
        print("\n连接已关闭")

if __name__ == "__main__":
    get_index_data()