# 股票基本信息功能文档

## 概述

股票基本信息功能用于获取和存储股票的基本资料，包括：
- 股票代码和名称
- 所属行业
- 上市日期
- 总股本和流通股本
- 总市值和流通市值

## 数据来源

支持多数据源自动故障切换：

1. **akshare_em (东方财富)** - 主数据源
   - 数据最全：名称、行业、市值、股本等
   - 接口: `stock_individual_info_em`

2. **baostock (证券宝)** - 备选数据源
   - 提供：名称、上市日期
   - 需要登录

## 数据库表结构

### stock_basic_info 表

```sql
CREATE TABLE stock_basic_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,       -- 股票代码
    name TEXT,                       -- 股票名称
    industry TEXT,                   -- 所属行业
    list_date TEXT,                  -- 上市日期 (YYYYMMDD)
    total_shares REAL,               -- 总股本
    float_shares REAL,               -- 流通股本
    total_mv REAL,                   -- 总市值
    circ_mv REAL,                    -- 流通市值
    data_source TEXT,                -- 数据来源
    updated_at DATETIME,             -- 更新时间
    created_at DATETIME              -- 创建时间
);
```

## 使用方法

### 命令行工具 (cron.py)

```bash
# 正常获取数据（会自动更新股票基本信息）
python cron.py --fetch-only

# 跳过股票基本信息更新
python cron.py --fetch-only --skip-stock-info

# 仅更新股票基本信息
python cron.py --update-stock-info-only

# 指定数据源
python cron.py --fetch-only --data-source akshare_em
```

### Python API

```python
from local_db import LocalDatabase
from fetcher import StockDataFetcher

# 初始化
db = LocalDatabase('./data/stock_data.db')
fetcher = StockDataFetcher(local_db=db)

# 获取并保存单只股票信息
info = fetcher.data_source.get_stock_basic_info('000001')
if info:
    db.save_stock_basic_info(info, 'akshare_em')
    print(f"名称: {info['name']}")
    print(f"行业: {info['industry']}")

# 批量获取和保存
codes = ['000001', '600519', '000333']
stats = fetcher.fetch_and_save_stock_basic_info(codes)
print(f"成功保存: {stats['saved']} 只")

# 从数据库查询
info = db.get_stock_basic_info('000001')
print(f"名称: {info['name']}")

# 搜索股票
results = db.search_stock_by_name('茅台')
for stock in results:
    print(f"{stock['code']}: {stock['name']}")

# 获取统计信息
stats = db.get_stock_info_stats()
print(f"总数: {stats['total_count']}")
```

## 更新策略

### 自动更新（默认）

- **频率**: 7天内更新过的股票会跳过
- **触发时机**: 
  - `fetch_all()` 方法默认会更新股票信息
  - 可通过 `update_stock_info=False` 参数禁用

### 手动更新

```bash
# 仅更新股票信息
python cron.py --update-stock-info-only

# 在完整流程中跳过
python cron.py --skip-stock-info
```

## 与 Watchlist 的集成

股票基本信息会自动用于更新 watchlist 中的股票名称：

```python
# 更新自选股名称（从 stock_basic_info 表同步到 watchlist 表）
fetcher.update_watchlist_stock_names()
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                    python-fetcher                           │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────┐    │
│  │  DataSource  │────▶│   Fetcher    │────▶│ Local DB │    │
│  │   Manager    │     │              │     │          │    │
│  └──────────────┘     └──────────────┘     └──────────┘    │
│         │                                            │      │
│         ▼                                            ▼      │
│  ┌──────────────┐                          ┌──────────┐    │
│  │ akshare_em   │                          │  SQLite  │    │
│  │ baostock     │                          │          │    │
│  └──────────────┘                          └──────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Stockton   │
                       │   (Analysis) │
                       └──────────────┘
```

## 注意事项

1. **数据源优先级**: akshare_em > baostock
2. **缓存策略**: 7天内更新过的股票会跳过
3. **错误处理**: 单个股票失败不会中断批量处理
4. **性能**: 每次请求间隔 0.5 秒，避免请求过快

## 故障排查

### 获取不到数据

检查数据源可用性：
```bash
python test_data_source.py
```

### 数据库查询为空

确认是否已执行更新：
```bash
python cron.py --update-stock-info-only
```

### 查看统计数据

```python
from local_db import LocalDatabase
db = LocalDatabase()
print(db.get_stock_info_stats())
```
