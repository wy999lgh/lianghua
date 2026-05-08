"""
交易系统日志模块

从 grid_trading/utils/logger.py 迁移并增强：
- 支持文件和控制台双输出
- 日志路径和级别可配置
- 提供 TradingLogger 类和向后兼容的 setup_logger 函数
- 支持按日期分割日志 (TimedRotatingFileHandler)
- 支持按级别分文件存储 (INFO/ERROR 分离)
- 支持 JSON 结构化日志输出
- 交易专用日志方法 (log_trade, log_signal, log_risk)
- 性能计时装饰器 (log_execution_time)
- 毫秒级时间戳
"""

import logging
import os
import sys
import json
import time
import functools
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Callable, Any, Union


class JsonFormatter(logging.Formatter):
    """
    JSON 格式日志格式化器

    输出 JSON 结构化日志，便于日志分析和处理。
    """

    def __init__(self, datefmt: str = '%Y-%m-%d %H:%M:%S'):
        super().__init__(datefmt=datefmt)
        self.datefmt = datefmt

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON 字符串"""
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'msecs': int(record.msecs),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class LevelFilter(logging.Filter):
    """
    日志级别过滤器

    用于过滤特定级别范围的日志。
    """

    def __init__(self, min_level: int, max_level: int = logging.CRITICAL):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录"""
        return self.min_level <= record.levelno <= self.max_level


