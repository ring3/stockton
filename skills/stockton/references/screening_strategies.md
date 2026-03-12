# Screening Strategies Reference

Detailed explanation of all preset screening strategies.

## Strategy Categories

### 1. Value Strategies

Focus: Undervalued stocks with strong fundamentals

#### `value` - Classic Value

**Criteria:**
- PE < 20
- PB < 2
- Dividend yield > 2%
- ROE > 10%
- Debt ratio < 60%

**Rationale:** 
Benjamin Graham-style value investing. Look for companies trading below intrinsic value with adequate quality filters.

**When to use:**
- Bear markets or market corrections
- Late economic cycle
- Risk-off environments
- Building defensive portfolios

**Expected output:** 20-50 stocks from full market, 5-15 from CSI300

### 2. Growth Strategies

Focus: High-growth companies

#### `growth` - High Growth

**Criteria:**
- Revenue growth > 20%
- Profit growth > 20%
- ROE > 15%
- Debt ratio < 50%

**Rationale:**
Focus on companies with strong revenue and profit momentum. Quality filters (ROE, debt) avoid speculative growth.

**When to use:**
- Early-mid economic cycle
- Bull markets
- Risk-on environments
- Building aggressive portfolios

#### `small_cap_growth` - Small Cap Growth

**Criteria:**
- Market cap < 20 billion CNY
- Revenue growth > 30%
- Profit growth > 30%
- ROE > 10%

**Rationale:**
Small caps have higher growth potential but also higher risk. Strict growth criteria compensate for lower liquidity.

**When to use:**
- Strong bull markets
- Liquidity abundant environments
- High risk tolerance

**Risk warning:** Small caps can be illiquid and volatile

### 3. Quality Strategies

Focus: High-quality businesses

#### `quality` - Quality Factor

**Criteria:**
- ROE > 15%
- Debt ratio < 40%
- Gross margin > 30%
- Current ratio > 1.5

**Rationale:**
Warren Buffett-style quality investing. Focus on companies with durable competitive advantages (high margins) and strong balance sheets.

**When to use:**
- Core portfolio construction
- Any market condition
- Long-term holdings

### 4. Blue Chip Strategies

Focus: Large-cap dividend stocks

#### `blue_chip` - Blue Chip Dividend

**Criteria:**
- Market cap > 50 billion CNY
- PE < 25
- PB < 3
- ROE > 12%
- Dividend yield > 2%

**Rationale:**
Large-cap stocks with consistent dividends provide stability and income. Quality filters ensure sustainability.

**When to use:**
- Conservative portfolios
- Income-focused strategies
- Market uncertainty

### 5. Momentum Strategies

Focus: Trend-following

#### `momentum` - Price Momentum

**Criteria:**
- 20-day return > 10%
- 60-day return > 15%
- Price above MA20
- Volume ratio > 1.0

**Scoring:**
- 20-day momentum: +10 points (strong), +7 (good), +5 (moderate)
- 60-day momentum: +10 points (strong), +7 (good), +5 (moderate)
- Trend consistency: +5 points

**Rationale:**
Trend-following strategy based on "momentum effect" - stocks that have performed well tend to continue performing well in short term.

**When to use:**
- Strong trending markets
- Breakout confirmations
- Short-term trading

**Risk warning:** Momentum can reverse quickly; use stop losses

#### `dual_momentum` - Dual Momentum (Absolute + Relative)

**Criteria:**
- 20-day return > 5% (absolute momentum)
- 60-day return > 10% (absolute momentum)
- Both returns positive (trend confirmation)
- ROE > 8% (quality filter)
- Debt ratio < 60% (safety filter)

**Scoring:**
Same as momentum strategy, plus quality bonus.

**Rationale:**
Gary Antonacci's dual momentum concept:
1. **Absolute momentum:** Only invest in assets with positive trend
2. **Relative momentum:** Select strongest performers
3. **Quality filter:** Avoid momentum traps (low-quality junk rallies)

**When to use:**
- Best for tactical allocation
- Can be used for market timing (cash when no qualifiers)
- Reduces drawdowns vs pure momentum

**Expected behavior:**
- Strong bull markets: Many qualifiers, high returns
- Weak/flat markets: Few/no qualifiers, preserves capital
- Bear markets: Zero qualifiers (all filtered out by absolute momentum)

## Multi-Factor Scoring

All strategies use multi-factor scoring (0-120 points):

### Financial Score (0-70 points)

**Profitability (0-25):**
- ROE > 20%: +10
- ROE 15-20%: +8
- ROE 10-15%: +6
- ROE 8-10%: +4

**Growth (0-25):**
- Revenue growth > 30%: +10
- Revenue growth 20-30%: +8
- Profit growth > 30%: +10
- Profit growth 20-30%: +8

**Safety (0-20):**
- Debt ratio < 40%: +10
- Debt ratio 40-50%: +6
- Current ratio > 2: +10
- Current ratio 1.5-2: +6

### Technical Score (0-50 points)

**Momentum (0-30):**
- 20-day return > 20%: +10
- 20-day return 10-20%: +7
- 60-day return > 30%: +10
- 60-day return 15-30%: +7
- 120-day return > 50%: +5
- Trend consistency: +5

**Technical Pattern (0-20):**
- Bullish arrangement (MA5>MA10>MA20): +15
- Price > MA20 by 5%: +10
- Volume ratio > 2: +10

## Combining Strategies

### Portfolio Construction Example

**Conservative (60% value + 40% quality):**
```python
value_stocks = screen_stocks(strategy='value', top_n=15)
quality_stocks = screen_stocks(strategy='quality', top_n=10)
```

**Balanced (40% value + 30% growth + 30% quality):**
```python
value = screen_stocks(strategy='value', top_n=10)
growth = screen_stocks(strategy='growth', top_n=8)
quality = screen_stocks(strategy='quality', top_n=8)
```

**Aggressive (50% growth + 30% momentum + 20% small_cap):**
```python
growth = screen_stocks(strategy='growth', top_n=10)
momentum = screen_stocks(strategy='momentum', top_n=6)
small_cap = screen_stocks(strategy='small_cap_growth', top_n=4)
```

## Custom Screening

Create custom criteria:

```python
from skills.stockton.scripts.stock_screener import ScreenCriteria

criteria = ScreenCriteria(
    pe_max=15,              # Deep value
    pb_max=1.5,
    roe_min=12,
    revenue_growth_min=10,  # Some growth
    market_cap_min=100,     # Mid-cap+
    momentum_60d_min=10     # With momentum
)

results = screen_by_criteria(criteria, top_n=20)
```

## Index-Based Screening

Screen within specific indices for higher quality:

```python
# Large-cap value
screen_stocks_advanced(strategy='value', index_name='沪深300', top_n=10)

# Mid-cap growth
screen_stocks_advanced(strategy='growth', index_name='中证500', top_n=10)

# Small-cap momentum
screen_stocks_advanced(strategy='momentum', index_name='中证1000', top_n=10)
```

## Backtesting Considerations

**Rebalancing frequency:**
- Momentum strategies: Weekly (momentum decays quickly)
- Growth strategies: Monthly
- Value strategies: Quarterly (value takes time)

**Transaction costs:**
- Small-cap strategies: Higher costs due to lower liquidity
- Momentum strategies: Higher turnover = higher costs

**Market regime dependency:**
- Momentum works best in trending markets
- Value works best in recovery phases
- Quality works in all markets but outperforms in downturns
