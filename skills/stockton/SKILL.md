---
name: stockton
description: A股行情数据获取与分析工具（基于akshare），提供个股历史K线、实时行情、技术指标计算、趋势分析、财务分析、多因子选股，以及大盘市场概览数据（指数行情、涨跌统计、板块涨跌榜、股指期货贴水、ETF期权IV）。所有结果支持字典/JSON格式，便于传给LLM进一步分析。Use when Kimi needs to get Chinese A-stock market data, analyze stock trends, get financial data, screen stocks, get market overview data (indices, sectors, statistics, futures basis, ETF IV), or provide trading decision support with structured data output for LLM processing.
---

# Stockton - A股量化分析工具（Akshare版）

Stockton 提供 A 股市场的完整数据获取和分析能力，包括**行情数据**、**财务分析**、**智能选股**和**大盘市场数据**，基于 **akshare** 数据源，所有结果均可转换为 **JSON 格式**，便于传给 LLM 进一步分析。

## 核心功能

### 个股数据
1. **历史行情数据获取** - 日线数据（OHLCV）、前复权处理、技术指标（MA、量比等）
2. **实时行情数据** - 最新价格、涨跌幅、量比、换手率、市盈率、市净率
3. **筹码分布数据（仅A股）** - 获利比例、平均成本、筹码集中度
4. **趋势交易分析** - 多头排列判断、买入信号生成、综合评分

### 财务分析
5. **财务报表数据** - 利润表、资产负债表、现金流量表
6. **关键财务指标** - ROE、ROA、毛利率、净利率、资产负债率、营收增长率等
7. **财务健康度评分** - 盈利能力、成长能力、财务安全、估值吸引力四维评分
8. **估值分析** - PE、PB、PS、股息率

### 智能选股
9. **预设策略选股** - 价值投资、成长投资、质量投资、蓝筹股、小盘成长
10. **自定义条件筛选** - 支持估值、成长、财务、技术、市值等多维度条件
11. **多因子评分** - 综合财务评分+技术评分排序

### 大盘市场数据
12. **主要指数行情** - 上证指数、深证成指、创业板指、科创50、沪深300等
13. **市场涨跌统计** - 上涨/下跌家数、涨停跌停数、两市成交额
14. **板块涨跌榜** - 领涨/领跌板块排名
15. **市场情绪分析** - 基于数据计算市场情绪指标
16. **股指期货贴水/升水** - IF(沪深300)、IC(中证500)、IM(中证1000)、IH(上证50)的基差、年化贴水率
17. **ETF期权隐含波动率(IV)** - 50ETF、300ETF、500ETF、创业板ETF的期权IV数据

## 快速开始

```python
from skills.stockton.scripts.data_fetcher import get_stock_data, get_stock_data_for_llm
from skills.stockton.scripts.stock_analyzer import analyze_trend, analyze_for_llm
from skills.stockton.scripts.market_analyzer import get_market_overview, analyze_market_for_llm
from skills.stockton.scripts.financial_analyzer import analyze_financial
from skills.stockton.scripts.stock_screener import screen_stocks, list_screen_strategies

# ========== 个股数据 ==========
# 获取个股数据（字典格式）
stock_result = get_stock_data('600519', days=60)

# 个股趋势分析（LLM格式）
stock_analysis = analyze_for_llm('600519', days=60)

# ========== 财务分析 ==========
# 分析个股财务状况
financial_result = analyze_financial('600519', format_type='dict')
# 或 LLM格式
financial_prompt = analyze_financial('600519', format_type='prompt')

# ========== 智能选股 ==========
# 使用预设策略选股（价值投资）
value_stocks = screen_stocks(strategy='value', top_n=10)

# 查看所有可用策略
strategies = list_screen_strategies()

# ========== 大盘数据 ==========
# 获取市场概览（字典格式）
market_result = get_market_overview(format_type='dict')

# 大盘市场分析（LLM格式）
market_analysis = analyze_market_for_llm()

# ========== 传给 LLM ==========
llm_input = f"""
{market_analysis}

---

{stock_analysis}

---

{financial_prompt}

请基于以上大盘、个股和财务数据，给出投资分析和建议。
"""
```

## 选股策略详解

### 预设策略

| 策略ID | 策略名称 | 筛选条件 | 适用场景 |
|--------|---------|---------|---------|
| `value` | 价值投资 | PE<20, PB<2, 股息率>2%, ROE>10% | 稳健型投资者，追求安全边际 |
| `growth` | 成长投资 | 营收增长>20%, 利润增长>20%, ROE>15% | 进取型投资者，追求高增长 |
| `quality` | 质量投资 | ROE>15%, 负债率<40%, 毛利率>30% | 注重企业质量和盈利能力 |
| `blue_chip` | 蓝筹股 | 市值>500亿, PE<25, 股息率>2%, ROE>12% | 追求稳定分红的大盘股 |
| `small_cap_growth` | 小盘成长 | 市值<200亿, 营收增长>30%, 利润增长>30% | 高风险高回报的小盘成长股 |

