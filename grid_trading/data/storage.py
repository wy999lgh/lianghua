import sqlite3
import os
import pandas as pd
from typing import Optional
from .config import TABLE_SCHEMA, DEFAULT_DB_PATH

class DBManager:
    """数据库管理类"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """初始化数据库表"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        # 不再预创建固定表，改为按需创建
        pass

    def _ensure_table_exists(self, cursor, table_name: str):
        """确保表存在"""
        cursor.execute(TABLE_SCHEMA.format(table_name=table_name))

    def save_data(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        """
        保存数据到数据库
        
        Args:
            df: 清洗后的 DataFrame
            table_name: 表名 (如 stock_600519)
            if_exists: 'fail', 'replace', 'append' (默认)
        """
        if df.empty:
            return

        conn = sqlite3.connect(self.db_path)
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

    def get_data(self, table_name: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        查询数据
        
        Args:
            table_name: 表名 (如 stock_600519)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: 查询结果
        """
        conn = sqlite3.connect(self.db_path)
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
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
