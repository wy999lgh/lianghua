"""API路由定义

此模块定义所有API端点，包括策略配置、回测执行、结果获取和策略监控。
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import sqlite3
import pandas as pd


def get_table_name_from_symbol(symbol: str) -> str:
    """根据股票代码获取对应的表名称"""
    # 优先尝试 stock_ 前缀，如果失败则尝试 etf_
    # 这里简单根据代码特征判断，更严谨的做法是查询数据库或 DataFetcher
    if symbol.startswith("stock_") or symbol.startswith("etf_"):
        return symbol
    if len(symbol) == 6 and (symbol.startswith("5") or symbol.startswith("1")):
        return f"etf_{symbol}"
    return f"stock_{symbol}"

from grid_trading.data.legacy_loader import DataLoader
from grid_trading.strategy.grid_strategy import GridStrategy
from grid_trading.backtest.backtest_engine import BacktestEngine
from grid_trading.data.config import DEFAULT_DB_PATH

from grid_trading.data.fetcher import Fetcher
from grid_trading.data.cleaner import Cleaner
from grid_trading.data.storage import DBManager

# 创建路由器实例
router = APIRouter()

# 定义请求和响应模型

class DataFetchRequest(BaseModel):
    """数据获取请求模型"""
    symbol: str
    start_date: str
    end_date: str

class DataFetchResponse(BaseModel):
    """数据获取响应模型"""
    status: str
    message: str
    record_count: int

class StrategyConfig(BaseModel):
    """策略配置模型"""
    symbol: Optional[str] = None
    base_price: float
    upper_step: float
    lower_step: float
    upper_count: int
    lower_count: int
    max_position: Optional[float] = None
    min_position: Optional[float] = None


class BacktestRequest(BaseModel):
    """回测请求模型"""
    config: StrategyConfig
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class BacktestResponse(BaseModel):
    """回测响应模型"""
    status: str
    backtest_id: str
    message: str


class BacktestResult(BaseModel):
    """回测结果模型"""
    backtest_id: str
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict[str, Any]]
    position_details: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]


class StrategyStatus(BaseModel):
    """策略状态模型"""
    status: str
    current_position: float
    current_price: float
    base_price: float
    grid_lines: List[float]


class StockDataItem(BaseModel):
    """股票数据项模型"""
    id: int
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: Optional[float] = None
    amplitude: Optional[float] = None
    change_percent: Optional[float] = None
    change_amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    atr14: Optional[float] = None


class StockDataResponse(BaseModel):
    """股票数据响应模型"""
    symbol: str
    count: int
    data: List[StockDataItem]
    date_range: Dict[str, str]


# 模拟存储
backtest_results = {}
strategy_status = {}


@router.post("/data/fetch", response_model=DataFetchResponse)
def fetch_data(request: DataFetchRequest):
    """
    手动获取并更新股票/ETF数据
    
    Args:
        request: 包含symbol, start_date, end_date的请求体
        
    Returns:
        DataFetchResponse: 包含状态、消息和更新记录数
    """
    try:
        symbol = request.symbol
        # 移除可能的前缀
        if symbol.startswith("stock_"):
            symbol = symbol[6:]
        elif symbol.startswith("etf_"):
            symbol = symbol[4:]
            
        start_date = request.start_date.replace("-", "")
        end_date = request.end_date.replace("-", "")
        
        print(f"开始获取数据: {symbol}, {start_date}-{end_date}")
        
        # 1. 识别类型 (ETF 或 股票 或 指数)
        is_etf = False
        is_index = False
        
        # 指数判断: 000开头且通常较小，或者特定开头
        # 这里简单判断: 如果长度为6且以000开头，可能是上证指数或中证指数
        # 但股票也有000开头的(深市)。
        # 更准确的方法是前端传递类型，或者尝试多种方式。
        # 既然用户提到了 000985 (中证全指)，我们尝试加 sh 前缀作为指数获取
        if len(symbol) == 6 and (symbol.startswith("5") or symbol.startswith("1")):
            is_etf = True
        elif symbol == "000985" or symbol.startswith("sh") or symbol.startswith("sz"):
             # 特殊处理已知指数或带前缀的
             is_index = True
             if not symbol.startswith("sh") and not symbol.startswith("sz"):
                 # 000985 在新浪接口通常是 sh000985
                 if symbol == "000985":
                     symbol = "sh" + symbol
        
        # 2. 获取数据
        fetcher = Fetcher()
        if is_etf:
            print(f"识别为ETF: {symbol}")
            raw_df = fetcher.fetch_etf_daily(symbol, start_date, end_date)
        elif is_index:
            print(f"识别为指数: {symbol}")
            raw_df = fetcher.fetch_index_daily(symbol, start_date, end_date)
        else:
            print(f"识别为股票: {symbol}")
            # 尝试先作为股票获取
            raw_df = fetcher.fetch_stock_daily(symbol, start_date, end_date)
            # 如果股票获取失败且是以000开头的，尝试作为指数获取 (例如 000001 上证指数)
            if raw_df.empty and symbol.startswith("000"):
                 print(f"股票获取失败，尝试作为指数获取: sh{symbol}")
                 raw_df = fetcher.fetch_index_daily(f"sh{symbol}", start_date, end_date)
            
        if raw_df.empty:
            return DataFetchResponse(
                status="warning", 
                message=f"未获取到数据 ({symbol})，请检查代码或日期范围", 
                record_count=0
            )
            
        # 3. 清洗数据
        cleaner = Cleaner()
        cleaned_df = cleaner.clean_stock_data(raw_df, symbol)
        
        if cleaned_df.empty:
            return DataFetchResponse(
                status="warning", 
                message="数据获取成功但清洗后为空", 
                record_count=0
            )
            
        # 4. 保存数据
        db_manager = DBManager(DEFAULT_DB_PATH)
        table_name = get_table_name_from_symbol(symbol)
        db_manager.save_data(cleaned_df, table_name)
        
        record_count = len(cleaned_df)
        print(f"成功保存 {record_count} 条记录到表 {table_name}")
        
        return DataFetchResponse(
            status="success",
            message=f"成功更新 {symbol} 数据，共 {record_count} 条记录",
            record_count=record_count
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"数据获取失败: {str(e)}")


@router.post("/strategies/config", response_model=Dict[str, Any])
def create_strategy_config(config: StrategyConfig):
    """创建策略配置"""
    # 这里可以添加配置验证和存储逻辑
    return {
        "status": "success",
        "config_id": "config_123",
        "config": config.dict()
    }


@router.post("/backtest/run", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest):
    """执行回测"""
    try:
        # 创建策略配置
        grid_config = {
            'initial_base_price': request.config.base_price,
            'buy_percent': request.config.lower_step / 100,  # 转换为百分比
            'sell_percent': request.config.upper_step / 100,  # 转换为百分比
            'buy_amount': 100,  # 默认买入量
            'sell_amount': 100,  # 默认卖出量
            'max_position': request.config.max_position if request.config.max_position is not None else 100000000.0,
            'min_position': request.config.min_position if request.config.min_position is not None else 0.0,
            'price_range': [
                request.config.base_price *
                (1 - request.config.lower_step / 100 * request.config.lower_count),
                request.config.base_price *
                (1 + request.config.upper_step / 100 * request.config.upper_count)
            ],
            'update_method': 'trigger_price',
            'commission_rate': 0.0001  # ETF佣金：0.10‰
        }

        # 创建回测引擎
        backtest_engine = BacktestEngine()

        # 运行回测
        # 使用请求中的symbol，如果未提供则使用默认值
        symbol = request.config.symbol if request.config.symbol else "159633"
        
        # 处理空日期字符串
        start_date = request.start_date if request.start_date else None
        end_date = request.end_date if request.end_date else None
        result = backtest_engine.run_backtest(
            symbol_or_file=symbol,
            grid_config=grid_config,
            start_date=start_date,
            end_date=end_date
        )

        # 生成回测ID
        backtest_id = f"backtest_{len(backtest_results) + 1}"

        # 处理回测结果，转换为前端需要的格式
        trade_records = result.get("trade_records", [])
        
        # 计算每笔交易的现金和总资产
        initial_cash = 1000000.0  # 初始资金 100万
        cash = initial_cash
        trades_with_cash = []
        
        for trade in trade_records:
            # 计算现金变化
            if trade["signal"] == "buy":
                # 买入：现金减少（价格*数量 + 佣金）
                cash_change = - (trade["price"] * trade["amount"] + trade.get("commission", 0))
            else:  # sell
                # 卖出：现金增加（价格*数量 - 佣金）
                cash_change = trade["price"] * trade["amount"] - trade.get("commission", 0)
            
            # 更新现金
            cash += cash_change
            
            # 计算市值（持仓数量 * 当前价格）
            market_value = trade["position"] * trade["price"]
            
            # 计算总资产
            total_asset = cash + market_value
            
            # 创建包含现金和总资产的交易记录
            trade_with_cash = {
                "datetime": trade["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                "signal": trade["signal"],
                "price": trade["price"],
                "amount": trade["amount"],
                "position": trade["position"],
                "commission": trade.get("commission", 0),
                "cash": round(cash, 2),
                "market_value": round(market_value, 2),
                "total_asset": round(total_asset, 2)
            }
            
            trades_with_cash.append(trade_with_cash)
        
        # 处理持仓明细记录
        position_records = result.get("position_records", [])
        position_details = []
        
        # 计算持仓明细的现金和总资产
        current_cash = initial_cash
        previous_asset = initial_cash
        
        for pos in position_records:
            # 计算市值
            market_value = pos["position"] * pos["price"]
            
            # 计算总资产
            total_asset = current_cash + market_value
            
            # 计算盈亏
            profit_loss = total_asset - previous_asset
            
            # 更新前一天的资产
            previous_asset = total_asset
            
            # 创建持仓明细记录
            position_detail = {
                "datetime": pos["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                "position": pos["position"],
                "price": pos["price"],
                "market_value": round(market_value, 2),
                "cash": round(current_cash, 2),
                "total_asset": round(total_asset, 2),
                "profit_loss": round(profit_loss, 2)
            }
            
            position_details.append(position_detail)
        
        processed_result = {
            "total_return": result.get("total_return_percent", 0),
            "max_drawdown": 0,  # 暂时设为0，需要在BacktestEngine中实现
            "sharpe_ratio": 0,  # 暂时设为0，需要在BacktestEngine中实现
            "trades": trades_with_cash,
            "position_details": position_details,
            "equity_curve": [
                {
                    "datetime": item["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                    "equity": item["equity"],
                    "return": item["return"]
                }
                for item in result.get("equity_curve", [])
            ]
        }

        # 存储处理后的回测结果
        backtest_results[backtest_id] = processed_result

        return BacktestResponse(
            status="success",
            backtest_id=backtest_id,
            message="回测执行成功"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"回测执行失败: {str(e)}")


@router.get("/backtest/results/{backtest_id}", response_model=BacktestResult)
def get_backtest_result(backtest_id: str):
    """获取回测结果"""
    if backtest_id not in backtest_results:
        raise HTTPException(status_code=404, detail="回测结果不存在")

    result = backtest_results[backtest_id]

    return BacktestResult(
        backtest_id=backtest_id,
        total_return=result.get("total_return", 0),
        max_drawdown=result.get("max_drawdown", 0),
        sharpe_ratio=result.get("sharpe_ratio", 0),
        trades=result.get("trades", []),
        position_details=result.get("position_details", []),
        equity_curve=result.get("equity_curve", [])
    )


@router.get("/strategies/status/{strategy_id}", response_model=StrategyStatus)
def get_strategy_status(strategy_id: str):
    """获取策略状态"""
    if strategy_id not in strategy_status:
        # 模拟策略状态
        strategy_status[strategy_id] = {
            "status": "running",
            "current_position": 0.5,
            "current_price": 100.5,
            "base_price": 100.0,
            "grid_lines": [95.0, 97.5, 100.0, 102.5, 105.0]
        }

    status = strategy_status[strategy_id]

    return StrategyStatus(
        status=status["status"],
        current_position=status["current_position"],
        current_price=status["current_price"],
        base_price=status["base_price"],
        grid_lines=status["grid_lines"]
    )


@router.get("/data/symbols")
def get_available_symbols():
    """获取可用的交易对"""
    return {
        "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    }


@router.get("/data/history/{symbol:path}")
def get_historical_data(symbol: str):
    """获取历史数据"""
    try:
        data_loader = DataLoader()
        df = data_loader.load_data()

        # 转换为前端可用的格式
        data = []
        for idx, row in df.iterrows():
            data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": row.get("open", 0),
                "high": row.get("high", 0),
                "low": row.get("low", 0),
                "close": row.get("close", 0),
                "volume": row.get("volume", 0)
            })

        return {
            "symbol": symbol,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


@router.get("/stock-data", response_model=StockDataResponse)
def get_stock_data(
    symbol: str = Query(default="159633", description="股票代码"),
    start_date: Optional[str] = Query(default=None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(default=100, le=1000, description="返回数据条数"),
    offset: int = Query(default=0, description="偏移量")
):
    """获取标准化股票数据"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        
        # 根据symbol获取表名称
        table_name = get_table_name_from_symbol(symbol)
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            # 如果指定表不存在，使用默认表
            table_name = "stock_data_standard"
            print(f"警告: 表 {table_name} 不存在，使用默认表 stock_data_standard")
        
        # 构建WHERE条件
        where_conditions = []
        if start_date:
            where_conditions.append(f"date >= '{start_date}'")
        if end_date:
            where_conditions.append(f"date <= '{end_date}'")
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        # 查询数据
        query = f"""
        SELECT id,
               date, 
               open_price as open, 
               close_price as close, 
               high_price as high, 
               low_price as low, 
               volume, 
               amount, 
               amplitude, 
               price_change_pct as change_percent, 
               price_change as change_amount, 
               turnover_rate, 
               atr14
        FROM {table_name}
        {where_clause}
        ORDER BY date DESC
        LIMIT {limit} OFFSET {offset}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 转换为Pydantic模型列表
        stock_data_items = []
        for _, row in df.iterrows():
            item = StockDataItem(
                id=int(row['id']),
                date=row['date'],
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                volume=int(row['volume']),
                amount=float(row['amount']) if pd.notna(row['amount']) else None,
                amplitude=float(row['amplitude']) if pd.notna(row['amplitude']) else None,
                change_percent=float(row['change_percent']) if pd.notna(row['change_percent']) else None,
                change_amount=float(row['change_amount']) if pd.notna(row['change_amount']) else None,
                turnover_rate=float(row['turnover_rate']) if pd.notna(row['turnover_rate']) else None,
                atr14=float(row['atr14']) if pd.notna(row['atr14']) else None
            )
            stock_data_items.append(item)
        
        # 获取总数和日期范围（考虑日期过滤）
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        
        # 构建统计查询的WHERE条件
        count_where_clause = where_clause.replace('WHERE ', '') if where_clause else ''
        count_query = f"SELECT COUNT(*) as count FROM {table_name} {where_clause}".strip()
        total_count = pd.read_sql_query(count_query, conn).iloc[0]['count']
        
        # 获取过滤后的日期范围
        if count_where_clause:
            date_range_query = f"""
                SELECT MIN(date) as min_date, MAX(date) as max_date 
                FROM {table_name} 
                WHERE {count_where_clause}
            """
        else:
            date_range_query = f"""
                SELECT MIN(date) as min_date, MAX(date) as max_date 
                FROM {table_name}
            """
        
        date_range_df = pd.read_sql_query(date_range_query, conn)
        conn.close()
        
        date_range = {
            "start": date_range_df.iloc[0]['min_date'],
            "end": date_range_df.iloc[0]['max_date']
        }
        
        return StockDataResponse(
            symbol=symbol,
            count=int(total_count),
            data=stock_data_items,
            date_range=date_range
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


@router.get("/stock-data/stats/{symbol}")
def get_stock_data_stats(symbol: str):
    """获取股票数据统计信息"""
    try:
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        
        # 根据symbol获取表名称
        table_name = get_table_name_from_symbol(symbol)
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            # 如果指定表不存在，使用默认表
            table_name = "stock_data_standard"
            print(f"警告: 表 {table_name} 不存在，使用默认表 stock_data_standard")
        
        # 基本统计
        stats_query = f"""
        SELECT 
            COUNT(*) as total_records,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            MIN(open_price) as min_open,
            MAX(open_price) as max_open,
            MIN(close_price) as min_close,
            MAX(close_price) as max_close,
            AVG(volume) as avg_volume,
            MIN(volume) as min_volume,
            MAX(volume) as max_volume
        FROM {table_name}
        """
        
        stats_df = pd.read_sql_query(stats_query, conn)
        conn.close()
        
        stats = stats_df.iloc[0].to_dict()
        
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
                    "average": int(stats['avg_volume']),
                    "min": int(stats['min_volume']),
                    "max": int(stats['max_volume'])
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
