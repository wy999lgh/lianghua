"""
通用辅助函数模块

提供项目中常用的工具函数：
- 路径处理
- 日期格式化/解析
- 数字格式化
"""

import os
from datetime import datetime, date
from typing import Union, Optional


def get_project_root() -> str:
    """
    获取项目根目录路径

    Returns:
        str: 项目根目录的绝对路径

    Example:
        >>> root = get_project_root()
        >>> print(root)
        'd:\\AI量化999'
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_dir(path: str) -> str:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径（支持相对路径和绝对路径）

    Returns:
        str: 目录的绝对路径

    Example:
        >>> log_dir = ensure_dir('logs')
        >>> data_dir = ensure_dir('data/cache')
    """
    # 处理相对路径
    if not os.path.isabs(path):
        path = os.path.join(get_project_root(), path)

    os.makedirs(path, exist_ok=True)
    return path


def get_data_path(relative_path: str) -> str:
    """
    获取数据文件的绝对路径

    Args:
        relative_path: 相对于项目根目录的路径

    Returns:
        str: 绝对路径

    Example:
        >>> db_path = get_data_path('data/stock_data.db')
    """
    return os.path.join(get_project_root(), relative_path)


# ==================================================
# 日期处理函数
# ==================================================

def format_date(
    d: Union[datetime, date, str],
    fmt: str = '%Y-%m-%d'
) -> str:
    """
    格式化日期为字符串

    Args:
        d: datetime、date 对象或日期字符串
        fmt: 输出格式，默认 '%Y-%m-%d'

    Returns:
        str: 格式化后的日期字符串

    Example:
        >>> format_date(datetime.now())
        '2024-01-15'
        >>> format_date(date(2024, 1, 15), '%Y/%m/%d')
        '2024/01/15'
    """
    if isinstance(d, str):
        # 尝试解析常见格式
        d = parse_date(d)

    if isinstance(d, datetime):
        return d.strftime(fmt)
    elif isinstance(d, date):
        return d.strftime(fmt)
    else:
        raise TypeError(f"不支持的日期类型: {type(d)}")


def parse_date(
    s: str,
    fmt: Optional[str] = None
) -> date:
    """
    解析日期字符串为 date 对象

    Args:
        s: 日期字符串
        fmt: 日期格式，为 None 时自动检测常见格式

    Returns:
        date: 解析后的日期对象

    Raises:
        ValueError: 无法解析的日期格式

    Example:
        >>> parse_date('2024-01-15')
        datetime.date(2024, 1, 15)
        >>> parse_date('20240115', '%Y%m%d')
        datetime.date(2024, 1, 15)
    """
    if fmt:
        return datetime.strptime(s, fmt).date()

    # 自动检测常见格式
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y%m%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
    ]

    for f in formats:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue

    raise ValueError(f"无法解析日期字符串: {s}")


def parse_datetime(
    s: str,
    fmt: Optional[str] = None
) -> datetime:
    """
    解析日期时间字符串为 datetime 对象

    Args:
        s: 日期时间字符串
        fmt: 格式字符串，为 None 时自动检测

    Returns:
        datetime: 解析后的 datetime 对象
    """
    if fmt:
        return datetime.strptime(s, fmt)

    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y%m%d',
    ]

    for f in formats:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue

    raise ValueError(f"无法解析日期时间字符串: {s}")


def get_today(fmt: str = '%Y-%m-%d') -> str:
    """
    获取今天的日期字符串

    Args:
        fmt: 日期格式

    Returns:
        str: 今天的日期字符串
    """
    return date.today().strftime(fmt)


# ==================================================
# 数字格式化函数
# ==================================================

def format_number(
    n: Union[int, float],
    decimals: int = 2,
    thousands_sep: bool = True
) -> str:
    """
    格式化数字

    Args:
        n: 要格式化的数字
        decimals: 小数位数
        thousands_sep: 是否使用千分位分隔符

    Returns:
        str: 格式化后的数字字符串

    Example:
        >>> format_number(1234567.89)
        '1,234,567.89'
        >>> format_number(1234.5, decimals=0)
        '1,235'
        >>> format_number(1234.5, thousands_sep=False)
        '1234.50'
    """
    if thousands_sep:
        return f"{n:,.{decimals}f}"
    else:
        return f"{n:.{decimals}f}"


def format_percent(
    n: Union[int, float],
    decimals: int = 2,
    multiply: bool = True
) -> str:
    """
    格式化百分比

    Args:
        n: 要格式化的数字
        decimals: 小数位数
        multiply: 是否乘以 100（True: 0.05 -> 5.00%，False: 5 -> 5.00%）

    Returns:
        str: 格式化后的百分比字符串

    Example:
        >>> format_percent(0.1234)
        '12.34%'
        >>> format_percent(12.34, multiply=False)
        '12.34%'
        >>> format_percent(-0.05)
        '-5.00%'
    """
    if multiply:
        n = n * 100
    return f"{n:.{decimals}f}%"


def format_currency(
    n: Union[int, float],
    decimals: int = 2,
    symbol: str = '¥'
) -> str:
    """
    格式化货币金额

    Args:
        n: 金额
        decimals: 小数位数
        symbol: 货币符号

    Returns:
        str: 格式化后的货币字符串

    Example:
        >>> format_currency(12345.67)
        '¥12,345.67'
        >>> format_currency(12345.67, symbol='$')
        '$12,345.67'
    """
    return f"{symbol}{n:,.{decimals}f}"


def format_shares(n: int) -> str:
    """
    格式化股数（带单位）

    Args:
        n: 股数

    Returns:
        str: 格式化后的字符串

    Example:
        >>> format_shares(1000)
        '1,000股'
        >>> format_shares(10000)
        '1万股'
    """
    if abs(n) >= 10000:
        return f"{n / 10000:.2f}万股"
    return f"{n:,}股"


# ==================================================
# 其他辅助函数
# ==================================================

def safe_divide(
    numerator: Union[int, float],
    denominator: Union[int, float],
    default: float = 0.0
) -> float:
    """
    安全除法，避免除零错误

    Args:
        numerator: 被除数
        denominator: 除数
        default: 除数为零时的默认返回值

    Returns:
        float: 除法结果或默认值

    Example:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 0, default=-1)
        -1
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float]
) -> Union[int, float]:
    """
    将值限制在指定范围内

    Args:
        value: 原始值
        min_val: 最小值
        max_val: 最大值

    Returns:
        限制后的值

    Example:
        >>> clamp(15, 0, 10)
        10
        >>> clamp(-5, 0, 10)
        0
    """
    return max(min_val, min(value, max_val))
