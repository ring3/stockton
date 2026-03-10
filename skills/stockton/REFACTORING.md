# Stockton Skill 架构重构文档

## 概述

本次重构将原本分散的数据获取逻辑统一为**策略模式（Strategy Pattern）**架构，实现了：

1. **多数据源自动切换** - efinance 优先，akshare 备用
2. **统一数据接口** - 通过 `DataFetcherManager` 获取所有数据
3. **数据缓存机制** - SQLite 数据库存储历史数据
4. **完整的实时数据** - 实时行情 + 筹码分布

---

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                        调用层                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ data_fetcher.py │  │stock_analyzer.py│  │market_analyzer.py│ │
│  │  get_stock_data │  │   个股技术分析   │  │   大盘统计分析   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DataFetcherManager                           │
│                      (策略管理器)                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  职责：                                                      ││
│  │  1. 管理多个 Fetcher（按优先级排序）                          ││
│  │  2. 自动故障切换（Failover）                                  ││
│  │  3. 提供统一的数据获取接口                                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  EfinanceFetcher │  │  AkshareFetcher  │  │   (其他数据源)    │
│    Priority 0    │  │    Priority 1    │  │                  │
│    (efinance)    │  │    (akshare)     │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 接口设计

### 1. BaseFetcher 抽象基类

所有数据源必须实现以下抽象方法：

```python
class BaseFetcher(ABC):
    # ===== 个股数据接口 =====
    
    @abstractmethod
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取原始日线数据"""
        pass
    
    @abstractmethod
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化列名（统一为：date, open, high, low, close, volume, amount, pct_chg）"""
        pass
    
    @abstractmethod
    def _get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """获取实时行情
        返回: {
            'code', 'name', 'price', 'change_pct', 'change_amount',
            'volume', 'amount', 'turnover_rate', 'volume_ratio', 'amplitude',
            'high', 'low', 'open_price', 'pe_ratio', 'pb_ratio', 'total_mv', 'circ_mv'
        }
        """
        pass
    
    @abstractmethod
    def _get_chip_distribution(self, stock_code: str) -> Optional[dict]:
        """获取筹码分布
        返回: {
            'code', 'date', 'profit_ratio', 'avg_cost', 
            'concentration_90', 'concentration_70'
        }
        """
        pass
    
    # ===== 大盘数据接口（新增） =====
    
    @abstractmethod
    def _get_market_indices(self) -> pd.DataFrame:
        """获取主要指数实时行情（上证、深证、创业板等）"""
        pass
    
    @abstractmethod
    def _get_market_overview(self) -> pd.DataFrame:
        """获取市场概览（全部A股实时行情，用于涨跌统计）"""
        pass
    
    @abstractmethod
    def _get_sector_rankings(self) -> pd.DataFrame:
        """获取行业板块涨跌排行"""
        pass
```

### 2. DataFetcherManager 统一入口

```python
class DataFetcherManager:
    # 个股数据
    def get_daily_data(self, stock_code, start_date, end_date, days) -> Tuple[pd.DataFrame, str]:
        """获取日线数据（自动切换数据源）"""
        pass
    
    # 大盘数据（新增）
    def get_market_indices(self) -> Tuple[pd.DataFrame, str]:
        """获取主要指数行情"""
        pass
    
    def get_market_overview(self) -> Tuple[pd.DataFrame, str]:
        """获取市场概览"""
        pass
    
    def get_sector_rankings(self) -> Tuple[pd.DataFrame, str]:
        """获取板块排行"""
        pass
```

### 3. 对外统一接口

```python
# data_fetcher.py - 个股数据入口
def get_stock_data(stock_code: str, days: int = 60) -> Dict[str, Any]:
    """
    获取股票完整数据
    
    Returns:
        {
            'success': bool,
            'code': str,
            'name': str,
            'daily_data': List[StockDailyData],  # 历史日线
            'realtime_quote': RealtimeQuote,      # 实时行情（可选）
            'chip_distribution': dict,            # 筹码分布（可选）
            'data_source': str,                   # 实际使用的数据源
            'fetch_time': str,
        }
    """
    pass

# market_analyzer.py - 大盘数据入口
class MarketDataAnalyzer:
    def get_market_overview(self) -> MarketOverview:
        """获取市场概览（指数 + 涨跌统计 + 板块排行）"""
        pass
```

