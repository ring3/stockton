# 数据完整性报告 - 各数据源字段与单位对比

## 数据库表结构要求

表名: `data_if300`, `data_ic500`, `data_etf`

字段列表:
```sql
code TEXT,           -- 股票代码
date TEXT,           -- 日期
open REAL,           -- 开盘价
high REAL,           -- 最高价
low REAL,            -- 最低价
close REAL,          -- 收盘价
volume INTEGER,      -- 成交量 (单位: 股)
amount REAL,         -- 成交额 (单位: 元)
ma5 REAL,            -- 5日均线
ma10 REAL,           -- 10日均线
ma20 REAL,           -- 20日均线
ma60 REAL,           -- 60日均线
change_pct REAL,     -- 涨跌幅 (单位: %)
turnover_rate REAL   -- 换手率 (单位: %)
```

---

## 各数据源字段完整性对比

### 字段覆盖情况

| 字段 | akshare_em (东财) | akshare_sina (新浪) | akshare_tx (腾讯) | baostock |
|------|-------------------|---------------------|-------------------|----------|
| code | ✅ | ✅ | ✅ | ✅ |
| date | ✅ | ✅ | ✅ | ✅ |
| open | ✅ | ✅ | ✅ | ✅ |
| high | ✅ | ✅ | ✅ | ✅ |
| low | ✅ | ✅ | ✅ | ✅ |
| close | ✅ | ✅ | ✅ | ✅ |
| **volume** | ✅ | ✅ | ✅ | ✅ |
| **amount** | ✅ | ✅ | ❌ **None** | ✅ |
| **ma5/10/20/60** | ✅ 计算 | ✅ 计算 | ✅ 计算 | ✅ 计算 |
| **change_pct** | ✅ 原始 | ✅ 计算 | ✅ 计算 | ✅ 原始 |
| **turnover_rate** | ✅ | ✅ | ❌ **None** | ✅ |

**字段缺失总结:**
- **腾讯 (akshare_tx)**: 缺少 `amount` 和 `turnover_rate`
- 其他数据源: 所有字段都有

---

## 单位一致性检查

### volume (成交量)

| 数据源 | 原始单位 | 转换逻辑 | 最终单位 | 状态 |
|--------|----------|----------|----------|------|
| akshare_em | 股 | 直接使用 | 股 | ✅ 正确 |
| akshare_sina | 股 | 直接使用 | 股 | ✅ 正确 |
| akshare_tx | 手 | `* 100` | 股 | ✅ 正确 |
| baostock | 股 | 直接使用 | 股 | ✅ 正确 |

**转换代码:**
```python
# 腾讯适配器 (line 410)
df['volume'] = df['volume'] * 100  # 手转股
```

### amount (成交额)

| 数据源 | 原始单位 | 转换逻辑 | 最终单位 | 状态 |
|--------|----------|----------|----------|------|
| akshare_em | 元 | 直接使用 | 元 | ✅ 正确 |
| akshare_sina | 元 | 直接使用 | 元 | ✅ 正确 |
| akshare_tx | 无 | 无 | None | ⚠️ 缺失 |
| baostock | 元 | 直接使用 | 元 | ✅ 正确 |

**注意:** 腾讯接口不返回成交额字段

### change_pct (涨跌幅)

| 数据源 | 原始单位 | 转换逻辑 | 最终单位 | 状态 |
|--------|----------|----------|----------|------|
| akshare_em | % | 直接使用 | % | ✅ 正确 |
| akshare_sina | 无 | `pct_change * 100` | % | ✅ 正确 |
| akshare_tx | 无 | `pct_change * 100` | % | ✅ 正确 |
| baostock | % | 直接使用 | % | ✅ 正确 |

**转换代码:**
```python
# 新浪和腾讯适配器
df['change_pct'] = df['close'].pct_change() * 100
```

### turnover_rate (换手率)

