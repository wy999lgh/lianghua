# -*- coding: utf-8 -*-
"""
网格交易系统 - 回测偏差检查器
Bias checker for detecting common backtesting pitfalls
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import warnings


class BiasChecker:
    """
    回测偏差检查器 - 检测常见的回测陷阱

    该类提供多种检查方法来识别回测中的常见问题：
    - 未来数据泄露 (Future Data Leak)
    - 幸存者偏差 (Survivorship Bias)
    - 前视偏差 (Look-ahead Bias)
    - 交易成本不合理
    - 滑点影响
    - 过拟合风险
    """

    # 默认阈值配置
    DEFAULT_THRESHOLDS = {
        'min_commission_rate': 0.0001,  # 最小佣金率 0.01%
        'max_commission_rate': 0.01,    # 最大佣金率 1%
        'min_slippage_rate': 0.0,       # 最小滑点率
        'max_slippage_rate': 0.005,     # 最大滑点率 0.5%
        'max_params_per_sample': 0.01,  # 每个样本最多参数数量比例
        'min_samples_per_param': 100,   # 每个参数至少需要的样本数
    }

    def __init__(self, thresholds: Dict[str, float] = None):
        """
        初始化偏差检查器

        Args:
            thresholds: 自定义阈值配置，覆盖默认值
        """
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        if thresholds:
            self.thresholds.update(thresholds)

    def check_all(self, data: pd.DataFrame = None,
                  trade_records: List[Dict] = None,
                  strategy_params: Dict = None) -> Dict[str, Any]:
        """
        运行所有偏差检查

        Args:
            data: 回测使用的市场数据，需包含日期索引
            trade_records: 交易记录列表
            strategy_params: 策略参数字典，需包含 'params' 和 'sample_size'

        Returns:
            Dict: 包含所有检查结果的字典，包括总体是否通过
        """
        results = {}

        if data is not None and not data.empty:
            results['future_data'] = self.check_future_data(data)
            results['survivorship_bias'] = self.check_survivorship_bias(data)
            results['look_ahead_bias'] = self.check_look_ahead_bias(data)

        if trade_records:
            results['transaction_cost'] = self.check_transaction_costs(
                trade_records)
            results['slippage'] = self.check_slippage_impact(trade_records)

        if strategy_params:
            results['overfitting'] = self.check_overfitting_risk(
                strategy_params)

        # 计算总体是否通过
        results['passed'] = all(
            r.get('passed', True) for r in results.values()
            if isinstance(r, dict) and 'passed' in r
        )

        # 生成总结
        results['summary'] = self._generate_summary(results)

        return results

    def check_future_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检查是否使用了未来数据

        检查内容：
        1. 日期索引是否有序（应该递增）
        2. 是否存在超出当前日期的数据
        3. 数据是否存在时间穿越的迹象

        Args:
            data: 市场数据DataFrame，索引应为日期

        Returns:
            Dict: 检查结果
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'details': {}
        }

        if data.empty:
            result['warnings'].append("数据为空，无法进行未来数据检查")
            return result

        # 获取日期索引
        if isinstance(data.index, pd.DatetimeIndex):
            dates = data.index
        elif 'date' in data.columns:
            dates = pd.to_datetime(data['date'])
        elif 'datetime' in data.columns:
            dates = pd.to_datetime(data['datetime'])
        else:
            result['warnings'].append("未找到日期列，跳过日期顺序检查")
            return result

        # 检查1: 日期是否递增
        is_sorted = dates.is_monotonic_increasing
        result['details']['is_date_sorted'] = is_sorted
        if not is_sorted:
            result['passed'] = False
            result['issues'].append("日期索引未按递增顺序排列，可能存在数据混乱")

        # 检查2: 是否有未来日期
        today = datetime.now()
        future_dates = dates[dates > today]
        result['details']['future_dates_count'] = len(future_dates)
        if len(future_dates) > 0:
            result['passed'] = False
            result['issues'].append(
                f"数据中包含 {len(future_dates)} 条未来日期的数据，"
                f"最远日期: {future_dates.max()}"
            )

        # 检查3: 检查数据是否存在重复日期
        duplicates = dates.duplicated().sum()
        result['details']['duplicate_dates'] = duplicates
        if duplicates > 0:
            result['warnings'].append(f"发现 {duplicates} 个重复日期")

        # 检查4: 日期间隔是否异常（工作日应连续）
        if len(dates) > 1:
            date_diffs = pd.Series(dates).diff().dropna()
            max_gap = date_diffs.max()
            if hasattr(max_gap, 'days'):
                result['details']['max_date_gap_days'] = max_gap.days
                if max_gap.days > 10:  # 超过10天的间隔
                    result['warnings'].append(
                        f"数据存在较大的日期间隔（最大 {max_gap.days} 天），"
                        "请确认是否有数据缺失"
                    )

        return result

    def check_survivorship_bias(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检查幸存者偏差

        检查内容：
        1. 数据中是否只包含当前存活的股票
        2. 是否有退市股票的标记
        3. 数据的完整性检查

        Args:
            data: 市场数据DataFrame

        Returns:
            Dict: 检查结果
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'details': {}
        }

        if data.empty:
            result['warnings'].append("数据为空，无法进行幸存者偏差检查")
            return result

        # 检查1: 是否存在退市标记字段
        delisting_indicators = ['delisted', 'is_delisted', 'status',
                                'is_active', 'active', 'trade_status']
        has_delisting_field = any(
            col in data.columns for col in delisting_indicators)
        result['details']['has_delisting_field'] = has_delisting_field

        if not has_delisting_field:
            result['warnings'].append(
                "数据中未发现退市状态字段，可能存在幸存者偏差风险。"
                "建议添加退市股票数据或使用包含历史退市信息的数据源。"
            )

        # 检查2: 如果是多股票数据，检查是否有股票在中途停止
        if 'code' in data.columns or 'symbol' in data.columns:
            code_col = 'code' if 'code' in data.columns else 'symbol'

            # 获取日期列
            if isinstance(data.index, pd.DatetimeIndex):
                dates = data.index
            elif 'date' in data.columns:
                dates = pd.to_datetime(data['date'])
            else:
                dates = None

            if dates is not None:
                unique_codes = data[code_col].unique()
                result['details']['total_symbols'] = len(unique_codes)

                # 检查每个股票的数据范围
                min_date = dates.min()
                max_date = dates.max()

                incomplete_symbols = []
                for code in unique_codes[:100]:  # 限制检查数量以提高效率
                    code_data = data[data[code_col] == code]
                    if isinstance(code_data.index, pd.DatetimeIndex):
                        code_dates = code_data.index
                    elif 'date' in code_data.columns:
                        code_dates = pd.to_datetime(code_data['date'])
                    else:
                        continue

                    # 如果股票数据未覆盖到最新日期，可能是退市或停牌
                    if len(code_dates) > 0:
                        code_max_date = code_dates.max()
                        # 如果最后交易日期比数据集最新日期早超过5天
                        if (max_date - code_max_date).days > 5:
                            incomplete_symbols.append(code)

                result['details']['incomplete_symbols'] = len(
                    incomplete_symbols)
                if incomplete_symbols:
                    result['warnings'].append(
                        f"发现 {len(incomplete_symbols)} 只股票数据未覆盖到最新日期，"
                        "这是正常的（可能包含退市股票），表明数据可能不存在严重的幸存者偏差。"
                    )

        # 检查3: 数据开始时间检查
        if isinstance(data.index, pd.DatetimeIndex):
            start_date = data.index.min()
        elif 'date' in data.columns:
            start_date = pd.to_datetime(data['date']).min()
        else:
            start_date = None

        if start_date is not None:
            years_of_data = (datetime.now() - start_date).days / 365
            result['details']['years_of_data'] = round(years_of_data, 2)

            if years_of_data < 3:
                result['warnings'].append(
                    f"数据仅覆盖 {years_of_data:.1f} 年，较短的时间范围"
                    "可能无法充分检测幸存者偏差的影响。"
                )

        return result

    def check_look_ahead_bias(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检查前视偏差

        检查内容：
        1. 检查数据是否包含可能导致前视偏差的字段
        2. 检查是否存在对未来数据的依赖
        3. 检查技术指标计算是否正确

        Args:
            data: 市场数据DataFrame

        Returns:
            Dict: 检查结果
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'details': {}
        }

        if data.empty:
            result['warnings'].append("数据为空，无法进行前视偏差检查")
            return result

        # 检查1: 检查是否存在可能包含未来信息的字段
        future_info_fields = [
            'next_close', 'next_open', 'next_high', 'next_low',
            'future_return', 'forward_return', 'target', 'label',
            'next_day', 'tomorrow', 'future_price'
        ]

        suspicious_fields = [col for col in data.columns
                             if any(f in col.lower() for f in future_info_fields)]

        result['details']['suspicious_fields'] = suspicious_fields
        if suspicious_fields:
            result['warnings'].append(
                f"发现可能包含未来信息的字段: {suspicious_fields}。"
                "请确保这些字段仅用于标签生成，而非策略信号生成。"
            )

        # 检查2: 检查OHLC数据的合理性
        price_cols = {
            'open': ['open', 'Open', 'OPEN', '开盘价'],
            'high': ['high', 'High', 'HIGH', '最高价'],
            'low': ['low', 'Low', 'LOW', '最低价'],
            'close': ['close', 'Close', 'CLOSE', '收盘价']
        }

        found_cols = {}
        for price_type, possible_names in price_cols.items():
            for name in possible_names:
                if name in data.columns:
                    found_cols[price_type] = name
                    break

        if len(found_cols) == 4:
            # 检查 high >= max(open, close) 且 low <= min(open, close)
            open_col = found_cols['open']
            high_col = found_cols['high']
            low_col = found_cols['low']
            close_col = found_cols['close']

            invalid_high = (data[high_col] <
                            data[[open_col, close_col]].max(axis=1)).sum()
            invalid_low = (
                data[low_col] > data[[open_col, close_col]].min(axis=1)).sum()

            result['details']['invalid_high_count'] = int(invalid_high)
            result['details']['invalid_low_count'] = int(invalid_low)

            if invalid_high > 0 or invalid_low > 0:
                result['warnings'].append(
                    f"OHLC数据存在不一致: {invalid_high} 条记录的最高价异常，"
                    f"{invalid_low} 条记录的最低价异常。"
                )

        # 检查3: 检查是否有使用收盘价作为买入价的情况（常见的前视偏差）
        if 'signal' in data.columns and 'close' in data.columns:
            result['warnings'].append(
                "提醒: 如果使用收盘价作为交易价格，请确保信号是基于当日收盘前的数据生成。"
                "使用次日开盘价作为交易价格可以更好地避免前视偏差。"
            )

        return result

    def check_transaction_costs(self, trade_records: List[Dict]) -> Dict[str, Any]:
        """
        检查交易成本是否合理

        检查内容：
        1. 检查是否计算了交易成本
        2. 检查佣金率是否在合理范围内
        3. 检查交易成本对收益的影响

        Args:
            trade_records: 交易记录列表

        Returns:
            Dict: 检查结果
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'details': {}
        }

        if not trade_records:
            result['warnings'].append("无交易记录，无法进行交易成本检查")
            return result

        # 统计交易成本
        total_commission = 0.0
        total_turnover = 0.0
        trades_with_commission = 0
        trades_without_commission = 0

        for trade in trade_records:
            commission = trade.get('commission', 0)
            price = trade.get('price', 0)
            amount = trade.get('amount', trade.get('quantity', 0))
            turnover = price * amount

            total_turnover += turnover

            if commission > 0:
                trades_with_commission += 1
                total_commission += commission
            else:
                trades_without_commission += 1

        result['details']['total_trades'] = len(trade_records)
        result['details']['trades_with_commission'] = trades_with_commission
        result['details']['trades_without_commission'] = trades_without_commission
        result['details']['total_commission'] = round(total_commission, 2)
        result['details']['total_turnover'] = round(total_turnover, 2)

        # 检查1: 是否有交易没有计算佣金
        if trades_without_commission > 0:
            if trades_with_commission == 0:
                result['passed'] = False
                result['issues'].append(
                    "所有交易都没有计算交易成本，这将导致回测结果过于乐观。"
                    "请添加佣金和印花税的计算。"
                )
            else:
                ratio = trades_without_commission / len(trade_records)
                if ratio > 0.1:
                    result['warnings'].append(
                        f"{trades_without_commission} 笔交易（{ratio*100:.1f}%）"
                        "没有计算交易成本。"
                    )

        # 检查2: 佣金率是否合理
        if total_turnover > 0 and total_commission > 0:
            avg_commission_rate = total_commission / total_turnover
            result['details']['avg_commission_rate'] = round(
                avg_commission_rate, 6)

            if avg_commission_rate < self.thresholds['min_commission_rate']:
                result['warnings'].append(
                    f"平均佣金率 ({avg_commission_rate*100:.4f}%) 低于正常水平 "
                    f"({self.thresholds['min_commission_rate']*100:.4f}%)，"
                    "回测结果可能过于乐观。"
                )
            elif avg_commission_rate > self.thresholds['max_commission_rate']:
                result['warnings'].append(
                    f"平均佣金率 ({avg_commission_rate*100:.4f}%) 高于正常水平 "
                    f"({self.thresholds['max_commission_rate']*100:.4f}%)，"
                    "交易成本可能过高。"
                )

        return result

    def check_slippage_impact(self, trade_records: List[Dict]) -> Dict[str, Any]:
        """
        检查滑点影响

        检查内容：
        1. 检查是否考虑了滑点
        2. 检查滑点设置是否合理
        3. 评估滑点对整体收益的影响

        Args:
            trade_records: 交易记录列表

        Returns:
            Dict: 检查结果
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'details': {}
        }

        if not trade_records:
            result['warnings'].append("无交易记录，无法进行滑点检查")
            return result

        # 统计滑点信息
        trades_with_slippage = 0
        total_slippage = 0.0
        total_turnover = 0.0
        slippage_values = []

        for trade in trade_records:
            slippage = trade.get('slippage', 0)
            price = trade.get('price', 0)
            amount = trade.get('amount', trade.get('quantity', 0))
            turnover = price * amount

            total_turnover += turnover

            if slippage != 0:
                trades_with_slippage += 1
                total_slippage += abs(slippage)
                if price > 0:
                    slippage_values.append(abs(slippage) / price)

        result['details']['total_trades'] = len(trade_records)
        result['details']['trades_with_slippage'] = trades_with_slippage
        result['details']['total_slippage'] = round(total_slippage, 2)

        # 检查1: 是否考虑了滑点
        if trades_with_slippage == 0:
            result['warnings'].append(
                "回测未考虑滑点影响。在实际交易中，尤其是大单和流动性较差的品种，"
                "滑点可能显著影响收益。建议添加滑点模拟。"
            )

        # 检查2: 滑点率是否合理
        if slippage_values:
            avg_slippage_rate = np.mean(slippage_values)
            max_slippage_rate = np.max(slippage_values)

            result['details']['avg_slippage_rate'] = round(
                avg_slippage_rate, 6)
            result['details']['max_slippage_rate'] = round(
                max_slippage_rate, 6)

            if avg_slippage_rate > self.thresholds['max_slippage_rate']:
                result['warnings'].append(
                    f"平均滑点率 ({avg_slippage_rate*100:.4f}%) 较高，"
                    "请确认是否反映了真实的市场情况。"
                )

        # 检查3: 大额交易的滑点
        large_trades = [t for t in trade_records
                        if t.get('amount', 0) * t.get('price', 0) > 100000]
        large_trades_without_slippage = [t for t in large_trades
                                         if t.get('slippage', 0) == 0]

        if large_trades_without_slippage:
            result['details']['large_trades_without_slippage'] = len(
                large_trades_without_slippage)
            result['warnings'].append(
                f"发现 {len(large_trades_without_slippage)} 笔大额交易（>10万）未计算滑点，"
                "大额交易通常会产生更大的滑点影响。"
            )

        return result

    def check_overfitting_risk(self, strategy_params: Dict) -> Dict[str, Any]:
        """
        检查过拟合风险

        检查内容：
        1. 参数数量与样本数量的比例
        2. 参数优化范围是否过大
        3. 样本外测试的必要性

        Args:
            strategy_params: 策略参数字典，应包含:
                - params: 参数字典或参数数量
                - sample_size: 样本数量（交易日数或交易次数）
                - optimization_ranges: (可选) 参数优化范围

        Returns:
            Dict: 检查结果
        """
        result = {
            'passed': True,
            'issues': [],
            'warnings': [],
            'details': {}
        }

        if not strategy_params:
            result['warnings'].append("未提供策略参数信息，无法进行过拟合检查")
            return result

        # 获取参数信息
        params = strategy_params.get('params', {})
        if isinstance(params, dict):
            param_count = len(params)
        else:
            param_count = int(params)

        sample_size = strategy_params.get('sample_size', 0)

        result['details']['param_count'] = param_count
        result['details']['sample_size'] = sample_size

        # 检查1: 参数数量与样本数量的比例
        if sample_size > 0 and param_count > 0:
            params_per_sample = param_count / sample_size
            samples_per_param = sample_size / param_count

            result['details']['params_per_sample'] = round(
                params_per_sample, 6)
            result['details']['samples_per_param'] = round(
                samples_per_param, 2)

            if samples_per_param < self.thresholds['min_samples_per_param']:
                result['passed'] = False
                result['issues'].append(
                    f"每个参数仅有 {samples_per_param:.1f} 个样本支撑 "
                    f"(建议至少 {self.thresholds['min_samples_per_param']})，"
                    "存在严重的过拟合风险。"
                )
            elif samples_per_param < self.thresholds['min_samples_per_param'] * 2:
                result['warnings'].append(
                    f"每个参数有 {samples_per_param:.1f} 个样本，"
                    "过拟合风险中等。建议增加样本量或减少参数。"
                )

        # 检查2: 参数数量警告
        if param_count > 10:
            result['warnings'].append(
                f"策略使用了 {param_count} 个参数，参数过多会增加过拟合风险。"
                "建议简化策略或使用更严格的验证方法。"
            )

        # 检查3: 检查是否有优化范围信息
        optimization_ranges = strategy_params.get('optimization_ranges', {})
        if optimization_ranges:
            total_combinations = 1
            for param_name, param_range in optimization_ranges.items():
                if isinstance(param_range, (list, tuple)):
                    total_combinations *= len(param_range)
                elif isinstance(param_range, dict):
                    # 假设是 {'start': x, 'stop': y, 'step': z}
                    start = param_range.get('start', 0)
                    stop = param_range.get('stop', 1)
                    step = param_range.get('step', 1)
                    if step > 0:
                        total_combinations *= int((stop - start) / step) + 1

            result['details']['total_optimization_combinations'] = total_combinations

            if total_combinations > 1000:
                result['warnings'].append(
                    f"参数优化组合数量为 {total_combinations}，"
                    "大量的参数组合会增加数据窥探偏差。"
                    "建议使用样本外验证或交叉验证。"
                )

        # 检查4: 建议
        if sample_size > 0:
            if sample_size < 252:  # 少于一年
                result['warnings'].append(
                    f"样本量仅为 {sample_size} 个交易日（不足一年），"
                    "较短的回测周期可能无法覆盖不同市场状态。"
                )
            elif sample_size < 252 * 3:  # 少于三年
                result['warnings'].append(
                    "回测周期不足三年，建议使用更长的历史数据进行验证。"
                )

        return result

    def _generate_summary(self, results: Dict) -> Dict[str, Any]:
        """
        生成检查结果摘要

        Args:
            results: 所有检查结果

        Returns:
            Dict: 摘要信息
        """
        summary = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings_count': 0,
            'critical_issues': []
        }

        check_names = ['future_data', 'survivorship_bias', 'look_ahead_bias',
                       'transaction_cost', 'slippage', 'overfitting']

        for check_name in check_names:
            if check_name in results and isinstance(results[check_name], dict):
                summary['total_checks'] += 1
                check_result = results[check_name]

                if check_result.get('passed', True):
                    summary['passed_checks'] += 1
                else:
                    summary['failed_checks'] += 1

                warnings = check_result.get('warnings', [])
                summary['warnings_count'] += len(warnings)

                issues = check_result.get('issues', [])
                for issue in issues:
                    summary['critical_issues'].append({
                        'check': check_name,
                        'issue': issue
                    })

        return summary

    def generate_report(self, results: Dict) -> str:
        """
        生成偏差检查的文本报告

        Args:
            results: check_all() 返回的结果

        Returns:
            str: 格式化的文本报告
        """
        lines = [
            "=" * 60,
            "回测偏差检查报告",
            "=" * 60,
            ""
        ]

        # 总体结果
        overall_passed = results.get('passed', False)
        status = "通过 ✓" if overall_passed else "未通过 ✗"
        lines.append(f"【总体结果】: {status}")
        lines.append("")

        # 各项检查结果
        check_names = {
            'future_data': '未来数据检查',
            'survivorship_bias': '幸存者偏差检查',
            'look_ahead_bias': '前视偏差检查',
            'transaction_cost': '交易成本检查',
            'slippage': '滑点影响检查',
            'overfitting': '过拟合风险检查'
        }

        for check_key, check_name in check_names.items():
            if check_key in results and isinstance(results[check_key], dict):
                check_result = results[check_key]
                passed = check_result.get('passed', True)
                status_icon = "✓" if passed else "✗"

                lines.append(f"【{check_name}】 {status_icon}")

                # 输出问题
                for issue in check_result.get('issues', []):
                    lines.append(f"  ✗ {issue}")

                # 输出警告
                for warning in check_result.get('warnings', []):
                    lines.append(f"  ⚠ {warning}")

                # 如果都通过且无警告
                if passed and not check_result.get('warnings') and not check_result.get('issues'):
                    lines.append("  ✓ 检查通过，未发现问题")

                lines.append("")

        # 摘要
        summary = results.get('summary', {})
        if summary:
            lines.append("-" * 60)
            lines.append("【检查摘要】")
            lines.append(f"  总检查项: {summary.get('total_checks', 0)}")
            lines.append(f"  通过: {summary.get('passed_checks', 0)}")
            lines.append(f"  未通过: {summary.get('failed_checks', 0)}")
            lines.append(f"  警告数量: {summary.get('warnings_count', 0)}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
