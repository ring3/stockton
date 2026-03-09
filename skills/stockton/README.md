# Stockton Skill

A股行情数据获取与分析 OpenClaw 技能

## 快速开始

```python
from skills.stockton.scripts.data_fetcher import get_stock_data_for_llm
from skills.stockton.scripts.stock_analyzer import analyze_for_llm
from skills.stockton.scripts.market_analyzer import analyze_market_for_llm

# 获取个股分析
stock = analyze_for_llm('600519', days=60)

# 获取大盘分析  
market = analyze_market_for_llm()

# 传给 LLM 分析
print(f"{market}\n\n{stock}\n\n请给出投资建议。")
```

## 文件结构

```
skills/stockton/
├── SKILL.md                     # 主文档
├── README.md                    # 本文件
├── scripts/
│   ├── data_fetcher.py          # 数据获取 (A股/ETF/港股)
│   ├── stock_analyzer.py        # 趋势分析 (买入信号)
│   └── market_analyzer.py       # 大盘分析 (指数/板块)
├── tests/
│   ├── check_proxy.py           # 代理检查
│   ├── PROXY_FIX.md             # 代理修复指南
│   ├── test_basic.py            # 基础测试
│   └── test_network.py          # 网络测试
└── references/
    ├── data_provider.md         # 数据源文档
    └── trading_strategy.md      # 交易策略文档
```

## 依赖

```bash
pip install pandas numpy akshare
```

## 测试

```bash
cd skills/stockton/tests

# 检查代理
python check_proxy.py

# 基础测试 (无需网络)
python test_basic.py

# 完整测试
python test_network.py
```

## 已知问题

**Windows 代理错误**: 如果系统设置了代理，akshare 可能无法连接。解决方案：
1. 运行 `python check_proxy.py` 检查
2. 参照 `tests/PROXY_FIX.md` 修复

## License

MIT
