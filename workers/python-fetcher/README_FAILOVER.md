# 多数据源自动故障切换 - 功能说明

## 🎯 核心功能

系统实现了**请求级别的自动故障切换**，当一个数据源请求失败时，自动尝试其他数据源，直到成功或所有数据源都失败。

## 📊 支持的数据源

| 数据源 | 优先级 | 特点 | 是否支持指数成分股 |
|--------|--------|------|-------------------|
| **akshare_tx** (腾讯) | 1 | 速度最快，无代理问题 | ❌ |
| **akshare_sina** (新浪) | 2 | 数据完整，有成交额和换手率 | ❌ |
| **baostock** | 3 | 稳定性好，17:30延迟 | ⚠️ 有限 |
| **akshare_em** (东财) | 4 | 数据最全，可能被代理阻止 | ✅ |

## 🔄 故障切换流程

### 初始化时
```
按优先级测试各数据源 → 选择第一个可用的作为主数据源
```

### 请求失败时
```
主数据源请求失败
    ↓
自动尝试下一个数据源
    ↓
成功 → 更新主数据源，返回结果
    ↓
失败 → 继续尝试下一个...
    ↓
所有都失败 → 抛出异常
```

### 指数成分股获取
```
优先使用 akshare_em（支持最好）
    ↓
失败 → 尝试主数据源
    ↓
失败 → 尝试其他数据源
    ↓
都失败 → 返回空列表（非致命）
```

## 🚀 快速开始

### 命令行使用

```bash
# 使用默认自动故障切换（推荐）
python cron.py --fetch-only

# 指定首选数据源（失败时自动切换）
python cron.py --fetch-only --data-source akshare_tx

# 使用 baostock（稳定性优先）
python cron.py --fetch-only --data-source baostock
```

### 环境变量

```bash
# 设置默认首选数据源
set DATA_SOURCE=akshare_tx

# 然后直接运行
python cron.py --fetch-only
```

## 💡 使用示例

### 示例1：东财被代理阻止时的自动切换

```bash
# 首选东财，但网络不通
python cron.py --fetch-only --data-source akshare_em

# 日志输出：
# [INFO] 首选数据源: akshare_em
# [WARNING] akshare_em 获取 000001 失败: ProxyError(...)
# [INFO] 切换到 akshare_tx 重试获取 000001
# [INFO] 故障切换成功: 切换到 akshare_tx
# [OK] 成功获取 10 条记录
```

### 示例2：获取指数成分股自动回退

```bash
# 使用腾讯作为主数据源（不支持成分股）
python cron.py --fetch-only --data-source akshare_tx

# 获取成分股时自动使用东财
# [INFO] 使用 akshare_em 获取指数 000300 成分股
# [OK] 获取 300 只成分股
```

### 示例3：ETF数据获取故障切换

```bash
# 某些数据源可能不支持ETF
python cron.py --fetch-only

# 日志输出：
# [WARNING] akshare_tx 获取 510300 失败: ...
# [INFO] 切换到 akshare_sina 重试获取 510300
# [INFO] 切换到 baostock 重试获取 510300
# [OK] 成功获取数据
```

## 📋 数据源字段对比

数据库表结构：`code, date, open, high, low, close, volume, amount, ma5, ma10, ma20, ma60, change_pct, turnover_rate`

| 字段 | akshare_tx | akshare_sina | baostock | akshare_em |
|------|------------|--------------|----------|------------|
| **amount** (成交额) | ❌ 无 | ✅ 元 | ✅ 元 | ✅ 元 |
| **turnover_rate** (换手率) | ❌ 无 | ✅ | ✅ | ✅ |
| **MA均线** | ✅ 计算 | ✅ 计算 | ✅ 计算 | ✅ 原始 |
| **change_pct** (涨跌幅) | ✅ 计算 | ✅ 原始 | ✅ 原始 | ✅ 原始 |

**单位一致性**：
- `volume`：统一为"股"（腾讯原始是"手"，已×100转换）
- `turnover_rate`：统一为"%"（新浪/baostock原始是小数，已×100转换）

## ⚙️ 配置选项

### 命令行参数

```bash
python cron.py --fetch-only --data-source akshare_tx
```

可选值：
- `akshare_tx` - 腾讯（推荐，速度最快）
- `akshare_sina` - 新浪（数据完整）
- `baostock` - 证券宝（稳定性好）
- `akshare_em` - 东方财富（数据最全）

### 程序化使用

```python
from src.data_source import DataSourceManager

# 基本使用（自动故障切换）
manager = DataSourceManager()
records = manager.get_stock_history('000001', '20250301', '20250315')

# 指定首选数据源
manager = DataSourceManager(preferred_source='baostock')

# 自定义优先级
manager = DataSourceManager(
    preferred_source='akshare_sina',
    priority=['akshare_sina', 'akshare_tx', 'baostock', 'akshare_em']
)
```

## 📊 测试验证

运行测试脚本验证故障切换功能：

```bash
# 基础功能测试
python test_simple.py

# 自动故障切换测试
python test_auto_failover.py

# 数据源对比测试
python test_baostock.py
```

## 🔍 故障排除

### 问题1：所有数据源都失败

**症状**：
```
RuntimeError: 所有数据源都无法获取 000001 数据
```

**解决**：
1. 检查网络连接
2. 检查股票代码格式
3. 查看日志中的具体错误

### 问题2：频繁故障切换

**症状**：
```
[WARNING] akshare_tx 获取 XXX 失败
[INFO] 切换到 akshare_sina 重试获取 XXX
```

**解决**：
- 这是正常现象，系统已自动处理
- 可调整优先级使用更稳定的数据源

### 问题3：指数成分股获取失败

**症状**：
```
[ERROR] 所有数据源都无法获取指数 000300 成分股
```

**解决**：
- 非致命错误，程序会继续运行
- 系统会使用本地缓存的数据
- 手动更新：`python cron.py --update-components`

## 📈 性能特点

1. **首次故障切换**：有一定延迟（需尝试其他数据源）
2. **后续请求**：使用已成功切换的数据源，无额外开销
3. **指数成分股**：优先使用 akshare_em，即使主数据源是其他

## 📝 日志级别

查看详细故障切换过程：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

日志输出示例：
```
[INFO] 注册适配器: akshare_tx
[INFO] 选择数据源: akshare_tx
[DEBUG] 使用 akshare_tx 获取 000001 数据
[INFO] 成功获取 10 条记录
```

故障切换时：
```
[WARNING] akshare_em 获取 000001 失败: ProxyError(...)
[INFO] 切换到 akshare_tx 重试获取 000001
[INFO] 故障切换成功: 切换到 akshare_tx
```

## 🔗 相关文档

- [AUTO_FAILOVER.md](AUTO_FAILOVER.md) - 详细故障切换指南
- [DATA_SOURCE_V3.md](DATA_SOURCE_V3.md) - 数据源完整对比
- [data_source.py](src/data_source.py) - 源代码（顶部有详细注释）

## ✅ 总结

- **零配置**：无需配置，自动选择最佳数据源
- **高可用**：单个数据源失败不影响整体功能
- **智能切换**：指数成分股自动使用最佳数据源
- **详细日志**：完整记录故障切换过程
- **易于扩展**：可轻松添加新的数据源适配器
