"""
网格交易系统 - 数据库模块
使用SQLite作为本地数据库存储交易数据
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为项目根目录下的 data/grid_trading_system.db
        """
        if db_path is None:
            # 获取项目根目录 (假设当前文件在 grid_trading/db/database.py)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "data", "grid_trading_system.db")
            
        self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
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
                signal TEXT NOT NULL,  -- buy/sell
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
    
    def save_strategy_config(self, config: Dict) -> int:
        """
        保存策略配置
        
        Args:
            config: 策略配置字典
            
        Returns:
            int: 新创建记录的ID
        """
        conn = sqlite3.connect(self.db_path)
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
    
    def save_backtest_result(self, config_id: int, result: Dict):
        """
        保存回测结果
        
        Args:
            config_id: 对应的策略配置ID
            result: 回测结果字典
        """
        conn = sqlite3.connect(self.db_path)
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
    
    def save_trade_records(self, config_id: int, trades: List[Dict]):
        """
        保存交易记录
        
        Args:
            config_id: 对应的策略配置ID
            trades: 交易记录列表
        """
        conn = sqlite3.connect(self.db_path)
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
    
    def save_market_data(self, symbol: str, data: List[Dict]):
        """
        保存市场数据
        
        Args:
            symbol: 交易对符号
            data: 市场数据列表
        """
        conn = sqlite3.connect(self.db_path)
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
    
    def get_strategy_configs(self) -> List[Dict]:
        """
        获取所有策略配置
        
        Returns:
            List[Dict]: 策略配置列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM strategy_configs ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        columns = ['id', 'symbol', 'base_price', 'upper_step', 'lower_step', 
                  'upper_count', 'lower_count', 'max_position', 'min_position', 'created_at']
        configs = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return configs
    
    def get_backtest_results(self, config_id: Optional[int] = None) -> List[Dict]:
        """
        获取回测结果
        
        Args:
            config_id: 可选的策略配置ID
            
        Returns:
            List[Dict]: 回测结果列表
        """
        conn = sqlite3.connect(self.db_path)
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
        
        columns = ['id', 'config_id', 'total_return', 'max_drawdown', 'sharpe_ratio', 
                  'trade_count', 'start_date', 'end_date', 'created_at', 'symbol']
        results = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return results
    
    def get_trade_records(self, config_id: Optional[int] = None) -> List[Dict]:
        """
        获取交易记录
        
        Args:
            config_id: 可选的策略配置ID
            
        Returns:
            List[Dict]: 交易记录列表
        """
        conn = sqlite3.connect(self.db_path)
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
        
        columns = ['id', 'config_id', 'datetime', 'signal', 'price', 
                  'amount', 'position', 'commission', 'created_at']
        trades = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return trades
    
    def export_to_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        将表导出为DataFrame
        
        Args:
            table_name: 表名
            
        Returns:
            pd.DataFrame: 数据框
        """
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df


# 示例用法
if __name__ == "__main__":
    # 创建数据库管理器实例
    db_manager = DatabaseManager()
    
    print("SQLite数据库已成功集成到网格交易系统!")
    print(f"数据库文件位置: {db_manager.db_path}")
    
    # 显示所有表的结构
    conn = sqlite3.connect(db_manager.db_path)
    cursor = conn.cursor()
    
    tables = ['strategy_configs', 'backtest_results', 'trade_records', 'market_data']
    for table in tables:
        print(f"\n表 '{table}' 的结构:")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    
    conn.close()