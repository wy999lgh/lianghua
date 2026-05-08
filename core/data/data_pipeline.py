#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管道模块
功能：实现统一的数据加载流程（数据获取→清洗→因子计算→标准化）
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
import pandas as pd
import numpy as np

from .data_fetcher import DataFetcher
from .data_cleaner import DataCleaner
from .database import get_db
from ..analysis.factor_library import FactorLibrary
from ..analysis.factor_processor import FactorProcessor


class DataPipeline:
    """
    数据管道类
    
    实现完整的数据处理流程：
    1. 数据获取（从数据库或AKShare）
    2. 数据清洗（列名标准化、类型转换、去重）
    3. 因子计算（技术指标计算）
    4. 因子预处理（缺失值、去极值、标准化）
    5. 输出标准化格式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据管道
        
        参数：
        - config: 配置字典
        """
        self.config = config or {}
        
        # 初始化组件
        self.data_fetcher = DataFetcher()
        self.data_cleaner = DataCleaner()
        self.factor_library = FactorLibrary()
        self.factor_processor = FactorProcessor(
            missing_method=self.config.get('missing_method', 'ffill'),
            outlier_method=self.config.get('outlier_method', 'mad'),
            normalize_method=self.config.get('normalize_method', 'zscore')
        )
        
        # 数据存储
        self.raw_data = None
        self.clean_data = None
        self.factor_data = None
        self.processed_data = None
        
        # 元数据
        self.metadata = {}

    def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        data_type: Literal['stock', 'etf', 'index'] = 'stock',
        source: Literal['db', 'akshare'] = 'db'
    ) -> pd.DataFrame:
        """
        获取原始数据
        
        参数：
        - symbol: 标的代码
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - data_type: 数据类型 (stock/etf/index)
        - source: 数据源 (db/akshare)
        
        返回：
        pd.DataFrame - 原始数据
        """
        if source == 'db':
            # 从数据库获取
            self.raw_data = self.data_fetcher.get_data(symbol, start_date, end_date)
        else:
            # 从AKShare获取
            if data_type == 'stock':
                self.raw_data = self.data_fetcher.fetch_stock_daily(symbol, start_date, end_date)
            elif data_type == 'etf':
                self.raw_data = self.data_fetcher.fetch_etf_daily(symbol, start_date, end_date)
            elif data_type == 'index':
                self.raw_data = self.data_fetcher.fetch_index_daily(symbol, start_date, end_date)
        
        # 更新元数据
        self.metadata.update({
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'data_type': data_type,
            'source': source,
            'raw_rows': len(self.raw_data) if self.raw_data is not None else 0
        })
        
        return self.raw_data

    def clean_data(self, adjust_type: Optional[str] = None) -> pd.DataFrame:
        """
        清洗数据
        
        参数：
        - adjust_type: 复权类型 (None/qfq/hfq)
        
        返回：
        pd.DataFrame - 清洗后的数据
        """
        if self.raw_data is None:
            raise ValueError("请先调用fetch_data获取数据")
        
        # 根据数据类型选择清洗方法
        if self.metadata.get('data_type') in ['stock', 'etf']:
            self.clean_data = self.data_cleaner.clean_stock_data(
                self.raw_data, 
                self.metadata.get('symbol', ''), 
                adjust_type or 'qfq'
            )
        else:
            self.clean_data = self.data_cleaner.clean_index_data(
                self.raw_data, 
                self.metadata.get('symbol', '')
            )
        
        # 更新元数据
        self.metadata['clean_rows'] = len(self.clean_data)
        
        return self.clean_data

    def calculate_factors(
        self,
        factors: Optional[List[str]] = None,
        custom_factors: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        计算因子
        
        参数：
        - factors: 要计算的因子列表
        - custom_factors: 自定义因子配置
        
        返回：
        pd.DataFrame - 包含因子的数据
        """
        if self.clean_data is None:
            raise ValueError("请先调用clean_data清洗数据")
        
        # 默认计算的因子
        default_factors = [
            'ma5', 'ma10', 'ma20', 'ma60',  # 均线
            'ema12', 'ema26',                 # 指数均线
            'cmo14',                         # CMO动量指标
            'bb',                             # 布林带
            'atr14'                           # ATR
        ]
        
        factors_to_calc = factors or default_factors
        
        # 创建因子数据副本
        self.factor_data = self.clean_data.copy()
        
        # 计算因子
        close = self.clean_data['close']
        high = self.clean_data['high']
        low = self.clean_data['low']
        
        for factor in factors_to_calc:
            if factor.startswith('ma'):
                # 移动平均线
                period = int(factor[2:])
                self.factor_data[f'{factor}'] = self.factor_library.ma(close, period=period)
                
            elif factor.startswith('ema'):
                # 指数移动平均线
                period = int(factor[3:])
                self.factor_data[f'{factor}'] = self.factor_library.ema(close, period=period)
                
            elif factor.startswith('cmo'):
                # CMO动量指标
                period = int(factor[3:]) if len(factor) > 3 else 14
                self.factor_data[f'{factor}'] = self.factor_library.cmo(close, period=period)
                
            elif factor == 'bb':
                # 布林带
                bb_df = self.factor_library.bollinger_bands_ema(close, period=20)
                self.factor_data = pd.concat([self.factor_data, bb_df], axis=1)
                
            elif factor.startswith('atr'):
                # ATR
                period = int(factor[3:]) if len(factor) > 3 else 14
                atr = self._calculate_atr(high, low, close, period)
                self.factor_data[f'{factor}'] = atr
                
            elif factor == 'rolling_zscore':
                # 滚动Z-Score
                self.factor_data[f'{factor}'] = self.factor_library.rolling_zscore(close, period=20)
                
            elif factor == 'rolling_slope':
                # 滚动斜率
                self.factor_data[f'{factor}'] = self.factor_library.rolling_slope(close, period=20)
        
        # 更新元数据
        self.metadata['factors_calculated'] = factors_to_calc
        
        return self.factor_data

    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """
        计算ATR指标
        
        参数：
        - high: 最高价序列
        - low: 最低价序列
        - close: 收盘价序列
        - period: 计算周期
        
        返回：
        pd.Series - ATR序列
        """
        # 计算真实波动范围
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 使用Wilder's Smoothing计算ATR
        atr = tr.rolling(window=period).mean()
        
        return atr

    def process_factors(self) -> pd.DataFrame:
        """
        预处理因子（缺失值处理、去极值、标准化）
        
        返回：
        pd.DataFrame - 预处理后的因子数据
        """
        if self.factor_data is None:
            raise ValueError("请先调用calculate_factors计算因子")
        
        # 获取因子列（排除原始行情列）
        factor_columns = [col for col in self.factor_data.columns 
                         if col not in ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']]
        
        if not factor_columns:
            # 如果没有因子列，直接返回
            self.processed_data = self.factor_data
            return self.processed_data
        
        # 提取因子数据
        factors_df = self.factor_data[factor_columns]
        
        # 预处理流水线
        processed_factors = self.factor_processor.process_pipeline(factors_df)
        
        # 合并回原始数据
        self.processed_data = self.factor_data.copy()
        self.processed_data[factor_columns] = processed_factors
        
        # 更新元数据
        self.metadata['factors_processed'] = factor_columns
        
        return self.processed_data

    def get_output(self, format: Literal['dataframe', 'dict', 'strategy_input'] = 'dataframe') -> Any:
        """
        获取输出数据
        
        参数：
        - format: 输出格式 (dataframe/dict/strategy_input)
        
        返回：
        Any - 格式化后的输出数据
        """
        if self.processed_data is None:
            raise ValueError("请先完成数据处理流程")
        
        if format == 'dataframe':
            return self.processed_data
        
        elif format == 'dict':
            return self.processed_data.to_dict('records')
        
        elif format == 'strategy_input':
            # 转换为策略输入格式
            result = []
            for _, row in self.processed_data.iterrows():
                data_point = {
                    'datetime': row['date'] if isinstance(row['date'], datetime) 
                                else pd.to_datetime(row['date']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'amount': float(row.get('amount', 0)),
                    'factors': {}
                }
                
                # 添加因子数据
                factor_columns = [col for col in self.processed_data.columns 
                                 if col not in ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']]
                for col in factor_columns:
                    data_point['factors'][col] = float(row[col]) if not pd.isna(row[col]) else 0.0
                
                result.append(data_point)
            
            return result
        
        else:
            raise ValueError(f"不支持的输出格式: {format}")

    def run_pipeline(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        data_type: Literal['stock', 'etf', 'index'] = 'stock',
        source: Literal['db', 'akshare'] = 'db',
        adjust_type: Optional[str] = None,
        factors: Optional[List[str]] = None,
        output_format: Literal['dataframe', 'dict', 'strategy_input'] = 'dataframe'
    ) -> Any:
        """
        运行完整的数据管道
        
        参数：
        - symbol: 标的代码
        - start_date: 开始日期
        - end_date: 结束日期
        - data_type: 数据类型
        - source: 数据源
        - adjust_type: 复权类型
        - factors: 要计算的因子列表
        - output_format: 输出格式
        
        返回：
        Any - 处理后的输出数据
        """
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行数据管道
        self.fetch_data(symbol, start_date, end_date, data_type, source)
        self.clean_data(adjust_type)
        self.calculate_factors(factors)
        self.process_factors()
        
        # 记录结束时间
        end_time = datetime.now()
        self.metadata['pipeline_duration'] = (end_time - start_time).total_seconds()
        
        return self.get_output(output_format)

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取元数据
        
        返回：
        Dict[str, Any] - 元数据字典
        """
        return self.metadata

    def save_to_db(self, table_name: Optional[str] = None) -> None:
        """
        将处理后的数据保存到数据库
        
        参数：
        - table_name: 表名（可选，默认为stock_{symbol}）
        """
        if self.processed_data is None:
            raise ValueError("请先完成数据处理流程")
        
        db = get_db()
        actual_table_name = table_name or f"{self.metadata.get('data_type', 'stock')}_{self.metadata.get('symbol', '')}"
        
        db.save_data(self.processed_data, actual_table_name, if_exists='replace')


class PipelineConfig:
    """
    管道配置类
    """
    
    def __init__(self):
        # 数据源配置
        self.source = 'db'  # 'db' or 'akshare'
        
        # 数据类型
        self.data_type = 'stock'  # 'stock', 'etf', 'index'
        
        # 复权类型
        self.adjust_type = 'qfq'  # None, 'qfq', 'hfq'
        
        # 因子配置
        self.factors = [
            'ma5', 'ma10', 'ma20', 'ma60',
            'ema12', 'ema26',
            'cmo14',
            'bb',
            'atr14'
        ]
        
        # 因子预处理配置
        self.missing_method = 'ffill'  # 'ffill', 'mean', 'median'
        self.outlier_method = 'mad'    # 'mad', 'iqr', 'percentile'
        self.normalize_method = 'zscore'  # 'zscore', 'minmax', 'rank'
        
        # 输出配置
        self.output_format = 'dataframe'  # 'dataframe', 'dict', 'strategy_input'
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'source': self.source,
            'data_type': self.data_type,
            'adjust_type': self.adjust_type,
            'factors': self.factors,
            'missing_method': self.missing_method,
            'outlier_method': self.outlier_method,
            'normalize_method': self.normalize_method,
            'output_format': self.output_format
        }
