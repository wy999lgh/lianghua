import pandas as pd
import numpy as np
from datetime import datetime
import os

class DataLoader:
    """
    数据加载器类，用于加载和处理历史行情数据
    
    功能：
    - 加载CSV格式的历史行情数据
    - 处理数据格式，确保符合backtrader的要求
    - 提供数据访问接口
    """
    
    def __init__(self, data_dir=None):
        """
        初始化数据加载器
        
        参数：
        data_dir: str - 数据目录路径，如果为None则使用默认路径
        """
        if data_dir:
            self.data_dir = data_dir
        else:
            # 使用默认数据目录路径
            # 直接指定项目根目录的data目录
            # 基于当前文件路径计算
            current_file = os.path.abspath(__file__)
            
            # 找到项目根目录 '网格01'
            path_parts = os.path.normpath(current_file).split(os.sep)
            project_root_index = -1
            for i, part in enumerate(path_parts):
                if part == '网格01':
                    project_root_index = i
                    break
            
            if project_root_index != -1:
                # 构建项目根目录路径
                project_root = os.sep.join(path_parts[:project_root_index + 1])
                # 添加data目录
                self.data_dir = os.path.join(project_root, 'data')
            else:
                # 如果找不到项目根目录，使用当前目录的上两级
                self.data_dir = os.path.abspath(os.path.join(os.path.dirname(current_file), '../../data'))
    
    def load_csv_data(self, file_name, start_date=None, end_date=None):
        """
        加载CSV格式的历史行情数据
        
        参数：
        file_name: str - CSV文件名
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"
        
        返回：
        pd.DataFrame - 处理后的行情数据
        """
        # 构建文件路径
        file_path = f"{self.data_dir}/{file_name}"
        
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
            df = df.astype({
                'open': 'float64',
                'close': 'float64',
                'high': 'float64',
                'low': 'float64',
                'volume': 'float64',
                'amount': 'float64'
            })
            
            # 按照日期排序
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            return pd.DataFrame()
    
    def get_data_for_backtrader(self, file_name, start_date=None, end_date=None):
        """
        获取适用于backtrader的数据格式
        
        参数：
        file_name: str - CSV文件名
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"
        
        返回：
        pd.DataFrame - 符合backtrader要求的数据
        """
        df = self.load_csv_data(file_name, start_date, end_date)
        
        # backtrader要求数据按时间升序排列
        # 确保索引是datetime类型
        if not df.empty:
            # 转换为backtrader需要的格式
            # backtrader会自动识别open, high, low, close, volume列
            pass
        
        return df
    
    def get_data_summary(self, file_name):
        """
        获取数据摘要信息
        
        参数：
        file_name: str - CSV文件名
        
        返回：
        dict - 数据摘要信息
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
                    'min': df['open'].min(),
                    'max': df['open'].max(),
                    'mean': df['open'].mean()
                },
                'close': {
                    'min': df['close'].min(),
                    'max': df['close'].max(),
                    'mean': df['close'].mean()
                },
                'volume': {
                    'min': df['volume'].min(),
                    'max': df['volume'].max(),
                    'mean': df['volume'].mean()
                }
            }
        }
        
        return summary
    
    def load_data(self, start_date=None, end_date=None):
        """
        默认数据加载方法，加载默认的CSV数据文件
        
        参数：
        start_date: str - 开始日期，格式为"YYYY-MM-DD"
        end_date: str - 结束日期，格式为"YYYY-MM-DD"
        
        返回：
        pd.DataFrame - 处理后的行情数据
        """
        # 默认数据文件名
        default_file_name = "19900101-20251014_159633_日线_前复权.csv"
        return self.load_csv_data(default_file_name, start_date, end_date)

# 测试代码
if __name__ == "__main__":
    # 使用默认数据目录路径
    loader = DataLoader()
    
    # 加载数据
    file_name = "19900101-20251014_159633_日线_前复权.csv"
    df = loader.load_csv_data(file_name)
    
    if not df.empty:
        print("数据加载成功！")
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
        print(f"收盘价范围: {summary['data_range']['close']['min']} - {summary['data_range']['close']['max']}")
    else:
        print("数据加载失败！")
