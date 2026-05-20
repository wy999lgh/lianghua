# 指数日线数据分表设计文档

## 设计概述

采用**按指数代码分表**策略，每个指数独立一张表，表名格式：`index_daily_{指数代码}`

## 设计理由

### 分表优势
1. **查询性能提升**：单表数据量减少，索引更高效
2. **维护便利**：单个指数数据可独立备份、清理
3. **并发优化**：不同指数数据操作互不干扰
4. **扩展性强**：新增指数只需创建新表

### 适用场景
- 单指数历史数据量大（>100万条）
- 多指数并行分析需求
- 需要按指数独立管理数据生命周期

---

## 表结构

### 主表：index_basic（保持不变）
```sql
CREATE TABLE index_basic (
    index_code VARCHAR(10) PRIMARY KEY,
    index_name VARCHAR(50) NOT NULL,
    market VARCHAR(10) NOT NULL,
    period VARCHAR(10) NOT NULL,
    adjust_type VARCHAR(10) NOT NULL,
    list_date DATE,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 分表：index_daily_{code}
```sql
-- 示例：上证指数 999999
CREATE TABLE index_daily_999999 (
    trade_date DATE PRIMARY KEY,
    open NUMERIC(10,2) NOT NULL,
    high NUMERIC(10,2) NOT NULL,
    low NUMERIC(10,2) NOT NULL,
    close NUMERIC(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    amount NUMERIC(20,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 注释
COMMENT ON TABLE index_daily_999999 IS '上证指数 999999 日线数据';
COMMENT ON COLUMN index_daily_999999.trade_date IS '交易日期';
COMMENT ON COLUMN index_daily_999999.open IS '开盘价';
COMMENT ON COLUMN index_daily_999999.high IS '最高价';
COMMENT ON COLUMN index_daily_999999.low IS '最低价';
COMMENT ON COLUMN index_daily_999999.close IS '收盘价';
COMMENT ON COLUMN index_daily_999999.volume IS '成交量';
COMMENT ON COLUMN index_daily_999999.amount IS '成交额';
```

---

## 索引设计

```sql
-- 主键索引（自动创建）
-- trade_date 作为主键

-- 可选：按日期范围查询优化
CREATE INDEX idx_index_daily_999999_date_range 
ON index_daily_999999(trade_date DESC);
```

---

## 数据迁移脚本

```sql
-- 从旧表迁移数据到新分表
INSERT INTO index_daily_999999 (trade_date, open, high, low, close, volume, amount, created_at)
SELECT trade_date, open, high, low, close, volume, amount, created_at
FROM index_daily
WHERE index_code = '999999'
ON CONFLICT (trade_date) DO NOTHING;
```

---

## Python 动态建表脚本

```python
import psycopg2

def create_index_daily_table(conn, index_code, index_name):
    """
    创建指数日线数据分表
    
    参数:
        conn: 数据库连接
        index_code: 指数代码，如 '999999'
        index_name: 指数名称，如 '上证指数'
    """
    table_name = f"index_daily_{index_code}"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        trade_date DATE PRIMARY KEY,
        open NUMERIC(10,2) NOT NULL,
        high NUMERIC(10,2) NOT NULL,
        low NUMERIC(10,2) NOT NULL,
        close NUMERIC(10,2) NOT NULL,
        volume BIGINT NOT NULL,
        amount NUMERIC(20,2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    COMMENT ON TABLE {table_name} IS '{index_name} {index_code} 日线数据';
    """
    
    cur = conn.cursor()
    cur.execute(create_sql)
    conn.commit()
    cur.close()
    
    print(f"表 {table_name} 创建成功")
```

---

## 查询示例

### 查询单指数数据
```sql
-- 查询上证指数最新10条数据
SELECT * FROM index_daily_999999 
ORDER BY trade_date DESC 
LIMIT 10;
```

### 动态查询（存储过程）
```sql
-- 根据指数代码动态查询
CREATE OR REPLACE FUNCTION get_index_daily(p_index_code VARCHAR, p_limit INT DEFAULT 10)
RETURNS TABLE (
    trade_date DATE,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    amount NUMERIC
) AS $$
BEGIN
    RETURN QUERY EXECUTE format(
        'SELECT trade_date, open, high, low, close, volume, amount 
         FROM index_daily_%s 
         ORDER BY trade_date DESC 
         LIMIT %s',
        p_index_code, p_limit
    );
END;
$$ LANGUAGE plpgsql;

-- 使用
SELECT * FROM get_index_daily('999999', 10);
```

---

## 表清单

| 表名 | 说明 | 数据量 |
|------|------|--------|
| index_basic | 指数基础信息 | 1条 |
| index_daily_999999 | 上证指数日线 | 6,599条 |

---

## 注意事项

1. **表名规范**：`index_daily_{指数代码}`，代码不含特殊字符
2. **主键设计**：分表使用 `trade_date` 作为主键，无需复合主键
3. **外键关系**：通过 index_basic 表维护元数据关系
4. **备份策略**：可按单表备份，灵活性更高
