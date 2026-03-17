# 数据验证总结

## 结论

经过代码审查和实际测试，**各数据源的输出满足要求，单位已统一**。

---

## 字段完整性

### 必需字段 (14个)

| 字段 | akshare_em | akshare_sina | akshare_tx | baostock | 说明 |
|------|------------|--------------|------------|----------|------|
| code | ✅ | ✅ | ✅ | ✅ | 股票代码 |
| date | ✅ | ✅ | ✅ | ✅ | 日期 |
| open | ✅ | ✅ | ✅ | ✅ | 开盘价 |
| high | ✅ | ✅ | ✅ | ✅ | 最高价 |
| low | ✅ | ✅ | ✅ | ✅ | 最低价 |
| close | ✅ | ✅ | ✅ | ✅ | 收盘价 |
| volume | ✅ | ✅ | ✅ | ✅ | 成交量 |
| amount | ✅ | ✅ | ❌ **None** | ✅ | 成交额 |
| ma5 | ✅ | ✅ | ✅ | ✅ | 5日均线 |
| ma10 | ✅ | ✅ | ✅ | ✅ | 10日均线 |
| ma20 | ✅ | ✅ | ✅ | ✅ | 20日均线 |
| ma60 | ✅ | ✅ | ✅ | ✅ | 60日均线 |
| change_pct | ✅ | ✅ | ✅ | ✅ | 涨跌幅 |
| turnover_rate | ✅ | ✅ | ❌ **None** | ✅ | 换手率 |

### 字段缺失说明

**腾讯 (akshare_tx)** 缺失 2 个字段:
1. `amount` - 腾讯接口不返回成交额
2. `turnover_rate` - 腾讯接口不返回换手率

**影响:**
- 使用腾讯数据源时，数据库中 `amount` 和 `turnover_rate` 字段将为 NULL
- 不影响 K 线显示和技术分析（MA 均线等）
- 如需完整数据，建议使用新浪或 baostock 数据源

---

## 单位统一性

### 1. volume (成交量) - 统一为 "股"

| 数据源 | 原始单位 | 转换逻辑 | 状态 |
|--------|----------|----------|------|
| akshare_em | 股 | 直接使用 | ✅ |
| akshare_sina | 股 | 直接使用 | ✅ |
| **akshare_tx** | **手** | `* 100` 转换为股 | ✅ |
| baostock | 股 | 直接使用 | ✅ |

**验证示例 (000001 2025-03-14):**
```
腾讯原始值: 1722418 (手)
转换后值:   172241800 (股) ✅
```

### 2. amount (成交额) - 统一为 "元"

| 数据源 | 原始单位 | 状态 |
|--------|----------|------|
| akshare_em | 元 | ✅ |
| akshare_sina | 元 | ✅ |
| akshare_tx | 无此字段 | ⚠️ None |
| baostock | 元 | ✅ |

### 3. change_pct (涨跌幅) - 统一为 "%"

| 数据源 | 原始值 | 转换逻辑 | 状态 |
|--------|--------|----------|------|
| akshare_em | % | 直接使用 | ✅ |
| akshare_sina | 无 | `pct_change() * 100` | ✅ |
| akshare_tx | 无 | `pct_change() * 100` | ✅ |
| baostock | % | 直接使用 | ✅ |

**说明:** 涨跌幅通过当日收盘价相对前一日收盘价计算，统一为百分比形式。

### 4. turnover_rate (换手率) - 统一为 "%"

| 数据源 | 原始单位 | 转换逻辑 | 状态 |
|--------|----------|----------|------|
| akshare_em | % | 直接使用 | ✅ |
| akshare_sina | 小数 | `* 100` 转换为% | ✅ |
| akshare_tx | 无此字段 | 无 | ⚠️ None |
| baostock | 小数 | `* 100` 转换为% | ✅ |

**转换示例:**
```python
# 新浪/baostock 原始值: 0.0088 (小数)
# 转换后: 0.88 (%)
'turnover_rate': float(row['turnover_rate']) * 100
```

---

## MA均线计算

所有数据源使用统一的 `_calculate_ma()` 方法:

```python
def _calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    return df
```

**特点:**
- 基于收盘价计算
- 数据不足时返回 None (如第1-4条记录 ma5 为 None)
- 所有数据源的均线计算逻辑完全一致

---

## 代码中的单位转换

### 腾讯适配器 (akshare_tx)
```python
# Line 410: 手转股
df['volume'] = df['volume'] * 100

# Line 424: amount 缺失
'amount': None

# Line 430: turnover_rate 缺失
'turnover_rate': None
```

### 新浪适配器 (akshare_sina)
```python
# Line 340: 计算涨跌幅 (%)
df['change_pct'] = df['close'].pct_change() * 100

# Line 358: 小数转%
'turnover_rate': float(row['turnover_rate']) * 100
```

### baostock 适配器
```python
# Line 545: 小数转%
'turnover_rate': float(row['turnover_rate']) * 100
```

---

## 使用建议

### 场景1: 需要完整数据（含成交额、换手率）
```bash
# 推荐: 新浪 或 baostock
python cron.py --fetch-only --data-source akshare_sina
python cron.py --fetch-only --data-source baostock
```

### 场景2: 速度优先（K线分析为主）
```bash
# 推荐: 腾讯（速度最快）
python cron.py --fetch-only --data-source akshare_tx
# 注意: amount 和 turnover_rate 将为 NULL
```

### 场景3: 自动故障切换（推荐）
```bash
# 系统自动选择可用数据源
python cron.py --fetch-only
```

---

## 数据库兼容性

所有数据源返回的数据都可以直接插入 SQLite 数据库:

```sql
INSERT INTO data_if300 
(code, date, open, high, low, close, volume, amount, 
 ma5, ma10, ma20, ma60, change_pct, turnover_rate)
VALUES 
(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**说明:**
- 腾讯数据源插入时，`amount` 和 `turnover_rate` 为 NULL
- 其他字段所有数据源都有值
- 数据类型一致: volume 为 int，其他为 float 或 string

---

## 最终结论

✅ **单位统一正确**
- volume: 统一为"股"（腾讯已转换）
- amount: 统一为"元"（腾讯为 NULL）
- change_pct: 统一为"%"
- turnover_rate: 统一为"%"（新浪/baostock已转换）

✅ **字段基本完整**
- 14个必需字段中，腾讯缺失 2 个（amount, turnover_rate）
- 其他数据源所有字段都有
- 缺失字段不影响核心 K 线功能

✅ **数据可直接入库**
- 所有数据源返回的数据结构一致
- 可直接用于数据库插入
- 无需额外转换

⚠️ **注意事项**
- 使用腾讯数据源时，amount 和 turnover_rate 为 NULL
- 如需完整数据，建议使用新浪或 baostock
- 系统支持自动故障切换，无需手动处理
