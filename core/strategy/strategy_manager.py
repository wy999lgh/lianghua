#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略管理器
功能：管理所有交易策略，支持策略注册、加载、对比等功能
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional, Any
from datetime import datetime

from core.strategy.base_strategy import BaseStrategy


class StrategyManager:
    """
    策略管理器类

    负责管理所有交易策略，支持策略注册、加载、对比等功能
    """

    def __init__(self, strategies_dir: Optional[str] = None):
        """
        初始化策略管理器

        参数：
        - strategies_dir: 策略目录路径，如果为None则使用默认路径
        """
        self.strategies: Dict[str, Type[BaseStrategy]] = {}
        self.strategy_instances: Dict[str, BaseStrategy] = {}

        # 设置策略目录
        if strategies_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.strategies_dir = os.path.join(current_dir, 'strategies')
        else:
            self.strategies_dir = strategies_dir

        # 确保策略目录存在
        os.makedirs(self.strategies_dir, exist_ok=True)

        # 自动注册当前目录中的策略
        self._auto_register_strategies()

    def _auto_register_strategies(self) -> None:
        """
        自动注册策略目录中的策略
        """
        # 检查策略目录是否存在
        if not os.path.exists(self.strategies_dir):
            return

        # 遍历策略目录中的所有Python文件
        for filename in os.listdir(self.strategies_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    # 移除.py扩展名
                    module_name = filename[:-3]

                    # 构建模块路径
                    module_path = f"core.strategy.strategies.{module_name}"

                    # 动态导入模块
                    module = importlib.import_module(module_path)

                    # 查找模块中的策略类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            issubclass(obj, BaseStrategy) and
                                obj != BaseStrategy):
                            # 注册策略
                            self.register_strategy(obj)
                            print(f"[OK] 自动注册策略: {name}")

                except Exception as e:
                    print(f"[FAIL] 加载策略文件 {filename} 失败: {e}")

    def register_strategy(self, strategy_class: Type[BaseStrategy]) -> None:
        """
        注册一个策略类

        参数：
        - strategy_class: 策略类（继承自BaseStrategy）
        """
        # 创建一个临时实例来获取策略名称
        temp_instance = strategy_class(name="temp")
        strategy_name = temp_instance.name

        self.strategies[strategy_name] = strategy_class
        print(f"[OK] 策略已注册: {strategy_name}")

    def create_strategy(self, strategy_name: str,
                        config: Optional[Dict[str, Any]] = None) -> BaseStrategy:
        """
        创建策略实例

        参数：
        - strategy_name: 策略名称
        - config: 策略配置（可选）

        返回：
        BaseStrategy - 策略实例
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"策略不存在: {strategy_name}")

        strategy_class = self.strategies[strategy_name]
        strategy = strategy_class(name=strategy_name)

        if config is not None:
            strategy.set_config(config)

        self.strategy_instances[strategy_name] = strategy
        return strategy

    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """
        获取已创建的策略实例

        参数：
        - strategy_name: 策略名称

        返回：
        BaseStrategy - 策略实例，如果不存在则返回None
        """
        return self.strategy_instances.get(strategy_name)

    def list_strategies(self) -> List[str]:
        """
        获取所有已注册的策略名称列表

        返回：
        List[str] - 策略名称列表
        """
        return list(self.strategies.keys())

    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        获取策略信息

        参数：
        - strategy_name: 策略名称

        返回：
        Dict[str, Any] - 策略信息字典，如果策略不存在则返回None
        """
        if strategy_name not in self.strategies:
            return None

        strategy_class = self.strategies[strategy_name]
        temp_instance = strategy_class(name=strategy_name)
        
        # 获取参数描述（如果策略类定义了的话）
        param_descriptions = getattr(strategy_class, 'PARAM_DESCRIPTIONS', {})

        return {
            'name': temp_instance.name,
            'description': temp_instance.description,
            'version': temp_instance.version,
            'config': temp_instance.get_config(),
            'param_descriptions': param_descriptions
        }

    def compare_strategies(self, strategy_names: List[str],
                           symbol: str, start_date: str, end_date: str,
                           initial_cash: float = 100000.0) -> Dict[str, Any]:
        """
        对比多个策略的回测结果

        参数：
        - strategy_names: 策略名称列表
        - symbol: 股票或ETF代码
        - start_date: 开始日期
        - end_date: 结束日期
        - initial_cash: 初始资金

        返回：
        Dict[str, Any] - 对比结果
        """
        from core.backtest.backtester import BacktestEngine

        results = {}
        engine = BacktestEngine()

        for strategy_name in strategy_names:
            if strategy_name not in self.strategies:
                print(f"✗ 策略不存在: {strategy_name}")
                continue

            try:
                print(f"正在回测策略: {strategy_name}")

                # 创建策略实例
                strategy = self.create_strategy(strategy_name)
                config = strategy.get_config()

                # 运行回测
                result = engine.run_backtest(
                    symbol_or_file=symbol,
                    grid_config=config,
                    start_date=start_date,
                    end_date=end_date
                )

                results[strategy_name] = result
                print(f"✓ 策略 {strategy_name} 回测完成")

            except Exception as e:
                print(f"✗ 策略 {strategy_name} 回测失败: {e}")

        # 生成对比报告
        comparison_report = self._generate_comparison_report(results)

        return {
            'results': results,
            'comparison_report': comparison_report
        }

    def _generate_comparison_report(self, results: Dict[str, Dict]) -> str:
        """
        生成策略对比报告

        参数：
        - results: 回测结果字典

        返回：
        str - 对比报告（Markdown格式）
        """
        report = "# 策略对比报告\n\n"

        report += "## 回测概览\n\n"
        report += "| 策略名称 | 初始资金 | 最终资金 | 总收益 | 总收益率 | 交易次数 |\n"
        report += "|---------|---------|---------|--------|----------|----------|\n"

        for strategy_name, result in results.items():
            report += (f"| {strategy_name} | {result.get('initial_value', 0):.2f} | "
                       f"{result.get('final_value', 0):.2f} | {result.get('total_return', 0):.2f} | "
                       f"{result.get('total_return_percent', 0):.2f}% | "
                       f"{len(result.get('trade_records', []))} |\n")

        report += "\n## 详细对比\n\n"

        for strategy_name, result in results.items():
            report += f"### {strategy_name}\n\n"
            report += f"- 初始资金: {result.get('initial_value', 0):.2f}\n"
            report += f"- 最终资金: {result.get('final_value', 0):.2f}\n"
            report += f"- 总收益: {result.get('total_return', 0):.2f}\n"
            report += f"- 总收益率: {result.get('total_return_percent', 0):.2f}%\n"
            report += f"- 交易次数: {len(result.get('trade_records', []))}\n"

            if 'strategy_performance' in result:
                perf = result['strategy_performance']
                report += f"- 胜率: {perf.get('win_rate', 0) * 100:.2f}%\n"
                report += f"- 盈利因子: {perf.get('profit_factor', 0):.2f}\n"

            report += "\n"

        return report

    def save_comparison_report(self, report: str, filename: str) -> None:
        """
        保存对比报告到文件

        参数：
        - report: 报告内容
        - filename: 文件名
        """
        # 确保reports目录存在
        reports_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', '..', 'tests')
        os.makedirs(reports_dir, exist_ok=True)

        filepath = os.path.join(reports_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✓ 对比报告已保存到: {filepath}")

    def remove_strategy(self, strategy_name: str) -> bool:
        """
        移除已注册的策略

        参数：
        - strategy_name: 策略名称

        返回：
        bool - 是否成功移除
        """
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            if strategy_name in self.strategy_instances:
                del self.strategy_instances[strategy_name]
            return True
        return False

    def clear_all(self) -> None:
        """清除所有已注册的策略和实例"""
        self.strategies.clear()
        self.strategy_instances.clear()


# 全局策略管理器实例
_strategy_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    """
    获取全局策略管理器实例

    返回：
    StrategyManager - 策略管理器实例
    """
    global _strategy_manager

    if _strategy_manager is None:
        _strategy_manager = StrategyManager()

    return _strategy_manager
