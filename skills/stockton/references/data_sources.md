# 数据源参考

理解多数据源架构和降级逻辑。

## 架构概览

```
用户请求
    ↓
DataFetcherManager（优先级0、1、2...）
    ↓
EfinanceFetcher → AkshareFetcher → [未来: BaostockFetcher, TushareFetcher]
    ↓
数据库缓存（SQLite）
    ↓
原始数据
```

## 数据源优先级

### 优先级0：EfinanceFetcher

**包：** `efinance`

**优点：**
- 响应速度快
- API设计简洁
- 自动重试逻辑
- 适合批量请求

**缺点：**
- 数据类型有限（无财报、无指数成分股）
- 较少预计算技术指标

**最适合：**
- 历史K线数据
- 实时行情
- ETF数据

**速率限制：** 请求间隔1.5-3.0秒

### 优先级1：AkshareFetcher

**包：** `akshare`

**优点：**
- 数据覆盖全面
- 财务报表
- 指数成分股
- 行业分类
- 衍生品数据（期货、期权）
- 多备用源（东方财富→新浪→腾讯→网易）

**缺点：**
- 比efinance慢
- 更容易API变更
- 需要更多重试逻辑

**最适合：**
- 财务分析
- 股票筛选
- 市场概览数据
- 指数成分股

**速率限制：** 请求间隔2.0-5.0秒

### 优先级2：数据库缓存

**类型：** SQLite (`data/stock_data.db`)

**用途：**
- 避免重复获取历史数据
- 存储计算的技术指标
- 缓存指数成分股
- 支持离线分析

**缓存策略：**
| 数据类型 | 缓存时长 | 说明 |
|---------|---------|------|
| 历史K线 | 永久 | 直到手动清除 |
| 指数成分股 | 1天 | 每日更新 |
| 实时行情 | 不缓存 | 始终最新 |
| 财务报表 | 90天 | 季度更新 |

## 数据源对比

| 功能 | Efinance | Akshare | 数据库 |
|------|----------|---------|--------|
| A股K线 | ✅ 快 | ✅ 可靠 | ✅ 已缓存 |
| ETF数据 | ✅ | ✅ | ✅ |
| 港股 | ✅ | ✅ | ✅ |
| 财务报表 | ❌ | ✅ | ✅ 已缓存 |
| 指数成分股 | ❌ | ✅ | ✅ 已缓存 |
| 行业数据 | ❌ | ✅ | ✅ 已缓存 |
| 期货贴水 | ❌ | ✅ | ❌ |
| 期权IV | ❌ | ✅ | ❌ |
| 实时行情 | ✅ | ⚠️（常被阻） | ❌ |

## 降级行为

### 场景1：Efinance成功
```
用户请求600519数据
    ↓
EfinanceFetcher 0.5秒内成功
    ↓
返回数据（快速路径）
```

### 场景2：Efinance失败，Akshare成功
```
用户请求600519数据
    ↓
EfinanceFetcher 失败（超时）
    ↓
等待2秒，尝试AkshareFetcher
    ↓
Akshare 1秒内成功
    ↓
返回数据（总计3秒）
```

### 场景3：所有源失败
```
用户请求600519数据
    ↓
Efinance失败 → Akshare失败
    ↓
检查数据库缓存
    ↓
如有缓存：返回缓存数据
如无缓存：抛出DataFetchError
```

## 网络和代理处理

### 自动代理绕过

两个fetcher都自动清除代理设置以避免连接问题：

```python
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
```

### 连接错误处理

常见错误和处理：

| 错误 | 原因 | 处理 |
|------|------|------|
| 超时 | 网络慢 | 指数退避重试 |
| 连接拒绝 | 代理/防火墙 | 清除代理，重试 |
| SSLError | 证书问题 | 记录警告，尝试备用源 |
| 速率限制 | 请求过多 | 休眠5-10秒，重试 |
| 空响应 | API变更 | 记录错误，尝试下一源 |

## 添加新数据源

添加BaostockFetcher示例：

```python
# 在 data_provider/baostock_fetcher.py
from .base import BaseFetcher

class BaostockFetcher(BaseFetcher):
    name = "BaostockFetcher"
    priority = 2  # 优先级低于efinance/akshare
    
    def _fetch_raw_data(self, stock_code, start_date, end_date):
        # 实现baostock特定获取
        pass
    
    def _normalize_data(self, df, stock_code):
        # 转换baostock列为标准格式
        pass
    
    # 实现其他抽象方法...
```

在 `DataFetcherManager._init_default_fetchers()` 中注册：

```python
try:
    from .baostock_fetcher import BaostockFetcher
    self._fetchers.append(BaostockFetcher())
except Exception as e:
    logger.debug(f"BaostockFetcher不可用: {e}")
```

## 数据质量指标

每个数据响应包含源信息：

```python
{
    'success': True,
    'code': '600519',
    'data_source': 'EfinanceFetcher',  # 或 'AkshareFetcher'
    'daily_data': [...]
}
```

用于：
- 监控哪些源在工作
- 识别数据质量问题
- 优化优先级顺序

## 预加载策略

为优化筛选性能，收盘后预加载数据：

```python
from skills.stockton.scripts.preload_data import preload_index_data

# 预加载主要指数
preload_index_data(['沪深300', '中证500', '中证1000'], days=130)
```

**为何130天？**
- 60天：短期趋势分析
- 120天：动量计算（20日、60日、120日）
- 130天：周末/假期缓冲

**最佳运行时间：**
- 收盘后（15:30 北京时间）
- 次日开盘前（09:15 北京时间）
- 推荐：每日19:00-21:00

## 离线模式

如所有外部源失败，工具可使用数据库缓存以有限的离线模式运行：

```python
# 检查数据是否在缓存中
db = get_db()
if db.has_today_data('600519'):
    # 使用缓存数据
    data = db.get_analysis_context('600519')
else:
    # 报错 - 无网络且无缓存
    raise DataFetchError("无网络且无缓存数据")
```

**离线模式限制：**
- 实时行情不可用
- 市场概览不可用
- 指数成分股更新不可用
- 仅历史数据（至最后缓存日期）
