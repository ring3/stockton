# Usage Examples

Practical examples for common use cases.

## Example 1: Daily Market Analysis Workflow

**Use case:** Generate daily market summary for investment committee

```python
from skills.stockton.scripts.market_analyzer import analyze_market_for_llm
from skills.stockton.scripts.financial_analyzer import analyze_financial
from skills.stockton.scripts.stock_screener import screen_stocks

# 1. Get market overview
market_analysis = analyze_market_for_llm()

# 2. Check leading sectors
# (Included in market_analysis output)

# 3. Screen for opportunities
value_picks = screen_stocks(strategy='value', top_n=5)
momentum_picks = screen_stocks(strategy='momentum', top_n=5)

# 4. Format for report
report = f"""
# Daily Market Report

{market_analysis}

## Value Opportunities
{chr(10).join([f"- {s.stock_name} ({s.stock_code}): Score {s.total_score}" for s in value_picks])}

## Momentum Leaders
{chr(10).join([f"- {s.stock_name} ({s.stock_code}): Score {s.total_score}" for s in momentum_picks])}
"""
```

## Example 2: Stock Comparison

**Use case:** Compare two stocks in the same industry

```python
from skills.stockton.scripts.data_fetcher import get_stock_data
from skills.stockton.scripts.financial_analyzer import analyze_financial

def compare_stocks(code1, code2):
    """Compare two stocks across multiple dimensions"""
    
    # Get data for both
    fin1 = analyze_financial(code1, format_type='dict')
    fin2 = analyze_financial(code2, format_type='dict')
    
    comparison = {
        'valuation': {
            code1: {'pe': fin1['估值']['PE'], 'pb': fin1['估值']['PB']},
            code2: {'pe': fin2['估值']['PE'], 'pb': fin2['估值']['PB']}
        },
        'profitability': {
            code1: {'roe': fin1['成长']['ROE'], 'gross': fin1['财务']['毛利率']},
            code2: {'roe': fin2['成长']['ROE'], 'gross': fin2['财务']['毛利率']}
        },
        'safety': {
            code1: {'debt': fin1['财务']['资产负债率']},
            code2: {'debt': fin2['财务']['资产负债率']}
        }
    }
    
    return comparison

# Compare Moutai vs Wuliangye
comparison = compare_stocks('600519', '000858')
```

## Example 3: Portfolio Screening

**Use case:** Build a diversified portfolio using multiple strategies

```python
from skills.stockton.scripts.stock_screener import screen_stocks_advanced

def build_diversified_portfolio():
    """Build portfolio using core-satellite approach"""
    
    portfolio = {
        'core': [],
        'satellite': []
    }
    
    # Core: Large-cap value from CSI300
    core_stocks = screen_stocks_advanced(
        strategy='value',
        index_name='沪深300',
        top_n=5
    )
    portfolio['core'] = core_stocks
    
    # Satellite 1: Growth from CSI500
    growth_stocks = screen_stocks_advanced(
        strategy='growth',
        index_name='中证500',
        top_n=3
    )
    portfolio['satellite'].extend(growth_stocks)
    
    # Satellite 2: Momentum from CSI1000
    momentum_stocks = screen_stocks_advanced(
        strategy='momentum',
        index_name='中证1000',
        top_n=2
    )
    portfolio['satellite'].extend(momentum_stocks)
    
    return portfolio

# Build portfolio
portfolio = build_diversified_portfolio()
total_stocks = len(portfolio['core']) + len(portfolio['satellite'])
print(f"Portfolio: {total_stocks} stocks")
```

## Example 4: Momentum Ranking

**Use case:** Rank stocks by momentum strength

```python
from skills.stockton.scripts.storage import get_db
from skills.stockton.scripts.data_provider import DataFetcherManager

# Get CSI300 constituents
df, _ = DataFetcherManager().get_index_components('000300')
codes = df['stock_code'].tolist()

# Calculate momentum for each
db = get_db()
momentum_scores = []

for code in codes[:50]:  # Top 50 for speed
    mom = db.get_momentum_data(code)
    if mom:
        momentum_scores.append({
            'code': code,
            'name': mom['name'],
            'm20': mom['momentum_20d'],
            'm60': mom['momentum_60d'],
            'consistency': mom['trend_consistency'],
            'score': mom['momentum_20d'] + mom['momentum_60d']
        })

# Sort by score
top_momentum = sorted(momentum_scores, key=lambda x: x['score'], reverse=True)[:10]
```

## Example 5: Market Timing Signal

**Use case:** Generate market timing signal based on futures basis

```python
from skills.stockton.scripts.market_analyzer import get_market_overview

def market_timing_signal():
    """
    Generate market timing signal based on futures basis
    
    Returns:
        -1: Bearish (deep discount)
         0: Neutral
        +1: Bullish (premium)
    """
    market = get_market_overview(format_type='dict')
    
    if 'futures_basis' not in market:
        return 0  # No data
    
    # Check IM (CSI1000 futures) - most sensitive to sentiment
    im_basis = market['futures_basis'].get('IM', {})
    annualized = im_basis.get('annualized_rate', 0)
    
    if annualized < -10:
        return -1  # Deep discount = bearish
    elif annualized > 2:
        return 1   # Premium = bullish
    else:
        return 0   # Neutral

signal = market_timing_signal()
signals = {-1: 'Bearish', 0: 'Neutral', 1: 'Bullish'}
print(f"Market signal: {signals[signal]}")
```

## Example 6: Custom Screening Pipeline

**Use case:** Create custom screening with multiple filters

