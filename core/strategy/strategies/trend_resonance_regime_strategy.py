#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三指标共振趋势/震荡判读策略
功能：使用 RM + CMO + BB 对市场状态进行趋势与震荡判读
"""

from datetime import datetime as dt
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

from core.analysis import FactorLibrary
from core.strategy.base_strategy import BaseStrategy


class TrendResonanceRegimeStrategy(BaseStrategy):
    """
    三指标共振判读策略

    判读输出：
    - trend_up: 上行趋势
    - trend_down: 下行趋势
    - range: 震荡
    - neutral: 过渡态（样本不足或信号不一致）
    """

    PARAM_DESCRIPTIONS = {
        'beta_window': {'name': 'Beta计算窗口', 'desc': '残差动量Beta系数的计算窗口大小，默认60'},
        'rm_z_window': {'name': 'RM标准化窗口', 'desc': '残差动量Z-score标准化的滚动窗口，默认60'},
        'rm_slope_window': {'name': 'RM斜率窗口', 'desc': '残差动量斜率计算窗口，默认10'},
        'cmo_period': {'name': 'CMO周期', 'desc': '钱德动量振荡器的计算周期，默认20'},
        'bb_period': {'name': '布林带周期', 'desc': '布林带的计算周期，默认20'},
        'bb_std_mult': {'name': '布林带标准差倍数', 'desc': '布林带上下轨距离中轨的标准差倍数，默认2.0'},
        'bb_width_pct_window': {'name': '带宽分位窗口', 'desc': '布林带带宽百分位的滚动计算窗口，默认60'},
        'bb_breakout_pct': {'name': '突破带宽分位', 'desc': '带宽分位超过该值才认为扩张突破有效，默认0.20'},
        'bb_squeeze_pct': {'name': '收敛带宽分位', 'desc': '带宽分位低于该阈值视作收敛（震荡候选），默认0.20'},
        'rm_range_abs': {'name': 'RM震荡阈值', 'desc': '|RM_Z|低于该阈值视作震荡候选，默认0.50'},
        'cmo_range_abs': {'name': 'CMO震荡阈值', 'desc': '|CMO|低于该阈值视作震荡候选，默认15.0'},
        'vote_threshold': {'name': '投票阈值', 'desc': '三指标投票通过的最低票数，2/3投票设置为2'},
        'max_buffer': {'name': '最大缓冲区', 'desc': '保留的历史价格最大数量，默认500'}
    }

    DEFAULT_CONFIG = {
        # 残差动量 RM 参数
        "beta_window": 60,
        "rm_z_window": 60,
        "rm_slope_window": 10,
        # CMO 参数
        "cmo_period": 20,
        # BB 参数
        "bb_period": 20,
        "bb_std_mult": 2.0,
        "bb_width_pct_window": 60,
        # 判读阈值
        "bb_breakout_pct": 0.20,      # 带宽分位超过该值才认为扩张突破有效
        "bb_squeeze_pct": 0.20,       # 带宽分位低于该值视作收敛（震荡候选）
        "rm_range_abs": 0.50,         # |RM_Z| 低于该阈值视作震荡候选
        "cmo_range_abs": 15.0,        # |CMO| 低于该阈值视作震荡候选
        # 共振规则
        "vote_threshold": 2,          # 2/3 投票
        # 缓冲区长度（保留更多历史便于稳定计算）
        "max_buffer": 500,
    }

    def __init__(self, name: str = "trend_resonance_regime", description: str = ""):
        if not description:
            description = "基于 RM+CMO+BB 的趋势/震荡判读策略（2/3 共振）"
        if name == "temp":
            name = "trend_resonance_regime"
        super().__init__(name=name, description=description)

        self.config = self.DEFAULT_CONFIG.copy()
        self.close_buffer: List[float] = []
        self.benchmark_close_buffer: List[float] = []
        self.time_buffer: List[dt] = []
        self.last_benchmark_price: Optional[float] = None
        self.last_regime: str = "neutral"

    def set_benchmark_price(self, benchmark_price: float) -> None:
        """
        更新最新基准价格（用于仅调用 update_price 的场景）
        """
        self.last_benchmark_price = float(benchmark_price)

    def update_with_market(
        self,
        price: float,
        benchmark_price: float,
        timestamp: Optional[dt] = None
    ) -> Dict[str, Any]:
        """
        使用标的价格 + 基准价格进行一次完整判读
        """
        self.last_benchmark_price = float(benchmark_price)
        return self._update_internal(
            price=float(price),
            benchmark_price=float(benchmark_price),
            ts=timestamp or dt.now(),
        )

    def update_price(self, price: float, datetime: Optional[dt] = None) -> Dict[str, Any]:
        """
        兼容基类接口：若未同时提供基准价，则使用最近一次 set_benchmark_price 的值
        """
        ts = datetime or dt.now()
        benchmark_price = self.last_benchmark_price
        if benchmark_price is None:
            return {
                "signal": "neutral",
                "regime": "neutral",
                "reason": "缺少基准价格，请先调用 set_benchmark_price 或 update_with_market",
                "timestamp": ts,
            }
        return self._update_internal(price=float(price), benchmark_price=float(benchmark_price), ts=ts)

    def _update_internal(self, price: float, benchmark_price: float, ts: dt) -> Dict[str, Any]:
        self.close_buffer.append(price)
        self.benchmark_close_buffer.append(benchmark_price)
        self.time_buffer.append(ts)
        self._trim_buffers()

        min_required = max(
            self.config["beta_window"],
            self.config["rm_z_window"],
            self.config["cmo_period"],
            self.config["bb_period"],
            self.config["bb_width_pct_window"],
        ) + 1
        if len(self.close_buffer) < min_required:
            self.last_regime = "neutral"
            return {
                "signal": "neutral",
                "regime": "neutral",
                "reason": f"样本不足，当前 {len(self.close_buffer)}，至少需要 {min_required}",
                "timestamp": ts,
            }

        indicators = self._calculate_indicators()
        regime_result = self._judge_regime(indicators)
        result = {
            "signal": regime_result["regime"],
            "regime": regime_result["regime"],
            "votes": regime_result["votes"],
            "indicators": indicators,
            "timestamp": ts,
        }
        self.last_regime = regime_result["regime"]
        return result

    def _trim_buffers(self) -> None:
        max_buffer = int(self.config.get("max_buffer", 500))
        if len(self.close_buffer) > max_buffer:
            self.close_buffer = self.close_buffer[-max_buffer:]
            self.benchmark_close_buffer = self.benchmark_close_buffer[-max_buffer:]
            self.time_buffer = self.time_buffer[-max_buffer:]

    def _calculate_indicators(self) -> Dict[str, float]:
        close = pd.Series(self.close_buffer, dtype=float)
        benchmark_close = pd.Series(self.benchmark_close_buffer, dtype=float)

        # 收益率序列
        y_ret = close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
        x_ret = benchmark_close.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)

        # RM 相关
        rm = FactorLibrary.residual_momentum(
            y_ret=y_ret,
            x_ret=x_ret,
            beta_window=int(self.config["beta_window"]),
        )
        rm_z = FactorLibrary.rolling_zscore(
            rm,
            window=int(self.config["rm_z_window"]),
        )
        rm_slope = FactorLibrary.rolling_slope(
            rm,
            window=int(self.config["rm_slope_window"]),
        )

        # CMO
        cmo = FactorLibrary.cmo(
            close,
            period=int(self.config["cmo_period"]),
        )

        # BB 相关
        bb = FactorLibrary.bollinger_bands_ema(
            close,
            period=int(self.config["bb_period"]),
            std_mult=float(self.config["bb_std_mult"]),
        )
        bb_width_pct = FactorLibrary.rolling_percentile_rank(
            bb["bb_width"],
            window=int(self.config["bb_width_pct_window"]),
        )
        bb_slope = FactorLibrary.rolling_slope(
            bb["bb_mid"],
            window=int(self.config["rm_slope_window"]),
        )

        last = {
            "close": float(close.iloc[-1]),
            "benchmark_close": float(benchmark_close.iloc[-1]),
            "rm": float(rm.iloc[-1]),
            "rm_z": float(rm_z.iloc[-1]),
            "rm_slope": float(rm_slope.iloc[-1]),
            "cmo": float(cmo.iloc[-1]),
            "bb_mid": float(bb["bb_mid"].iloc[-1]),
            "bb_upper": float(bb["bb_upper"].iloc[-1]),
            "bb_lower": float(bb["bb_lower"].iloc[-1]),
            "bb_width": float(bb["bb_width"].iloc[-1]),
            "bb_pos": float(bb["bb_pos"].iloc[-1]),
            "bb_width_pct": float(bb_width_pct.iloc[-1]),
            "bb_slope": float(bb_slope.iloc[-1]),
        }
        return last

    def _judge_regime(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        close = indicators["close"]
        rm_z = indicators["rm_z"]
        cmo = indicators["cmo"]
        bb_upper = indicators["bb_upper"]
        bb_lower = indicators["bb_lower"]
        bb_width_pct = indicators["bb_width_pct"]

        # 指标投票
        rm_signal = 1 if rm_z > 0 else (-1 if rm_z < 0 else 0)
        cmo_signal = 1 if cmo > 0 else (-1 if cmo < 0 else 0)

        bb_breakout_pct = float(self.config["bb_breakout_pct"])
        bb_signal = 0
        if close > bb_upper and bb_width_pct >= bb_breakout_pct:
            bb_signal = 1
        elif close < bb_lower and bb_width_pct >= bb_breakout_pct:
            bb_signal = -1

        up_votes = int(rm_signal == 1) + int(cmo_signal == 1) + int(bb_signal == 1)
        down_votes = int(rm_signal == -1) + int(cmo_signal == -1) + int(bb_signal == -1)
        threshold = int(self.config["vote_threshold"])

        if up_votes >= threshold:
            regime = "trend_up"
        elif down_votes >= threshold:
            regime = "trend_down"
        else:
            # 震荡判读：带宽收敛 + 动量弱
            is_squeeze = bb_width_pct < float(self.config["bb_squeeze_pct"])
            rm_weak = abs(rm_z) < float(self.config["rm_range_abs"])
            cmo_weak = abs(cmo) < float(self.config["cmo_range_abs"])
            regime = "range" if (is_squeeze and rm_weak and cmo_weak) else "neutral"

        return {
            "regime": regime,
            "votes": {
                "rm_signal": rm_signal,
                "cmo_signal": cmo_signal,
                "bb_signal": bb_signal,
                "up_votes": up_votes,
                "down_votes": down_votes,
            },
        }

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def set_config(self, config: Dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("config 必须是 dict")
        self.config.update(config)

    def get_latest_regime(self) -> str:
        """
        获取最近一次判读结果
        """
        return self.last_regime

    def reset(self) -> None:
        super().reset()
        self.close_buffer = []
        self.benchmark_close_buffer = []
        self.time_buffer = []
        self.last_benchmark_price = None
        self.last_regime = "neutral"
