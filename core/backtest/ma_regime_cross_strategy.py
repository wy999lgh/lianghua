#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线牛熊 + MA60 交叉策略（Backtrader 适配）
功能：以 MA200 判定牛熊为第一条件；牛市内收盘价上穿 MA60 买入、下穿 MA60 卖出；熊市强制空仓。
"""

from typing import Dict, List, Any, Optional

import backtrader as bt


class MARegimeCrossStrategy(bt.Strategy):
    params = (
        ("ma_regime_period", 200),
        ("ma_trade_period", 60),
        ("trade_size", 1),
    )

    def _calc_all_in_size(self, price: float) -> float:
        cash = float(self.broker.getcash())
        if cash <= 0 or price <= 0:
            return 0.0
        commission_rate = 0.0
        try:
            comminfo = self.broker.getcommissioninfo(self.datas[0])
            commission_rate = float(getattr(getattr(comminfo, "p", None), "commission", 0.0) or 0.0)
        except Exception:
            commission_rate = 0.0

        denom = price * (1.0 + max(0.0, commission_rate))
        if denom <= 0:
            return 0.0
        return max(0.0, cash / denom)

    def __init__(self):
        self.sma_regime = bt.indicators.SMA(self.datas[0].close, period=self.p.ma_regime_period)
        self.sma_trade = bt.indicators.SMA(self.datas[0].close, period=self.p.ma_trade_period)
        self.cross = bt.indicators.CrossOver(self.datas[0].close, self.sma_trade)

        self.order = None
        self.trade_records: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []

    def next(self):
        dt = self.datas[0].datetime.datetime()
        close = float(self.datas[0].close[0])
        sma200 = float(self.sma_regime[0])

        # 记录权益曲线（每日）
        self.equity_curve.append({
            "datetime": dt,
            "equity": float(self.broker.getvalue()),
        })

        if self.order:
            return

        # 指标未就绪
        if sma200 != sma200:
            return

        in_bull = close > sma200

        # 熊市：强制空仓
        if not in_bull:
            if self.position.size > 0:
                self.order = self.close()
                self.order.addinfo(signal="sell", reason="bear_regime_ma200", signal_dt=dt, signal_price=close)
            return

        # 牛市：MA60 上穿买，下穿卖
        if self.position.size == 0 and self.cross[0] > 0:
            size = self._calc_all_in_size(close)
            if size <= 0:
                return
            self.order = self.buy(size=size)
            self.order.addinfo(signal="buy", reason="close_cross_up_ma60", signal_dt=dt, signal_price=close)
            return

        if self.position.size > 0 and self.cross[0] < 0:
            self.order = self.close()
            self.order.addinfo(signal="sell", reason="close_cross_down_ma60", signal_dt=dt, signal_price=close)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            dt = self.datas[0].datetime.datetime()
            exec_dt = dt
            try:
                exec_dt = bt.num2date(order.executed.dt)
            except Exception:
                exec_dt = dt
            sig = order.info.get("signal") or ("buy" if order.isbuy() else "sell")
            reason = order.info.get("reason", "")
            signal_dt = order.info.get("signal_dt", "")
            signal_price = order.info.get("signal_price", "")
            size = abs(float(getattr(order.executed, "size", 0.0)))
            price = float(getattr(order.executed, "price", 0.0))
            commission = float(getattr(order.executed, "comm", 0.0))
            self.trade_records.append({
                "datetime": exec_dt,
                "signal": sig,
                "price": price,
                "amount": size,
                "position": float(self.position.size),
                "commission": commission,
                "reason": reason,
                "signal_datetime": signal_dt,
                "signal_price": signal_price,
            })
            self.order = None
            return

        if order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None

    def get_trade_records(self) -> List[Dict[str, Any]]:
        return self.trade_records

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        return self.equity_curve
