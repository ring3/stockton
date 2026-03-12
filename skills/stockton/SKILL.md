---
name: stockton
description: A-share stock market data analysis and quantitative screening tool. Provides historical K-line data, technical indicators, financial analysis, multi-factor stock screening, and market overview data (indices, sectors, futures basis, ETF IV). All results support JSON format for LLM processing. Use when user asks to "analyze stock", "get stock data", "screen stocks", "check market data", "analyze financial reports", or mentions specific stock codes (e.g., 600519, 000001), indices (e.g., CSI300, CSI500), or market trends.
license: MIT
compatibility: Requires Python 3.11+, pandas, numpy, akshare. Works in Claude.ai, Claude Code, and API environments with code execution enabled.
metadata:
  author: Stockton Team
  version: 1.2.0
  category: Workflow Automation
  mcp-server: none
  last_updated: 2026-03-11
---

# Stockton - A股量化分析工具

Stockton provides complete A-share market data and analysis capabilities, including **market data**, **financial analysis**, **intelligent stock screening**, and **market overview data**. All results can be converted to **JSON format** for LLM analysis.

## Instructions

### Step 1: Identify User's Analysis Needs

When user mentions stock analysis, first determine what type of analysis they need:

| User Request Type | Action | Example Query |
|------------------|--------|---------------|
| Single stock analysis | Get historical data + technical analysis | "Analyze 贵州茅台" / "600519走势如何" |
| Financial analysis | Get financial indicators + health score | "分析茅台的财务状况" / "这只股票基本面如何" |
| Stock screening | Run multi-factor screening | "帮我选一些价值股" / "筛选成长股" |
| Market overview | Get market statistics + sentiment | "今天大盘怎么样" / "市场情绪如何" |
| Comparative analysis | Analyze multiple stocks | "对比一下茅台和五粮液" |

### Step 2: Get Stock Data

For single stock analysis, use:

```python
from skills.stockton.scripts.data_fetcher import get_stock_data
from skills.stockton.scripts.stock_analyzer import analyze_for_llm

# Get 60 days of historical data
stock_data = get_stock_data('600519', days=60)

# Get LLM-formatted analysis
analysis = analyze_for_llm('600519', days=60)
```

**Expected output:** Dictionary with OHLCV data, technical indicators (MA5/MA10/MA20), trend signals.

### Step 3: Analyze Financial Health

```python
from skills.stockton.scripts.financial_analyzer import analyze_financial

# Get financial analysis
financial = analyze_financial('600519', format_type='dict')
```

**Expected output:** Financial indicators (ROE, margins, growth rates) + 4-dimension health score (0-100).

### Step 4: Screen Stocks (if requested)

```python
from skills.stockton.scripts.stock_screener import screen_stocks

# Use preset strategies
value_stocks = screen_stocks(strategy='value', top_n=10)
growth_stocks = screen_stocks(strategy='growth', top_n=10)
momentum_stocks = screen_stocks(strategy='momentum', top_n=10)
```

**Available strategies:** value, growth, quality, blue_chip, small_cap_growth, momentum, dual_momentum

### Step 5: Get Market Overview (if requested)

```python
from skills.stockton.scripts.market_analyzer import get_market_overview, analyze_market_for_llm

# Market statistics
market = get_market_overview(format_type='dict')

# LLM-formatted market analysis
market_analysis = analyze_market_for_llm()
```

**Expected output:** Index performance, up/down counts, sector rankings, futures basis, ETF IV data.

## Data Source Priority

The skill uses multiple data sources with automatic fallback:

1. **Efinance** (Priority 0) - Preferred for speed and stability
2. **Akshare** (Priority 1) - Comprehensive fallback
3. **Database Cache** - Local SQLite for previously fetched data

**Cache Strategy:**
- Index components cached for 1 day
- Historical data cached permanently (until deleted)
- Real-time data not cached (always fetched fresh)

## Examples

### Example 1: Complete Stock Analysis Workflow

**User says:** "帮我分析一下贵州茅台这只股票"

**Actions:**
1. Fetch 60-day historical data for 600519
2. Get financial indicators and health score
3. Check technical signals (MA trends, volume)
4. Compare with market indices (CSI300 vs individual stock)

**Result:**
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

