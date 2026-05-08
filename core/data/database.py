# -*- coding: utf-8 -*-
"""
网格交易系统 - 统一数据库操作层
Unified database operations for the grid trading system

合并自:
- grid_trading/data/storage.py (DBManager - 行情数据 CRUD)
- grid_trading/db/database.py (DatabaseManager - 策略/回测/交易记录 CRUD)
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Union
import pandas as pd

from config.database_config import get_database_config, DatabaseConfig


# 行情数据表结构定义
MARKET_DATA_TABLE_SCHEMA = """
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


class Database:
    """
    统一数据库管理类

    整合行情数据存储和策略系统数据存储功能:
    - 行情数据 CRUD (save_data, get_data)
    - 策略配置 CRUD (save_strategy_config, get_strategy_configs)
    - 回测结果 CRUD (save_backtest_result, get_backtest_results)
    - 交易记录 CRUD (save_trade_records, get_trade_records)
    - 市场数据 CRUD (save_market_data)
    - 数据导出 (export_to_dataframe)
    """

    def __init__(
        self,
        stock_db_path: Optional[str] = None,
        trading_db_path: Optional[str] = None,
        config: Optional[DatabaseConfig] = None
    ):
        """
        初始化数据库管理器

        Args:
            stock_db_path: 行情数据库路径，默认从配置获取
            trading_db_path: 交易系统数据库路径，默认从配置获取
            config: 数据库配置对象，优先级最高
        """
        if config is None:
            config = get_database_config()

        self.config = config
        self.stock_db_path = stock_db_path or config.get_stock_data_db_path()
        self.trading_db_path = trading_db_path or config.get_trading_system_db_path()

        # 确保目录存在
        self._ensure_directories()

        # 初始化数据库
        self._init_stock_db()
        self._init_trading_db()

    def _ensure_directories(self):
        """确保数据库目录存在"""
        for db_path in [self.stock_db_path, self.trading_db_path]:
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

    def _init_stock_db(self):
        """初始化行情数据库 (按需创建表)"""
        # 不再预创建固定表，改为按需创建
        pass

    def _init_trading_db(self):
        """初始化交易系统数据库表结构"""
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        # 创建策略配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                base_price REAL NOT NULL,
                upper_step REAL NOT NULL,
                lower_step REAL NOT NULL,
                upper_count INTEGER NOT NULL,
                lower_count INTEGER NOT NULL,
                max_position REAL NOT NULL,
                min_position REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建回测结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER,
                total_return REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                trade_count INTEGER,
                start_date TEXT,
                end_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (config_id) REFERENCES strategy_configs (id)
            )
        ''')

        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER,
                datetime TEXT NOT NULL,
                signal TEXT NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                position REAL NOT NULL,
                commission REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (config_id) REFERENCES strategy_configs (id)
            )
        ''')

        # 创建K线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # ==================== 行情数据操作 (来自 DBManager) ====================

    def _ensure_table_exists(self, cursor, table_name: str):
        """确保行情数据表存在"""
        cursor.execute(MARKET_DATA_TABLE_SCHEMA.format(table_name=table_name))

    def save_data(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'append'
    ):
        """
        保存行情数据到数据库

        Args:
            df: 清洗后的 DataFrame
            table_name: 表名 (如 stock_600519, etf_510300)
            if_exists: 'fail', 'replace', 'append' (默认)
        """
        if df.empty:
            return

        conn = sqlite3.connect(self.stock_db_path)
        cursor = conn.cursor()

        try:
            # 确保表存在
            self._ensure_table_exists(cursor, table_name)

            # 使用 INSERT OR REPLACE 避免主键冲突
            columns = df.columns.tolist()
            placeholders = ', '.join(['?'] * len(columns))
            columns_str = ', '.join(columns)

            sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            data = df.values.tolist()
            cursor.executemany(sql, data)
            conn.commit()
        except Exception as e:
            print(f"Save data to {table_name} failed: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_data(
        self,
        table_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        查询行情数据

        Args:
            table_name: 表名 (如 stock_600519, etf_510300)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            pd.DataFrame: 查询结果
        """
        conn = sqlite3.connect(self.stock_db_path)

        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            conn.close()
            return pd.DataFrame()

        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"

        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            print(f"Query data failed: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def list_tables(self, db_type: str = 'stock') -> List[str]:
        """
        列出数据库中的所有表

        Args:
            db_type: 'stock' 或 'trading'

        Returns:
            List[str]: 表名列表
        """
        db_path = self.stock_db_path if db_type == 'stock' else self.trading_db_path
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        conn.close()
        return tables

    # ==================== 策略配置操作 (来自 DatabaseManager) ====================

    def save_strategy_config(self, config: Dict) -> int:
        """
        保存策略配置

        Args:
            config: 策略配置字典，包含:
                - symbol: 标的代码
                - base_price: 基准价格
                - upper_step: 上涨步长
                - lower_step: 下跌步长
                - upper_count: 上涨格数
                - lower_count: 下跌格数
                - max_position: 最大仓位
                - min_position: 最小仓位

        Returns:
            int: 新创建记录的ID
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO strategy_configs 
            (symbol, base_price, upper_step, lower_step, upper_count, lower_count, max_position, min_position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            config['symbol'], config['base_price'], config['upper_step'],
            config['lower_step'], config['upper_count'], config['lower_count'],
            config['max_position'], config['min_position']
        ))

        config_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return config_id

    def get_strategy_configs(self) -> List[Dict]:
        """
        获取所有策略配置

        Returns:
            List[Dict]: 策略配置列表
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM strategy_configs ORDER BY created_at DESC')
        rows = cursor.fetchall()

        columns = [
            'id', 'symbol', 'base_price', 'upper_step', 'lower_step',
            'upper_count', 'lower_count', 'max_position', 'min_position', 'created_at'
        ]
        configs = [dict(zip(columns, row)) for row in rows]

        conn.close()
        return configs

    def get_strategy_config_by_id(self, config_id: int) -> Optional[Dict]:
        """
        根据 ID 获取策略配置

        Args:
            config_id: 策略配置 ID

        Returns:
            Optional[Dict]: 策略配置字典，不存在返回 None
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM strategy_configs WHERE id = ?', (config_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            columns = [
                'id', 'symbol', 'base_price', 'upper_step', 'lower_step',
                'upper_count', 'lower_count', 'max_position', 'min_position', 'created_at'
            ]
            return dict(zip(columns, row))
        return None

    # ==================== 回测结果操作 (来自 DatabaseManager) ====================

    def save_backtest_result(self, config_id: int, result: Dict):
        """
        保存回测结果

        Args:
            config_id: 对应的策略配置ID
            result: 回测结果字典，包含:
                - total_return: 总收益率
                - max_drawdown: 最大回撤
                - sharpe_ratio: 夏普比率
                - trade_count: 交易次数
                - start_date: 开始日期
                - end_date: 结束日期
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO backtest_results 
            (config_id, total_return, max_drawdown, sharpe_ratio, trade_count, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            config_id, result.get('total_return'), result.get('max_drawdown'),
            result.get('sharpe_ratio'), result.get('trade_count'),
            result.get('start_date'), result.get('end_date')
        ))

        conn.commit()
        conn.close()

    def get_backtest_results(self, config_id: Optional[int] = None) -> List[Dict]:
        """
        获取回测结果

        Args:
            config_id: 可选的策略配置ID，为 None 则获取所有

        Returns:
            List[Dict]: 回测结果列表
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        if config_id:
            cursor.execute('''
                SELECT br.*, sc.symbol 
                FROM backtest_results br
                JOIN strategy_configs sc ON br.config_id = sc.id
                WHERE br.config_id = ?
                ORDER BY br.created_at DESC
            ''', (config_id,))
        else:
            cursor.execute('''
                SELECT br.*, sc.symbol 
                FROM backtest_results br
                JOIN strategy_configs sc ON br.config_id = sc.id
                ORDER BY br.created_at DESC
            ''')

        rows = cursor.fetchall()

        columns = [
            'id', 'config_id', 'total_return', 'max_drawdown', 'sharpe_ratio',
            'trade_count', 'start_date', 'end_date', 'created_at', 'symbol'
        ]
        results = [dict(zip(columns, row)) for row in rows]

        conn.close()
        return results

    # ==================== 交易记录操作 (来自 DatabaseManager) ====================

    def save_trade_records(self, config_id: int, trades: List[Dict]):
        """
        保存交易记录

        Args:
            config_id: 对应的策略配置ID
            trades: 交易记录列表，每条记录包含:
                - datetime: 交易时间
                - signal: 交易信号 (buy/sell)
                - price: 成交价格
                - amount: 成交数量
                - position: 持仓数量
                - commission: 手续费 (可选)
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        for trade in trades:
            cursor.execute('''
                INSERT INTO trade_records 
                (config_id, datetime, signal, price, amount, position, commission)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                config_id, trade['datetime'], trade['signal'], trade['price'],
                trade['amount'], trade['position'], trade.get('commission', 0)
            ))

        conn.commit()
        conn.close()

    def get_trade_records(self, config_id: Optional[int] = None) -> List[Dict]:
        """
        获取交易记录

        Args:
            config_id: 可选的策略配置ID，为 None 则获取所有

        Returns:
            List[Dict]: 交易记录列表
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        if config_id:
            cursor.execute('''
                SELECT * FROM trade_records 
                WHERE config_id = ?
                ORDER BY datetime DESC
            ''', (config_id,))
        else:
            cursor.execute('''
                SELECT * FROM trade_records 
                ORDER BY datetime DESC
            ''')

        rows = cursor.fetchall()

        columns = [
            'id', 'config_id', 'datetime', 'signal', 'price',
            'amount', 'position', 'commission', 'created_at'
        ]
        trades = [dict(zip(columns, row)) for row in rows]

        conn.close()
        return trades

    # ==================== 市场数据操作 (来自 DatabaseManager) ====================

    def save_market_data(self, symbol: str, data: List[Dict]):
        """
        保存市场数据到 market_data 表

        Args:
            symbol: 交易对符号
            data: 市场数据列表，每条包含 date, open, high, low, close, volume
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        for item in data:
            cursor.execute('''
                INSERT INTO market_data 
                (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, item['date'], item['open'], item['high'],
                item['low'], item['close'], item['volume']
            ))

        conn.commit()
        conn.close()

    # ==================== 导出功能 (来自 DatabaseManager) ====================

    def export_to_dataframe(
        self,
        table_name: str,
        db_type: str = 'trading'
    ) -> pd.DataFrame:
        """
        将表导出为 DataFrame

        Args:
            table_name: 表名
            db_type: 'stock' 或 'trading'

        Returns:
            pd.DataFrame: 数据框
        """
        db_path = self.stock_db_path if db_type == 'stock' else self.trading_db_path
        conn = sqlite3.connect(db_path)

        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            return df
        except Exception as e:
            print(f"Export table {table_name} failed: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def delete_strategy_config(self, config_id: int) -> bool:
        """
        删除策略配置及关联的回测结果和交易记录

        Args:
            config_id: 策略配置 ID

        Returns:
            bool: 是否成功删除
        """
        conn = sqlite3.connect(self.trading_db_path)
        cursor = conn.cursor()

        try:
            # 删除关联的交易记录
            cursor.execute(
                'DELETE FROM trade_records WHERE config_id = ?', (config_id,))
            # 删除关联的回测结果
            cursor.execute(
                'DELETE FROM backtest_results WHERE config_id = ?', (config_id,))
            # 删除策略配置
            cursor.execute(
                'DELETE FROM strategy_configs WHERE id = ?', (config_id,))

            conn.commit()
            return True
        except Exception as e:
            print(f"Delete strategy config {config_id} failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


# 保持向后兼容的别名
DBManager = Database
DatabaseManager = Database
