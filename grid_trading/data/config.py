import os

# 默认数据库路径 (相对于项目根目录)
# 假设当前文件路径是 AI量化999/grid_trading/data/config.py
# 向上 3 级目录是项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "stock_data.db")

# 数据源重试配置
RETRY_COUNT = 3
RETRY_DELAY = 1  # 秒

# 数据字段映射 (AKShare -> 本地数据库)
COLUMN_MAPPING = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_chg",
    "涨跌额": "change",
    "换手率": "turnover",
}

# 数据库表结构定义
TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    open REAL,
    close REAL,
    high REAL,
    low REAL,
    volume REAL,
    amount REAL,
    change REAL,
    pct_chg REAL,
    amplitude REAL,
    turnover REAL,
    adjust_type TEXT,
    period TEXT,
    atr14 REAL
);
"""