class TradingLogger:
    """
    交易系统日志记录器

    支持文件和控制台双输出，可配置日志级别和文件路径。
    支持按日期分割、按级别分文件、JSON 输出等高级功能。

    Example:
        >>> logger = TradingLogger('backtest')
        >>> logger.info('回测开始')
        >>> logger.warning('风险警告')
        >>> logger.log_trade('AAPL', 'BUY', 150.0, 100)
    """

    # 默认日志格式（毫秒级时间戳）
    DEFAULT_FORMAT = '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_DATEFMT = '%Y-%m-%d %H:%M:%S'

    def __init__(
        self,
        name: str,
        log_file: str = 'logs/trading.log',
        level: int = logging.INFO,
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        json_output: bool = False,
        timed_rotating: bool = False,
        when: str = 'midnight',
        error_log_file: Optional[str] = None
    ):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
            log_file: 日志文件路径（相对于项目根目录或绝对路径）
            level: 日志级别（logging.DEBUG, INFO, WARNING, ERROR, CRITICAL）
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_bytes: 单个日志文件最大大小（字节），仅在 timed_rotating=False 时生效
            backup_count: 保留的日志文件数量
            json_output: 是否使用 JSON 格式输出
            timed_rotating: 是否按时间分割日志（使用 TimedRotatingFileHandler）
            when: 时间分割方式 ('midnight', 'H', 'D', 'W0'-'W6')
            error_log_file: 错误日志文件路径，默认为 logs/trading_error.log
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.json_output = json_output
        self._error_log_file = error_log_file
        self._setup_logger(
            log_file, level, console_output, file_output,
            max_bytes, backup_count, json_output, timed_rotating, when
        )

    def _get_formatter(self, json_output: bool = False) -> logging.Formatter:
        """获取日志格式化器"""
        if json_output:
            return JsonFormatter(datefmt=self.DEFAULT_DATEFMT)
        return logging.Formatter(self.DEFAULT_FORMAT, datefmt=self.DEFAULT_DATEFMT)

    def _resolve_log_path(self, log_file: str) -> str:
        """解析日志文件路径"""
        if not os.path.isabs(log_file):
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))
            log_file = os.path.join(project_root, log_file)

        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        return log_file

    def _setup_logger(
        self,
        log_file: str,
        level: int,
        console_output: bool,
        file_output: bool,
        max_bytes: int,
        backup_count: int,
        json_output: bool,
        timed_rotating: bool,
        when: str
    ):
        """配置日志记录器"""
        # 如果已经配置过，跳过
        if self.logger.handlers:
            self.logger.setLevel(level)
            return

        formatter = self._get_formatter(json_output)

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件处理器
        if file_output and log_file:
            log_file = self._resolve_log_path(log_file)

            if timed_rotating:
                # 使用 TimedRotatingFileHandler 按时间分割
                file_handler = TimedRotatingFileHandler(
                    log_file,
                    when=when,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            else:
                # 使用 RotatingFileHandler 按大小分割
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # 添加错误日志文件处理器（仅记录 ERROR 及以上级别）
            error_log_file = self._error_log_file
            if error_log_file is None:
                # 默认错误日志文件路径
                log_dir = os.path.dirname(log_file)
                error_log_file = os.path.join(log_dir, 'trading_error.log')
            else:
                error_log_file = self._resolve_log_path(error_log_file)

            if timed_rotating:
                error_handler = TimedRotatingFileHandler(
                    error_log_file,
                    when=when,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            else:
                error_handler = RotatingFileHandler(
                    error_log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            error_handler.setFormatter(formatter)
            error_handler.setLevel(logging.ERROR)
            error_handler.addFilter(LevelFilter(logging.ERROR))
            self.logger.addHandler(error_handler)

        self.logger.setLevel(level)

    # 便捷方法
    def debug(self, msg: str, *args, **kwargs):
        """记录 DEBUG 级别日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """记录 INFO 级别日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """记录 WARNING 级别日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """记录 ERROR 级别日志"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(msg, *args, **kwargs)

    def set_level(self, level: int):
        """动态设置日志级别"""
        self.logger.setLevel(level)

    # ==================== 交易专用日志方法 ====================

    def log_trade(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        **kwargs
    ):
        """
        记录交易操作

        Args:
            symbol: 股票/交易品种代码
            action: 交易动作 (BUY/SELL/CANCEL 等)
            price: 交易价格
            quantity: 交易数量
            **kwargs: 其他交易信息（如 order_id, strategy, cost 等）
        """
        extra_info = ', '.join(f'{k}={v}' for k, v in kwargs.items())
        msg = f"[TRADE] {symbol} | {action} | price={price:.4f} | qty={quantity}"
        if extra_info:
            msg += f" | {extra_info}"
        self.info(msg)

    def log_signal(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        **kwargs
    ):
        """
        记录交易信号

        Args:
            symbol: 股票/交易品种代码
            signal_type: 信号类型 (BUY_SIGNAL/SELL_SIGNAL/HOLD 等)
            price: 当前价格
            **kwargs: 其他信号信息（如 indicator, strength, reason 等）
        """
        extra_info = ', '.join(f'{k}={v}' for k, v in kwargs.items())
        msg = f"[SIGNAL] {symbol} | {signal_type} | price={price:.4f}"
        if extra_info:
            msg += f" | {extra_info}"
        self.info(msg)

    def log_risk(
        self,
        risk_type: str,
        message: str,
        **kwargs
    ):
        """
        记录风险事件

        Args:
            risk_type: 风险类型 (POSITION_LIMIT/DRAWDOWN/VOLATILITY 等)
            message: 风险描述信息
            **kwargs: 其他风险信息（如 level, threshold, current_value 等）
        """
        extra_info = ', '.join(f'{k}={v}' for k, v in kwargs.items())
        msg = f"[RISK] {risk_type} | {message}"
        if extra_info:
            msg += f" | {extra_info}"
        self.warning(msg)


def log_execution_time(func_or_logger: Union[Callable, TradingLogger, None] = None):
    """
    装饰器：记录函数执行时间

    可以直接使用，也可以传入 logger 实例。

    Usage:
        @log_execution_time
        def my_func():
            pass

        @log_execution_time(logger)
        def my_func():
            pass

        @log_execution_time()
        def my_func():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                elapsed_ms = (end_time - start_time) * 1000

                log_msg = f"[PERF] {func.__module__}.{func.__name__} executed in {elapsed_ms:.3f}ms"

                if isinstance(func_or_logger, TradingLogger):
                    func_or_logger.debug(log_msg)
                elif isinstance(func_or_logger, logging.Logger):
                    func_or_logger.debug(log_msg)
                else:
                    # 使用默认 logger
                    logging.getLogger('performance').debug(log_msg)
        return wrapper

    # 处理不同的调用方式
    if func_or_logger is None:
        # @log_execution_time()
        return decorator
    elif callable(func_or_logger) and not isinstance(func_or_logger, (TradingLogger, logging.Logger)):
        # @log_execution_time (不带括号，直接装饰函数)
        return decorator(func_or_logger)
    else:
        # @log_execution_time(logger)
        return decorator


def setup_logger(
    name: str = "grid_trading",
    log_file: Optional[str] = "logs/trading.log",
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    配置并返回一个日志记录器（向后兼容函数）

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（相对于项目根目录或绝对路径）
        level: 日志级别
        console_output: 是否输出到控制台
        file_output: 是否输出到文件

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果 logger 已经有 handlers，说明已经配置过，直接返回
    if logger.handlers:
        return logger

    # 创建 formatter（毫秒级时间戳）
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台 handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件 handler
    if file_output and log_file:
        # 处理相对路径
        if not os.path.isabs(log_file):
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))
            log_file = os.path.join(project_root, log_file)

        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> TradingLogger:
    """
    获取 TradingLogger 实例的便捷函数

    Args:
        name: 日志记录器名称

    Returns:
        TradingLogger: 日志记录器实例
    """
    return TradingLogger(name)
