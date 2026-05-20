"""数据管理相关路由

此模块包含数据获取、查询和统计相关的API端点。
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import pandas as pd
import numpy as np
import datetime as dt
import re

from core.cache import get_cached, set_cache, invalidate_cache

logger = logging.getLogger(__name__)

from api.schemas import (
    DataFetchRequest,
    DataFetchResponse,
    StockDataItem,
    StockDataResponse,
    EMADataItem,
    EMADataResponse,
    SymbolInfo,
    SymbolListResponse,
)
from core.data import DataFetcher, DataCleaner
from core.data.database import Database, get_db
from core.data.legacy_loader import DataLoader
from core.analysis import FactorLibrary
from config import get_database_config

# 创建路由器实例
router = APIRouter()


def _linear_regression_slope_r2(values: list[float]) -> tuple[float, float]:
    y = np.asarray(values, dtype=float)
    n = int(y.size)
    if n <= 1:
        return 0.0, 0.0

    x = np.arange(n, dtype=float)
    x_mean = float(x.mean())
    y_mean = float(y.mean())
    denom = float(((x - x_mean) ** 2).sum())
    if denom == 0.0:
        return 0.0, 0.0

    slope = float(((x - x_mean) * (y - y_mean)).sum() / denom)
    intercept = y_mean - slope * x_mean
    y_pred = intercept + slope * x
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y_mean) ** 2).sum())
    r2 = 0.0 if ss_tot == 0.0 else float(1.0 - ss_res / ss_tot)
    return slope, r2


def _ma_reg_slope(ma_values: list[float], window: int = 10) -> float:
    """
    计算均线线性回归斜率（更平滑的趋势判断）
    
    Args:
        ma_values: 均线值列表
        window: 用于计算回归的窗口大小，默认10
    
    Returns:
        float: 线性回归斜率，正数表示上升，负数表示下降；
               当数据不足时返回 None
    """
    if len(ma_values) < window:
        return None  # 返回 None 表示数据不足
    
    y = np.array(ma_values[-window:], dtype=float)
    x = np.arange(window, dtype=float)
    return np.polyfit(x, y, 1)[0]


def _classify_ema_trend_directions(ema_values: list[float], period: int, slope_window: int = 10, threshold_ratio: float = 0.001) -> list[str]:
    """
    EMA 趋势方向判断（回归斜率 + 阈值过滤 + 颜色区分）
    
    通过对最近 N 个 EMA 值进行线性回归，根据回归斜率判断均线方向。
    使用阈值过滤可以避免微小波动导致颜色频繁变化，使趋势判断更稳定。
    
    场景说明：
    1. 回归斜率：使用线性回归计算最近N个EMA值的斜率
    2. 阈值过滤：只有当斜率超过一定阈值时才认为趋势发生变化
    3. 颜色区分：根据方向返回不同颜色（红/绿/灰）
    
    Args:
        ema_values: EMA 值列表
        period: EMA 周期（用于计算阈值基准）
        slope_window: 线性回归窗口大小，默认10
        threshold_ratio: 阈值比例，默认0.001（0.1%），用于过滤微小波动
    
    Returns:
        list[str]: 方向序列，包含 'up' / 'down' / 'flat'
    
    Direction Rules:
        - up: 线性回归斜率 > 阈值，表示均线向上趋势
        - down: 线性回归斜率 < -阈值，表示均线向下趋势
        - flat: 斜率在阈值范围内，表示均线走平或横盘
    """
    if not ema_values:
        return []

    directions = []
    
    # 计算动态阈值：基于EMA平均值的一定比例
    # 这样阈值会根据价格水平自适应
    ema_mean = np.mean([v for v in ema_values if v > 0]) if ema_values else 1.0
    threshold = ema_mean * threshold_ratio * (period / 20)  # 周期调整因子
    
    for i in range(len(ema_values)):
        # 滑动窗口：只取最近 slope_window 个点，O(1) 而非 O(n)
        start = max(0, i - slope_window + 1)
        current_window = ema_values[start:i+1]
        slope = _ma_reg_slope(current_window, window=slope_window)
        
        if slope is not None:
            # 数据足够，使用线性回归斜率判断（带阈值过滤）
            if slope > threshold:
                directions.append("up")
            elif slope < -threshold:
                directions.append("down")
            else:
                directions.append("flat")
        else:
            # 数据不足，回退到相邻值比较方法（也应用阈值）
            if i == 0:
                directions.append("flat")
            else:
                current = ema_values[i]
                previous = ema_values[i-1]
                diff = current - previous
                if diff > threshold:
                    directions.append("up")
                elif diff < -threshold:
                    directions.append("down")
                else:
                    directions.append("flat")

    return directions


def _simple_direction_classify(ema_values: list[float]) -> list[str]:
    """
    简单方向判断（不使用斜率过滤）
    
    通过直接比较相邻EMA值来判断方向，不使用线性回归。
    适用于不需要平滑趋势判断的场景。
    
    Args:
        ema_values: EMA 值列表
    
    Returns:
        list[str]: 方向序列，包含 'up' / 'down' / 'flat'
    """
    if not ema_values:
        return []

    directions = []
    
    for i in range(len(ema_values)):
        if i == 0:
            directions.append("flat")
        else:
            current = ema_values[i]
            previous = ema_values[i-1]
            if current > previous:
                directions.append("up")
            elif current < previous:
                directions.append("down")
            else:
                directions.append("flat")

    return directions


def _to_date_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (dt.date, dt.datetime)):
        return v.date().isoformat() if isinstance(v, dt.datetime) else v.isoformat()
    s = str(v)
    return s.replace(" 00:00:00", "")


def get_table_name_from_symbol(symbol: str) -> str:
    """根据股票代码获取对应的表名称"""
    return get_table_name_candidates(symbol)[0]


def get_table_name_candidates(symbol: str) -> list[str]:
    """根据输入代码生成可能的行情表名候选列表（优先匹配 *_daily_* 命名）"""
    s = str(symbol or "").strip()
    if not s:
        return []

    candidates: list[str] = []

    def _add(name: str) -> None:
        if name and name not in candidates:
            candidates.append(name)

    if s.startswith(("stock_daily_", "etf_daily_", "index_daily_")):
        _add(s)
        return candidates

    if s.startswith(("stock_", "etf_", "index_")):
        prefix, code = s.split("_", 1)
        _add(f"{prefix}_daily_{code}")
        _add(s)
        return candidates

    if s.startswith(("sh", "sz")) and len(s) >= 8:
        code = s[2:]
        _add(f"index_daily_{code}")
        _add(f"index_{code}")
        _add(f"stock_daily_{code}")
        _add(f"etf_daily_{code}")
        return candidates

    if len(s) == 6 and s.isdigit():
        if s.startswith(("5", "1")):
            _add(f"etf_daily_{s}")
            _add(f"etf_{s}")
        if s.startswith(("9", "0", "3")):
            _add(f"index_daily_{s}")
            _add(f"index_{s}")
        _add(f"stock_daily_{s}")
        _add(f"stock_{s}")
        return candidates

    _add(f"stock_daily_{s}")
    _add(f"stock_{s}")
    _add(f"etf_daily_{s}")
    _add(f"etf_{s}")
    _add(f"index_daily_{s}")
    _add(f"index_{s}")
    return candidates


def get_db_path() -> str:
    """获取数据库连接信息 (已弃用，返回固定占位符)"""
    return "postgres"


@router.post("/fetch", summary="获取股票历史数据")
async def fetch_data(request: DataFetchRequest):
    """
    手动获取股票/ETF 历史行情数据并存入数据库
    """
    try:
        # 初始化数据获取器
        fetcher = DataFetcher()

        # 调用获取和保存逻辑
        fetcher.update_stock(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            adjust=request.adjust,
            period=request.period
        )

        return {
            "status": "success",
            "message": f"Successfully fetched and saved data for {request.symbol}",
            "symbol": request.symbol,
        }
    except Exception as e:
        logger.error(f"Error fetching data for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/symbols")
def get_available_symbols():
    """获取数据库中可用的标的代码列表（来源：动态行情分表）"""
    try:
        db = get_db()
        tables = db.list_tables()
        symbols: set[str] = set()

        for t in tables:
            m = re.match(r"^(stock_daily|etf_daily|index_daily)_(\d{6})$", t)
            if m:
                symbols.add(m.group(2))
                continue
            m2 = re.match(r"^(stock|etf|index)_(\d{6})$", t)
            if m2:
                symbols.add(m2.group(2))

        return {"symbols": sorted(symbols)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用标的失败: {str(e)}")


@router.get("/data/symbols/list")
def get_symbol_detail_list(
    type: Optional[str] = Query(default=None, description="标的类型筛选 (stock/etf/index)，多个用逗号分隔"),
    keyword: Optional[str] = Query(default=None, description="搜索关键词（按代码/名称模糊匹配）"),
    limit: int = Query(default=200, ge=1, le=2000, description="返回条数"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    sync_if_empty: bool = Query(default=True, description="若 instrument_basic 为空则自动同步一次（仅同步本库已有行情表的代码）"),
):
    """获取标的详细信息列表（类型、代码、名称）"""
    try:
        db = get_db()

        types: list[str] = []
        if type:
            types = [t.strip() for t in str(type).split(",") if t.strip()]

        items = db.list_instrument_basic(instrument_types=types, keyword=keyword, limit=limit, offset=offset)
        if items or not sync_if_empty:
            return {"status": "success", "data": items}

        _sync_instrument_basic_from_db_tables(db, types)
        items = db.list_instrument_basic(instrument_types=types, keyword=keyword, limit=limit, offset=offset)
        return {"status": "success", "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取标的详细信息列表失败: {str(e)}")


@router.post("/data/symbols/sync")
def sync_symbol_detail_list(
    type: Optional[str] = Query(default=None, description="同步类型 (stock/etf/index)，多个用逗号分隔；为空表示全部"),
):
    """同步标的基础信息到 instrument_basic（来源：AkShare + 本库已有行情分表代码）"""
    try:
        db = get_db()
        types: list[str] = []
        if type:
            types = [t.strip() for t in str(type).split(",") if t.strip()]

        written = _sync_instrument_basic_from_db_tables(db, types)
        return {"status": "success", "written": int(written)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步标的基础信息失败: {str(e)}")


def _sync_instrument_basic_from_db_tables(db: Database, types: list[str]) -> int:
    allowed = {"stock", "etf", "index"}
    wanted = [t for t in (types or list(allowed)) if t in allowed]
    tables = db.list_tables()

    codes_by_type: dict[str, set[str]] = {"stock": set(), "etf": set(), "index": set()}
    for tname in tables:
        m = re.match(r"^(stock_daily|etf_daily|index_daily)_(\d{6})$", tname)
        if m:
            prefix = m.group(1)
            code = m.group(2)
            if prefix.startswith("stock"):
                codes_by_type["stock"].add(code)
            elif prefix.startswith("etf"):
                codes_by_type["etf"].add(code)
            elif prefix.startswith("index"):
                codes_by_type["index"].add(code)
            continue

        m2 = re.match(r"^(stock|etf|index)_(\d{6})$", tname)
        if m2:
            prefix = m2.group(1)
            code = m2.group(2)
            codes_by_type[prefix].add(code)

    items: list[dict] = []
    seen: set[tuple[str, str]] = set()

    if "stock" in wanted and codes_by_type["stock"]:
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            col_code = "code" if "code" in df.columns else ("代码" if "代码" in df.columns else None)
            col_name = "name" if "name" in df.columns else ("名称" if "名称" in df.columns else None)
            if col_code and col_name:
                df = df[[col_code, col_name]].copy()
                df[col_code] = df[col_code].astype(str).str.zfill(6)
                df = df[df[col_code].isin(codes_by_type["stock"])]
                for _, r in df.iterrows():
                    items.append(
                        {
                            "type": "stock",
                            "code": str(r[col_code]),
                            "name": str(r[col_name] or "").strip(),
                            "market": "CN",
                            "source": "akshare",
                        }
                    )
                    seen.add(("stock", str(r[col_code])))
        except Exception:
            pass

    if "etf" in wanted and codes_by_type["etf"]:
        try:
            import akshare as ak
            df = ak.fund_etf_spot_em()
            # 打印列名以便调试
            print(f"[DEBUG] ETF columns: {df.columns.tolist()}")
            col_code = "代码" if "代码" in df.columns else ("code" if "code" in df.columns else None)
            col_name = "名称" if "名称" in df.columns else ("name" if "name" in df.columns else None)
            if col_code and col_name:
                df = df[[col_code, col_name]].copy()
                df[col_code] = df[col_code].astype(str).str.zfill(6)
                df = df[df[col_code].isin(codes_by_type["etf"])]
                for _, r in df.iterrows():
                    name_val = str(r[col_name] or "").strip()
                    items.append(
                        {
                            "type": "etf",
                            "code": str(r[col_code]),
                            "name": name_val if name_val else str(r[col_code]),
                            "market": "CN",
                            "source": "akshare",
                        }
                    )
                    seen.add(("etf", str(r[col_code])))
        except Exception as e:
            print(f"[ERROR] Failed to fetch ETF names: {e}")
            pass

    if "index" in wanted and codes_by_type["index"]:
        conn = db._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema='public' AND table_name='index_basic'
                )
                """
            )
            exists = bool(cur.fetchone()[0])
            if exists:
                cur.execute("SELECT index_code, index_name FROM index_basic")
                rows = cur.fetchall()
                for code, name in rows:
                    scode = str(code).strip()
                    if scode.startswith(("sh", "sz")) and len(scode) >= 8:
                        scode = scode[2:]
                    scode = scode.zfill(6)
                    if scode in codes_by_type["index"]:
                        items.append(
                            {
                                "type": "index",
                                "code": scode,
                                "name": str(name or "").strip(),
                                "market": "CN",
                                "source": "index_basic",
                            }
                        )
                        seen.add(("index", scode))
        finally:
            db._release_connection(conn)

    for t in wanted:
        for code in sorted(codes_by_type.get(t, set())):
            key = (t, code)
            if key in seen:
                continue
            items.append(
                {
                    "type": t,
                    "code": code,
                    "name": code,
                    "market": "CN",
                    "source": "table_name",
                }
            )

    return db.upsert_instrument_basic(items)

