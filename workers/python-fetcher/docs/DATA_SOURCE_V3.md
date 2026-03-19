# 多数据源适配器 V3 - 完整指南

## 概述

支持 4 个数据源，自动故障切换：
1. **akshare_tx** (腾讯) - 推荐，速度最快
2. **akshare_sina** (新浪) - 备选，数据完整
3. **baostock** - 备选，稳定性好，但有延迟
4. **akshare_em** (东财) - 数据最全，但可能被代理阻止

---

## 快速开始

### 1. 使用腾讯数据源（推荐）

```bash
cd workers/python-fetcher

# 仅获取数据
python cron.py --fetch-only --data-source akshare_tx

# 完整流程
python cron.py --data-source akshare_tx --url YOUR_URL --api-key YOUR_KEY
```

### 2. 使用 Baostock 数据源

```bash
# 使用 baostock
python cron.py --fetch-only --data-source baostock
```

### 3. 环境变量配置

```bash
# Windows CMD
set DATA_SOURCE=akshare_tx

# Windows PowerShell
$env:DATA_SOURCE="akshare_tx"

# Linux/Mac
export DATA_SOURCE=akshare_tx
```

---

## 数据源详细对比

### 网络连通性

| 数据源 | 连通性 | 备注 |
|--------|--------|------|
| akshare_tx | ✅ 可用 | 腾讯接口，无代理问题 |
| akshare_sina | ✅ 可用 | 新浪接口，无代理问题 |
| baostock | ✅ 可用 | 证券宝，API稳定 |
| akshare_em | ❌ 可能被阻止 | 东财接口，部分网络环境被代理阻止 |

### 数据延迟

| 数据源 | 延迟 | 备注 |
|--------|------|------|
| akshare_tx/sina/em | 实时 | 当日收盘后即可获取 |
| baostock | ~17:30 | 日线数据交易日17:30入库 |

### 字段完整性对比

数据库表字段需求: `code`, `date`, `open`, `high`, `low`, `close`, `volume`, `amount`, `ma5`, `ma10`, `ma20`, `ma60`, `change_pct`, `turnover_rate`

| 字段 | akshare_tx | akshare_sina | baostock | akshare_em |
|------|------------|--------------|----------|------------|
| code | ✅ | ✅ | ✅ | ✅ |
| date | ✅ | ✅ | ✅ | ✅ |
| open | ✅ | ✅ | ✅ | ✅ |
| high | ✅ | ✅ | ✅ | ✅ |
| low | ✅ | ✅ | ✅ | ✅ |
| close | ✅ | ✅ | ✅ | ✅ |
| volume | ✅ | ✅ | ✅ | ✅ |
| **amount** | ❌ **无** | ✅ | ✅ | ✅ |
| **ma5/10/20/60** | ✅ 计算 | ✅ 计算 | ✅ 计算 | ✅ 原始 |
| **change_pct** | ✅ 计算 | ✅ 原始 | ✅ 原始 | ✅ 原始 |
| **turnover_rate** | ❌ **无** | ✅ | ✅ | ✅ |

### 单位一致性

| 字段 | akshare_tx | akshare_sina | baostock | akshare_em | 说明 |
|------|------------|--------------|----------|------------|------|
| volume | 股 | 股 | 股 | 股 | ✅ 统一为"股" |
| amount | ❌ 无 | 元 | 元 | 元 | ⚠️ 腾讯无此字段 |
| change_pct | % | % | % | % | ✅ 统一为% |
| turnover_rate | ❌ 无 | % | % | % | ⚠️ 新浪/baostock原始为小数，已×100转换 |

### 代码格式

| 数据源 | 格式 | 示例 |
|--------|------|------|
| akshare_tx/sina | sz000001 | sz000001, sh600000 |
| akshare_em | 000001 | 000001, 600000 |
| baostock | sh.600000 | sh.600000, sz.000001 |

### 指数成分股支持

| 数据源 | 支持 | 说明 |
|--------|------|------|
| akshare_tx | ❌ | 不支持 |
| akshare_sina | ❌ | 不支持 |
| baostock | ⚠️ 有限 | 没有直接接口，可用 query_all_stock 间接获取 |
| akshare_em | ✅ | 支持，使用 index_stock_cons_weight_csindex |

---

## 各数据源特点详解

### 1. 腾讯 (akshare_tx)

**优势:**
- ⚡ 速度最快
- ✅ 网络连通性好
- ✅ 稳定性高

**劣势:**
- ❌ 无成交额 (amount) 字段
- ❌ 无换手率 (turnover_rate) 字段
- ❌ 不支持指数成分股

**适用场景:** 
- 只需要 K 线数据进行技术分析
- 对实时性要求高
- 不需要成交额和换手率

### 2. 新浪 (akshare_sina)

