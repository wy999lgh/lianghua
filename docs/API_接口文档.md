# AI量化交易系统 API 接口文档

> 📅 最后更新：2026-04-26  
> 📌 版本：v1.0.0  
> 🔗 在线文档：http://localhost:8000/docs

---

## 目录

1. [系统概览](#系统概览)
2. [接口规范](#接口规范)
3. [系统模块](#系统模块)
4. [数据管理模块](#数据管理模块)
5. [策略配置模块](#策略配置模块)
6. [回测模块](#回测模块)
7. [前端调用说明](#前端调用说明)
8. [错误码说明](#错误码说明)

---

## 系统概览

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | Python 异步 Web 框架 |
| 数据库 | PostgreSQL 17 | 关系型数据库 |
| 数据验证 | Pydantic | 请求/响应数据模型 |
| 前端框架 | Vue 3.5 | 前端 UI 框架 |
| HTTP 客户端 | Axios 1.7 | 前端 HTTP 请求库 |
| API 文档 | Swagger UI | 自动生成在线文档 |

### 基础路径

```
http://localhost:8000
```

### 接口分组

| 标签 | 路由前缀 | 说明 |
|------|----------|------|
| 系统 | `/` | 系统级接口 |
| 数据管理 | `/data/` | 行情数据与标的管理 |
| 策略配置 | `/strategies/` | 策略参数配置 |
| 回测 | `/backtest/` | 回测执行与结果 |

---

## 接口规范

### 请求格式

所有 POST/PUT 请求使用 JSON 格式：

```
Content-Type: application/json
```

### 响应格式

统一使用 JSON 格式响应：

```json
{
  "status": "success",
  "data": {},
  "message": "操作成功"
}
```

### 日期格式

所有日期字段使用 `YYYY-MM-DD` 格式，例如：`2026-04-26`

---

## 系统模块

**路由前缀：** `/api/`  
**文件位置：** `api/routers/system.py`

### 1. 根路径

**功能说明：** 返回 API 基本信息

**请求方式：** `GET /api/`

**响应示例：**

```json
{
  "message": "网格交易量化策略系统API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 2. 健康检查

**功能说明：** 检查系统健康状态

**请求方式：** `GET /api/health`

**响应示例：**

```json
{
  "status": "healthy"
}
```

---

## 数据管理模块

**路由前缀：** `/data/`  
**文件位置：** `api/routers/data.py`

### 1. 获取可用标的代码列表

**功能说明：** 基于动态行情分表表名解析，返回当前数据库中已有行情数据的标的代码列表

**请求方式：** `GET /data/symbols`

**响应示例：**

```json
{
  "symbols": ["159633", "000001", "600519", "000858"]
}
```

### 4. 获取标的详细信息列表 ✨ 新增

**功能说明：** 获取数据库中所有标的的详细信息（类型、代码、名称、数据表名）

**请求方式：** `GET /data/symbols/list`

**查询参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 否 | null | 标的类型筛选 (stock/etf/index)，多个类型用逗号分隔 |
| keyword | string | 否 | null | 搜索关键词，按代码或名称模糊匹配 |

**请求示例：**

```
GET /data/symbols/list?type=stock,etf&keyword=159
```

### 5. 同步标的基础信息 ✨ 新增

**功能说明：** 将本库已存在行情分表对应的标的代码，同步为可供前端选择的“类型/代码/名称”列表（写入 `instrument_basic`）

**请求方式：** `POST /data/symbols/sync`

**查询参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 否 | null | 同步类型 (stock/etf/index)，多个类型用逗号分隔 |

**响应示例：**

```json
{
  "count": 2,
  "data": [
    {
      "code": "000001",
      "name": "平安银行",
      "type": "stock",
      "table_name": "stock_daily_000001"
    },
    {
      "code": "159633",
      "name": "科创50ETF",
      "type": "etf",
      "table_name": "etf_daily_159633"
    }
  ]
}
```

**标的类型说明：**

| type | 说明 | 前缀 |
|------|------|------|
| stock | 股票 | stock_daily_* |
| etf | ETF | etf_daily_* |
| index | 指数 | index_daily_* |

### 5. 获取历史数据（路径参数）

**功能说明：** 通过路径参数获取指定标的的历史数据（简化版）

**请求方式：** `GET /api/data/data/history/{symbol}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 标的代码，支持路径格式 |

**响应示例：**

```json
{
  "symbol": "159633",
  "data": [
    {
      "date": "2024-01-01",
      "open": 1.05,
      "high": 1.10,
      "low": 1.03,
      "close": 1.08,
      "volume": 1234567
    }
  ]
}
```

### 6. 获取股票数据统计信息

**功能说明：** 获取指定标的的统计数据（记录数、日期范围、价格范围等）

**请求方式：** `GET /api/data/stock-data/stats/{symbol}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 标的代码 |

**响应示例：**

```json
{
  "symbol": "159633",
  "table_name": "stock_data_159633",
  "record_count": 245,
  "date_range": {
    "min": "2024-01-01",
    "max": "2024-12-31"
  },
  "price_range": {
    "min": 0.85,
    "max": 1.25
  }
}
```

### 7. 获取 EMA 指标数据

**功能说明：** 计算并返回指定周期的 EMA 指标数据，包含方向判断和颜色信号

**请求方式：** `GET /api/data/ema-data`

**查询参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 是 | - | 标的代码 |
| period | int | 否 | 20 | EMA 周期 |
| limit | int | 否 | 100 | 返回数据条数 |

**响应示例：**

```json
{
  "symbol": "159633",
  "period": 20,
  "count": 100,
  "data": [
    {
      "time": "2024-01-15",
      "value": 1.025,
      "direction": "up",
      "color": "#26a69a"
    },
    {
      "time": "2024-01-16",
      "value": 1.018,
      "direction": "down",
      "color": "#ef5350"
    }
  ]
}
```

**方向说明：**

| direction | color | 说明 |
|-----------|-------|------|
| `up` | `#26a69a` (绿色) | EMA 上升 |
| `down` | `#ef5350` (红色) | EMA 下降 |
| `flat` | `#888888` (灰色) | EMA 持平 |

---

## 策略配置模块

**路由前缀：** `/api/strategies/`  
**文件位置：** `api/routers/strategies.py`

### 1. 创建策略配置

**功能说明：** 保存网格交易策略参数配置到数据库

**请求方式：** `POST /api/strategies/config`

**请求参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| symbol | string | 否 | null | 标的代码 |
| base_price | float | 是 | - | 网格基准价格 |
| upper_step | float | 是 | - | 上步长百分比 |
| lower_step | float | 是 | - | 下步长百分比 |
| upper_count | int | 否 | 100 | 上格数量 |
| lower_count | int | 否 | 100 | 下格数量 |
| max_position | float | 否 | null | 最大持仓限制 |
| min_position | float | 否 | null | 最小持仓限制 |
| initial_cash | float | 否 | 1000000.0 | 初始资金 |
| buy_quantity | float | 否 | null | 买入数量 |
| sell_quantity | float | 否 | null | 卖出数量 |

**请求示例：**

```json
{
  "symbol": "159633",
  "base_price": 1.0,
  "upper_step": 1.0,
  "lower_step": 1.0,
  "upper_count": 100,
  "lower_count": 100,
  "initial_cash": 1000000,
  "buy_quantity": 1000,
  "sell_quantity": 1000
}
```

**响应示例：**

```json
{
  "config_id": 123
}
```

### 2. 列出策略配置

**功能说明：** 获取所有已保存的策略配置列表

**请求方式：** `GET /api/strategies/configs`

**响应示例：**

```json
{
  "items": [
    {
      "id": 1,
      "symbol": "159633",
      "base_price": 1.0,
      "upper_step": 1.0,
      "lower_step": 1.0,
      "upper_count": 100,
      "lower_count": 100,
      "max_position": 100000000.0,
      "min_position": 0.0,
      "initial_cash": 1000000.0,
      "buy_quantity": 1000,
      "sell_quantity": 1000
    }
  ]
}
```

---

## 回测模块

**路由前缀：** `/api/backtest/`  
**文件位置：** `api/routers/backtest.py`

### 1. 执行回测

**功能说明：** 运行网格交易策略回测，返回回测 ID

**请求方式：** `POST /api/backtest/run`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| config | object | 是 | 策略配置对象 |
| start_date | string | 否 | 回测开始日期 |
| end_date | string | 否 | 回测结束日期 |

**config 对象参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 标的代码 |
| base_price | float | 是 | 网格基准价格 |
| upper_step | float | 是 | 上步长百分比 |
| lower_step | float | 是 | 下步长百分比 |
| upper_count | int | 是 | 上格数量 |
| lower_count | int | 是 | 下格数量 |
| initial_cash | float | 否 | 初始资金 |
| buy_quantity | float | 否 | 买入数量 |
| sell_quantity | float | 否 | 卖出数量 |

**请求示例：**

```json
{
  "config": {
    "symbol": "159633",
    "base_price": 1.0,
    "upper_step": 1.0,
    "lower_step": 1.0,
    "upper_count": 100,
    "lower_count": 100,
    "initial_cash": 1000000,
    "buy_quantity": 1000,
    "sell_quantity": 1000
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**响应示例：**

```json
{
  "status": "success",
  "backtest_id": "BT_159633_20260426_120000",
  "message": "回测执行成功"
}
```

### 2. 获取回测结果

**功能说明：** 根据回测 ID 获取完整的回测结果

**请求方式：** `GET /api/backtest/results/{backtest_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| backtest_id | string | 是 | 回测唯一标识符 |

**响应示例：**

```json
{
  "backtest_id": "BT_159633_20260426_120000",
  "total_return": 15.23,
  "max_drawdown": -5.67,
  "sharpe_ratio": 1.85,
  "trades": [
    {
      "datetime": "2024-01-15 09:30:00",
      "signal": "buy",
      "price": 0.99,
      "amount": 1000,
      "position": 1000,
      "commission": 9.9
    },
    {
      "datetime": "2024-01-16 14:30:00",
      "signal": "sell",
      "price": 1.01,
      "amount": 1000,
      "position": 0,
      "commission": 10.1
    }
  ],
  "position_details": [
    {
      "date": "2024-01-15",
      "position": 1000,
      "price": 0.99,
      "value": 990
    }
  ],
  "equity_curve": [
    {
      "date": "2024-01-15",
      "equity": 1000000,
      "return": 0.0
    }
  ]
}
```

---

## 因子管理模块

**路由前缀：** `/api/factors/`  
**文件位置：** `api/routers/factors.py`

### 1. 获取因子模板列表

**功能说明：** 获取所有可用的因子计算模板

**请求方式：** `GET /api/factors/templates`

**响应示例：**

```json
{
  "code": 200,
  "data": {
    "ma5": {
      "name": "5日移动平均",
      "description": "简单移动平均线",
      "params": {"period": 5}
    },
    "ma20": {
      "name": "20日移动平均",
      "description": "简单移动平均线",
      "params": {"period": 20}
    },
    "macd": {
      "name": "MACD指标",
      "description": "移动平均收敛发散指标",
      "params": {"fast": 12, "slow": 26, "signal": 9}
    }
  }
}
```

### 2. 获取处理方法选项

**功能说明：** 获取因子预处理的方法选项

**请求方式：** `GET /api/factors/methods`

**响应示例：**

```json
{
  "code": 200,
  "data": {
    "missing": {
      "ffill": "前向填充",
      "mean": "均值填充",
      "median": "中位数填充"
    },
    "outlier": {
      "mad": "MAD法(3倍中位数绝对偏差)",
      "iqr": "IQR法(1.5倍四分位距)",
      "percentile": "百分位数法(1%-99%)"
    },
    "normalize": {
      "zscore": "Z-score标准化",
      "minmax": "Min-Max缩放",
      "rank": "排名标准化"
    }
  }
}
```

### 3. 计算因子

**功能说明：** 计算指定因子并返回处理后的数据

**请求方式：** `POST /api/factors/compute`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 标的代码 |
| start_date | string | 是 | 开始日期 YYYY-MM-DD |
| end_date | string | 是 | 结束日期 YYYY-MM-DD |
| factors | string[] | 是 | 要计算的因子列表 |
| params | object | 否 | 预处理参数 |

**params 对象参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| missing_method | string | 否 | 缺失值处理方法 (ffill/mean/median) |
| outlier_method | string | 否 | 去极值方法 (mad/iqr/percentile) |
| normalize_method | string | 否 | 标准化方法 (zscore/minmax/rank) |

**请求示例：**

```json
{
  "symbol": "000001",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "factors": ["ma5", "ma20", "macd"],
  "params": {
    "missing_method": "ffill",
    "outlier_method": "mad",
    "normalize_method": "zscore"
  }
}
```

**响应示例：**

```json
{
  "code": 200,
  "data": {
    "symbol": "000001",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "factors": {
      "ma5": {
        "values": [15.2, 15.5, 15.8],
        "dates": ["2024-01-02", "2024-01-03", "2024-01-04"],
        "stats": {
          "mean": 15.5,
          "std": 0.8,
          "min": 14.2,
          "max": 17.1
        }
      }
    }
  }
}
```

### 4. 获取因子列表

**功能说明：** 获取所有已配置的因子列表

**请求方式：** `GET /api/factors/list`

**响应示例：**

```json
{
  "code": 200,
  "data": {
    "factors": [
      {"name": "ma5", "display_name": "5日均线", "category": "趋势", "enabled": true},
      {"name": "ma20", "display_name": "20日均线", "category": "趋势", "enabled": true},
      {"name": "macd", "display_name": "MACD", "category": "动量", "enabled": true}
    ]
  }
}
```

### 5. 保存因子配置

**功能说明：** 保存因子处理配置

**请求方式：** `POST /api/factors/config`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| factor_name | string | 是 | 因子名称 |
| description | string | 否 | 因子描述 |
| missing_method | string | 否 | 缺失值处理方法 |
| outlier_method | string | 否 | 去极值方法 |
| normalize_method | string | 否 | 标准化方法 |
| enabled | boolean | 否 | 是否启用 |

**请求示例：**

```json
{
  "factor_name": "ma20",
  "description": "20日移动平均线",
  "missing_method": "ffill",
  "outlier_method": "mad",
  "normalize_method": "zscore",
  "enabled": true
}
```

### 6. 预览因子数据

**功能说明：** 预览因子最近N天的数据

**请求方式：** `GET /api/factors/preview`

**查询参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| symbol | string | 是 | 标的代码 |
| factor_name | string | 是 | 因子名称 |
| days | int | 否 | 预览天数，默认30 |

**响应示例：**

```json
{
  "code": 200,
  "data": [
    {"date": "2024-12-01", "close": 15.2, "ma20": 15.0},
    {"date": "2024-12-02", "close": 15.5, "ma20": 15.1}
  ]
}
```

---

## 前端调用说明

**文件位置：** `frontend/src/services/api.js`

### Axios 配置

```javascript
const api = axios.create({
  baseURL: '', // 使用相对路径，通过代理转发到后端
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})
```

### 代理配置

前端通过 Vite 代理将请求转发到后端：

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### 通用回测组件调用示例

**文件位置：** `frontend/src/components/BacktestUniversal.vue`

#### 调用数据接口

```javascript
// 获取可用标的列表（基础版）
async loadAvailableSymbols() {
  const resp = await this.$axios.get('/api/data/symbols')
  this.availableSymbols = resp?.data?.symbols || []
}

// 获取标的详细信息列表（推荐）
async loadSymbolList() {
  const resp = await this.$axios.get('/api/data/symbols/list', {
    params: {
      type: 'stock,etf',  // 可选：类型筛选
      keyword: '159'      // 可选：关键词搜索
    }
  })
  this.symbolList = resp?.data?.data || []
}

// 获取股票数据
async loadStockData() {
  const resp = await this.$axios.post('/api/data/stock-data', {
    symbol: this.form.symbol,
    start_date: this.form.start_date,
    end_date: this.form.end_date,
  })
  this.stockData = resp?.data?.data || []
}
```

#### 使用 SymbolSelector 组件（推荐）

```vue
<template>
  <el-form-item label="回测标的">
    <SymbolSelector 
      v-model="form.symbol" 
      :type-filter="['stock', 'etf']"
      @change="handleSymbolChange"
    />
  </el-form-item>
</template>

<script>
import SymbolSelector from '@/components/SymbolSelector.vue'

export default {
  components: {
    SymbolSelector
  },
  data() {
    return {
      form: {
        symbol: ''
      }
    }
  },
  methods: {
    handleSymbolChange(symbolInfo) {
      console.log('选中标的:', symbolInfo)
      // symbolInfo 包含: { code, name, type, table_name }
    }
  }
}
</script>
```

#### 调用策略配置接口

```javascript
// 保存策略配置
async saveStrategyConfig() {
  const payload = {
    symbol: this.form.symbol,
    base_price: this.form.base_price,
    upper_step: this.form.upper_step,
    lower_step: this.form.lower_step,
    upper_count: this.form.upper_count,
    lower_count: this.form.lower_count,
    initial_cash: this.form.initial_cash,
    buy_quantity: this.form.buy_quantity,
    sell_quantity: this.form.sell_quantity,
  }
  const resp = await this.$axios.post('/api/strategies/config', payload)
  this.selectedConfigId = resp?.data?.config_id
}

// 获取策略配置列表
async loadStrategyConfigs() {
  const resp = await this.$axios.get('/api/strategies/configs')
  this.strategyConfigs = resp?.data?.items || []
}
```

#### 调用回测接口

```javascript
// 执行回测
async runBacktest() {
  const payload = {
    config: {
      symbol: this.form.symbol,
      base_price: this.form.base_price,
      upper_step: this.form.upper_step,
      lower_step: this.form.lower_step,
      upper_count: this.form.upper_count,
      lower_count: this.form.lower_count,
      initial_cash: this.form.initial_cash,
      buy_quantity: this.form.buy_quantity,
      sell_quantity: this.form.sell_quantity,
    },
    start_date: this.form.start_date,
    end_date: this.form.end_date,
  }
  
  // 执行回测
  const runResp = await this.$axios.post('/api/backtest/run', payload)
  const backtestId = runResp?.data?.backtest_id
  
  // 获取回测结果
  const resResp = await this.$axios.get(`/api/backtest/results/${backtestId}`)
  this.result = resResp?.data
}
```

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| 标的代码不存在 | 数据库中无该标的的历史数据 | 提示用户选择有效标的 |
| 日期范围无效 | 结束日期早于开始日期 | 提示用户检查日期 |
| 回测执行失败 | 回测引擎内部错误 | 显示详细错误信息 |
| 策略配置保存失败 | 数据库写入错误 | 提示用户重试 |

---

## 附录

### A. 数据模型定义

所有 Pydantic 模型定义位于 `api/schemas.py`：

| 模型名 | 说明 |
|--------|------|
| DataFetchRequest | 数据获取请求 |
| DataFetchResponse | 数据获取响应 |
| EMADataItem | EMA 数据项 |
| EMADataResponse | EMA 数据响应 |
| StockDataItem | 股票数据项 |
| StockDataResponse | 股票数据响应 |
| StrategyConfig | 策略配置 |
| StrategyStatus | 策略状态 |
| BacktestRequest | 回测请求 |
| BacktestResponse | 回测响应 |
| BacktestResult | 回测结果 |

### B. 相关文件索引

| 文件 | 说明 |
|------|------|
| `api/app.py` | API 路由注册中心 |
| `api/schemas.py` | Pydantic 数据模型 |
| `api/routers/system.py` | 系统接口 |
| `api/routers/data.py` | 数据管理接口 |
| `api/routers/strategies.py` | 策略配置接口 |
| `api/routers/backtest.py` | 回测接口 |
| `frontend/src/services/api.js` | 前端 Axios 配置 |
| `frontend/src/components/BacktestUniversal.vue` | 通用回测组件 |
| `frontend/vite.config.js` | Vite 代理配置 |

### C. 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-04-26 | v1.0.0 | 初始版本，完成前后端接口文档 |

---

> 📝 **维护说明：** 本文档由 AI 自动生成，每次接口变更需同步更新本文档。
> 🔗 **在线调试：** 启动后端后访问 http://localhost:8000/docs 进行在线测试。
