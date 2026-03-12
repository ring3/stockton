# 使用示例

常见用例的实用示例。

## 示例1：每日市场分析工作流

**用例：** 为投委会生成每日市场摘要

```python
from skills.stockton.scripts.market_analyzer import analyze_market_for_llm
from skills.stockton.scripts.financial_analyzer import analyze_financial
from skills.stockton.scripts.stock_screener import screen_stocks

# 1. 获取市场概览
market_analysis = analyze_market_for_llm()

# 2. 检查领涨板块
#（已包含在market_analysis输出中）

# 3. 筛选机会
value_picks = screen_stocks(strategy='value', top_n=5)
momentum_picks = screen_stocks(strategy='momentum', top_n=5)

# 4. 格式化报告
report = f"""
# 每日市场报告

{market_analysis}

## 价值投资机会
{chr(10).join([f"- {s.stock_name} ({s.stock_code}): 评分 {s.total_score}" for s in value_picks])}

## 动量领涨股
{chr(10).join([f"- {s.stock_name} ({s.stock_code}): 评分 {s.total_score}" for s in momentum_picks])}
"""
```

## 示例2：股票对比

**用例：** 对比同行业两只股票

```python
from skills.stockton.scripts.data_fetcher import get_stock_data
from skills.stockton.scripts.financial_analyzer import analyze_financial

def compare_stocks(code1, code2):
    """对比两只股票的多维度表现"""
    
    # 获取两只股票的数据
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

# 对比茅台 vs 五粮液
comparison = compare_stocks('600519', '000858')
```

## 示例3：组合筛选

**用例：** 使用多策略构建多元化组合

```python
from skills.stockton.scripts.stock_screener import screen_stocks_advanced

def build_diversified_portfolio():
    """使用核心-卫星法构建组合"""
    
    portfolio = {
        'core': [],
        'satellite': []
    }
    
    # 核心：沪深300大盘价值股
    core_stocks = screen_stocks_advanced(
        strategy='value',
        index_name='沪深300',
        top_n=5
    )
    portfolio['core'] = core_stocks
    
    # 卫星1：中证500成长股
    growth_stocks = screen_stocks_advanced(
        strategy='growth',
        index_name='中证500',
        top_n=3
    )
    portfolio['satellite'].extend(growth_stocks)
    
    # 卫星2：中证1000动量股
    momentum_stocks = screen_stocks_advanced(
        strategy='momentum',
        index_name='中证1000',
        top_n=2
    )
    portfolio['satellite'].extend(momentum_stocks)
    
    return portfolio

# 构建组合
portfolio = build_diversified_portfolio()
total_stocks = len(portfolio['core']) + len(portfolio['satellite'])
print(f"组合: {total_stocks} 只股票")
```

## 示例4：动量排名

**用例：** 按动量强度排名股票

```python
from skills.stockton.scripts.storage import get_db
from skills.stockton.scripts.data_provider import DataFetcherManager

# 获取沪深300成分股
df, _ = DataFetcherManager().get_index_components('000300')
codes = df['stock_code'].tolist()

# 计算每只股票动量
db = get_db()
momentum_scores = []

for code in codes[:50]:  # 前50只提速
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

# 按评分排序
top_momentum = sorted(momentum_scores, key=lambda x: x['score'], reverse=True)[:10]
```

## 示例5：市场择时信号

**用例：** 基于期货贴水生成市场择时信号

```python
from skills.stockton.scripts.market_analyzer import get_market_overview

def market_timing_signal():
    """
    基于期货贴水生成市场择时信号
    
    返回:
        -1: 看空（深度贴水）
         0: 中性
        +1: 看多（升水）
    """
    market = get_market_overview(format_type='dict')
    
    if 'futures_basis' not in market:
        return 0  # 无数据
    
    # 检查IM（中证1000期货）- 对情绪最敏感
    im_basis = market['futures_basis'].get('IM', {})
    annualized = im_basis.get('annualized_rate', 0)
    
    if annualized < -10:
        return -1  # 深度贴水 = 看空
    elif annualized > 2:
        return 1   # 升水 = 看多
    else:
        return 0   # 中性

signal = market_timing_signal()
signals = {-1: '看空', 0: '中性', 1: '看多'}
print(f"市场信号: {signals[signal]}")
```

## 示例6：自定义筛选流程

**用例：** 创建带多过滤条件的自定义筛选

```python
from skills.stockton.scripts.stock_screener import ScreenCriteria, screen_by_criteria

def custom_quality_screen():
    """
    自定义筛选：高质量+合理估值+动量
    """
    criteria = ScreenCriteria(
        # 质量过滤
        roe_min=15,
        debt_ratio_max=40,
        gross_margin_min=25,
        
        # 估值过滤（不太贵）
        pe_max=40,
        pb_max=5,
        
        # 动量过滤（趋势向上）
        momentum_60d_min=5,
        above_ma20=True,
        
        # 指数聚焦（中证500中盘）
        index_components='中证500'
    )
    
    results = screen_by_criteria(criteria, top_n=15)
    return results

quality_picks = custom_quality_screen()
```