---

## 数据流向

### 个股数据获取流程

```
get_stock_data('600519')
    ↓
DataFetcherManager.get_daily_data('600519')
    ↓（自动故障切换）
EfinanceFetcher.get_daily_data('600519')
    ├── _fetch_raw_data()          # 获取原始数据
    ├── _normalize_data()          # 标准化列名
    ├── _clean_data()              # 数据清洗
    ├── _calculate_indicators()    # 计算技术指标（MA5/10/20, 量比）
    ├── _get_realtime_quote()      # 获取实时行情 → df.attrs['_realtime_quote']
    └── _get_chip_distribution()   # 获取筹码分布 → df.attrs['_chip_distribution']
    ↓
返回 DataFrame（包含 attrs）
    ↓
data_fetcher.py 从 df.attrs 提取额外数据
    ↓
组装 StockDataResult 返回
```

### 大盘数据获取流程

```
MarketDataAnalyzer.get_market_overview()
    ↓
DataFetcherManager.get_market_indices()      # 获取指数
DataFetcherManager.get_market_overview()     # 获取涨跌统计
DataFetcherManager.get_sector_rankings()     # 获取板块排行
    ↓（每个方法内部自动切换数据源）
EfinanceFetcher / AkshareFetcher
    └── _get_market_indices() / _get_market_overview() / _get_sector_rankings()
```

---

## 数据存储设计

### SQLite 表结构

```sql
CREATE TABLE stock_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,              -- 股票代码
    name TEXT,                       -- 股票名称
    date TEXT NOT NULL,              -- 日期
    open REAL, high REAL, low REAL, close REAL,
    volume REAL, amount REAL, pct_chg REAL,
    ma5 REAL, ma10 REAL, ma20 REAL, ma60 REAL, volume_ratio REAL,
    data_source TEXT,                -- 数据来源
    realtime_quote TEXT,             -- JSON 格式实时行情（仅最新日期）
    chip_distribution TEXT,          -- JSON 格式筹码分布（仅最新日期）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, date)
);

CREATE INDEX idx_code_date ON stock_daily(code, date);
```

### 存储策略

- **历史数据**：只存储 OHLCV + 技术指标
- **最新日期**：额外存储 `realtime_quote` 和 `chip_distribution` JSON 数据
- **缓存逻辑**：`has_today_data()` 检查今日数据是否存在，存在则直接返回缓存

---

## 移除的组件

### 1. AkshareDataSource 类（已删除）

**原因**：与新的架构重复，且直接依赖 akshare

**替代**：统一使用 `get_stock_data()` 函数

```python
# 之前（已删除）
from data_fetcher import AkshareDataSource
source = AkshareDataSource()
data = source.get_daily_data('600519')

# 现在
from data_fetcher import get_stock_data
result = get_stock_data('600519')
data = result['daily_data']
```

### 2. 直接依赖关系（已移除）

**之前的问题**：
- `market_analyzer.py` 直接调用 `ak.stock_zh_index_spot_sina()`
- `data_fetcher.py` 直接实例化 `EfinanceFetcher`

**解决方案**：
- 所有数据获取必须通过 `DataFetcherManager`
- 外部模块不直接依赖具体 fetcher 实现

---

## 向后兼容

### 保留的数据类

```python
# 用于结果封装（不用于数据获取）
class StockDailyData:
    date, open, high, low, close, volume, amount, pct_chg, ma5, ma10, ma20, ma60, volume_ratio

class RealtimeQuote:
    code, name, price, change_pct, change_amount, volume, amount, 
    turnover_rate, volume_ratio, amplitude, high, low, open_price, 
    pe_ratio, pb_ratio, total_mv, circ_mv

class ChipDistribution:
    code, date, profit_ratio, avg_cost, concentration_90, concentration_70
```

