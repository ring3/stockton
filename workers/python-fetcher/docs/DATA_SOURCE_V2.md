# 多数据源适配器 V2 使用指南

## 概述

由于网络环境限制（代理阻止了东方财富 API），我们实现了多数据源适配器架构，支持：
- **腾讯数据源** (`akshare_tx`) - 推荐
- **新浪数据源** (`akshare_sina`) - 备选  
- **东方财富** (`akshare_em`) - 数据最全但可能被代理阻止

## 快速开始

### 1. 使用腾讯数据源（推荐）

```bash
cd workers/python-fetcher

# 仅获取数据到本地
python cron.py --fetch-only --data-source akshare_tx

# 完整流程（获取 + 同步）
python cron.py --data-source akshare_tx --url YOUR_URL --api-key YOUR_KEY
```

### 2. 环境变量配置

```bash
# 设置默认数据源
export DATA_SOURCE=akshare_tx

# 然后直接运行
python cron.py --fetch-only
```

## 数据源对比

| 特性 | 腾讯 (akshare_tx) | 新浪 (akshare_sina) | 东财 (akshare_em) |
|------|-------------------|---------------------|-------------------|
| **网络连通性** | ✅ 可用 | ✅ 可用 | ❌ 被代理阻止 |
| **股票数据** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **指数成分股** | ❌ 不支持 | ❌ 不支持 | ✅ 支持 |
| **换手率** | ❌ 无 | ✅ 有 | ✅ 有 |
| **均线数据** | ✅ 自动计算 | ✅ 自动计算 | ✅ 自带 |
| **数据速度** | ⚡ 最快 | 🚀 快 | 🐢 较慢 |
| **代码格式** | sz000001 | sz000001 | 000001 |

## 架构说明

### 自动故障切换

```
DataSourceManager 会按优先级尝试数据源:
1. akshare_tx (腾讯) - 首选
2. akshare_sina (新浪) - 备选
3. akshare_em (东财) - 最后备选
```

### 指数成分股处理

腾讯和新浪接口不支持获取指数成分股，因此：
1. 首次运行时会尝试使用东财接口获取（如果网络允许）
2. 如果东财不可用，使用本地缓存的数据
3. 缓存有效期为 30 天

## API 接口详情

### 腾讯接口 (stock_zh_a_hist_tx)

```python
import akshare as ak

# 参数说明
# - symbol: sz000001 (带市场前缀)
# - start_date: 20250101
# - end_date: 20250315
# - adjust: qfq (前复权)

df = ak.stock_zh_a_hist_tx(
    symbol='sz000001',
    start_date='20250101',
    end_date='20250315',
    adjust='qfq'
)

# 返回列: date, open, close, high, low, amount
# 注意: amount 单位是手，已自动转换为股数
```

### 新浪接口 (stock_zh_a_daily)

```python
import akshare as ak

# 参数说明
# - symbol: sz000001 (带市场前缀)
# - start_date: 20250101
# - end_date: 20250315
# - adjust: qfq (前复权)

df = ak.stock_zh_a_daily(
    symbol='sz000001',
    start_date='20250101',
    end_date='20250315',
    adjust='qfq'
)

# 返回列: date, open, high, low, close, volume, amount, outstanding_share, turnover
```

## 代码转换

腾讯和新浪接口需要带市场前缀的股票代码：

```python
# 转换规则
000001 -> sz000001  (深市)
600000 -> sh600000  (沪市)
300750 -> sz300750  (创业板)
688981 -> sh688981  (科创板)
```

系统自动处理此转换，无需手动修改。

## 测试

### 测试单个数据源

```bash
# 测试腾讯接口
python test_akshare_alternatives.py

# 简单测试
python test_simple.py
```

### 验证数据完整性

```bash
# 检查本地数据库
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM data_if300;"
sqlite3 data/stock_data.db "SELECT * FROM data_if300 WHERE code='000001' ORDER BY date DESC LIMIT 5;"
```

## 故障排除

### 问题1: 所有数据源都不可用

**症状**: 
```
RuntimeError: 没有可用的数据源
```

**解决方案**:
1. 检查网络连接
2. 禁用代理：`unset HTTP_PROXY HTTPS_PROXY`
3. 尝试切换网络环境

### 问题2: 指数成分股获取失败

**症状**:
```
无法获取指数 000300 成分股
```

**解决方案**:
腾讯/新浪接口不支持获取成分股，系统会：
1. 尝试使用东财接口（如果被代理阻止会失败）
2. 使用本地缓存的数据（如果有）
3. 手动提供成分股列表

### 问题3: 数据不完整

**症状**: 某些字段为 null

**原因**: 
- 腾讯接口没有 turnover_rate（换手率）
- 腾讯接口没有 amount（成交额）

**解决方案**: 使用新浪接口获取完整数据
```bash
python cron.py --fetch-only --data-source akshare_sina
```

## 性能优化

### 批量获取

```bash
# 每批处理 50 只股票（默认）
python cron.py --fetch-only --data-source akshare_tx

# 减小批量大小以避免频率限制
python cron.py --fetch-only --data-source akshare_sina --batch-size 30
```

### 增量更新

系统会自动检测数据库中已有数据，只获取新数据：
- 首次运行：获取全部历史数据（2023-01-01 至今）
- 后续运行：只获取缺失的数据

## 更新计划

未来可能支持的数据源：
- Tushare (付费)
- Baostock
- QMT (本地量化平台)
- 本地 CSV 文件

## 参考

- [Akshare 文档 - 腾讯接口](https://akshare.akfamily.xyz/data/stock/stock.html#id13)
- [Akshare 文档 - 新浪接口](https://akshare.akfamily.xyz/data/stock/stock.html#id12)
- [Akshare 文档 - 东财接口](https://akshare.akfamily.xyz/data/stock/stock.html#id8)
