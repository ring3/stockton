# Stockton API 参考文档

所有模块的完整 API 文档。

## 数据获取模块

### `get_stock_data(stock_code, days=60, start_date=None, end_date=None)`

获取带技术指标的历史股票数据。

**参数：**
- `stock_code` (str)：股票代码（如 '600519', '000001'）
- `days` (int)：获取天数（默认：60）
- `start_date` (str, 可选)：开始日期 'YYYY-MM-DD'
- `end_date` (str, 可选)：结束日期 'YYYY-MM-DD'

**返回：**
```python
{
    'success': True,
    'code': '600519',
    'name': '贵州茅台',
    'daily_data': [...],
    'data_source': 'EfinanceFetcher',
    'realtime_quote': {...}  # 可选
}
```

### `get_stock_data_for_llm(stock_code, days=60, format_type="prompt")`

获取格式化为 LLM 可读的股票数据。

**参数：**
- `format_type` (str)："prompt" 或 "json"

**返回：** 格式化后的字符串。

## 股票分析模块

### `analyze_for_llm(stock_code, days=60)`

分析股票趋势并生成 LLM 格式的报告。

**分析内容：**
- 价格趋势（涨/跌）
- 移动平均线（MA5/MA10/MA20）
- 量比
- 筹码分布（如有）
- 交易信号

**信号说明：**
- `buy`（买入）：价格 > MA5 > MA10 > MA20，量比 > 1.5
- `strong_buy`（强烈买入）：所有买入条件 + 价格突破
- `hold`（持有）：价格在MA10和MA20之间
- `sell`（卖出）：价格 < MA20

## 财务分析模块

### `analyze_financial(stock_code, format_type="dict")`

分析公司财务健康状况。

**返回：**
```python
{
    'stock_code': '600519',
    'stock_name': '贵州茅台',
    'health_score': 85,  # 0-100分
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

**健康评分计算：**
- 盈利能力：0-25分（ROE、毛利率）
- 成长能力：0-25分（营收/利润增长）
- 财务安全：0-20分（负债、流动比率）
- 估值：0-20分（PE、PB）
- 额外：0-10分（持续表现）

## 股票筛选模块

### `screen_stocks(strategy='value', top_n=20, market='A股')`

使用预设策略筛选股票。

**策略说明：**

| 策略 | 标准 | 适用场景 |
|------|------|---------|
| `value`（价值） | PE<20, PB<2, 股息率>2%, ROE>10% | 保守型投资者 |
| `growth`（成长） | 营收增长>20%, 利润增长>20%, ROE>15% | 进取型投资者 |
| `quality`（质量） | ROE>15%, 负债<40%, 毛利率>30% | 质量导向型 |
| `blue_chip`（蓝筹） | 市值>500亿, PE<25, 股息率>2%, ROE>12% | 分红型投资者 |
| `small_cap_growth`（小盘成长） | 市值<200亿, 营收>30%, 利润>30% | 高风险高回报 |
| `momentum`（动量） | 20日涨幅>10%, 60日涨幅>15%, 价格>MA20 | 趋势跟踪 |
| `dual_momentum`（双动量） | 绝对动量+质量过滤 | 动量投资者 |

### `screen_stocks_advanced(strategy='value', index_name=None, industry=None, top_n=20)`

高级筛选，支持指数/行业过滤。

**指数选项：**
- `沪深300`：大盘蓝筹
- `中证500`：中盘成长
- `中证1000`：小盘成长
- `上证50`：超大盘

## 市场分析模块

### `get_market_overview(format_type="dict")`

获取全面的市场概览。

**返回：**
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

生成 LLM 格式的市场分析，包含：
- 指数表现摘要
- 市场情绪（牛/熊/中性）
- 板块表现（前5涨跌）
- 期货贴水解读
- IV水平分析

## 数据预加载模块

### `preload_index_data(indices=['沪深300', '中证500'], days=60)`

预加载指数成分股的历史数据。

**使用场景：** 收盘后运行，为次日分析做准备。

**示例：**
```python
from skills.stockton.scripts.preload_data import preload_index_data

result = preload_index_data(['沪深300', '中证500'], days=60)
print(f"成功加载 {result['success_count']} 只股票")
```

## 数据库存储模块

### `get_db()`

获取数据库管理器实例用于直接访问。

**功能：**
- 自动缓存历史数据
- 缓存指数成分股
- 股票名称查询
- 技术指标存储

**示例：**
```python
from skills.stockton.scripts.storage import get_db

db = get_db()
name = db.get_stock_name('600519')
momentum = db.get_momentum_data('600519')
tech_data = db.get_latest_tech_data('600519')
```

## 错误处理

所有函数返回结构化错误响应：

```python
{
    'success': False,
    'error_message': '错误描述',
    'code': '600519'
}
```

常见错误代码：
- `DataFetchError`：网络或数据源问题
- `RateLimitError`：请求过多
- `DataSourceUnavailableError`：所有数据源失败