**优势:**
- ✅ 数据字段完整
- ✅ 网络连通性好
- ✅ 有换手率数据

**劣势:**
- 需要自行计算均线
- 不支持指数成分股

**适用场景:**
- 需要完整数据字段
- 需要换手率数据

### 3. Baostock

**优势:**
- ✅ 稳定性好，API限制少
- ✅ 数据范围大 (1990年至今)
- ✅ 字段完整（有成交额、换手率）
- ✅ 支持分钟线数据

**劣势:**
- ⏰ 日线数据有延迟 (~17:30入库)
- 🔐 需要登录 (bs.login())
- 📝 所有数据为字符串，需要转换
- 指数成分股支持有限

**适用场景:**
- 对数据延迟不敏感（非实时交易）
- 需要长期历史数据
- 需要分钟线数据

**数据更新时间:**
- 日线数据：交易日 17:30 完成入库
- 分钟线数据：交易日 20:30 完成入库
- 财务数据：第二自然日 1:30 完成入库

### 4. 东财 (akshare_em)

**优势:**
- ✅ 数据最全
- ✅ 有原始均线数据
- ✅ 支持指数成分股

**劣势:**
- ❌ 可能被代理阻止
- 速度较慢

**适用场景:**
- 网络环境允许访问东财
- 需要指数成分股数据

---

## 使用建议

### 推荐配置

```bash
# 首选 - 腾讯 (速度最快)
python cron.py --fetch-only --data-source akshare_tx

# 需要完整字段 - 新浪
python cron.py --fetch-only --data-source akshare_sina

# 需要稳定性 - Baostock
python cron.py --fetch-only --data-source baostock
```

### 自动故障切换

系统会按以下优先级自动选择可用数据源：
1. akshare_tx (腾讯)
2. akshare_sina (新浪)
3. baostock
4. akshare_em (东财)

如果首选数据源不可用，会自动切换到下一个。

### 指数成分股处理

腾讯、新浪、baostock 不支持直接获取指数成分股，系统会：
1. 尝试使用 akshare_em 获取（如果网络允许）
2. 如果失败，使用本地缓存的数据
3. 缓存有效期为 30 天

---

## 测试

### 测试单个数据源

```bash
# 测试腾讯
python test_simple.py

# 测试 baostock
python test_baostock_simple.py

# 对比所有数据源
python test_baostock.py
```

### 验证数据完整性

```bash
# 检查数据库
sqlite3 data/stock_data.db "SELECT * FROM data_if300 WHERE code='000001' ORDER BY date DESC LIMIT 5;"
```

---

## 故障排除

### 问题1: Baostock 登录失败

**症状:**
```
Baostock login failed
```

**解决方案:**
- 检查网络连接
- 可能是 baostock 服务器问题，等待后重试
- 切换到其他数据源

### 问题2: 数据延迟

**症状:** 
- Baostock 获取不到当日最新数据

**原因:**
- Baostock 日线数据 17:30 才入库

**解决方案:**
- 使用 akshare_tx 或 akshare_sina 获取实时数据
- 等待 17:30 后再获取

### 问题3: 换手率异常

**症状:**
- 换手率显示为 0.94 而不是 94%

**原因:**
- 不同数据源换手率单位不同

**解决方案:**
- 系统已自动处理单位转换
- 新浪/baostock 原始为小数，已 ×100 转为百分比

---

## API 参考

### Baostock 核心接口

```python
import baostock as bs

# 登录
bs.login()

# 获取历史K线
rs = bs.query_history_k_data_plus(
    "sh.600000",  # 股票代码
    "date,code,open,high,low,close,volume,amount,turn,pctChg",  # 字段
    start_date='2025-03-01',
    end_date='2025-03-15',
    frequency='d',       # d=日, w=周, m=月, 5=5分钟
    adjustflag='2'       # 1=后复权, 2=前复权, 3=不复权
)

# 获取所有股票
rs = bs.query_all_stock(day='20250315')

# 登出
bs.logout()
```

### 数据源管理器

```python
from src.data_source import DataSourceManager

# 初始化（自动选择）
manager = DataSourceManager()

# 指定首选数据源
manager = DataSourceManager(preferred_source='baostock')

# 获取数据
records = manager.get_stock_history('000001', '20250301', '20250315')

# 获取指数成分股
components = manager.get_index_components('000300')
```

---

## 参考文档

- [Akshare 文档 - 腾讯接口](https://akshare.akfamily.xyz/data/stock/stock.html#id13)
- [Akshare 文档 - 新浪接口](https://akshare.akfamily.xyz/data/stock/stock.html#id12)
- [Akshare 文档 - 东财接口](https://akshare.akfamily.xyz/data/stock/stock.html#id8)
- [Baostock 官方文档](http://baostock.com/baostock/index.php)
