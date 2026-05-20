# -*- coding: utf-8 -*-
"""
网格交易系统 - 统一数据库操作层 (PostgreSQL)
Unified database operations for the grid trading system

特性:
- 使用 psycopg3 (支持 Python 3.13+)
- 使用连接池
- 动态行情分表（stock_daily_* / etf_daily_* / index_daily_*）
- SQL 注入防护（表名白名单校验 + 参数化查询）
- 事务安全（try/commit/rollback 标准模式）
"""

import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Union
import pandas as pd

from config.database_config import get_database_config, DatabaseConfig

try:
    import psycopg
    from psycopg_pool import ConnectionPool
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False


MARKET_DATA_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    open DOUBLE PRECISION,
    close DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    amount DOUBLE PRECISION,
    change DOUBLE PRECISION,
    pct_chg DOUBLE PRECISION,
    amplitude DOUBLE PRECISION,
    turnover DOUBLE PRECISION,
    adjust_type TEXT,
    period TEXT,
    atr14 DOUBLE PRECISION
);
"""


class Database:
    """
    统一数据库管理类

    整合行情数据存储和策略系统数据存储功能:
    - 行情数据 CRUD (save_data, get_data)
    - 标的列表管理 (upsert_instrument_basic, list_instrument_basic)
    - 策略配置 CRUD (save_strategy_config, get_strategy_configs)
    - 回测结果 CRUD (save_backtest_result, get_backtest_results)
    - 交易记录 CRUD (save_trade_records, get_trade_records)
    - 市场数据 CRUD (save_market_data)
    - 数据导出 (export_to_dataframe)
    """

    _pool = None
    _pool_config_hash = ""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        初始化数据库管理器
        Args:
            config: 数据库配置对象
        """
        if config is None:
            config = get_database_config()

        self.config = config

        current_hash = hashlib.md5(
            f"{config.postgres_host}:{config.postgres_port}:{config.postgres_database}:{config.postgres_user}".encode()
        ).hexdigest()

        if Database._pool is None or Database._pool_config_hash != current_hash:
            if Database._pool is not None:
                Database._pool.close()
            password = config.get_postgres_password()
            conninfo = f"host={config.postgres_host} port={config.postgres_port} dbname={config.postgres_database} user={config.postgres_user} password={password}"
            Database._pool = ConnectionPool(
                min_size=5,
                max_size=50,
                conninfo=conninfo
            )
            Database._pool_config_hash = current_hash

        self._init_stock_db()
        self._init_trading_db()

    @classmethod
    def close_pool(cls):
        """关闭连接池（应用退出时调用）"""
        if cls._pool:
            cls._pool.close()
            cls._pool = None
            cls._pool_config_hash = ""

    def _init_stock_db(self):
        """初始化行情数据库 (按需创建表)"""
        pass

    def _init_trading_db(self):
        """初始化交易系统数据库表结构"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ddl = """
            CREATE TABLE IF NOT EXISTS instrument_basic (
                instrument_type TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                market TEXT,
                source TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (instrument_type, code)
            );
            CREATE TABLE IF NOT EXISTS strategy_configs (
                id BIGSERIAL PRIMARY KEY,
                strategy_name TEXT DEFAULT '',
                symbol TEXT NOT NULL,
                base_price DOUBLE PRECISION NOT NULL,
                upper_step DOUBLE PRECISION NOT NULL,
                lower_step DOUBLE PRECISION NOT NULL,
                upper_count INTEGER NOT NULL,
                lower_count INTEGER NOT NULL,
                max_position DOUBLE PRECISION NOT NULL,
                min_position DOUBLE PRECISION NOT NULL,
                initial_cash DOUBLE PRECISION DEFAULT 1000000.0,
                buy_quantity INTEGER DEFAULT 100,
                sell_quantity INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS backtest_results (
                id BIGSERIAL PRIMARY KEY,
                config_id BIGINT,
                strategy_name TEXT DEFAULT '',
                strategy_type TEXT DEFAULT 'grid',
                symbol TEXT,
                start_date TEXT,
                end_date TEXT,
                initial_cash DOUBLE PRECISION,
                final_cash DOUBLE PRECISION,
                total_return DOUBLE PRECISION,
                annual_return DOUBLE PRECISION,
                sharpe_ratio DOUBLE PRECISION,
                sortino_ratio DOUBLE PRECISION,
                calmar_ratio DOUBLE PRECISION,
                max_drawdown DOUBLE PRECISION,
                volatility DOUBLE PRECISION,
                win_rate DOUBLE PRECISION,
                benchmark_return DOUBLE PRECISION,
                trade_count INTEGER,
                full_report TEXT,
                chart_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS trade_records (
                id BIGSERIAL PRIMARY KEY,
                config_id BIGINT,
                datetime TEXT NOT NULL,
                signal TEXT NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                position DOUBLE PRECISION NOT NULL,
                commission DOUBLE PRECISION DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS market_data (
                id BIGSERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open DOUBLE PRECISION NOT NULL,
                high DOUBLE PRECISION NOT NULL,
                low DOUBLE PRECISION NOT NULL,
                close DOUBLE PRECISION NOT NULL,
                volume DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS a_stock_list (
                stock_code TEXT PRIMARY KEY,
                stock_name TEXT
            );
            """
            for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
                cur.execute(stmt)
            conn.commit()
        finally:
            self._release_connection(conn)

    def _get_connection(self):
        """获取数据库连接"""
        try:
            conn = Database._pool.getconn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return conn
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                return Database._pool.getconn()
        except Exception as e:
            raise RuntimeError(f"获取PostgreSQL连接失败: {str(e)}") from e

    def _release_connection(self, conn):
        """归还数据库连接"""
        if conn is None:
            return
        try:
            if not conn.closed:
                if conn.transaction_status != psycopg.pq.TransactionStatus.IDLE:
                    conn.rollback()
                Database._pool.putconn(conn)
        except Exception:
            try:
                if not conn.closed:
                    conn.close()
            except Exception:
                pass

    def _validate_table_name(self, table_name: str) -> str:
        """校验表名合法性，防止SQL注入"""
        name = str(table_name or "").strip()
        if not name:
            raise ValueError("table_name 不能为空")
        for ch in name:
            if not (ch.isalnum() or ch == "_"):
                raise ValueError(f"table_name 包含非法字符: {table_name}")
        return name

    def _ensure_table_exists(self, cursor, table_name: str):
        """确保行情数据表存在"""
        cursor.execute(MARKET_DATA_TABLE_SCHEMA.format(table_name=table_name))

    def save_data(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        """
        保存行情数据到数据库（使用 ON CONFLICT UPSERT）

        Args:
            df: 清洗后的 DataFrame
            table_name: 表名 (如 stock_daily_600519, etf_daily_510300)
            if_exists: 'fail', 'replace', 'append' (默认)
        """
        if df.empty:
            return

        table_name = self._validate_table_name(table_name)
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            self._ensure_table_exists(cur, table_name)

            cols = df.columns.tolist()
            if "date" not in cols:
                raise ValueError("行情数据缺少 date 列")

            if if_exists == 'replace':
                cur.execute(f"DELETE FROM {table_name}")

            insert_cols = ", ".join([f'"{c}"' for c in cols])
            update_set = ", ".join([f'"{c}"=EXCLUDED."{c}"' for c in cols if c != "date"])
            sql = (
                f"INSERT INTO {table_name} ({insert_cols}) VALUES %s "
                f"ON CONFLICT (date) DO UPDATE SET {update_set}"
            )
            values = [tuple(row) for row in df.itertuples(index=False)]
            psycopg.extras.execute_values(cur, sql, values, page_size=2000)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._release_connection(conn)

    def get_data(self, table_name: str, start_date: Optional[str] = None,
                 end_date: Optional[str] = None, limit: int = 100,
                 offset: int = 0, order_by: str = "ASC") -> pd.DataFrame:
        """
        查询行情数据（支持 LIMIT/OFFSET 分页）

        Args:
            table_name: 表名
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 限制返回行数
            offset: 偏移量
            order_by: 排序方式 ASC/DESC

        Returns:
            pd.DataFrame: 查询结果
        """
        table_name = self._validate_table_name(table_name)
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "AND column_name IN ('date', 'trade_date')",
                (table_name,),
            )
            row = cur.fetchone()
            if not row:
                return pd.DataFrame()
            date_col = row[0]

            order = "ASC" if order_by.upper() not in ("ASC", "DESC") else order_by.upper()
            query = (
                f"SELECT * FROM {table_name} WHERE 1=1 "
                + (f" AND {date_col} >= %s" if start_date else "")
                + (f" AND {date_col} <= %s" if end_date else "")
                + f" ORDER BY {date_col} {order} LIMIT %s OFFSET %s"
            )
            params = []
            if start_date:
                params.append(start_date)
            if end_date:
                params.append(end_date)
            params.extend([limit, offset])

            return pd.read_sql_query(query, conn, params=params)
        except Exception:
            return pd.DataFrame()
        finally:
            self._release_connection(conn)

    def get_stock_data_stats(self, table_name: str) -> Dict:
        """
        获取行情数据统计信息（使用SQL聚合）

        Args:
            table_name: 表名

        Returns:
            Dict: 统计信息
        """
        table_name = self._validate_table_name(table_name)
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "AND column_name IN ('date', 'trade_date')",
                (table_name,),
            )
            row = cur.fetchone()
            if not row:
                return {}
            date_col = row[0]

            cur.execute(
                f"SELECT COUNT(*), MIN({date_col}), MAX({date_col}), "
                f"MIN(close), MAX(close), AVG(volume) FROM {table_name}"
            )
            row = cur.fetchone()
            return {
                "count": row[0],
                "start_date": str(row[1]) if row[1] else None,
                "end_date": str(row[2]) if row[2] else None,
                "min_price": float(row[3]) if row[3] else None,
                "max_price": float(row[4]) if row[4] else None,
                "avg_volume": float(row[5]) if row[5] else None,
            }
        except Exception:
            return {}
        finally:
            self._release_connection(conn)

    def list_tables(self) -> List[str]:
        """
        列出数据库中所有行情分表

        Returns:
            List[str]: 表名列表
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
            return [row[0] for row in cur.fetchall()]
        except Exception:
            return []
        finally:
            self._release_connection(conn)

    def upsert_instrument_basic(self, items: List[Dict], source: str = "auto"):
        """批量 Upsert 标的基本信息

        Args:
            items: 标的列表，每项包含:
                - type: 类型 (stock/etf/index)
                - code: 6 位代码
                - name: 名称
                - market: 市场（可选）
            source: 数据来源标识
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            for item in items:
                cur.execute(
                    """INSERT INTO instrument_basic (instrument_type, code, name, market, source)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (instrument_type, code) DO UPDATE SET
                       name = EXCLUDED.name, market = EXCLUDED.market,
                       source = EXCLUDED.source, updated_at = CURRENT_TIMESTAMP""",
                    (
                        item.get("type", "stock"),
                        item.get("code", ""),
                        item.get("name", ""),
                        item.get("market"),
                        source,
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._release_connection(conn)

    def list_instrument_basic(self, instrument_types: Optional[List[str]] = None,
                              keyword: Optional[str] = None, limit: int = 200,
                              offset: int = 0) -> List[Dict]:
        """查询已入库的标的基本信息

        Args:
            instrument_types: 类型过滤，None 表示不过滤
            keyword: 关键词（按 code/name 模糊匹配）
            limit: 返回条数
            offset: 偏移量

        Returns:
            List[Dict]: 标的列表
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            conditions = []
            params = []

            if instrument_types:
                placeholders = ", ".join(["%s"] * len(instrument_types))
                conditions.append(f"instrument_type IN ({placeholders})")
                params.extend(instrument_types)

            if keyword:
                conditions.append("(code ILIKE %s OR name ILIKE %s)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            params.extend([limit, offset])

            cur.execute(
                f"SELECT instrument_type, code, name, market, source "
                f"FROM instrument_basic {where} ORDER BY code LIMIT %s OFFSET %s",
                params,
            )
            return [
                {"type": r[0], "code": r[1], "name": r[2],
                 "market": r[3], "source": r[4]}
                for r in cur.fetchall()
            ]
        except Exception:
            return []
        finally:
            self._release_connection(conn)

    def get_stock_name(self, stock_code: str) -> Optional[str]:
        """
        根据股票代码获取中文名称

        Args:
            stock_code: 股票代码，如 '000001.SZ'

        Returns:
            str: 股票中文名称，如果未找到返回 None
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT stock_name FROM a_stock_list WHERE stock_code = %s",
                (stock_code,)
            )
            result = cur.fetchone()
            return result[0] if result else None
        except Exception:
            return None
        finally:
            self._release_connection(conn)

    def get_stock_names(self, stock_codes: List[str]) -> Dict[str, str]:
        """
        批量根据股票代码获取中文名称

        Args:
            stock_codes: 股票代码列表

        Returns:
            Dict[str, str]: 股票代码到中文名称的映射
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            placeholders = ", ".join(["%s"] * len(stock_codes))
            cur.execute(
                f"SELECT stock_code, stock_name FROM a_stock_list WHERE stock_code IN ({placeholders})",
                tuple(stock_codes)
            )
            return {r[0]: r[1] for r in cur.fetchall()}
        except Exception:
            return {}
        finally:
            self._release_connection(conn)

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        根据关键词搜索股票（支持代码和名称模糊匹配）

        Args:
            keyword: 搜索关键词
            limit: 返回条数限制

        Returns:
            List[Dict]: 包含 stock_code 和 stock_name 的字典列表
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT stock_code, stock_name FROM a_stock_list "
                "WHERE stock_code ILIKE %s OR stock_name ILIKE %s "
                "ORDER BY stock_code LIMIT %s",
                (f"%{keyword}%", f"%{keyword}%", limit)
            )
            return [{"stock_code": r[0], "stock_name": r[1]} for r in cur.fetchall()]
        except Exception:
            return []
        finally:
            self._release_connection(conn)

    def get_name_from_table(self, table_name: str) -> Optional[str]:
        """
        根据行情数据表名获取中文名称

        Args:
            table_name: 表名，如 'etf_daily_159633'、'stock_daily_000001'、'stock_daily_000001.SZ'

        Returns:
            str: 对应的中文名称，如果未找到返回 None
        """
        conn = self._get_connection()
        try:
            parts = table_name.split('_')
            if len(parts) < 3:
                return None

            code_parts = parts[2:]
            stock_code = '_'.join(code_parts)

            cur = conn.cursor()

            cur.execute(
                "SELECT stock_name FROM a_stock_list WHERE stock_code = %s",
                (stock_code,)
            )
            result = cur.fetchone()

            if result and result[0]:
                return result[0]

            if '.' not in stock_code:
                if len(stock_code) == 6 and stock_code.isdigit():
                    cur.execute(
                        "SELECT stock_name FROM a_stock_list WHERE stock_code = %s OR stock_code = %s",
                        (f"{stock_code}.SZ", f"{stock_code}.SH")
                    )
                    result = cur.fetchone()
                    if result and result[0]:
                        return result[0]

                cur.execute(
                    "SELECT stock_name FROM a_stock_list WHERE stock_code LIKE %s",
                    (f"{stock_code}.%",)
                )
                result = cur.fetchone()
                if result and result[0]:
                    return result[0]

            return None
        except Exception:
            return None
        finally:
            self._release_connection(conn)

    def get_names_from_tables(self, table_names: List[str]) -> Dict[str, str]:
        """
        批量根据行情数据表名获取中文名称

        Args:
            table_names: 表名列表

        Returns:
            Dict[str, str]: 表名到中文名称的映射
        """
        conn = self._get_connection()
        try:
            codes = []
            for table in table_names:
                parts = table.split('_')
                if len(parts) >= 3:
                    code_parts = parts[2:]
                    code = '_'.join(code_parts)
                    codes.append(code)

            cur = conn.cursor()
            code_to_name = {}

            if codes:
                placeholders = ", ".join(["%s"] * len(codes))
                cur.execute(
                    f"SELECT stock_code, stock_name FROM a_stock_list WHERE stock_code IN ({placeholders})",
                    tuple(codes)
                )
                for r in cur.fetchall():
                    if r[1]:
                        code_to_name[r[0]] = r[1]

            missing_codes = [c for c in codes if c not in code_to_name and '.' not in c and len(c) == 6 and c.isdigit()]
            if missing_codes:
                for code in missing_codes:
                    cur.execute(
                        "SELECT stock_name FROM a_stock_list WHERE stock_code = %s OR stock_code = %s",
                        (f"{code}.SZ", f"{code}.SH")
                    )
                    result = cur.fetchone()
                    if result and result[0]:
                        code_to_name[code] = result[0]

            remaining_codes = [c for c in codes if c not in code_to_name and '.' not in c]
            if remaining_codes:
                like_conditions = " OR ".join(["stock_code LIKE %s"] * len(remaining_codes))
                params = [f"{c}.%" for c in remaining_codes]
                cur.execute(
                    f"SELECT stock_code, stock_name FROM a_stock_list WHERE {like_conditions}",
                    params
                )
                for r in cur.fetchall():
                    code_part = r[0].split('.')[0]
                    if code_part in remaining_codes and code_part not in code_to_name and r[1]:
                        code_to_name[code_part] = r[1]

            result = {}
            for table in table_names:
                parts = table.split('_')
                if len(parts) >= 3:
                    code_parts = parts[2:]
                    code = '_'.join(code_parts)
                    result[table] = code_to_name.get(code, None)

            return result
        except Exception:
            return {table: None for table in table_names}
        finally:
            self._release_connection(conn)

    def save_strategy_config(self, config: Dict) -> int:
        """
        保存策略配置

        Args:
            config: 策略配置字典，包含:
                - strategy_name: 策略名称（中文）
                - symbol: 标的代码
                - base_price: 基准价格
                - upper_step: 上涨步长
                - lower_step: 下跌步长
                - upper_count: 上涨格数
                - lower_count: 下跌格数
                - max_position: 最大仓位
                - min_position: 最小仓位
                - initial_cash: 初始资金
                - buy_quantity: 买入数量
                - sell_quantity: 卖出数量

        Returns:
            int: 新创建记录的ID
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO strategy_configs
                   (strategy_name, symbol, base_price, upper_step, lower_step, upper_count, lower_count, max_position, min_position, initial_cash, buy_quantity, sell_quantity)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    config.get("strategy_name", ""),
                    config.get("symbol", ""),
                    config.get("base_price", 0),
                    config.get("upper_step", 0),
                    config.get("lower_step", 0),
                    config.get("upper_count", 0),
                    config.get("lower_count", 0),
                    config.get("max_position", 0),
                    config.get("min_position", 0),
                    config.get("initial_cash", 1000000.0),
                    config.get("buy_quantity", 100),
                    config.get("sell_quantity", 100),
                ),
            )
            config_id = cur.fetchone()[0]
            conn.commit()
            return config_id
        except Exception:
            conn.rollback()
            raise
        finally:
            self._release_connection(conn)

    def get_strategy_configs(self) -> List[Dict]:
        """
        获取所有策略配置

        Returns:
            List[Dict]: 策略配置列表
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM strategy_configs ORDER BY created_at DESC")
            columns = [desc[0] for desc in cur.description]
            result = []
            for row in cur.fetchall():
                config = dict(zip(columns, row))
                if 'initial_cash' in config and config['initial_cash'] is not None:
                    config['initial_cash'] = float(config['initial_cash'])
                if 'max_position' in config and config['max_position'] is not None:
                    config['max_position'] = float(config['max_position'])
                if 'min_position' in config and config['min_position'] is not None:
                    config['min_position'] = float(config['min_position'])
                result.append(config)
            return result
        except Exception:
            return []
        finally:
            self._release_connection(conn)

    def get_strategy_config_by_id(self, config_id: int) -> Optional[Dict]:
        """
        根据 ID 获取策略配置

        Args:
            config_id: 策略配置 ID

        Returns:
            Optional[Dict]: 策略配置字典
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM strategy_configs WHERE id = %s", (config_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
        except Exception:
            return None
        finally:
            self._release_connection(conn)

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
                - strategy_name: 策略名称
                - strategy_type: 策略类型
                - symbol: 标的代码
                - full_report: 完整报告数据
                - chart_data: 图表数据
        """
        import json
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO backtest_results
                   (config_id, strategy_name, strategy_type, symbol, start_date, end_date,
                    initial_cash, final_cash, total_return, annual_return,
                    sharpe_ratio, sortino_ratio, calmar_ratio, max_drawdown,
                    volatility, win_rate, benchmark_return, trade_count, full_report, chart_data)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    config_id,
                    result.get("strategy_name", ""),
                    result.get("strategy_type", "grid"),
                    result.get("symbol", ""),
                    result.get("start_date"),
                    result.get("end_date"),
                    result.get("initial_cash", 1000000),
                    result.get("final_cash", 1000000),
                    result.get("total_return"),
                    result.get("annual_return"),
                    result.get("sharpe_ratio"),
                    result.get("sortino_ratio"),
                    result.get("calmar_ratio"),
                    result.get("max_drawdown"),
                    result.get("volatility"),
                    result.get("win_rate"),
                    result.get("benchmark_return"),
                    result.get("trade_count"),
                    json.dumps(result.get("full_report", {})),
                    json.dumps(result.get("chart_data", {})),
                ),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
        except Exception:
            conn.rollback()
            return None
        finally:
            self._release_connection(conn)

    def get_backtest_results(self, config_id: Optional[int] = None) -> List[Dict]:
        """
        获取回测结果

        Args:
            config_id: 可选的策略配置ID，为 None 则获取所有

        Returns:
            List[Dict]: 回测结果列表
        """
        import json
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            if config_id:
                cur.execute(
                    """SELECT br.*, COALESCE(sc.symbol, br.symbol) as symbol 
                       FROM backtest_results br
                       LEFT JOIN strategy_configs sc ON br.config_id = sc.id
                       WHERE br.config_id = %s ORDER BY br.created_at DESC""",
                    (config_id,),
                )
            else:
                cur.execute(
                    """SELECT br.*, COALESCE(sc.symbol, br.symbol) as symbol 
                       FROM backtest_results br
                       LEFT JOIN strategy_configs sc ON br.config_id = sc.id
                       ORDER BY br.created_at DESC"""
                )
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
            for res in results:
                if res.get("full_report") and isinstance(res["full_report"], str):
                    try:
                        res["full_report"] = json.loads(res["full_report"])
                    except:
                        pass
                if res.get("chart_data") and isinstance(res["chart_data"], str):
                    try:
                        res["chart_data"] = json.loads(res["chart_data"])
                    except:
                        pass
            return results
        except Exception:
            return []
        finally:
            self._release_connection(conn)

    def get_backtest_result_by_id(self, backtest_id: int) -> Optional[Dict]:
        """
        根据ID获取单个回测结果

        Args:
            backtest_id: 回测结果ID

        Returns:
            Dict: 回测结果详细信息
        """
        import json
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT br.*, COALESCE(sc.symbol, br.symbol) as symbol 
                   FROM backtest_results br
                   LEFT JOIN strategy_configs sc ON br.config_id = sc.id
                   WHERE br.id = %s""",
                (backtest_id,),
            )
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                result = dict(zip(columns, row))
                if result.get("full_report"):
                    result["full_report"] = json.loads(result["full_report"])
                if result.get("chart_data"):
                    result["chart_data"] = json.loads(result["chart_data"])
                return result
            return None
        except Exception:
            return None
        finally:
            self._release_connection(conn)

    def delete_backtest_result(self, backtest_id: int) -> bool:
        """
        删除回测结果

        Args:
            backtest_id: 回测结果ID

        Returns:
            bool: 是否删除成功
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM backtest_results WHERE id = %s", (backtest_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            self._release_connection(conn)

    def save_trade_records(self, config_id: int, trades: List[Dict]):
        """
        保存交易记录（批量INSERT）

        Args:
            config_id: 对应的策略配置ID
            trades: 交易记录列表，每条包含:
                - datetime: 交易时间
                - signal: 交易信号 (buy/sell)
                - price: 成交价格
                - amount: 成交数量
                - position: 持仓数量
                - commission: 手续费 (可选)
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            values = [
                (
                    config_id,
                    t["datetime"],
                    t["signal"],
                    t["price"],
                    t["amount"],
                    t["position"],
                    t.get("commission", 0),
                )
                for t in trades
            ]
            psycopg.extras.execute_values(
                cur,
                """INSERT INTO trade_records
                   (config_id, datetime, signal, price, amount, position, commission)
                   VALUES %s""",
                values,
            )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            self._release_connection(conn)

    def get_trade_records(self, config_id: Optional[int] = None) -> List[Dict]:
        """
        获取交易记录

        Args:
            config_id: 可选的策略配置ID，为 None 则获取所有

        Returns:
            List[Dict]: 交易记录列表
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            if config_id:
                cur.execute(
                    "SELECT * FROM trade_records WHERE config_id = %s ORDER BY datetime DESC",
                    (config_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM trade_records ORDER BY datetime DESC")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception:
            return []
        finally:
            self._release_connection(conn)

    def save_market_data(self, symbol: str, data: List[Dict]):
        """
        保存市场数据到 market_data 表

        Args:
            symbol: 交易对符号
            data: 市场数据列表，每条包含 date, open, high, low, close, volume
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            for item in data:
                cur.execute(
                    """INSERT INTO market_data (symbol, date, open, high, low, close, volume)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        symbol,
                        item["date"],
                        item["open"],
                        item["high"],
                        item["low"],
                        item["close"],
                        item["volume"],
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            self._release_connection(conn)

    def export_to_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        将表导出为 DataFrame

        Args:
            table_name: 表名

        Returns:
            pd.DataFrame: 数据帧
        """
        table_name = self._validate_table_name(table_name)
        conn = self._get_connection()
        try:
            return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        except Exception:
            return pd.DataFrame()
        finally:
            self._release_connection(conn)

    def delete_strategy_config(self, config_id: int) -> bool:
        """
        删除策略配置及关联的回测结果和交易记录（事务包裹）

        Args:
            config_id: 策略配置 ID

        Returns:
            bool: 是否成功删除
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM trade_records WHERE config_id = %s", (config_id,))
            cur.execute(
                "DELETE FROM backtest_results WHERE config_id = %s", (config_id,))
            cur.execute(
                "DELETE FROM strategy_configs WHERE id = %s", (config_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            self._release_connection(conn)

    def execute_sql(self, sql: str, params: tuple = None, fetch: bool = False):
        """
        执行SQL语句

        Args:
            sql: SQL语句
            params: 参数元组
            fetch: 是否返回查询结果

        Returns:
            查询结果（如果fetch=True），否则返回None
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            conn.commit()
            if fetch:
                return cur.fetchall()
            return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_connection(conn)


DBManager = Database
DatabaseManager = Database

_global_db_instance = None


def get_db() -> Database:
    """
    获取全局 Database 单例（优化连接池使用）

    Returns:
        Database: 全局 Database 实例
    """
    global _global_db_instance
    if _global_db_instance is None:
        _global_db_instance = Database()
    return _global_db_instance