@router.get("/data/history/{symbol:path}")
def get_historical_data(symbol: str):
    """获取历史数据"""
    try:
        candidates = get_table_name_candidates(symbol)
        db = get_db()
        df_all = pd.DataFrame()
        
        for cand in candidates:
            df = db.get_data(table_name=cand, order_by="ASC")
            if not df.empty:
                df_all = df
                break
        
        if df_all.empty:
            tried = ", ".join(candidates) if candidates else "(无)"
            raise HTTPException(status_code=404, detail=f"数据表不存在或无数据，已尝试: {tried}")

        # 确定日期列名（兼容 date 和 trade_date）
        date_col = 'date' if 'date' in df_all.columns else 'trade_date'

        # 转换为前端可用的格式
        data = []
        for _, row in df_all.iterrows():
            date_val = _to_date_str(row.get(date_col))
            data.append({
                "date": date_val,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0)) if pd.notna(row.get('volume')) else 0
            })

        return {
            "symbol": symbol,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


@router.get("/stock-data", response_model=StockDataResponse)
def get_stock_data(
    symbol: str = Query(default="159633", description="股票代码"),
    start_date: Optional[str] = Query(
        default=None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(
        default=None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(default=100, le=1000, description="返回数据条数"),
    offset: int = Query(default=0, description="偏移量")
):
    """获取标准化股票数据（优化版 - 数据库层面LIMIT/OFFSET + Redis缓存）"""
    # 尝试从缓存读取
    cached_result = get_cached(
        "stock_data",
        symbol=symbol, start_date=start_date, end_date=end_date,
        limit=limit, offset=offset,
    )
    if cached_result is not None:
        return StockDataResponse(**cached_result)

    try:
        candidates = get_table_name_candidates(symbol)
        db = get_db()
        df_all = pd.DataFrame()
        used_table = ""
        for cand in candidates:
            # 优化：在数据库层面LIMIT，避免全表查询
            # 先查询总条数（用于分页）
            df_count = db.get_data(table_name=cand, start_date=start_date, end_date=end_date, limit=1)
            if not df_count.empty:
                used_table = cand
                # 优化：直接在数据库层面排序和LIMIT
                df_all = db.get_data(
                    table_name=cand, 
                    start_date=start_date, 
                    end_date=end_date,
                    limit=limit,
                    offset=offset,
                    order_by="DESC"  # 最新数据在前
                )
                break
        
        if df_all.empty:
            tried = ", ".join(candidates) if candidates else "(无)"
            raise HTTPException(status_code=404, detail=f"数据表不存在或无数据，已尝试: {tried}")

        # 转换为Pydantic模型列表
        stock_data_items = []
        for _, row in df_all.iterrows():
            item = StockDataItem(
                id=int(row['id']) if pd.notna(row.get('id')) else 0,
                date=_to_date_str(row.get('date')),
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                volume=int(row['volume']) if pd.notna(row.get('volume')) else 0,
                amount=float(row['amount']) if pd.notna(
                    row.get('amount')) else None,
                amplitude=float(row['amplitude']) if pd.notna(
                    row.get('amplitude')) else None,
                change_percent=float(row['pct_chg']) if pd.notna(
                    row.get('pct_chg')) else None,
                change_amount=float(row['change']) if pd.notna(
                    row.get('change')) else None,
                turnover_rate=float(row['turnover']) if pd.notna(
                    row.get('turnover')) else None,
                atr14=float(row['atr14']) if pd.notna(row.get('atr14')) else None
            )
            stock_data_items.append(item)

        result = StockDataResponse(
            symbol=symbol,
            count=int(len(df_all)),
            data=stock_data_items,
            date_range={
                "start": _to_date_str(df_all["date"].min()),
                "end": _to_date_str(df_all["date"].max())
            }
        )

        # 缓存结果（历史数据变化频率低，TTL 60 秒）
        set_cache(
            "stock_data", result.model_dump(), ttl=60,
            symbol=symbol, start_date=start_date, end_date=end_date,
            limit=limit, offset=offset,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


@router.get("/stock-data/stats/{symbol}")
def get_stock_data_stats(symbol: str):
    """获取股票数据统计信息"""
    try:
        candidates = get_table_name_candidates(symbol)
        db = get_db()
        df = pd.DataFrame()
        for cand in candidates:
            df = db.get_data(table_name=cand)
            if not df.empty:
                break
        if df.empty:
            tried = ", ".join(candidates) if candidates else "(无)"
            raise HTTPException(status_code=404, detail=f"数据表不存在或无数据，已尝试: {tried}")

        stats = {
            "total_records": int(len(df)),
            "earliest_date": _to_date_str(df["date"].min()),
            "latest_date": _to_date_str(df["date"].max()),
            "min_open": float(df["open"].min()) if "open" in df.columns else 0.0,
            "max_open": float(df["open"].max()) if "open" in df.columns else 0.0,
            "min_close": float(df["close"].min()) if "close" in df.columns else 0.0,
            "max_close": float(df["close"].max()) if "close" in df.columns else 0.0,
            "avg_volume": float(df["volume"].mean()) if "volume" in df.columns else 0.0,
            "min_volume": float(df["volume"].min()) if "volume" in df.columns else 0.0,
            "max_volume": float(df["volume"].max()) if "volume" in df.columns else 0.0,
        }

        return {
            "symbol": symbol,
            "statistics": {
                "total_records": int(stats['total_records']),
                "date_range": {
                    "start": stats['earliest_date'],
                    "end": stats['latest_date']
                },
                "price_range": {
                    "open": {"min": float(stats['min_open']), "max": float(stats['max_open'])},
                    "close": {"min": float(stats['min_close']), "max": float(stats['max_close'])}
                },
                "volume_stats": {
                    "average": float(stats['avg_volume']),
                    "min": float(stats['min_volume']),
                    "max": float(stats['max_volume'])
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/ema-data", response_model=EMADataResponse)
def get_ema_data(
    symbol: str = Query(default="159633", description="股票代码"),
    period: int = Query(default=20, description="EMA 周期"),
    limit: int = Query(default=100, le=1000, description="返回数据条数"),
    slope_filter: int = Query(default=1, description="是否启用斜率过滤: 0=关闭, 1=开启")
):
    """获取 EMA 指标数据（含方向判断和颜色信号）"""
    # 尝试从缓存读取（EMA 计算是昂贵操作）
    cached_result = get_cached(
        "ema_data",
        symbol=symbol, period=period, limit=limit, slope_filter=slope_filter,
    )
    if cached_result is not None:
        return EMADataResponse(**cached_result)

    try:
        candidates = get_table_name_candidates(symbol)
        db = get_db()
        df_all = pd.DataFrame()
        used_table = ""
        for cand in candidates:
            # 先查询总条数（确认表存在）
            df_count = db.get_data(table_name=cand, limit=1)
            if not df_count.empty:
                used_table = cand
                # 使用ORDER BY DESC获取最新数据
                df_all = db.get_data(
                    table_name=cand,
                    limit=limit,
                    order_by="DESC"
                )
                break
        if df_all.empty:
            tried = ", ".join(candidates) if candidates else "(无)"
            raise HTTPException(status_code=404, detail=f"数据表不存在或无数据，已尝试: {tried}")

        df_all = df_all.sort_values("date", ascending=True).copy()

        close_prices = df_all["close"]
        ema_values = FactorLibrary.ema(close_prices, period=period)

        df_ema = df_all[["date"]].copy()
        df_ema["ema"] = ema_values.reindex(df_all.index).astype(float)
        df_ema = df_ema.dropna(subset=["date", "ema"]).reset_index(drop=True)
        ema_list = df_ema["ema"].tolist()

        # 根据参数决定是否使用斜率过滤
        if slope_filter == 1:
            directions = _classify_ema_trend_directions(ema_list, period=period)
        else:
            directions = _simple_direction_classify(ema_list)

        color_map = {
            "up": "#ef4136",
            "down": "#22c55e",
            "flat": "#616161",
        }

        ema_data_items = []
        for row, direction in zip(df_ema.itertuples(index=False), directions):
            ema_val = float(row.ema)
            ema_data_items.append(
                EMADataItem(
                    time=_to_date_str(row.date),
                    value=round(ema_val, 2),
                    direction=direction,
                    color=color_map.get(direction, "#616161"),
                )
            )

        result = EMADataResponse(
            symbol=symbol,
            period=period,
            count=len(ema_data_items),
            data=ema_data_items
        )

        # 缓存结果（EMA 计算昂贵，TTL 设为 120 秒）
        set_cache(
            "ema_data", result.model_dump(), ttl=120,
            symbol=symbol, period=period, limit=limit, slope_filter=slope_filter,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 EMA 数据失败: {str(e)}")


