---
name: stockton
description: A股股票数据分析与量化选股工具，提供个股历史K线、技术指标、财务分析、多因子选股和市场概览数据。当用户询问"分析股票"、"获取股票数据"、"选股"、"查看大盘"、"分析财报"，或提到具体股票代码（如600519、000001）、指数（如沪深300、中证500）时使用。
license: MIT
compatibility: 需要 Python 3.11+、pandas、numpy、akshare。支持 Claude.ai、Claude Code 和 API 环境（需启用代码执行）。
metadata:
  author: Stockton Team
  version: 1.2.0
  category: 工作流自动化
  mcp-server: 无
  last_updated: 2026-03-11
---

# Stockton - A股量化分析工具

Stockton 提供完整的A股市场数据获取和分析能力，包括**行情数据**、**财务分析**、**智能选股**和**市场概览数据**，所有结果均可转换为 **JSON 格式** 便于 LLM 分析。

## 使用说明

### 第一步：识别用户分析需求

当用户提及股票分析时，首先判断需要的分析类型：

| 用户请求类型 | 操作 | 示例 |
|-------------|------|------|
| 个股分析 | 获取历史数据 + 技术分析 | "分析一下贵州茅台" / "600519走势怎么样" |
| 财务分析 | 获取财务指标 + 健康评分 | "茅台基本面如何" / "这只股票财务状况" |
| 股票筛选 | 运行多因子筛选 | "帮我选一些价值股" / "筛选成长股" |
| 市场概览 | 获取市场统计 + 情绪 | "今天大盘怎么样" / "市场情绪如何" |
| 对比分析 | 分析多只股票 | "对比茅台和五粮液" |

### 第二步：获取股票数据

个股分析使用：

```python
from skills.stockton.scripts.data_fetcher import get_stock_data
from skills.stockton.scripts.stock_analyzer import analyze_for_llm

# 获取60天历史数据
stock_data = get_stock_data('600519', days=60)

# 获取LLM格式的分析报告
analysis = analyze_for_llm('600519', days=60)
```

**预期输出：** 包含OHLCV数据、技术指标（MA5/MA10/MA20）、趋势信号的字典。

### 第三步：分析财务健康

```python
from skills.stockton.scripts.financial_analyzer import analyze_financial

# 获取财务分析
financial = analyze_financial('600519', format_type='dict')
```

**预期输出：** 财务指标（ROE、毛利率、增长率）+ 四维健康评分（0-100分）。

### 第四步：股票筛选（如需要）

```python
from skills.stockton.scripts.stock_screener import screen_stocks

# 使用预设策略
value_stocks = screen_stocks(strategy='value', top_n=10)
growth_stocks = screen_stocks(strategy='growth', top_n=10)
momentum_stocks = screen_stocks(strategy='momentum', top_n=10)
```

**可用策略：** value（价值）、growth（成长）、quality（质量）、blue_chip（蓝筹）、small_cap_growth（小盘成长）、momentum（动量）、dual_momentum（双动量）

### 第五步：获取市场概览（如需要）

```python
from skills.stockton.scripts.market_analyzer import get_market_overview, analyze_market_for_llm

# 市场统计数据
market = get_market_overview(format_type='dict')

# LLM格式的市场分析
market_analysis = analyze_market_for_llm()
```

**预期输出：** 指数表现、涨跌家数、板块排行、期货贴水、ETF期权IV数据。

## 数据源优先级

工具使用多数据源自动降级：

1. **Efinance**（优先级0）- 首选，速度快稳定性好
2. **Akshare**（优先级1）- 全面的备用源
3. **数据库缓存** - 本地SQLite缓存已获取的数据

**缓存策略：**
- 指数成分股缓存1天
- 历史数据永久缓存（直到删除）
- 实时数据不缓存（始终获取最新）

## 使用示例

### 示例1：完整股票分析流程

**用户说：** "帮我分析一下贵州茅台这只股票"

**操作：**
1. 获取600519的60天历史数据
2. 获取财务指标和健康评分
3. 检查技术信号（均线趋势、成交量）
4. 与市场指数对比（沪深300 vs 个股）

**结果：**
```json
{
  "stock_code": "600519",
  "stock_name": "贵州茅台",
  "technical": {
    "trend": "bullish_arrangement",
    "ma5": 1400.50,
    "ma20": 1380.30,
    "signal": "hold"
  },
  "financial": {
    "health_score": 85,
    "roe": 25.5,
    "pe": 28.5,
    "rating": "excellent"
  }
}
```

