# PostgreSQL 数据字典 (Data Dictionary)

本项目严格使用 PostgreSQL 17 作为唯一后端数据库。数据库表分为两大类：**系统核心表**（用于存储策略、回测和交易配置）与**动态行情表**（每个证券标的独立建表）。

以下是当前数据库中的表结构、命名规范及字段定义详细说明。

---

## 一、 系统核心表

### 1. `instrument_basic` (标的基础信息表)
用于存储证券标的的基础元数据（类型、代码、名称），为前端“标的选择”提供统一数据源。

| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `instrument_type` | `text` | `PRIMARY KEY (instrument_type, code)` | 标的类型（`stock`/`etf`/`index`） |
| `code` | `text` | `PRIMARY KEY (instrument_type, code)` | 证券代码（6 位） |
| `name` | `text` | `NOT NULL DEFAULT ''` | 证券名称 |
| `market` | `text` | - | 市场（可选） |
| `source` | `text` | - | 数据来源（可选，如 `akshare`/`index_basic`） |
| `updated_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 最近更新时间 |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 创建时间 |

### 2. `strategy_configs` (策略配置表)
用于存储网格等交易策略的初始化参数与配置信息。

| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `bigint` (BIGSERIAL) | `PRIMARY KEY` | 策略配置唯一ID |
| `symbol` | `text` | `NOT NULL` | 交易标的代码 (如 sh000300) |
| `base_price` | `double precision` | `NOT NULL` | 网格基准价格 |
| `upper_step` | `double precision` | `NOT NULL` | 上涨网格步长/比例 |
| `lower_step` | `double precision` | `NOT NULL` | 下跌网格步长/比例 |
| `upper_count` | `integer` | `NOT NULL` | 上涨方向网格数量 |
| `lower_count` | `integer` | `NOT NULL` | 下跌方向网格数量 |
| `max_position` | `double precision` | `NOT NULL` | 最大允许持仓量 |
| `min_position` | `double precision` | `NOT NULL` | 最小允许持仓量 |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 配置创建时间 |

### 3. `backtest_results` (回测结果表)
存储单次策略回测运行后的整体绩效评估指标。

| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `bigint` (BIGSERIAL) | `PRIMARY KEY` | 回测结果唯一ID |
| `config_id` | `bigint` | `NOT NULL` | 关联的策略配置ID |
| `start_date` | `text` | - | 回测开始日期 |
| `end_date` | `text` | - | 回测结束日期 |
| `initial_capital` | `double precision` | - | 初始资金 |
| `final_capital` | `double precision` | - | 期末资金 |
| `total_return` | `double precision` | - | 总收益率 |
| `annual_return` | `double precision` | - | 年化收益率 |
| `sharpe_ratio` | `double precision` | - | 夏普比率 |
| `max_drawdown` | `double precision` | - | 最大回撤率 |
| `trade_count` | `integer` | - | 交易次数 |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 回测运行时间 |

### 4. `trade_records` (交易记录表)
记录策略回测或实盘过程中触发的每一笔买卖操作明细。

| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `bigint` (BIGSERIAL) | `PRIMARY KEY` | 交易记录唯一ID |
| `config_id` | `bigint` | `NOT NULL` | 关联的策略配置ID |
| `datetime` | `text` | `NOT NULL` | 成交时间 |
| `signal` | `text` | `NOT NULL` | 交易信号类型 (buy/sell) |
| `price` | `double precision` | `NOT NULL` | 成交价格 |
| `amount` | `double precision` | `NOT NULL` | 成交数量 (绝对值) |
| `position` | `double precision` | `NOT NULL` | 成交后的当前持仓量 |
| `commission` | `double precision` | `DEFAULT 0` | 交易手续费 |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 记录写入时间 |

### 5. `market_data` (行情数据摘要表)
旧版/通用格式的行情汇总表（当前系统主要依赖分表策略）。

| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `id` | `bigint` (BIGSERIAL) | `PRIMARY KEY` | 记录唯一ID |
| `symbol` | `text` | - | 证券代码 |
| `date` | `text` | - | 交易日期 |
| `open` | `double precision` | - | 开盘价 |
| `high` | `double precision` | - | 最高价 |
| `low` | `double precision` | - | 最低价 |
| `close` | `double precision` | - | 收盘价 |
| `volume` | `double precision` | - | 成交量 |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 数据更新时间 |

---

## 二、 动态行情表 (分表)

为了提升查询性能，系统采用**一标的一表**的设计模式。表名根据标的类型自动生成，包含以下几类前缀：
- **股票**: `stock_daily_{代码}` (如 `stock_daily_000001`)
- **指数**: `index_daily_{代码}` (如 `index_daily_000300`)
- **ETF**: `etf_daily_{代码}` (如 `etf_daily_510300`)

所有动态行情表的结构保持完全一致，以 `index_daily_000300` 为例说明：

### 示例: `index_daily_000300` / `stock_daily_000001`
| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `trade_date` (或 `date`) | `date` | `NOT NULL UNIQUE` | 交易日期 (唯一键) |
| `open` | `numeric` | - | 开盘价 |
| `high` | `numeric` | - | 最高价 |
| `low` | `numeric` | - | 最低价 |
| `close` | `numeric` | - | 收盘价 |
| `volume` | `bigint` | - | 成交量 (手/股) |
| `amount` | `numeric` | - | 成交额 (元) |
| `change` | `numeric` | - | 涨跌额 (可选) |
| `pct_chg` | `numeric` | - | 涨跌幅 % (可选) |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 记录写入时间 |

> **注意：** 
> 1. 在通过代码 `Database.save_data()` 插入新数据时，系统使用了 `ON CONFLICT (date) DO UPDATE` 机制（Upsert），以确保每日行情数据的唯一性。
> 2. 由于历史导入工具的差异，部分表的日期列名为 `date`，部分为 `trade_date`。Python 层的 `get_data` 接口已做了智能兼容，对外统一返回 `date`。

### 实表示例: `etf_daily_159633` (ETF 日线行情)

- 表类型：动态行情表（分表）
- 命名规则：`etf_daily_{代码}`，本表示例为 `etf_daily_159633`
- 数据概况：共 `887` 行；日期范围 `2022-08-04` ~ `2026-04-03`
- 索引/唯一性：`trade_date` 为唯一索引（`etf_daily_159633_pkey`）

| 字段名 | 数据类型 | 约束/默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `trade_date` | `date` | `NOT NULL UNIQUE` | 交易日期（唯一键） |
| `open` | `numeric` | `NOT NULL` | 开盘价 |
| `high` | `numeric` | `NOT NULL` | 最高价 |
| `low` | `numeric` | `NOT NULL` | 最低价 |
| `close` | `numeric` | `NOT NULL` | 收盘价 |
| `volume` | `bigint` | `NOT NULL` | 成交量（手/股） |
| `amount` | `numeric` | `NOT NULL` | 成交额（元） |
| `created_at` | `timestamp` | `DEFAULT CURRENT_TIMESTAMP` | 记录写入时间 |