### 高级选股（支持板块和指数）

除了在全市场选股，还支持在指定板块或指数成分股中筛选：

```python
from skills.stockton.scripts.stock_screener import screen_stocks_advanced, list_available_indices, list_available_industries

# 1. 在沪深300成分股中选价值股
hs300_value = screen_stocks_advanced(
    strategy='value',
    index_name='沪深300',
    top_n=10
)

# 2. 在中证500成分股中选成长股
zz500_growth = screen_stocks_advanced(
    strategy='growth', 
    index_name='中证500',
    top_n=10
)

# 3. 在特定板块中选优质股
semiconductor_quality = screen_stocks_advanced(
    strategy='quality',
    industry='半导体',
    top_n=10
)

# 4. 查看支持的指数
indices = list_available_indices()
# 返回: ['沪深300', '中证500', '中证1000', '上证50']

# 5. 查看所有行业/板块
industries = list_available_industries()
# 返回: ['半导体', '白酒', '银行', '新能源', ...]
```

**支持的指数范围**：
- **沪深300**：大盘蓝筹，A股核心资产
- **中证500**：中盘成长，行业龙头
- **中证1000**：小盘成长，细分领域的隐形冠军
- **上证50**：超大盘，金融和消费巨头

**为什么要按板块/指数选股？**
1. **聚焦优质池**：指数成分股经过筛选，基本面相对较好，避免踩雷垃圾股
2. **风格匹配**：大盘股用价值投资，成长股用成长策略，提高成功率
3. **行业轮动**：在不同板块间轮动配置，把握市场热点

### 动量策略选股

动量策略基于"强者恒强"的市场现象，追逐上涨趋势中的股票。

```python
from skills.stockton.scripts.stock_screener import screen_stocks, ScreenCriteria

# 1. 纯价格动量策略 - 选近期涨幅最大的股票
momentum_stocks = screen_stocks(strategy='momentum', top_n=20)

# 2. 双动量策略 - 绝对动量+相对动量+基本面过滤
dual_momentum_stocks = screen_stocks(strategy='dual_momentum', top_n=20)

# 3. 自定义动量条件
from skills.stockton.scripts.stock_screener_advanced import screen_by_criteria
criteria = ScreenCriteria(
    momentum_20d_min=10,      # 20日涨跌幅>10%
    momentum_60d_min=20,      # 60日涨跌幅>20%
    require_positive_momentum=True,  # 要求所有周期动量为正
    index_components='沪深300'  # 只在沪深300中选
)
results = screen_by_criteria(criteria, top_n=10)
```

**动量策略参数说明**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `momentum_20d_min` | 最小20日涨跌幅(%) | 10 |
| `momentum_60d_min` | 最小60日涨跌幅(%) | 15 |
| `momentum_120d_min` | 最小120日涨跌幅(%) | - |
| `require_positive_momentum` | 是否要求所有周期动量为正 | False |

**动量评分体系**（额外最高30分）：
- 20日动量>20%：+10分
- 60日动量>30%：+10分  
- 120日动量>50%：+5分
- 趋势一致性（各周期都上涨）：+5分

**双动量策略原理**：
1. **绝对动量**：股票本身的20日、60日涨跌幅必须为正（趋势向上）
2. **相对动量**：在同池股票中选择动量最强的
3. **基本面过滤**：叠加ROE>8%、负债率<60%等条件，避免纯投机

### 选股结果解读

选股结果包含以下维度评分：
- **财务评分** (0-70分)：基于盈利能力、成长能力、财务安全的综合评估
- **技术评分** (0-50分)：基于历史K线数据的技术分析（无需实时接口）
- **综合评分** (0-120分)：总分90+为买入级，70-90为关注级，<70为观望级

### 技术面选股（基于历史K线数据）

技术评分基于数据库中缓存的历史K线数据计算，无需调用实时行情接口：

| 技术信号 | 评分 | 说明 |
|---------|------|------|
| 强势上涨 (>5%) | +15 | 突破形态，短期强势 |
| 温和上涨 (2-5%) | +10 | 稳健上涨 |
| 小幅上涨 (0-2%) | +5 | 温和走势 |
| 多头排列 | +15 | MA5 > MA10 > MA20，趋势向上 |
| 突破MA20 (>5%) | +10 | 价格突破20日均线 |
| 站稳MA20 (>0%) | +5 | 价格在MA20上方 |
| 放量 (>2倍量比) | +10 | 成交量放大，资金关注 |
| 温和放量 (>1.5倍) | +5 | 成交量温和放大 |

