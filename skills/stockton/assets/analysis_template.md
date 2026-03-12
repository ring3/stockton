# Stock Analysis Report Template

Use this template when formatting stock analysis output for LLM consumption.

## Individual Stock Analysis

```markdown
# {stock_name} ({stock_code}) Analysis Report

## Executive Summary
**Signal:** {buy/hold/sell} | **Score:** {score}/100 | **Trend:** {bullish/bearish/neutral}

## Price Performance
- **Current Price:** ¥{price:.2f}
- **Change:** {change_pct:+.2f}%
- **20-Day Return:** {momentum_20d:+.2f}%
- **60-Day Return:** {momentum_60d:+.2f}%

## Technical Analysis
### Moving Averages
- **MA5:** ¥{ma5:.2f} ({above/below} price)
- **MA20:** ¥{ma20:.2f} ({support/resistance})
- **MA60:** ¥{ma60:.2f} (trend: {up/down})

### Trend Signals
- **Arrangement:** {bullish_arrangement/MA_bearish/no_clear_trend}
- **Volume Ratio:** {volume_ratio:.2f}x ({normal/elevated/high})

## Fundamental Analysis
### Profitability (Score: {score}/25)
- **ROE:** {roe:.1f}% ({excellent/good/average})
- **Gross Margin:** {gross_margin:.1f}%
- **Net Margin:** {net_margin:.1f}%

### Growth (Score: {score}/25)
- **Revenue Growth:** {revenue_growth:+.1f}%
- **Profit Growth:** {profit_growth:+.1f}%

### Financial Safety (Score: {score}/20)
- **Debt Ratio:** {debt_ratio:.1f}% ({safe/moderate/high})

### Valuation (Score: {score}/20)
- **PE Ratio:** {pe:.1f}x ({undervalued/fair/overvalued})
- **PB Ratio:** {pb:.1f}x

## Overall Health Score: {score}/100
```

## Market Overview Template

```markdown
# A-Share Market Overview

## Key Indices
| Index | Price | Change | 
|-------|-------|--------|
| 上证指数 | {sh_price} | {sh_change:+.2f}% |
| 深证成指 | {sz_price} | {sz_change:+.2f}% |
| 创业板指 | {cy_price} | {cy_change:+.2f}% |

## Market Breadth
- **Advancing:** {up_count} stocks
- **Declining:** {down_count} stocks
- **Limit Up:** {limit_up}
- **Limit Down:** {limit_down}

## Futures Basis
| Future | Basis | Annualized | 
|--------|-------|------------|
| IF (沪深300) | {if_basis:+.2f}% | {if_annual:+.2f}% |
| IC (中证500) | {ic_basis:+.2f}% | {ic_annual:+.2f}% |
```

## Usage Notes

### Formatting Guidelines

1. **Always include:** Date, data source
2. **Round numbers:** 2 decimal places for prices, 1 for percentages
3. **Color coding:** Use emojis for quick visual scanning
   - 🟢 Positive/good
   - 🟡 Neutral/moderate
   - 🔴 Negative/poor

### Example Disclaimers

```markdown
---
**Disclaimer:** This analysis is for informational purposes only.
**Data Source:** {Efinance/Akshare/Cache}  
**Last Updated:** {timestamp}
```
