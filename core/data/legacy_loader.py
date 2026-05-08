# -*- coding: utf-8 -*-
"""
网格交易系统 - 数据加载器 (兼容层)
Legacy data loader for backward compatibility

迁移自: grid_trading/data/legacy_loader.py
保留原有功能以确保向后兼容
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Optional, Dict, Any

from config.database_config import get_project_root


class DataLoader:
    """
    数据加载器类，用于加载和处理历史行情数据

    功能：
    - 加载CSV格式的历史行情数据
    - 处理数据格式，确保符合backtrader的要求
    - 提供数据访问接口

    Note: 这是一个兼容层，保留原有功能。
    新代码建议使用 DataFetcher 和 Database 类。
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化数据加载器

        Args:
            data_dir: 数据目录路径，如果为 None 则使用默认路径
        """
        if data_dir:
            self.data_dir = data_dir
        else:
            # 使用配置模块获取项目根目录
            project_root = get_project_root()
            self.data_dir = os.path.join(project_root, 'data')

    def load_csv_data(
        self,
        file_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载CSV格式的历史行情数据

        Args:
            file_name: CSV文件名
            start_date: 开始日期，格式为 "YYYY-MM-DD"
            end_date: 结束日期，格式为 "YYYY-MM-DD"

        Returns:
            pd.DataFrame: 处理后的行情数据
        """
        # 构建文件路径
        file_path = os.path.join(self.data_dir, file_name)

        try:
            # 加载CSV文件
            df = pd.read_csv(file_path)

            # 处理日期列
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)

            # 筛选日期范围
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]

            # 重命名列名，使其符合backtrader的要求
            df = df.rename(columns={
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # 确保数据类型正确
            numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype('float64')

            # 按照日期排序
            df = df.sort_index()

            return df

        except Exception as e:
            print(f"加载数据失败: {e}")
            return pd.DataFrame()

    def get_data_for_backtrader(
        self,
        file_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取适用于backtrader的数据格式

        Args:
            file_name: CSV文件名
            start_date: 开始日期，格式为 "YYYY-MM-DD"
            end_date: 结束日期，格式为 "YYYY-MM-DD"

        Returns:
            pd.DataFrame: 符合backtrader要求的数据
        """
        df = self.load_csv_data(file_name, start_date, end_date)

        # backtrader要求数据按时间升序排列
        # 确保索引是datetime类型
        if not df.empty:
            # 转换为backtrader需要的格式
            # backtrader会自动识别open, high, low, close, volume列
            pass

        return df

    def get_data_summary(self, file_name: str) -> Dict[str, Any]:
        """
        获取数据摘要信息

        Args:
            file_name: CSV文件名

        Returns:
            dict: 数据摘要信息
        """
        df = self.load_csv_data(file_name)

        if df.empty:
            return {}

        summary = {
            'start_date': df.index.min().strftime('%Y-%m-%d'),
            'end_date': df.index.max().strftime('%Y-%m-%d'),
            'total_days': len(df),
            'columns': list(df.columns),
            'data_range': {
                'open': {
                    'min': float(df['open'].min()) if 'open' in df.columns else None,
                    'max': float(df['open'].max()) if 'open' in df.columns else None,
                    'mean': float(df['open'].mean()) if 'open' in df.columns else None
                },
                'close': {
                    'min': float(df['close'].min()) if 'close' in df.columns else None,
                    'max': float(df['close'].max()) if 'close' in df.columns else None,
                    'mean': float(df['close'].mean()) if 'close' in df.columns else None
                },
                'volume': {
                    'min': float(df['volume'].min()) if 'volume' in df.columns else None,
                    'max': float(df['volume'].max()) if 'volume' in df.columns else None,
                    'mean': float(df['volume'].mean()) if 'volume' in df.columns else None
                }
            }
        }

        return summary

    def load_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        默认数据加载方法，加载默认的CSV数据文件

        Args:
            start_date: 开始日期，格式为 "YYYY-MM-DD"
            end_date: 结束日期，格式为 "YYYY-MM-DD"

        Returns:
            pd.DataFrame: 处理后的行情数据
        """
        # 默认数据文件名
        default_file_name = "19900101-20251014_159633_日线_前复权.csv"
        return self.load_csv_data(default_file_name, start_date, end_date)

    def list_available_files(self, pattern: str = "*.csv") -> list:
        """
        列出数据目录中可用的文件

        Args:
            pattern: 文件匹配模式，默认 "*.csv"

        Returns:
            list: 文件名列表
        """
        import glob
        file_pattern = os.path.join(self.data_dir, pattern)
        files = glob.glob(file_pattern)
        return [os.path.basename(f) for f in files]


# 测试代码
if __name__ == "__main__":
    # 使用默认数据目录路径
    loader = DataLoader()

    # 列出可用文件
    print("可用的数据文件:")
    for f in loader.list_available_files():
        print(f"  - {f}")

    # 加载数据
    file_name = "19900101-20251014_159633_日线_前复权.csv"
    df = loader.load_csv_data(file_name)

    if not df.empty:
        print("\n数据加载成功！")
        print(f"数据形状: {df.shape}")
        print(f"数据列: {list(df.columns)}")
        print(f"数据时间范围: {df.index.min()} 到 {df.index.max()}")
        print(f"前5行数据:\n{df.head()}")

        # 获取数据摘要
        summary = loader.get_data_summary(file_name)
        print(f"\n数据摘要:")
        print(f"开始日期: {summary['start_date']}")
        print(f"结束日期: {summary['end_date']}")
        print(f"总天数: {summary['total_days']}")
        if summary['data_range']['close']['min'] is not None:
            print(
                f"收盘价范围: {summary['data_range']['close']['min']:.2f} - {summary['data_range']['close']['max']:.2f}")
    else:
        print("数据加载失败！")