**技术因子说明**：
- **多头排列**：短期均线在长期均线上方，趋势向上
- **突破形态**：价格相对MA20的位置，判断突破强度
- **量比**：当日成交量/5日平均成交量，判断资金活跃度
- **涨跌幅**：基于最近一个交易日的收盘价变化

**数据源**：技术指标从本地数据库获取，数据来源于已缓存的历史K线（`stock_daily`表中的`ma5`、`ma10`、`ma20`、`volume_ratio`等字段）

## 数据分析提示

### 财务分析要点

**盈利能力指标**：
- **ROE>15%**：优秀公司的标志，说明资本利用效率高
- **毛利率>30%**：说明有定价权和竞争优势
- **净利率>10%**：扣除费用后的真实盈利能力

**成长能力指标**：
- **营收增长>20%**：高成长公司的门槛
- **利润增长>营收增长**：说明规模效应显现，盈利能力增强

**财务安全指标**：
- **资产负债率<50%**：财务稳健，抗风险能力强
- **经营现金流>净利润**：利润有现金支撑，非账面利润

**估值指标**：
- **PE<20**：相对低估（成熟行业）
- **PE 20-40**：合理估值（成长行业）
- **PE>40**：高估或极高成长预期

### 股指期货贴水/升水分析
期货相对现货的升贴水反映市场情绪和机构对冲需求：

- **深度贴水**（年化<-5%）：期货大幅低于现货，反映市场悲观情绪，可能预示短期反弹或中性对冲需求强
- **轻度贴水**（年化-2%~-5%）：正常对冲成本范围，中性偏谨慎情绪
- **平水附近**（年化-2%~+2%）：市场情绪均衡，无明确方向
- **升水**（年化>+2%）：期货高于现货，反映乐观情绪或分红预期
- **跨品种比较**：IM贴水>IC>IF时，小盘股悲观情绪更重；反之则大盘股承压

### ETF期权隐含波动率(IV)分析
IV反映市场对未来的波动预期，是"恐慌指数"的微观版本：

- **IV<15%**：低波动环境，适合卖方策略，但需警惕波动率突变风险
- **IV 15%-25%**：正常波动区间，市场情绪平稳
- **IV>25%**：高波动环境，恐慌情绪升温，或存在事件驱动机会
- **期限结构**：近月IV>远月为Backwardation（恐慌）；近月<远月为Contango（平稳）
- **Skew偏度**：虚值Put IV>虚值Call IV时，市场担忧下跌风险（保护性需求）
- **跨品种比较**：小盘股(500/创业板)IV>大盘股(50/300)时，市场担忧尾部风险

## 最佳实践

### 1. 综合分析流程

```python
# 完整分析一只股票的流程
stock_code = '600519'

# 1. 获取基本面数据
financial = analyze_financial(stock_code, format_type='dict')

# 2. 获取技术面数据
technical = analyze_for_llm(stock_code, days=60)

# 3. 判断大盘环境
market = get_market_overview(format_type='dict')

# 4. 综合判断
# - 财务评分>70且技术趋势向上：考虑买入
# - 财务评分<50或技术趋势向下：回避
# - 大盘贴水扩大：降低仓位
```

### 2. 定期选股策略

```python
# 每周运行一次选股，构建观察池

# 价值股（核心持仓）
value_stocks = screen_stocks(strategy='value', top_n=20)

# 成长股（卫星配置）
growth_stocks = screen_stocks(strategy='growth', top_n=10)

# 结合财务分析深度研究
for stock in value_stocks[:5]:
    financial = analyze_financial(stock['stock_code'], format_type='dict')
    # 筛选财务评分>75的进入观察池
```

### 3. 风险控制要点

1. **分散投资**：单个股票仓位不超过20%
2. **止损纪律**：技术破位（如跌破MA20）或基本面恶化时止损
3. **关注贴水**：股指期货深度贴水时降低仓位
4. **估值警戒**：PE>50或PB>10时警惕估值风险

## 数据源

- **akshare**: 主要数据源，支持多源切换（东方财富→新浪→腾讯→网易）
- **efinance**: 备用数据源（如安装则优先使用）

## 数据存储与缓存

### SQLite 数据库

所有数据自动存储在本地 SQLite 数据库 (`data/stock_data.db`)，提供以下功能：

1. **日线数据缓存** - 自动缓存获取过的股票K线数据，避免重复网络请求
2. **股票名称映射** - 本地维护股票代码-名称映射表，快速查询
3. **指数成分股缓存** - 沪深300、中证500、中证1000、上证50成分股每日自动缓存
4. **技术指标存储** - MA5/MA10/MA20、量比等技术指标随K线数据一起存储