```python
from skills.stockton.scripts.stock_screener import ScreenCriteria, screen_by_criteria

def custom_quality_screen():
    """
    Custom screen: High quality + reasonable valuation + momentum
    """
    criteria = ScreenCriteria(
        # Quality filters
        roe_min=15,
        debt_ratio_max=40,
        gross_margin_min=25,
        
        # Valuation filters (not too expensive)
        pe_max=40,
        pb_max=5,
        
        # Momentum filters (trending up)
        momentum_60d_min=5,
        above_ma20=True,
        
        # Index focus (CSI500 mid-caps)
        index_components='中证500'
    )
    
    results = screen_by_criteria(criteria, top_n=15)
    return results

quality_picks = custom_quality_screen()
```

## Example 7: Pre-Market Preparation

**Use case:** Prepare watchlist before market opens

```python
from skills.stockton.scripts.preload_data import check_preload_status
from skills.stockton.scripts.stock_screener import screen_stocks
from skills.stockton.scripts.market_analyzer import get_market_overview

def pre_market_prep():
    """
    Run before 9:15 AM to prepare for trading day
    """
    # 1. Check data coverage
    status = check_preload_status(['沪深300', '中证500'])
    print("Data coverage:", status)
    
    # 2. Get overnight market data
    market = get_market_overview(format_type='dict')
    
    # 3. Generate watchlists
    watchlists = {
        'value': screen_stocks(strategy='value', top_n=10),
        'momentum': screen_stocks(strategy='momentum', top_n=10),
        'dual_momentum': screen_stocks(strategy='dual_momentum', top_n=10)
    }
    
    # 4. Check futures for sentiment
    if 'futures_basis' in market:
        im_basis = market['futures_basis'].get('IM', {}).get('annualized_rate', 0)
        sentiment = 'bearish' if im_basis < -5 else 'neutral'
    else:
        sentiment = 'unknown'
    
    return {
        'watchlists': watchlists,
        'sentiment': sentiment,
        'data_status': status
    }

prep = pre_market_prep()
```

## Example 8: Backtesting Data Collection

**Use case:** Collect historical data for backtesting

```python
from skills.stockton.scripts.data_fetcher import get_stock_data
from skills.stockton.scripts.stock_screener import screen_stocks
from datetime import datetime, timedelta

def collect_backtest_data(stock_codes, days=252):
    """
    Collect historical data for backtesting
    
    Args:
        stock_codes: List of stock codes
        days: Trading days to collect (252 = 1 year)
    """
    data = {}
    
    for code in stock_codes:
        result = get_stock_data(code, days=days)
        if result['success']:
            data[code] = {
                'name': result['name'],
                'prices': [d['close'] for d in result['daily_data']],
                'dates': [d['date'] for d in result['daily_data']],
                'volumes': [d['volume'] for d in result['daily_data']],
                'indicators': {
                    'ma20': [d.get('ma20') for d in result['daily_data']],
                    'ma60': [d.get('ma60') for d in result['daily_data']]
                }
            }
    
    return data

# Collect data for backtesting
csi300 = ['600519', '000858', '002594', '300750', '601398']  # Sample
backtest_data = collect_backtest_data(csi300, days=252)
```

## Example 9: Industry Rotation Analysis

**Use case:** Identify which industries are performing best

```python
from skills.stockton.scripts.stock_screener import StockScreener
from skills.stockton.scripts.market_analyzer import get_market_overview

def industry_rotation_analysis():
    """
    Analyze industry performance for rotation signals
    """
    screener = StockScreener()
    
    # Get available industries
    industries = screener.get_available_industries()
    
    # Sample key industries
    key_industries = ['半导体', '白酒', '银行', '新能源', '医药', '食品饮料']
    
    industry_scores = []
    
    for industry in key_industries:
        if industry in industries:
            # Get stocks in industry
            stocks = screener.get_industry_stocks(industry)
            
            # Calculate average momentum (simplified)
            # In practice, would get actual price data for each stock
            industry_scores.append({
                'industry': industry,
                'stock_count': len(stocks)
            })
    
    return industry_scores

rotation = industry_rotation_analysis()
```

## Example 10: Risk Monitoring

**Use case:** Monitor portfolio risk indicators

```python
from skills.stockton.scripts.market_analyzer import get_market_overview
from skills.stockton.scripts.storage import get_db

def risk_monitor(portfolio_codes):
    """
    Monitor risk indicators for a portfolio
    
    Returns risk alerts
    """
    alerts = []
    
    # 1. Check market-wide risk
    market = get_market_overview(format_type='dict')
    
    if 'futures_basis' in market:
        # Deep discount = high fear
        im_basis = market['futures_basis'].get('IM', {}).get('annualized_rate', 0)
        if im_basis < -10:
            alerts.append("HIGH RISK: Futures deep discount (-10%+)")
        elif im_basis < -5:
            alerts.append("MODERATE RISK: Futures discount (-5%+)")
    
    if 'etf_iv' in market:
        # High IV = high fear
        iv_values = [v.get('iv', 0) for v in market['etf_iv'].values()]
        avg_iv = sum(iv_values) / len(iv_values) if iv_values else 0
        if avg_iv > 25:
            alerts.append(f"HIGH IV WARNING: Avg IV {avg_iv:.1f}%")
    
    # 2. Check individual stock risk
    db = get_db()
    for code in portfolio_codes:
        tech = db.get_latest_tech_data(code)
        if tech:
            # Price below MA20 = downtrend
            if tech['price_vs_ma20'] < -5:
                alerts.append(f"{code}: Below MA20 by {tech['price_vs_ma20']:.1f}%")
    
    return alerts

# Monitor risk
portfolio = ['600519', '000858', '300750']
alerts = risk_monitor(portfolio)
for alert in alerts:
    print(f"⚠️ {alert}")
```
