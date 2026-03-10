---
name: stockton
description: A股行情数据获取与分析工具（基于akshare），提供个股历史K线、实时行情、技术指标计算、趋势分析，以及大盘市场概览数据（指数行情、涨跌统计、板块涨跌榜、股指期货贴水、ETF期权IV）。所有结果支持字典/JSON格式，便于传给LLM进一步分析。Use when Kimi needs to get Chinese A-stock market data, analyze stock trends, get market overview data (indices, sectors, statistics, futures basis, ETF IV), or provide trading decision support with structured data output for LLM processing.
---

# Stockton - A股行情数据工具（Akshare版）

Stockton 提供 A 股市场的完整数据获取和分析能力，包括**个股数据**和**大盘市场数据**，基于 **akshare** 数据源，所有结果均可转换为 **JSON 格式**，便于传给 LLM 进一步分析。

## 核心功能

### 个股数据
1. **历史行情数据获取** - 日线数据（OHLCV）、前复权处理、技术指标（MA、量比等）
2. **实时行情数据** - 最新价格、涨跌幅、量比、换手率、市盈率、市净率
3. **筹码分布数据（仅A股）** - 获利比例、平均成本、筹码集中度
4. **趋势交易分析** - 多头排列判断、买入信号生成、综合评分

### 大盘市场数据
1. **主要指数行情** - 上证指数、深证成指、创业板指、科创50、沪深300等
2. **市场涨跌统计** - 上涨/下跌家数、涨停跌停数、两市成交额
3. **板块涨跌榜** - 领涨/领跌板块排名
4. **市场情绪分析** - 基于数据计算市场情绪指标
5. **股指期货贴水/升水** - IF(沪深300)、IC(中证500)、IM(中证1000)、IH(上证50)的基差、年化贴水率
6. **ETF期权隐含波动率(IV)** - 50ETF、300ETF、500ETF、创业板ETF的期权IV数据

## 快速开始

```python
from skills.stockton.scripts.data_fetcher import get_stock_data, get_stock_data_for_llm
from skills.stockton.scripts.stock_analyzer import analyze_trend, analyze_for_llm
from skills.stockton.scripts.market_analyzer import get_market_overview, analyze_market_for_llm

# ========== 个股数据 ==========
# 获取个股数据（字典格式）
stock_result = get_stock_data('600519', days=60)

# 个股趋势分析（LLM格式）
stock_analysis = analyze_for_llm('600519', days=60)

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

请基于以上大盘和个股数据，给出交易建议。
"""
```

## 数据分析提示

当将数据传给 LLM 分析时，建议关注以下维度：

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

## 数据源

- **akshare**: 主要数据源，支持多源切换（东方财富→新浪→腾讯→网易）
- **efinance**: 备用数据源（如安装则优先使用）

## 版本

- 版本号：1.0.0
- 更新日期：2026-03-11
