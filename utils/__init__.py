"""
工具模块包

提供交易系统的通用工具功能：
- TradingLogger: 增强的日志记录器
- ConfigManager: YAML 配置管理（单例模式）
- NotificationManager: 企业微信通知管理
- TaskScheduler: 定时任务调度器
- helpers: 通用辅助函数
"""

# 日志相关
from .logger import (
    TradingLogger,
    setup_logger,
    get_logger,
)

# 配置管理相关
from .config_manager import (
    ConfigManager,
    get_config,
)

# 通知管理
from .notification import (
    NotificationManager,
    get_notification_manager,
)

# 定时任务调度
from .scheduler import (
    TaskScheduler,
    get_scheduler,
)

# 辅助函数
from .helpers import (
    # 路径相关
    get_project_root,
    ensure_dir,
    get_data_path,
    # 日期相关
    format_date,
    parse_date,
    parse_datetime,
    get_today,
    # 数字格式化
    format_number,
    format_percent,
    format_currency,
    format_shares,
    # 其他
    safe_divide,
    clamp,
)

__all__ = [
    # 日志
    'TradingLogger',
    'setup_logger',
    'get_logger',
    # 配置
    'ConfigManager',
    'get_config',
    # 通知
    'NotificationManager',
    'get_notification_manager',
    # 调度
    'TaskScheduler',
    'get_scheduler',
    # 路径
    'get_project_root',
    'ensure_dir',
    'get_data_path',
    # 日期
    'format_date',
    'parse_date',
    'parse_datetime',
    'get_today',
    # 数字
    'format_number',
    'format_percent',
    'format_currency',
    'format_shares',
    # 其他
    'safe_divide',
    'clamp',
]

__version__ = '2.0.0'
