# -*- coding: utf-8 -*-
"""
回测报告 - Markdown 渲染与写入
功能：将 ReportGenerator.generate_report 的结果渲染为 Markdown 文件并保存到磁盘
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import os


def render_backtest_report_markdown(
    symbol: str,
    strategy_name: str,
    params: Dict[str, Any],
    report: Dict[str, Any],
    trade_records: Optional[List[Dict[str, Any]]] = None,
    equity_curve: Optional[List[Dict[str, Any]]] = None
) -> str:
    param_name_map = {
        "ma_regime_period": "牛熊均线周期(MA200)",
        "ma_trade_period": "交易均线周期(MA60)",
        "trade_size": "每次交易数量",
        "commission_rate": "手续费率",
        "initial_cash": "初始资金",
        "start_date": "开始日期",
        "end_date": "结束日期",
    }

    metric_name_map = {
        "total_return": "总收益率",
        "annual_return": "年化收益率",
        "sharpe_ratio": "夏普比率",
        "sortino_ratio": "索提诺比率",
        "max_drawdown": "最大回撤",
        "calmar_ratio": "卡尔玛比率",
        "volatility": "波动率",
        "trade_count": "交易次数",
        "win_rate": "胜率",
        "profit_factor": "盈利因子",
        "profit_loss_ratio": "盈亏比",
        "total_commission": "总手续费",
        "initial_capital": "初始资金",
        "final_capital": "期末资金",
        "total_profit": "总盈亏",
        "start_date": "回测开始",
        "end_date": "回测结束",
        "trading_days": "交易日数",
    }

    signal_map = {
        "buy": "买入",
        "sell": "卖出",
        "hold": "观望",
    }

    reason_map = {
        "bear_regime_ma200": "熊市(跌破MA200)强制平仓",
        "close_cross_up_ma60": "收盘价上穿MA60买入",
        "close_cross_down_ma60": "收盘价下穿MA60卖出",
    }

    percent_keys = {
        "total_return",
        "annual_return",
        "max_drawdown",
        "volatility",
        "win_rate",
    }
    ratio_keys = {
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "profit_factor",
        "profit_loss_ratio",
    }
    money_keys = {
        "total_commission",
        "initial_capital",
        "final_capital",
        "total_profit",
    }
    int_keys = {
        "trade_count",
        "trading_days",
    }

    def _format_metric(key: str, value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, (int, float)):
            if key in int_keys:
                return str(int(value))
            if key in percent_keys:
                return f"{float(value) * 100:.2f}%"
            if key in ratio_keys:
                return f"{float(value):.2f}"
            if key in money_keys:
                return f"{float(value):.2f}"
            return f"{float(value):.2f}"
        return str(value).replace(" 00:00:00", "")

    def _to_dt_str(v: Any) -> str:
        if not v:
            return ""
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S").replace(" 00:00:00", "")
        return str(v).replace(" 00:00:00", "")

    def _extract_trade_pairs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not records:
            return []
        ordered = []
        for r in records:
            dtv = r.get("datetime") or r.get("dt") or r.get("time")
            ordered.append((str(dtv), r))
        ordered.sort(key=lambda x: x[0])

        buys: List[Dict[str, Any]] = []
        pairs: List[Dict[str, Any]] = []
        for _, r in ordered:
            sig = str(r.get("signal", "")).lower()
            if sig == "buy":
                buys.append(r)
                continue
            if sig != "sell" or not buys:
                continue
            b = buys.pop(0)

            buy_price = float(b.get("price", 0.0) or 0.0)
            sell_price = float(r.get("price", 0.0) or 0.0)
            qty = float(
                min(
                    float(b.get("amount", b.get("quantity", 0.0)) or 0.0),
                    float(r.get("amount", r.get("quantity", 0.0)) or 0.0),
                )
            )
            buy_comm = float(b.get("commission", 0.0) or 0.0)
            sell_comm = float(r.get("commission", 0.0) or 0.0)
            profit = (sell_price - buy_price) * qty - buy_comm - sell_comm
            cost = buy_price * qty + buy_comm
            profit_pct = (profit / cost) if cost > 0 else 0.0

            pairs.append({
                "buy_time": b.get("signal_datetime") or b.get("datetime") or "",
                "sell_time": r.get("signal_datetime") or r.get("datetime") or "",
                "buy_price": buy_price,
                "sell_price": sell_price,
                "qty": qty,
                "profit": profit,
                "profit_pct": profit_pct,
            })
        return pairs

    def _extract_drawdown_periods(records: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if not records:
            return []
        points = []
        for r in records:
            dtv = r.get("datetime")
            eqv = r.get("equity")
            if dtv is None or eqv is None:
                continue
            try:
                eq = float(eqv)
            except Exception:
                continue
            points.append((str(dtv), dtv, eq))
        points.sort(key=lambda x: x[0])
        if not points:
            return []

        peak_dt = points[0][1]
        peak_eq = points[0][2]
        trough_dt = peak_dt
        min_dd = 0.0
        in_dd = False
        periods: List[Dict[str, Any]] = []

        for _, dtv, eq in points[1:]:
            if eq >= peak_eq:
                if in_dd and min_dd < 0:
                    periods.append({
                        "start": peak_dt,
                        "end": trough_dt,
                        "drawdown": min_dd,
                    })
                peak_dt = dtv
                peak_eq = eq
                trough_dt = dtv
                min_dd = 0.0
                in_dd = False
                continue

            dd = (eq / peak_eq) - 1.0 if peak_eq > 0 else 0.0
            if dd < 0:
                in_dd = True
            if dd < min_dd:
                min_dd = dd
                trough_dt = dtv

        if in_dd and min_dd < 0:
            periods.append({
                "start": peak_dt,
                "end": trough_dt,
                "drawdown": min_dd,
            })

        periods.sort(key=lambda x: x["drawdown"])
        return periods

    lines: List[str] = []
    lines.append(f"# 回测报告：{symbol}")
    lines.append("")
    lines.append(f"- 策略：{strategy_name}")
    lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("## 策略参数")
    for k, v in (params or {}).items():
        display_name = param_name_map.get(str(k), str(k))
        lines.append(f"- {display_name}：{v}")
    lines.append("")

    lines.append("## 核心指标")
    key_order = [
        "total_return",
        "annual_return",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
        "calmar_ratio",
        "volatility",
        "trade_count",
        "win_rate",
        "profit_factor",
        "profit_loss_ratio",
        "total_commission",
        "initial_capital",
        "final_capital",
        "total_profit",
        "start_date",
        "end_date",
        "trading_days",
    ]
    for k in key_order:
        if k in report:
            display_name = metric_name_map.get(k, k)
            lines.append(f"- {display_name}：{_format_metric(k, report.get(k))}")
    lines.append("")

    if trade_records:
        trade_pairs = _extract_trade_pairs(trade_records)
        if trade_pairs:
            all_pairs = sorted(trade_pairs, key=lambda x: x["buy_time"])
            lines.append(f"## 每次买卖盈亏时间段（共 {len(all_pairs)} 次）")
            lines.append("| 买入时间 | 买入价 | 卖出时间 | 卖出价 | 数量 | 盈亏 | 盈亏率 |")
            lines.append("|---|---:|---|---:|---:|---:|---:|")
            for p in all_pairs:
                lines.append(
                    f"| {_to_dt_str(p.get('buy_time'))} | {p.get('buy_price')} | {_to_dt_str(p.get('sell_time'))} | {p.get('sell_price')} | {p.get('qty')} | {p.get('profit'):.2f} | {_format_metric('total_return', p.get('profit_pct'))} |"
                )
            lines.append("")

    dd_periods = _extract_drawdown_periods(equity_curve)
    if dd_periods:
        top_dd = dd_periods[:5]
        lines.append("## 前5个最大回撤时间段")
        lines.append("| 回撤开始(峰值) | 回撤结束(谷值) | 回撤幅度 |")
        lines.append("|---|---|---:|")
        for d in top_dd:
            lines.append(
                f"| {_to_dt_str(d.get('start'))} | {_to_dt_str(d.get('end'))} | {_format_metric('max_drawdown', d.get('drawdown'))} |"
            )
        lines.append("")

    if trade_records:
        lines.append(f"## 全部交易记录（共 {len(trade_records)} 条）")
        lines.append("| 信号时间 | 信号价 | 成交时间 | 动作 | 成交价 | 数量 | 原因 |")
        lines.append("|---|---:|---|---|---:|---:|---|")
        for t in trade_records:
            dt_val = _to_dt_str(t.get("datetime", ""))
            sig_dt = _to_dt_str(t.get("signal_datetime", ""))
            sig_price = t.get("signal_price", "")
            sig_val = t.get("signal", "")
            price = t.get("price", "")
            amt = t.get("amount", t.get("quantity", ""))
            reason = t.get("reason", "")
            sig_cn = signal_map.get(str(sig_val), str(sig_val))
            reason_cn = reason_map.get(str(reason), str(reason))
            lines.append(f"| {sig_dt} | {sig_price} | {dt_val} | {sig_cn} | {price} | {amt} | {reason_cn} |")
        lines.append("")

    bias = report.get("bias_check")
    if isinstance(bias, dict) and bias:
        lines.append("## 偏差检查")
        lines.append(f"- 是否通过：{bias.get('passed')}")
        summary = bias.get("summary")
        if isinstance(summary, dict):
            lines.append(f"- 检查项总数：{summary.get('total_checks')}")
            lines.append(f"- 通过项：{summary.get('passed_checks')}")
            lines.append(f"- 未通过项：{summary.get('failed_checks')}")
            lines.append(f"- 警告数量：{summary.get('warnings_count')}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_backtest_report_markdown(
    output_path: str,
    content: str
) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path
