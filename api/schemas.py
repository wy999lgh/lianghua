"""
Pydantic 请求/响应数据模型（统一响应格式）
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Generic, TypeVar


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应封装

    code=0 表示成功，非0表示业务错误
    """
    code: int = Field(default=0, description="状态码：0=成功，非0=业务错误")
    message: str = Field(default="ok")
    data: Optional[T] = None


# ==================== 数据相关模型 ====================

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


class EMADataItem(BaseModel):
    """EMA数据项模型"""
    time: str
    value: float
    direction: str  # up / down / flat
    color: str


class EMADataResponse(BaseModel):
    """EMA数据响应模型"""
    symbol: str
    period: int
    count: int
    data: List[EMADataItem]


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


# ==================== 标的列表相关模型 ====================

class SymbolInfo(BaseModel):
    """标的信息模型"""
    code: str  # 标的代码 (如 000001, 159633)
    name: str  # 标的名称
    type: str  # 标的类型 (stock/etf/index)
    table_name: str  # 数据表名


class SymbolListResponse(BaseModel):
    """标的列表响应模型"""
    count: int
    data: List[SymbolInfo]


# ==================== 策略相关模型 ====================

class StrategyConfig(BaseModel):
    """策略配置模型"""
    strategy_name: Optional[str] = Field(default="", description="策略名称（中文）")
    strategy_type: Optional[str] = Field(default="grid", description="策略类型：grid-网格交易策略，ema-均线牛熊策略")
    symbol: Optional[str] = None
    base_price: float = Field(gt=0, description="基准价格，必须大于0")
    upper_step: float = Field(gt=0, description="上涨步长，必须大于0")
    lower_step: float = Field(gt=0, description="下跌步长，必须大于0")
    upper_count: Optional[int] = Field(default=100, ge=0, description="上涨格数，不能为负数")
    lower_count: Optional[int] = Field(default=100, ge=0, description="下跌格数，不能为负数")
    max_position: Optional[float] = Field(default=None, ge=0, description="最大仓位，不能为负数")
    min_position: Optional[float] = Field(default=None, ge=0, description="最小仓位，不能为负数")
    initial_cash: Optional[float] = Field(default=1000000.0, gt=0, description="初始资金，必须大于0")
    buy_quantity: Optional[float] = Field(default=None, ge=0, description="买入数量，不能为负数")
    sell_quantity: Optional[float] = Field(default=None, ge=0, description="卖出数量，不能为负数")


class StrategyUpdate(BaseModel):
    """策略更新模型（所有字段可选）"""
    strategy_name: Optional[str] = Field(default=None, description="策略名称（中文）")
    strategy_type: Optional[str] = Field(default=None, description="策略类型：grid-网格交易策略，ema-均线牛熊策略")
    symbol: Optional[str] = None
    base_price: Optional[float] = Field(default=None, gt=0, description="基准价格，必须大于0")
    upper_step: Optional[float] = Field(default=None, gt=0, description="上涨步长，必须大于0")
    lower_step: Optional[float] = Field(default=None, gt=0, description="下跌步长，必须大于0")
    upper_count: Optional[int] = Field(default=None, ge=0, description="上涨格数，不能为负数")
    lower_count: Optional[int] = Field(default=None, ge=0, description="下跌格数，不能为负数")
    max_position: Optional[float] = Field(default=None, ge=0, description="最大仓位，不能为负数")
    min_position: Optional[float] = Field(default=None, ge=0, description="最小仓位，不能为负数")


class StrategyStatus(BaseModel):
    """策略状态模型"""
    status: str
    current_position: float
    current_price: float
    base_price: float
    grid_lines: List[float]


# ==================== 回测相关模型 ====================

class BacktestRequest(BaseModel):
    """回测请求模型（网格策略专用）"""
    config: StrategyConfig
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class GenericBacktestRequest(BaseModel):
    """通用回测请求模型（支持多种策略类型）"""
    strategy_name: Optional[str] = None
    strategy_type: str = "grid"
    symbol: Optional[str] = None
    initial_cash: Optional[float] = Field(default=1000000.0, gt=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class BacktestResponse(BaseModel):
    """回测响应模型"""
    status: str
    backtest_id: str
    message: str


class DirectBacktestRequest(BaseModel):
    """直接回测请求模型（通用回测页面专用）"""
    strategy_name: Optional[str] = None
    strategy_type: str = "grid"
    symbol: str = "159633"
    initial_cash: float = 1000000.0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: str = "daily"
    base_price: float = 10.0
    upper_step: float = 1.0
    lower_step: float = 1.0
    buy_quantity: int = 100
    sell_quantity: int = 100
    upper_count: int = 100
    lower_count: int = 100
    max_position: float = 100000000.0
    min_position: float = 0.0
    commission_rate: float = 0.0001


class BacktestResult(BaseModel):
    """回测结果模型（包含完整绩效指标）"""
    backtest_id: str
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    volatility: float = 0.0
    # 风险指标
    max_drawdown: float = 0.0
    max_drawdown_duration: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    sharpe_ratio: float = 0.0
    # 交易统计
    win_rate: float = 0.0
    profit_factor: float = 0.0
    profit_loss_ratio: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    avg_holding_period: float = 0.0
    total_commission: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    # 基准对比
    benchmark_return: float = 0.0
    excess_return: float = 0.0
    alpha: float = 0.0
    beta: float = 0.0
    information_ratio: float = 0.0
    tracking_error: float = 0.0
    correlation: float = 0.0
    # 其他指标
    daily_excess_return: float = 0.0
    excess_max_drawdown: float = 0.0
    daily_win_rate: float = 0.0
    # 交易和权益数据
    trades: List[Dict[str, Any]] = []
    position_details: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []
    benchmark_curve: List[Dict[str, Any]] = []