---

## 数据源对比

| 功能 | EfinanceFetcher | AkshareFetcher | 说明 |
|-----|-----------------|----------------|------|
| **个股日线** | `ef.stock.get_quote_history()` | `ak.stock_zh_a_hist()` | 两者都支持 |
| **实时行情** | `ef.stock.get_realtime_quotes()` | `ak.stock_zh_a_spot_em()` | 两者都支持 |
| **筹码分布** | `ef.stock.get_quote_history()` | `ak.stock_cyq_em()` | 两者都支持 |
| **大盘指数** | `ef.stock.get_quote_history(index_code)` | `ak.stock_zh_index_spot_sina()` | 两者都支持 |
| **市场概览** | `ef.stock.get_realtime_quotes()` | `ak.stock_zh_a_spot_em()` | 两者都支持 |
| **板块排行** | ❌ 不支持 | `ak.stock_board_industry_name_em()` | 仅 akshare |

**优先级策略**：
1. 优先尝试 efinance（Priority 0）
2. efinance 失败或不可用时，自动切换到 akshare（Priority 1）
3. 板块排行等特殊功能，akshare 作为唯一/备用数据源

---

## 使用示例

### 获取个股数据

```python
from data_fetcher import get_stock_data

# 基本用法
result = get_stock_data('600519', days=60)

# 强制刷新（忽略缓存）
result = get_stock_data('600519', days=60, force_refresh=True)

# 禁用缓存
result = get_stock_data('600519', days=60, use_cache=False)

# 访问实时行情和筹码分布
if result['success']:
    print(f"名称: {result['name']}")
    print(f"数据源: {result['data_source']}")
    
    if result.get('realtime_quote'):
        rt = result['realtime_quote']
        print(f"最新价: {rt.price}, 换手率: {rt.turnover_rate}")
    
    if result.get('chip_distribution'):
        chip = result['chip_distribution']
        print(f"获利比例: {chip['profit_ratio']}, 平均成本: {chip['avg_cost']}")
```

### 获取大盘数据

```python
from market_analyzer import MarketDataAnalyzer

analyzer = MarketDataAnalyzer()
overview = analyzer.get_market_overview()

print(f"上证指数: {overview.indices[0].current}")
print(f"上涨家数: {overview.up_count}")
print(f"涨停家数: {overview.limit_up_count}")
print(f"领涨板块: {[s.name for s in overview.top_sectors]}")
```

---

## 错误处理

```python
# 所有数据获取方法统一抛出 DataFetchError
try:
    df, source = manager.get_daily_data('600519')
except DataFetchError as e:
    # 所有数据源都失败
    logger.error(f"获取失败: {e}")

# 大盘数据同样
try:
    df, source = manager.get_market_indices()
except DataFetchError as e:
    logger.error(f"获取指数失败: {e}")
```

---

## 扩展指南

### 添加新的数据源

1. 创建新的 Fetcher 类继承 `BaseFetcher`
2. 实现所有抽象方法
3. 设置合适的 `priority`
4. 在 `data_provider/__init__.py` 中注册

```python
# 示例：添加 TushareFetcher
class TushareFetcher(BaseFetcher):
    name = "TushareFetcher"
    priority = 2  # 优先级低于 efinance 和 akshare
    
    def _fetch_raw_data(self, stock_code, start_date, end_date):
        # 实现数据获取
        pass
    
    def _normalize_data(self, df, stock_code):
        # 实现列名标准化
        pass
    
    # ... 其他抽象方法
```

---

## 总结

本次重构实现了：

1. **架构统一** - 所有数据获取通过 `DataFetcherManager`
2. **自动容错** - 多数据源自动切换，单点故障不影响服务
3. **数据完整** - 历史数据 + 实时行情 + 筹码分布
4. **缓存优化** - SQLite 缓存减少 API 调用
5. **接口简洁** - 外部只需调用 `get_stock_data()` 或 `MarketDataAnalyzer`
