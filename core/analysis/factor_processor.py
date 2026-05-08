# -*- coding: utf-8 -*-
"""
因子预处理器
Factor Processor

提供因子数据的预处理流水线，包括缺失值处理、去极值、标准化和中性化
"""

import pandas as pd
import numpy as np
from typing import Optional, Literal


class FactorProcessor:
    """
    因子预处理器

    提供完整的因子预处理流水线，包括：
    1. 缺失值处理（Missing Value Handling）
    2. 去极值处理（Outlier Removal）
    3. 标准化处理（Normalization）
    4. 中性化处理（Neutralization）

    Attributes:
        missing_method: 缺失值处理方法，可选 'ffill', 'mean', 'median'
        outlier_method: 去极值方法，可选 'mad', 'iqr', 'percentile'
        normalize_method: 标准化方法，可选 'zscore', 'minmax', 'rank'

    Example:
        >>> processor = FactorProcessor(
        ...     missing_method='ffill',
        ...     outlier_method='mad',
        ...     normalize_method='zscore'
        ... )
        >>> processed_data = processor.process_pipeline(factor_data)
    """

    def __init__(
        self,
        missing_method: Literal['ffill', 'mean', 'median'] = 'ffill',
        outlier_method: Literal['mad', 'iqr', 'percentile'] = 'mad',
        normalize_method: Literal['zscore', 'minmax', 'rank'] = 'zscore'
    ):
        """
        初始化因子预处理器

        Args:
            missing_method: 缺失值处理方法
                - 'ffill': 前向填充（Forward Fill）
                - 'mean': 均值填充
                - 'median': 中位数填充
            outlier_method: 去极值方法
                - 'mad': 中位数绝对偏差法（Median Absolute Deviation）
                - 'iqr': 四分位距法（Interquartile Range）
                - 'percentile': 百分位数法
            normalize_method: 标准化方法
                - 'zscore': Z-score 标准化
                - 'minmax': Min-Max 缩放到 [0, 1]
                - 'rank': 排名标准化
        """
        self.missing_method = missing_method
        self.outlier_method = outlier_method
        self.normalize_method = normalize_method

    def process_pipeline(self, factor_data: pd.DataFrame) -> pd.DataFrame:
        """
        完整预处理流水线

        按顺序执行：缺失值处理 -> 去极值 -> 标准化 -> 中性化

        Args:
            factor_data: 原始因子数据，DataFrame格式

        Returns:
            pd.DataFrame: 预处理后的因子数据

        Example:
            >>> processor = FactorProcessor()
            >>> clean_data = processor.process_pipeline(raw_factor_data)
        """
        # 复制数据，避免修改原始数据
        data = factor_data.copy()

        # 1. 缺失值处理
        data = self.handle_missing_values(data)

        # 2. 去极值处理
        data = self.remove_outliers(data)

        # 3. 标准化处理
        data = self.normalize(data)

        # 4. 中性化处理
        data = self.neutralize(data)

        return data

    def handle_missing_values(
        self,
        data: pd.DataFrame,
        method: Optional[str] = None
    ) -> pd.DataFrame:
        """
        缺失值处理

        Args:
            data: 因子数据
            method: 处理方法，默认使用初始化时设置的方法
                - 'ffill': 前向填充，用前一个有效值填充
                - 'mean': 用列均值填充
                - 'median': 用列中位数填充

        Returns:
            pd.DataFrame: 处理后的数据

        Note:
            前向填充后仍可能存在开头的缺失值，会用后向填充补充
        """
        method = method or self.missing_method
        result = data.copy()

        if method == 'ffill':
            # 前向填充，再后向填充处理开头的缺失值
            result = result.ffill().bfill()
        elif method == 'mean':
            # 均值填充
            result = result.fillna(result.mean())
        elif method == 'median':
            # 中位数填充
            result = result.fillna(result.median())
        else:
            raise ValueError(f"不支持的缺失值处理方法: {method}")

        return result

    def remove_outliers(
        self,
        data: pd.DataFrame,
        method: Optional[str] = None
    ) -> pd.DataFrame:
        """
        去极值处理

        将超出阈值的极端值截断到边界值（Winsorization）

        Args:
            data: 因子数据
            method: 去极值方法，默认使用初始化时设置的方法
                - 'mad': 中位数绝对偏差法，阈值为 median ± 3*MAD
                - 'iqr': 四分位距法，阈值为 Q1-1.5*IQR 到 Q3+1.5*IQR
                - 'percentile': 百分位数法，截断到 [1%, 99%]

        Returns:
            pd.DataFrame: 去极值后的数据
        """
        method = method or self.outlier_method
        result = data.copy()

        if method == 'mad':
            # MAD 方法：中位数绝对偏差
            result = self._remove_outliers_mad(result)
        elif method == 'iqr':
            # IQR 方法：四分位距
            result = self._remove_outliers_iqr(result)
        elif method == 'percentile':
            # 百分位数方法
            result = self._remove_outliers_percentile(result)
        else:
            raise ValueError(f"不支持的去极值方法: {method}")

        return result

    def _remove_outliers_mad(
        self,
        data: pd.DataFrame,
        n_mad: float = 3.0
    ) -> pd.DataFrame:
        """
        MAD（中位数绝对偏差）去极值

        MAD = median(|Xi - median(X)|)
        边界 = median ± n_mad * 1.4826 * MAD

        1.4826 是将 MAD 转换为标准差估计的常数

        Args:
            data: 因子数据
            n_mad: MAD 倍数，默认 3.0

        Returns:
            pd.DataFrame: 去极值后的数据
        """
        result = data.copy()

        for col in result.columns:
            col_data = result[col]
            median = col_data.median()
            mad = (col_data - median).abs().median()

            # 1.4826 是将 MAD 转换为标准差的缩放因子
            threshold = n_mad * 1.4826 * mad
            lower_bound = median - threshold
            upper_bound = median + threshold

            result[col] = col_data.clip(lower=lower_bound, upper=upper_bound)

        return result

    def _remove_outliers_iqr(
        self,
        data: pd.DataFrame,
        k: float = 1.5
    ) -> pd.DataFrame:
        """
        IQR（四分位距）去极值

        IQR = Q3 - Q1
        边界 = [Q1 - k*IQR, Q3 + k*IQR]

        Args:
            data: 因子数据
            k: IQR 倍数，默认 1.5

        Returns:
            pd.DataFrame: 去极值后的数据
        """
        result = data.copy()

        for col in result.columns:
            col_data = result[col]
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - k * iqr
            upper_bound = q3 + k * iqr

            result[col] = col_data.clip(lower=lower_bound, upper=upper_bound)

        return result

    def _remove_outliers_percentile(
        self,
        data: pd.DataFrame,
        lower_pct: float = 0.01,
        upper_pct: float = 0.99
    ) -> pd.DataFrame:
        """
        百分位数去极值

        将数据截断到指定的百分位数范围

        Args:
            data: 因子数据
            lower_pct: 下界百分位数，默认 0.01 (1%)
            upper_pct: 上界百分位数，默认 0.99 (99%)

        Returns:
            pd.DataFrame: 去极值后的数据
        """
        result = data.copy()

        for col in result.columns:
            col_data = result[col]
            lower_bound = col_data.quantile(lower_pct)
            upper_bound = col_data.quantile(upper_pct)

            result[col] = col_data.clip(lower=lower_bound, upper=upper_bound)

        return result

    def normalize(
        self,
        data: pd.DataFrame,
        method: Optional[str] = None
    ) -> pd.DataFrame:
        """
        标准化处理

        Args:
            data: 因子数据
            method: 标准化方法，默认使用初始化时设置的方法
                - 'zscore': Z-score 标准化，均值为0，标准差为1
                - 'minmax': Min-Max 缩放到 [0, 1]
                - 'rank': 排名标准化，转换为百分位排名

        Returns:
            pd.DataFrame: 标准化后的数据
        """
        method = method or self.normalize_method
        result = data.copy()

        if method == 'zscore':
            # Z-score 标准化: (x - mean) / std
            result = (result - result.mean()) / result.std()
        elif method == 'minmax':
            # Min-Max 缩放: (x - min) / (max - min)
            result = (result - result.min()) / (result.max() - result.min())
        elif method == 'rank':
            # 排名标准化: 转换为百分位排名
            result = result.rank(pct=True)
        else:
            raise ValueError(f"不支持的标准化方法: {method}")

        return result

    def neutralize(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        中性化处理（市场中性化）

        简单实现：对每列去均值，使因子均值为0
        这是市场中性化的基本形式，去除市场整体因素的影响

        Args:
            data: 因子数据

        Returns:
            pd.DataFrame: 中性化后的数据

        Note:
            更复杂的中性化（如行业中性化、市值中性化）需要额外的分组信息，
            可以通过继承此类并重写此方法来实现
        """
        result = data.copy()

        # 市场中性化：去均值
        result = result - result.mean()

        return result
