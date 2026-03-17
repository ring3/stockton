# 多数据源适配器架构说明

## 概述

`data_source.py` 实现了多数据源适配器模式，支持：
- **akshare**: 主要数据源（支持股票历史数据、指数成分股）
- **efinance**: 备选数据源（支持股票历史数据，不支持指数成分股）

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                 DataSourceManager (数据源管理器)              │
│                  - 自动故障切换                                │
│                  - 自动禁用代理重试                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │ AkshareAdapter  │      │ EfinanceAdapter │              │
│  │ - 股票历史数据   │      │ - 股票历史数据   │              │
│  │ - 指数成分股     │      │ - 不支持成分股   │              │
│  └─────────────────┘      └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 使用方法

### 1. 基本使用

```python
from src import StockDataFetcher, LocalDatabase

# 初始化（自动选择可用数据源）
db = LocalDatabase()
fetcher = StockDataFetcher(db, preferred_source='akshare')

# 获取股票数据
prices = fetcher.get_stock_history('000001', 'data_if300')
```

### 2. 直接测试数据源

```python
from src.data_source import DataSourceManager

# 初始化数据源管理器
manager = DataSourceManager(preferred_source='akshare', disable_proxy_on_error=True)
print(f"当前数据源: {manager.current_source_name}")

# 获取股票数据
records = manager.get_stock_history('000001', '20250101', '20250301')

# 获取指数成分股
components = manager.get_index_components('000300')
```

### 3. 在 cron.py 中指定数据源

可以通过环境变量或修改 cron.py 来指定数据源：

```python
# cron.py
preferred_source = os.getenv('DATA_SOURCE', 'akshare')  # 默认 akshare
fetcher = StockDataFetcher(db, preferred_source=preferred_source)
```

## 代理处理

### 自动代理禁用

`disable_proxy_on_error=True` 会在每次请求前：
1. 保存当前代理环境变量
2. 删除代理环境变量
3. 执行请求
4. 恢复代理环境变量

### 手动设置代理

如果需要手动配置代理，可以在代码中设置：

```python
import os
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
os.environ['HTTPS_PROXY'] = 'https://proxy.example.com:8080'
```

## 数据源对比

| 功能 | akshare | efinance |
|------|---------|----------|
| 股票历史数据 | ✓ | ✓ |
| 指数成分股 | ✓ | ✗ |
| 成交额 | ✓ | ✗ |
| 换手率 | ✓ | ✗ |
| 涨跌幅 | ✓ | 自动计算 |

## 故障切换

当首选数据源不可用时，系统会自动切换到备选数据源：

1. 尝试连接首选数据源（如 akshare）
2. 如果失败，尝试 efinance
3. 如果都失败，抛出 RuntimeError

## 当前网络问题

当前环境存在网络限制：
- 连接 `push2his.eastmoney.com` 被拒绝
- 可能是系统防火墙或企业网络策略

### 可能的解决方案

1. **使用 VPN/代理**（需管理员权限配置）
2. **更换网络环境**（如使用手机热点）
3. **本地数据文件**（预下载历史数据文件）
4. **其他数据源**（如 Tushare、QMT 等付费数据源）

## 测试

运行测试脚本：

```bash
cd workers/python-fetcher
python test_datasource.py
```

## 扩展数据源

要添加新的数据源，继承 `DataSourceAdapter`：

```python
class TushareAdapter(DataSourceAdapter):
    name = "tushare"
    
    def __init__(self, token: str):
        import tushare as ts
        self.pro = ts.pro_api(token)
    
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        # 实现获取逻辑
        pass
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        # 实现获取逻辑
        pass
```

然后在 `DataSourceManager._register_adapters()` 中注册：

```python
def _register_adapters(self):
    # ... 其他适配器
    try:
        self.adapters['tushare'] = TushareAdapter(token='your_token')
    except Exception as e:
        logger.warning(f"Tushare not available: {e}")
```