## 示例7：盘前准备

**用例：** 开盘前准备观察清单

```python
from skills.stockton.scripts.preload_data import check_preload_status
from skills.stockton.scripts.stock_screener import screen_stocks
from skills.stockton.scripts.market_analyzer import get_market_overview

def pre_market_prep():
    """
    在9:15前运行，为交易日做准备
    """
    # 1. 检查数据覆盖
    status = check_preload_status(['沪深300', '中证500'])
    print("数据覆盖:", status)
    
    # 2. 获取隔夜市场数据
    market = get_market_overview(format_type='dict')
    
    # 3. 生成观察清单
    watchlists = {
        'value': screen_stocks(strategy='value', top_n=10),
        'momentum': screen_stocks(strategy='momentum', top_n=10),
        'dual_momentum': screen_stocks(strategy='dual_momentum', top_n=10)
    }
    
    # 4. 检查期货情绪
    if 'futures_basis' in market:
        im_basis = market['futures_basis'].get('IM', {}).get('annualized_rate', 0)
        sentiment = '看空' if im_basis < -5 else '中性'
    else:
        sentiment = '未知'
    
    return {
        'watchlists': watchlists,
        'sentiment': sentiment,
        'data_status': status
    }

prep = pre_market_prep()
```

## 示例8：回测数据收集

**用例：** 收集历史数据用于回测

```python
from skills.stockton.scripts.data_fetcher import get_stock_data
from skills.stockton.scripts.stock_screener import screen_stocks
from datetime import datetime, timedelta

def collect_backtest_data(stock_codes, days=252):
    """
    收集历史数据用于回测
    
    参数:
        stock_codes: 股票代码列表
        days: 收集交易日数（252 = 1年）
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

# 收集回测数据
csi300 = ['600519', '000858', '002594', '300750', '601398']  # 示例
backtest_data = collect_backtest_data(csi300, days=252)
```

## 示例9：板块轮动分析

**用例：** 识别哪些行业表现最好

```python
from skills.stockton.scripts.stock_screener import StockScreener
from skills.stockton.scripts.market_analyzer import get_market_overview

def industry_rotation_analysis():
    """
    分析行业表现用于轮动信号
    """
    screener = StockScreener()
    
    # 获取可用行业
    industries = screener.get_available_industries()
    
    # 示例关键行业
    key_industries = ['半导体', '白酒', '银行', '新能源', '医药', '食品饮料']
    
    industry_scores = []
    
    for industry in key_industries:
        if industry in industries:
            # 获取行业内股票
            stocks = screener.get_industry_stocks(industry)
            
            # 计算平均动量（简化）
            # 实际应获取每只股票的价格数据
            industry_scores.append({
                'industry': industry,
                'stock_count': len(stocks)
            })
    
    return industry_scores

rotation = industry_rotation_analysis()
```

## 示例10：风险监控

**用例：** 监控组合风险指标

```python
from skills.stockton.scripts.market_analyzer import get_market_overview
from skills.stockton.scripts.storage import get_db

def risk_monitor(portfolio_codes):
    """
    监控组合风险指标
    
    返回风险警报
    """
    alerts = []
    
    # 1. 检查市场风险
    market = get_market_overview(format_type='dict')
    
    if 'futures_basis' in market:
        # 深度贴水 = 高恐慌
        im_basis = market['futures_basis'].get('IM', {}).get('annualized_rate', 0)
        if im_basis < -10:
            alerts.append("高风险：期货深度贴水（-10%+）")
        elif im_basis < -5:
            alerts.append("中等风险：期货贴水（-5%+）")
    
    if 'etf_iv' in market:
        # 高IV = 高恐慌
        iv_values = [v.get('iv', 0) for v in market['etf_iv'].values()]
        avg_iv = sum(iv_values) / len(iv_values) if iv_values else 0
        if avg_iv > 25:
            alerts.append(f"高IV警告：平均IV {avg_iv:.1f}%")
    
    # 2. 检查个股风险
    db = get_db()
    for code in portfolio_codes:
        tech = db.get_latest_tech_data(code)
        if tech:
            # 价格低于MA20 = 下跌趋势
            if tech['price_vs_ma20'] < -5:
                alerts.append(f"{code}: 低于MA20 {tech['price_vs_ma20']:.1f}%")
    
    return alerts

# 监控风险
portfolio = ['600519', '000858', '300750']
alerts = risk_monitor(portfolio)
for alert in alerts:
    print(f"⚠️ {alert}")
```
