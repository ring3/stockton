# Stockton API Reference

Complete API documentation for all modules.

## Data Fetcher Module

### `get_stock_data(stock_code, days=60, start_date=None, end_date=None)`

Get historical stock data with technical indicators.

**Parameters:**
- `stock_code` (str): Stock code (e.g., '600519', '000001')
- `days` (int): Number of days to fetch (default: 60)
- `start_date` (str, optional): Start date 'YYYY-MM-DD'
- `end_date` (str, optional): End date 'YYYY-MM-DD'

**Returns:**
```python
{
    'success': True,
    'code': '600519',
    'name': '贵州茅台',
    'daily_data': [...],
    'data_source': 'EfinanceFetcher',
    'realtime_quote': {...}  # Optional
}
```

### `get_stock_data_for_llm(stock_code, days=60, format_type="prompt")`

Get stock data formatted for LLM consumption.

**Parameters:**
- `format_type` (str): "prompt" or "json"

**Returns:** Formatted string for LLM.

## Stock Analyzer Module

### `analyze_for_llm(stock_code, days=60)`

Analyze stock trend and generate LLM-formatted report.

**Analysis includes:**
- Price trend (up/down)
- Moving averages (MA5/MA10/MA20)
- Volume ratio
- Chip distribution (if available)
- Trading signals

**Signals:**
- `buy`: Price > MA5 > MA10 > MA20, Volume ratio > 1.5
- `strong_buy`: All buy conditions + price breakout
- `hold`: Price between MA10 and MA20
- `sell`: Price < MA20

## Financial Analyzer Module

### `analyze_financial(stock_code, format_type="dict")`

Analyze financial health of a company.

**Returns:**
```python
{
    'stock_code': '600519',
    'stock_name': '贵州茅台',
    'health_score': 85,  # 0-100
    'profitability': {
        'roe': 25.5,
        'gross_margin': 91.5,
        'net_margin': 52.5
    },
    'growth': {
        'revenue_growth': 17.0,
        'profit_growth': 19.0
    },
    'safety': {
        'debt_ratio': 25.0,
        'current_ratio': 3.5
    },
    'valuation': {
        'pe_ratio': 28.5,
        'pb_ratio': 8.5
    }
}
```

**Health Score Calculation:**
- Profitability: 0-25 points (ROE, margins)
- Growth: 0-25 points (revenue/profit growth)
- Safety: 0-20 points (debt, current ratio)
- Valuation: 0-20 points (PE, PB ratios)
- Bonus: 0-10 points (consistent performance)

## Stock Screener Module

### `screen_stocks(strategy='value', top_n=20, market='A股')`

Screen stocks using preset strategies.

**Strategies:**

| Strategy | Criteria | Use Case |
|----------|----------|----------|
| `value` | PE<20, PB<2, Dividend>2%, ROE>10% | Conservative investors |
| `growth` | Revenue growth>20%, Profit growth>20%, ROE>15% | Growth investors |
| `quality` | ROE>15%, Debt<40%, Gross margin>30% | Quality-focused |
| `blue_chip` | Market cap>50B, PE<25, Dividend>2% | Dividend investors |
| `small_cap_growth` | Market cap<20B, Revenue>30%, Profit>30% | High-risk/high-reward |
| `momentum` | 20d return>10%, 60d return>15%, Above MA20 | Trend followers |
| `dual_momentum` | Absolute momentum + Quality filter | Momentum investors |

### `screen_stocks_advanced(strategy='value', index_name=None, industry=None, top_n=20)`

Advanced screening with index/industry filters.

**Index Options:**
- `沪深300` (CSI300): Large-cap blue chips
- `中证500` (CSI500): Mid-cap growth
- `中证1000` (CSI1000): Small-cap
- `上证50` (SSE50): Mega-cap

## Market Analyzer Module

### `get_market_overview(format_type="dict")`

Get comprehensive market overview.

**Returns:**
```python
{
    'indices': {
        'sh000001': {'name': '上证指数', 'price': 3050.00, 'change_pct': 0.50},
        'sz399001': {'name': '深证成指', 'price': 9500.00, 'change_pct': 0.80}
    },
    'statistics': {
        'up_count': 2500,
        'down_count': 1500,
        'limit_up': 50,
        'limit_down': 10
    },
    'futures_basis': {
        'IF': {'basis_rate': -2.5, 'annualized': -8.5},
        'IC': {'basis_rate': -3.0, 'annualized': -10.2}
    },
    'etf_iv': {
        '510050': {'iv': 18.5, 'name': '50ETF'},
        '510300': {'iv': 20.2, 'name': '300ETF'}
    }
}
```

### `analyze_market_for_llm()`

Generate LLM-formatted market analysis including:
- Index performance summary
- Market sentiment (bullish/bearish/neutral)
- Sector performance (top 5 gainers/losers)
- Futures basis interpretation
- IV level analysis

## Data Preloading Module

### `preload_index_data(indices=['沪深300', '中证500'], days=60)`

Preload historical data for index constituents.

**Use case:** Run after market close to prepare for next day's analysis.

**Example:**
```python
from skills.stockton.scripts.preload_data import preload_index_data

result = preload_index_data(['沪深300', '中证500'], days=60)
print(f"Loaded {result['success_count']} stocks")
```

## Database Storage Module

### `get_db()`

Get database manager instance for direct access.

**Features:**
- Automatic caching of historical data
- Index constituent caching
- Stock name lookup
- Technical indicator storage

**Example:**
```python
from skills.stockton.scripts.storage import get_db

db = get_db()
name = db.get_stock_name('600519')
momentum = db.get_momentum_data('600519')
tech_data = db.get_latest_tech_data('600519')
```

## Error Handling

All functions return structured error responses:

```python
{
    'success': False,
    'error_message': 'Description of what went wrong',
    'code': '600519'
}
```

Common error codes:
- `DataFetchError`: Network or data source issues
- `RateLimitError`: Too many requests
- `DataSourceUnavailableError`: All data sources failed
