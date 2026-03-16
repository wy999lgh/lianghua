# AI量化网格交易系统 (AI-Quant-Grid-Trading)

这是一个基于Python的网格交易量化策略系统，集成了数据获取、策略回测、实盘模拟和Web可视化界面。

## 项目结构

```
AI量化999/
├── data/                   # 数据存储目录 (数据库、CSV文件)
│   ├── grid_trading_system.db  # 策略配置与交易记录数据库
│   └── stock_data.db           # 历史行情数据库
├── grid_trading/           # 核心代码包
│   ├── backtest/           # 回测引擎
│   ├── data/               # 数据处理模块
│   │   ├── api.py          # DataFetcher API
│   │   ├── cleaner.py      # 数据清洗
│   │   ├── config.py       # 配置
│   │   ├── fetcher.py      # AKShare数据获取
│   │   ├── storage.py      # 数据库存储
│   │   └── legacy_loader.py # 旧版CSV数据加载器
│   ├── db/                 # 数据库管理
│   ├── strategy/           # 策略逻辑
│   └── visualization/      # 可视化模块
├── web/                    # Web服务 (Backend & Frontend)
│   ├── backend/            # FastAPI后端
│   └── frontend/           # Vue前端
├── scripts/                # 运行脚本
│   ├── run_api.py          # 启动后端API服务
│   ├── run_frontend.bat    # 启动前端开发服务器
│   ├── setup_venv.bat      # 一键环境配置脚本
│   └── legacy/             # 旧版脚本归档
├── .trae/                  # Trae IDE配置与文档
└── requirements.txt        # 项目依赖列表
```

## 环境配置

本项目提供了自动化环境配置脚本，请按以下步骤操作：

1.  **安装 Python**: 确保系统已安装 Python 3.8 或更高版本。
2.  **运行配置脚本**:
    双击运行 `scripts/setup_venv.bat`。
    该脚本会自动：
    *   创建虚拟环境 (`.venv`)
    *   升级 pip
    *   安装所有依赖 (`requirements.txt`)

## 快速开始

### 1. 启动后端服务

在虚拟环境中运行：
```bash
python scripts/run_api.py
```
或者在激活虚拟环境后直接运行脚本。API服务默认运行在 `http://localhost:8000`。

### 2. 启动前端界面

双击运行 `scripts/run_frontend.bat`。
前端页面将自动打开（默认 `http://localhost:5173`）。

### 3. 数据获取

使用新的 `DataFetcher` 模块获取数据：

```python
from grid_trading.data import DataFetcher

# 初始化
fetcher = DataFetcher()

# 获取数据 (会自动保存到 data/stock_data.db)
fetcher.update_stock("600519", "20230101", "20231231")
```

## 核心模块说明

### DataFetcher (数据获取)
负责从 AKShare 获取股票、ETF、指数数据，并进行标准化清洗和本地存储。支持增量更新和断点续传。代码位于 `grid_trading/data/`。

### GridStrategy (网格策略)
实现了经典的网格交易逻辑，支持等差网格和等比网格，具备动态仓位管理和风险控制功能。代码位于 `grid_trading/strategy/grid_strategy.py`。

### Database (数据库)
使用 SQLite 存储所有数据：
*   `market_data` (或 `stock_{symbol}`): 行情数据
*   `strategy_configs`: 策略参数配置
*   `trade_records`: 交易流水
*   `backtest_results`: 回测绩效报告

## 开发指南

*   **添加新依赖**: 请使用 `pip install <package>` 后运行 `pip freeze > requirements.txt` 更新依赖列表。
*   **运行测试**: 使用 `pytest` 运行 `tests/` 目录下的测试用例。

## 注意事项

*   本项目仅供学习和研究使用，不构成投资建议。
*   实盘交易存在风险，请谨慎使用。