### 示例2：价值股筛选

**用户说：** "帮我选一些被低估的价值股，在沪深300里面找"

**操作：**
1. 获取沪深300成分股
2. 应用价值标准（PE<20、PB<2、股息率>2%、ROE>10%）
3. 按财务评分+技术评分排序
4. 返回前10名及分析

**结果：** 10只股票的列表，包含评分和匹配因子。

### 示例3：市场情绪分析

**用户说：** "今天市场情绪怎么样？期货贴水多少？"

**操作：**
1. 获取主要指数表现（上证、深证、创业板）
2. 计算涨跌统计
3. 获取IF/IC/IM/IH期货贴水
4. 计算年化贴水/升水率

**结果：** 市场概览，包含情绪指标和期货贴水分析。

### 示例4：动量策略筛选

**用户说：** "最近哪些股票涨势比较好？用动量策略筛选一下"

**操作：**
1. 应用动量标准（20日涨幅>10%、60日涨幅>15%）
2. 检查趋势一致性（各周期动量为正）
3. 按质量过滤（ROE>8%、负债<60%）
4. 按动量评分排序

**结果：** 动量最强的股票，包含20日/60日/120日收益率和趋势一致性评分。

## 参考文档

详细文档请查看：

- `references/api_reference.md` - 完整API文档
- `references/screening_strategies.md` - 详细策略参数
- `references/data_sources.md` - 数据源详情和降级逻辑
- `references/examples.md` - 更多使用示例

## 故障排除

### 错误："No data available for stock X"（股票X无数据）

**原因：**
- 股票代码不存在
- 股票停牌/退市
- 网络连接问题

**解决：**
1. 验证股票代码正确（6位数字，沪市600xxx，深市000xxx/300xxx）
2. 检查股票是否正常交易
3. 检查网络连接
4. 重试（数据源可能临时故障）

### 错误："Datasource unavailable"（数据源不可用）

**原因：**
- 所有数据源失败（网络/代理问题）
- 缺少必要依赖

**解决：**
1. 检查代理设置（工具会自动清除代理环境变量）
2. 安装缺少的依赖：`pip install akshare pandas numpy`
3. 检查防火墙设置

### 错误："Empty results from stock screening"（选股结果为空）

**原因：**
- 筛选条件过于严格
- 数据库无缓存（首次运行）
- 指数成分股数据未缓存

**解决：**
1. 放宽筛选条件（如提高PE上限、降低ROE下限）
2. 先运行预加载：`python -m skills.stockton.scripts.preload_data --indices 沪深300`
3. 检查日志中的数据源错误

### 警告："Efinance not available, using Akshare"（Efinance不可用，使用Akshare）

**原因：**
- Efinance包未安装
- Efinance初始化失败

**解决：**
- 安装efinance：`pip install efinance`
- 工具会自动降级到Akshare（较慢但可用）

### 选股时响应缓慢

**原因：**
- 首次获取多只股票数据
- 网络延迟

**解决：**
- 收盘后使用预加载脚本预加载数据
- 使用指数内选股（比全市场快）
- 限制 `top_n` 参数减少处理量

## 最佳实践

### 股票分析

1. **始终考虑市场背景** - 个股表现应结合市场趋势分析
2. **技术面+基本面结合** - 同时使用 `analyze_for_llm()` 和 `analyze_financial()` 获得完整图景
3. **考虑时间周期** - 短期交易侧重技术，长期侧重基本面

### 股票筛选

1. **使用指数成分股** - 在沪深300/中证500内筛选更快且质量更高
2. **预加载数据** - 收盘后运行 `preload_data.py` 为次日分析做准备
3. **多策略组合** - 分别运行价值+成长+动量策略，然后对比结果

### 市场分析

1. **期货贴水是关键** - 反映机构情绪；深度贴水需谨慎
2. **IV水平重要** - 高IV（>25%）表示事件风险或恐慌；低IV（<15%）表示自满
3. **板块轮动** - 使用板块排行识别当前市场主题

## 版本历史

- v1.2.0 (2026-03-11)：添加动量策略、双动量、数据库缓存、统一数据提供者接口
- v1.1.0 (2026-03-01)：添加财务分析器、股票筛选器（5种预设策略）
- v1.0.0 (2026-02-15)：初始版本，基础数据获取和技术分析