### 数据库接口

```python
from skills.stockton.scripts.storage import get_db

db = get_db()

# 查询股票名称
name = db.get_stock_name('600519')  # 返回：贵州茅台

# 获取指数成分股（带1日缓存）
components = db.get_index_components('000300', max_age_days=1)

# 获取技术指标数据
tech_data = db.get_latest_tech_data('600519')
# 返回：{
#   'close': 1401.88, 'pct_chg': 0.35, 'volume_ratio': 0.64,
#   'ma5': 1390.2, 'ma10': 1380.5, 'ma20': 1370.3,
#   'bullish_arrangement': False,  # 多头排列
#   'price_vs_ma20': 2.3  # 相对MA20位置(%)
# }
```

## 性能优化

- **缓存机制**：市场概览数据缓存180秒，避免重复请求
- **批量获取**：选股时限制处理股票数量，保证响应速度
- **数据持久化**：日线数据自动存储到SQLite，加速后续查询
- **指数成分股缓存**：每日自动更新，避免重复调用网络接口

## 定时任务 - 数据预加载

由于选股时**不会**自动获取缺失的历史K线数据（避免选股过程太慢），建议设置定时任务在收盘后预加载数据。

### 为什么需要预加载？

选股时技术评分的计算依赖历史K线数据（MA5/MA10/MA20、量比等）：
- **有K线数据**：综合评分 = 财务评分(0-70) + 技术评分(0-50)
- **无K线数据**：综合评分 = 财务评分(0-70) + 0

预加载后，选股时所有股票都有完整的技术评分，排名更准确。

### 预加载脚本

```python
from skills.stockton.scripts.preload_data import preload_index_data, check_preload_status

# 1. 预加载指定指数成分股（收盘后执行）
result = preload_index_data(
    indices=['沪深300', '中证500'],  # 要加载的指数
    days=60                           # 获取60天历史数据
)
print(f"成功加载 {result['success_count']} 只股票")

# 2. 检查数据覆盖情况
status = check_preload_status(['沪深300'])
# 返回: {'沪深300': {'total': 300, 'has_data': 298, 'coverage': '99.3%'}}

# 3. 命令行执行
# python -m skills.stockton.scripts.preload_data --indices 沪深300 中证500 --days 60
# python -m skills.stockton.scripts.preload_data --check  # 仅检查状态
```

### OpenClaw 定时任务配置

在 OpenClaw 中设置每晚 19:00（收盘后）自动执行预加载：

**方法1：使用 OpenClaw 的 scheduler 配置**（如支持）

```json
{
  "scheduled_tasks": [
    {
      "name": "preload-stock-data",
      "description": "每晚预加载沪深300和中证500数据",
      "schedule": "0 19 * * 1-5",
      "timezone": "Asia/Shanghai",
      "action": {
        "type": "python",
        "code": "from skills.stockton.scripts.preload_data import preload_index_data; preload_index_data(['沪深300', '中证500'], days=60)"
      }
    }
  ]
}
```

**方法2：使用系统定时任务**（推荐）

Linux/Mac (crontab):
```bash
# 编辑 crontab
crontab -e

# 添加行：周一至周五 19:00 执行
0 19 * * 1-5 cd /path/to/stockton && python -m skills.stockton.scripts.preload_data --indices 沪深300 中证500 --days 60 >> /var/log/stockton_preload.log 2>&1
```

Windows (任务计划程序):
```powershell
# PowerShell 创建计划任务
$action = New-ScheduledTaskAction -Execute "python" -Argument "-m skills.stockton.scripts.preload_data --indices 沪深300 中证500 --days 60" -WorkingDirectory "D:\coding\projects\stockton"
$trigger = New-ScheduledTaskTrigger -Daily -At 19:00
$settings = New-ScheduledTaskSettingsSet
Register-ScheduledTask -TaskName "StocktonPreload" -Action $action -Trigger $trigger -Settings $settings
```

### 预加载执行时间参考

| 指数 | 成分股数量 | 预计耗时 |
|------|-----------|---------|
| 沪深300 | 300只 | 5-8分钟 |
| 中证500 | 500只 | 8-12分钟 |
| 中证1000 | 1000只 | 15-20分钟 |

**注意**：首次加载需要全部获取，后续只获取缺失的数据（断点续传）。

## 版本

- 版本号：1.2.0
- 更新日期：2026-03-11
- 更新内容：
  - 新增财务分析模块
  - 新增智能选股功能（支持5种预设策略）
  - 新增板块选股和指数成分股选股功能
  - 新增多因子评分体系（财务+技术）
  - 新增数据库存储层，支持股票名称查询和指数成分股缓存
  - 技术面选股基于历史K线数据，无需实时接口
  - 完善文档和最佳实践
