#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告导出器模块
功能：定义统一的评估指标输出格式，支持多种输出格式（JSON、CSV、Markdown）
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
import json
import csv
import pandas as pd
import io
from dataclasses import dataclass, field

from .report_generator import ReportGenerator


@dataclass
class MetricSchema:
    """
    指标输出模式定义
    """
    # 基础绩效指标
    total_return: float = 0.0
    annual_return: float = 0.0
    cumulative_return: float = 0.0
    
    # 风险指标
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    volatility: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    
    # 基准对比
    alpha: float = 0.0
    beta: float = 0.0
    tracking_error: float = 0.0
    correlation: float = 0.0
    
    # 收益分布
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # 交易统计
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_trade_pnl: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    total_commission: float = 0.0
    
    # 元数据
    strategy_name: str = ""
    symbol: str = ""
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 0.0
    final_capital: float = 0.0
    backtest_duration: int = 0
    data_points: int = 0


class ReportExporter:
    """
    报告导出器
    
    支持多种输出格式：JSON、CSV、Markdown
    """
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        初始化报告导出器
        
        参数：
        - report_generator: 报告生成器实例（可选）
        """
        self.report_generator = report_generator or ReportGenerator()
    
    def export(
        self,
        portfolio_returns: pd.Series,
        trade_records: List[Dict],
        benchmark_returns: Optional[pd.Series] = None,
        equity_curve: Optional[pd.DataFrame] = None,
        strategy_name: str = "",
        symbol: str = "",
        start_date: str = "",
        end_date: str = "",
        initial_capital: float = 100000.0,
        output_format: Literal['json', 'csv', 'markdown'] = 'json',
        file_path: Optional[str] = None
    ) -> str:
        """
        导出报告
        
        参数：
        - portfolio_returns: 组合日收益率序列
        - trade_records: 交易记录列表
        - benchmark_returns: 基准收益率序列（可选）
        - equity_curve: 权益曲线（可选）
        - strategy_name: 策略名称
        - symbol: 标的代码
        - start_date: 开始日期
        - end_date: 结束日期
        - initial_capital: 初始资金
        - output_format: 输出格式（json/csv/markdown）
        - file_path: 输出文件路径（可选，None表示返回字符串）
        
        返回：
        str - 导出的报告内容
        """
        # 生成完整报告
        report = self.report_generator.generate_report(
            portfolio_returns=portfolio_returns,
            trade_records=trade_records,
            benchmark_returns=benchmark_returns,
            equity_curve=equity_curve,
            initial_capital=initial_capital
        )
        
        # 添加元数据
        report['strategy_name'] = strategy_name
        report['symbol'] = symbol
        report['start_date'] = start_date
        report['end_date'] = end_date
        
        # 根据格式导出
        if output_format == 'json':
            content = self._export_json(report)
        elif output_format == 'csv':
            content = self._export_csv(report)
        elif output_format == 'markdown':
            content = self._export_markdown(report)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        # 如果指定了文件路径，保存到文件
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def _export_json(self, report: Dict[str, Any]) -> str:
        """
        导出为JSON格式
        
        参数：
        - report: 报告字典
        
        返回：
        str - JSON字符串
        """
        # 标准化时间格式
        if 'start_date' in report and isinstance(report['start_date'], datetime):
            report['start_date'] = report['start_date'].isoformat()
        if 'end_date' in report and isinstance(report['end_date'], datetime):
            report['end_date'] = report['end_date'].isoformat()
        
        # 处理datetime类型的交易记录
        if 'trade_records' in report:
            for record in report['trade_records']:
                if 'datetime' in record and isinstance(record['datetime'], datetime):
                    record['datetime'] = record['datetime'].isoformat()
        
        # 处理权益曲线
        if 'equity_curve' in report and isinstance(report['equity_curve'], pd.DataFrame):
            report['equity_curve'] = report['equity_curve'].to_dict('records')
        
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def _export_csv(self, report: Dict[str, Any]) -> str:
        """
        导出为CSV格式
        
        参数：
        - report: 报告字典
        
        返回：
        str - CSV字符串
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入基础信息
        writer.writerow(['策略名称', report.get('strategy_name', '')])
        writer.writerow(['标的代码', report.get('symbol', '')])
        writer.writerow(['开始日期', report.get('start_date', '')])
        writer.writerow(['结束日期', report.get('end_date', '')])
        writer.writerow(['初始资金', report.get('initial_capital', '')])
        writer.writerow(['最终资金', report.get('final_capital', '')])
        writer.writerow([])
        
        # 写入绩效指标
        writer.writerow(['绩效指标', '值'])
        if 'returns' in report:
            writer.writerow(['总收益率', report['returns'].get('total_return', '')])
            writer.writerow(['年化收益率', report['returns'].get('annual_return', '')])
        
        if 'risk' in report:
            writer.writerow(['最大回撤', report['risk'].get('max_drawdown', '')])
            writer.writerow(['年化波动率', report['risk'].get('volatility', '')])
        
        if 'risk_adjusted' in report:
            writer.writerow(['夏普比率', report['risk_adjusted'].get('sharpe_ratio', '')])
            writer.writerow(['索提诺比率', report['risk_adjusted'].get('sortino_ratio', '')])
            writer.writerow(['卡尔玛比率', report['risk_adjusted'].get('calmar_ratio', '')])
        
        if 'trade_stats' in report:
            writer.writerow(['总交易次数', report['trade_stats'].get('total_trades', '')])
            writer.writerow(['胜率', report['trade_stats'].get('win_rate', '')])
            writer.writerow(['盈利因子', report['trade_stats'].get('profit_factor', '')])
        
        writer.writerow([])
        
        # 写入交易记录
        if 'trade_records' in report and report['trade_records']:
            writer.writerow(['交易记录'])
            writer.writerow(['时间', '信号', '价格', '数量', '持仓', '手续费', '利润'])
            for record in report['trade_records']:
                writer.writerow([
                    record.get('datetime', ''),
                    record.get('signal', ''),
                    record.get('price', ''),
                    record.get('amount', ''),
                    record.get('position', ''),
                    record.get('commission', ''),
                    record.get('profit', '')
                ])
        
        return output.getvalue()
    
    def _export_markdown(self, report: Dict[str, Any]) -> str:
        """
        导出为Markdown格式
        
        参数：
        - report: 报告字典
        
        返回：
        str - Markdown字符串
        """
        sections = []
        
        # 标题
        sections.append(f"# {report.get('strategy_name', '回测报告')}")
        sections.append("")
        
        # 基本信息表格
        info_rows = [
            ("标的代码", report.get('symbol', '-')),
            ("回测周期", f"{report.get('start_date', '-')} ~ {report.get('end_date', '-')}"),
            ("初始资金", f"{report.get('initial_capital', 0):,.2f}"),
            ("最终资金", f"{report.get('final_capital', 0):,.2f}"),
            ("总收益率", f"{report.get('returns', {}).get('total_return', 0) * 100:.2f}%"),
            ("年化收益率", f"{report.get('returns', {}).get('annual_return', 0) * 100:.2f}%")
        ]
        
        sections.append("## 基本信息")
        sections.append("| 项目 | 值 |")
        sections.append("|------|-----|")
        for key, value in info_rows:
            sections.append(f"| {key} | {value} |")
        sections.append("")
        
        # 绩效指标表格
        sections.append("## 绩效指标")
        sections.append("| 指标 | 值 |")
        sections.append("|------|-----|")
        
        # 收益指标
        if 'returns' in report:
            sections.append(f"| 总收益率 | {report['returns'].get('total_return', 0) * 100:.2f}% |")
            sections.append(f"| 年化收益率 | {report['returns'].get('annual_return', 0) * 100:.2f}% |")
        
        # 风险指标
        if 'risk' in report:
            sections.append(f"| 最大回撤 | {report['risk'].get('max_drawdown', 0) * 100:.2f}% |")
            sections.append(f"| 年化波动率 | {report['risk'].get('volatility', 0) * 100:.2f}% |")
            sections.append(f"| VaR(95%) | {report['risk'].get('var_95', 0) * 100:.2f}% |")
        
        # 风险调整收益
        if 'risk_adjusted' in report:
            sections.append(f"| 夏普比率 | {report['risk_adjusted'].get('sharpe_ratio', 0):.2f} |")
            sections.append(f"| 索提诺比率 | {report['risk_adjusted'].get('sortino_ratio', 0):.2f} |")
            sections.append(f"| 卡尔玛比率 | {report['risk_adjusted'].get('calmar_ratio', 0):.2f} |")
        
        # 基准对比
        if 'benchmark' in report:
            sections.append(f"| Alpha | {report['benchmark'].get('alpha', 0):.4f} |")
            sections.append(f"| Beta | {report['benchmark'].get('beta', 0):.2f} |")
            sections.append(f"| 信息比率 | {report['benchmark'].get('information_ratio', 0):.2f} |")
        
        # 交易统计
        if 'trade_stats' in report:
            sections.append("")
            sections.append("## 交易统计")
            sections.append("| 指标 | 值 |")
            sections.append("|------|-----|")
            sections.append(f"| 总交易次数 | {report['trade_stats'].get('total_trades', 0)} |")
            sections.append(f"| 胜率 | {report['trade_stats'].get('win_rate', 0) * 100:.2f}% |")
            sections.append(f"| 盈利因子 | {report['trade_stats'].get('profit_factor', 0):.2f} |")
            sections.append(f"| 平均盈亏 | {report['trade_stats'].get('average_trade_pnl', 0):.2f} |")
            sections.append(f"| 最大连续盈利 | {report['trade_stats'].get('max_consecutive_wins', 0)} |")
            sections.append(f"| 最大连续亏损 | {report['trade_stats'].get('max_consecutive_losses', 0)} |")
            sections.append(f"| 总手续费 | {report['trade_stats'].get('total_commission', 0):.2f} |")
        
        # 交易记录
        if 'trade_records' in report and report['trade_records']:
            sections.append("")
            sections.append("## 交易记录")
            sections.append("| 时间 | 信号 | 价格 | 数量 | 持仓 | 手续费 | 利润 |")
            sections.append("|------|------|------|------|------|--------|------|")
            for record in report['trade_records'][-20:]:  # 只显示最近20条
                dt = record.get('datetime', '')
                if isinstance(dt, datetime):
                    dt = dt.strftime('%Y-%m-%d %H:%M:%S')
                sections.append(f"| {dt} | {record.get('signal', '')} | {record.get('price', 0):.2f} | {record.get('amount', 0):.0f} | {record.get('position', 0):.0f} | {record.get('commission', 0):.2f} | {record.get('profit', 0):.2f} |")
        
        return '\n'.join(sections)
    
    def export_summary(
        self,
        reports: List[Dict[str, Any]],
        output_format: Literal['json', 'csv', 'markdown'] = 'json',
        file_path: Optional[str] = None
    ) -> str:
        """
        导出多策略对比报告
        
        参数：
        - reports: 多个策略报告列表
        - output_format: 输出格式
        - file_path: 输出文件路径
        
        返回：
        str - 导出的报告内容
        """
        summary = {
            'summary': {
                'total_strategies': len(reports),
                'generated_at': datetime.now().isoformat()
            },
            'strategies': reports
        }
        
        if output_format == 'json':
            content = json.dumps(summary, ensure_ascii=False, indent=2)
        elif output_format == 'csv':
            content = self._export_summary_csv(reports)
        elif output_format == 'markdown':
            content = self._export_summary_markdown(reports)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def _export_summary_csv(self, reports: List[Dict[str, Any]]) -> str:
        """导出多策略对比为CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['策略名称', '标的', '总收益率', '年化收益率', '最大回撤', '夏普比率', '交易次数', '胜率'])
        
        for report in reports:
            writer.writerow([
                report.get('strategy_name', ''),
                report.get('symbol', ''),
                f"{report.get('returns', {}).get('total_return', 0) * 100:.2f}%",
                f"{report.get('returns', {}).get('annual_return', 0) * 100:.2f}%",
                f"{report.get('risk', {}).get('max_drawdown', 0) * 100:.2f}%",
                f"{report.get('risk_adjusted', {}).get('sharpe_ratio', 0):.2f}",
                report.get('trade_stats', {}).get('total_trades', 0),
                f"{report.get('trade_stats', {}).get('win_rate', 0) * 100:.2f}%"
            ])
        
        return output.getvalue()
    
    def _export_summary_markdown(self, reports: List[Dict[str, Any]]) -> str:
        """导出多策略对比为Markdown"""
        sections = []
        sections.append("# 策略对比报告")
        sections.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"策略数量: {len(reports)}")
        sections.append("")
        
        sections.append("## 策略对比")
        sections.append("| 策略名称 | 标的 | 总收益率 | 年化收益率 | 最大回撤 | 夏普比率 | 交易次数 | 胜率 |")
        sections.append("|----------|------|----------|------------|----------|----------|----------|------|")
        
        for report in reports:
            sections.append(f"| {report.get('strategy_name', '-')} | {report.get('symbol', '-')} | {report.get('returns', {}).get('total_return', 0) * 100:.2f}% | {report.get('returns', {}).get('annual_return', 0) * 100:.2f}% | {report.get('risk', {}).get('max_drawdown', 0) * 100:.2f}% | {report.get('risk_adjusted', {}).get('sharpe_ratio', 0):.2f} | {report.get('trade_stats', {}).get('total_trades', 0)} | {report.get('trade_stats', {}).get('win_rate', 0) * 100:.2f}% |")
        
        return '\n'.join(sections)


def get_report_exporter() -> ReportExporter:
    """
    获取全局报告导出器实例（单例）
    
    返回：
    ReportExporter - 报告导出器实例
    """
    global _report_exporter
    if _report_exporter is None:
        _report_exporter = ReportExporter()
    return _report_exporter


# 全局单例
_report_exporter = None