### Example 2: Value Stock Screening

**User says:** "帮我选一些被低估的价值股，在沪深300里面找"

**Actions:**
1. Get CSI300 constituent stocks
2. Apply value criteria (PE<20, PB<2, dividend yield>2%, ROE>10%)
3. Rank by financial score + technical score
4. Return top 10 with analysis

**Result:** List of 10 stocks with scores and matching factors.

### Example 3: Market Sentiment Analysis

**User says:** "今天市场情绪怎么样？期货贴水多少？"

**Actions:**
1. Get main indices performance (SSE, SZSE, ChiNext)
2. Calculate up/down statistics
3. Get futures basis for IF/IC/IM/IH
4. Calculate annualized discount/premium rates

**Result:** Market overview with sentiment indicators and futures basis analysis.

### Example 4: Momentum Strategy Screening

**User says:** "最近哪些股票涨势比较好？用动量策略筛选一下"

**Actions:**
1. Apply momentum criteria (20-day return >10%, 60-day return >15%)
2. Check trend consistency (positive momentum across timeframes)
3. Filter by basic quality (ROE>8%, debt<60%)
4. Rank by momentum score

**Result:** Top momentum stocks with 20d/60d/120d returns and trend consistency scores.

## References

For detailed documentation, see:

- `references/api_reference.md` - Complete API documentation
- `references/screening_strategies.md` - Detailed strategy parameters
- `references/data_sources.md` - Data source details and fallback logic
- `references/examples.md` - More usage examples

## Troubleshooting

### Error: "No data available for stock X"

**Cause:** 
- Stock code doesn't exist
- Stock is suspended/delisted
- Network connectivity issues to data sources

**Solution:**
1. Verify stock code is correct (6 digits, SH:600xxx, SZ:000xxx/300xxx)
2. Check if stock is trading normally
3. Check network connectivity
4. Try again (data sources may have temporary issues)

### Error: "Datasource unavailable"

**Cause:**
- All data sources failed (network/proxy issues)
- Required dependencies not installed

**Solution:**
1. Check proxy settings (skill clears proxy env vars automatically)
2. Install missing dependencies: `pip install akshare pandas numpy`
3. Check firewall settings

### Error: "Empty results from stock screening"

**Cause:**
- Screening criteria too strict
- No stocks in database cache (first run)
- Index constituent data not cached

**Solution:**
1. Relax screening criteria (e.g., increase PE max, decrease ROE min)
2. Run preloading first: `python -m skills.stockton.scripts.preload_data --indices 沪深300`
3. Check logs for data source errors

### Warning: "Efinance not available, using Akshare"

**Cause:**
- Efinance package not installed
- Efinance initialization failed

**Solution:**
- Install efinance: `pip install efinance`
- Skill will automatically fall back to Akshare (slower but functional)

### Slow Response During Stock Screening

**Cause:**
- First-time data fetching for many stocks
- Network latency to data sources

**Solution:**
- Pre-load data after market close using the preload script
- Use index-based screening (faster than market-wide)
- Limit `top_n` parameter to reduce processing

## Best Practices

### For Stock Analysis

1. **Always check market context** - Individual stock performance should be analyzed alongside market trends
2. **Combine technical + fundamental** - Use both `analyze_for_llm()` and `analyze_financial()` for complete picture
3. **Consider time horizon** - Short-term trades need technical focus, long-term needs fundamental focus

### For Stock Screening

1. **Use index components** - Screening within CSI300/CSI500 is faster and higher quality than market-wide
2. **Pre-load data** - Run `preload_data.py` after market close for next-day analysis
3. **Multiple strategies** - Run value + growth + momentum separately, then compare results

### For Market Analysis

1. **Futures basis is key** - Indicates institutional sentiment; deep discount suggests caution
2. **IV levels matter** - High IV (>25%) suggests event risk or panic; low IV (<15%) suggests complacency
3. **Sector rotation** - Use sector rankings to identify current market themes

## Version History

- v1.2.0 (2026-03-11): Added momentum strategies, dual momentum, database caching, unified data provider interface
- v1.1.0 (2026-03-01): Added financial analyzer, stock screener with 5 preset strategies
- v1.0.0 (2026-02-15): Initial release with basic data fetching and technical analysis
