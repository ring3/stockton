# Data Sources Reference

Understanding the multi-source data architecture and fallback logic.

## Architecture Overview

```
User Request
    ↓
DataFetcherManager (Priority 0, 1, 2...)
    ↓
EfinanceFetcher → AkshareFetcher → [Future: BaostockFetcher, TushareFetcher]
    ↓
Database Cache (SQLite)
    ↓
Raw Data
```

## Data Source Priority

### Priority 0: EfinanceFetcher

**Package:** `efinance`

**Pros:**
- Fast response times
- Clean API design
- Automatic retry logic
- Good for bulk requests

**Cons:**
- Limited data types (no financial reports, no index constituents)
- Fewer technical indicators pre-calculated

**Best for:**
- Historical K-line data
- Real-time quotes
- ETF data

**Rate limiting:** 1.5-3.0 seconds between requests

### Priority 1: AkshareFetcher

**Package:** `akshare`

**Pros:**
- Comprehensive data coverage
- Financial reports
- Index constituents
- Industry classifications
- Derivatives data (futures, options)
- Multiple backup sources (Eastmoney → Sina → Tencent → Netease)

**Cons:**
- Slower than efinance
- More prone to API changes
- Requires more retry logic

**Best for:**
- Financial analysis
- Stock screening
- Market overview data
- Index constituents

**Rate limiting:** 2.0-5.0 seconds between requests

### Priority 2: Database Cache

**Type:** SQLite (`data/stock_data.db`)

**Purpose:**
- Avoid re-fetching historical data
- Store computed technical indicators
- Cache index constituents
- Enable offline analysis

**Cache policies:**
| Data type | Cache duration | Notes |
|-----------|---------------|-------|
| Historical K-line | Permanent | Until manually cleared |
| Index constituents | 1 day | Updates daily |
| Real-time quotes | No cache | Always fresh |
| Financial reports | 90 days | Quarterly updates |

## Data Source Comparison

| Feature | Efinance | Akshare | Database |
|---------|----------|---------|----------|
| A-share K-line | ✅ Fast | ✅ Reliable | ✅ Cached |
| ETF data | ✅ | ✅ | ✅ |
| HK stocks | ✅ | ✅ | ✅ |
| Financial reports | ❌ | ✅ | ✅ Cached |
| Index constituents | ❌ | ✅ | ✅ Cached |
| Industry data | ❌ | ✅ | ✅ Cached |
| Futures basis | ❌ | ✅ | ❌ |
| Options IV | ❌ | ✅ | ❌ |
| Real-time quotes | ✅ | ⚠️ (blocked often) | ❌ |

## Fallback Behavior

### Scenario 1: Efinance succeeds
```
User requests 600519 data
    ↓
EfinanceFetcher succeeds in 0.5s
    ↓
Return data (fast path)
```

### Scenario 2: Efinance fails, Akshare succeeds
```
User requests 600519 data
    ↓
EfinanceFetcher fails (timeout)
    ↓
Wait 2s, try AkshareFetcher
    ↓
Akshare succeeds in 1s
    ↓
Return data (3s total)
```

### Scenario 3: All sources fail
```
User requests 600519 data
    ↓
Efinance fails → Akshare fails
    ↓
Check database cache
    ↓
If cache exists: Return cached data
If no cache: Raise DataFetchError
```

## Network and Proxy Handling

### Automatic Proxy Bypass

Both fetchers automatically clear proxy settings to avoid connection issues:

```python
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
```

### Connection Error Handling

Common errors and handling:

| Error | Cause | Handling |
|-------|-------|----------|
| Timeout | Network slow | Retry with exponential backoff |
| Connection refused | Proxy/firewall | Clear proxy, retry |
| SSLError | Certificate issues | Log warning, try alternative source |
| Rate limit | Too many requests | Sleep 5-10s, retry |
| Empty response | API change | Log error, try next source |

## Adding a New Data Source

To add BaostockFetcher (example):

```python
# In data_provider/baostock_fetcher.py
from .base import BaseFetcher

class BaostockFetcher(BaseFetcher):
    name = "BaostockFetcher"
    priority = 2  # Lower priority than efinance/akshare
    
    def _fetch_raw_data(self, stock_code, start_date, end_date):
        # Implement baostock-specific fetching
        pass
    
    def _normalize_data(self, df, stock_code):
        # Convert baostock columns to standard format
        pass
    
    # Implement other abstract methods...
```

Register in `DataFetcherManager._init_default_fetchers()`:

```python
try:
    from .baostock_fetcher import BaostockFetcher
    self._fetchers.append(BaostockFetcher())
except Exception as e:
    logger.debug(f"BaostockFetcher unavailable: {e}")
```

## Data Quality Indicators

Each data response includes source information:

```python
{
    'success': True,
    'code': '600519',
    'data_source': 'EfinanceFetcher',  # or 'AkshareFetcher'
    'daily_data': [...]
}
```

Use this to:
- Monitor which sources are working
- Identify data quality issues
- Optimize priority order

## Preloading Strategy

To optimize screening performance, preload data after market close:

```python
from skills.stockton.scripts.preload_data import preload_index_data

# Preload major indices
preload_index_data(['沪深300', '中证500', '中证1000'], days=130)
```

**Why 130 days?**
- 60 days: Short-term trend analysis
- 120 days: Momentum calculation (20d, 60d, 120d)
- 130 days: Buffer for weekends/holidays

**Best time to run:**
- After market close (15:30 CN time)
- Before next market open (09:15 CN time)
- Recommended: 19:00-21:00 daily

## Offline Mode

If all external sources fail, skill can operate in limited offline mode using database cache:

```python
# Check if data exists in cache
db = get_db()
if db.has_today_data('600519'):
    # Use cached data
    data = db.get_analysis_context('600519')
else:
    # Raise error - no network and no cache
    raise DataFetchError("No network and no cached data")
```

**Limitations in offline mode:**
- Real-time quotes unavailable
- Market overview unavailable
- Index constituent updates unavailable
- Historical data only (up to last cache date)
