# -*- coding: utf-8 -*-
"""
网格交易系统 - 评估模块
Evaluation module for backtesting performance analysis

本模块提供回测绩效评估和偏差检查功能：
- ReportGenerator: 绩效报告生成器，计算各种绩效指标
- BiasChecker: 偏差检查器，检测回测中的常见陷阱
"""

from .report_generator import ReportGenerator
from .bias_checker import BiasChecker
from .markdown_report import render_backtest_report_markdown, write_backtest_report_markdown

__all__ = [
    'ReportGenerator',
    'BiasChecker',
    'render_backtest_report_markdown',
    'write_backtest_report_markdown',
]

__version__ = '1.0.0'