| 数据源 | 原始单位 | 转换逻辑 | 最终单位 | 状态 |
|--------|----------|----------|----------|------|
| akshare_em | % | 直接使用 | % | ✅ 正确 |
| akshare_sina | 小数 | `* 100` | % | ✅ 正确 |
| akshare_tx | 无 | 无 | None | ⚠️ 缺失 |
| baostock | 小数 | `* 100` | % | ✅ 正确 |

**转换代码:**
```python
# 新浪适配器 (line 358)
'turnover_rate': float(row['turnover_rate']) * 100

# baostock 适配器 (line 545)
'turnover_rate': float(row['turnover_rate']) * 100
```

---

## 数值示例对比

假设获取 000001 (平安银行) 2025-03-14 的数据:

### volume 字段

| 数据源 | 原始值 | 转换后值 | 说明 |
|--------|--------|----------|------|
| akshare_em | 172241765 | 172241765 | 直接使用 |
| akshare_sina | 172241765 | 172241765 | 直接使用 |
| akshare_tx | 1722417 | 172241700 | 手转股 (*100) |
| baostock | 172241765 | 172241765 | 直接使用 |

### turnover_rate 字段

| 数据源 | 原始值 | 转换后值 | 说明 |
|--------|--------|----------|------|
| akshare_em | 0.88 | 0.88 | 已经是% |
| akshare_sina | 0.0088 | 0.88 | 小数转% (*100) |
| akshare_tx | None | None | 无此字段 |
| baostock | 0.0088 | 0.88 | 小数转% (*100) |

### change_pct 字段

| 数据源 | 原始值 | 转换后值 | 说明 |
|--------|--------|----------|------|
| akshare_em | 1.25 | 1.25 | 已经是% |
| akshare_sina | 无 | 1.25 | 计算得出 |
| akshare_tx | 无 | 1.25 | 计算得出 |
| baostock | 1.25 | 1.25 | 已经是% |

---

## MA均线计算

所有数据源都使用统一的 `_calculate_ma()` 方法计算均线:

```python
def _calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    return df
```

**注意:** 
- 前 5 条记录的 ma5 为 None (需要 5 天数据)
- 前 10 条记录的 ma10 为 None (需要 10 天数据)
- 前 20 条记录的 ma20 为 None (需要 20 天数据)
- 前 60 条记录的 ma60 为 None (需要 60 天数据)

---

## 结论

### ✅ 单位统一正确

1. **volume**: 所有数据源最终都统一为 **股**
   - 腾讯原始是"手"，已正确转换 (*100)

2. **amount**: 除腾讯外都统一为 **元**
   - 腾讯返回 None

3. **change_pct**: 所有数据源都统一为 **%**
   - 新浪和腾讯通过 `pct_change() * 100` 计算

4. **turnover_rate**: 除腾讯外都统一为 **%**
   - 新浪和 baostock 原始是小数，已正确转换 (*100)
   - 腾讯返回 None

### ⚠️ 字段缺失

**腾讯 (akshare_tx)** 缺失字段:
- `amount` (成交额)
- `turnover_rate` (换手率)

**影响:**
- 数据库中对应字段将为 NULL
- 不影响 K 线数据的技术分析
- 影响需要成交额和换手率的策略

### 💡 使用建议

1. **需要完整数据** → 使用 `akshare_sina` 或 `baostock`
2. **速度优先** → 使用 `akshare_tx` (接受部分字段缺失)
3. **数据分析** → 建议使用 `akshare_sina` (字段完整且速度快)

---

## 验证脚本

运行以下脚本验证数据完整性:

```bash
python test_data_integrity.py
```

预期输出:
```
[检查] 腾讯 (akshare_tx)
  volume: 172241700 (股) ✅
  amount: None (缺失) ⚠️
  turnover_rate: None (缺失) ⚠️

[检查] 新浪 (akshare_sina)
  volume: 172241765 (股) ✅
  amount: 2057970454.4 (元) ✅
  turnover_rate: 0.88 (%) ✅

[检查] Baostock
  volume: 172241765 (股) ✅
  amount: 2057970454.4 (元) ✅
  turnover_rate: 0.88 (%) ✅
```
