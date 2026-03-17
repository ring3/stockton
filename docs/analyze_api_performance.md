# Akshare API 性能分析

## 按功能分类的API调用

### 1. 历史数据类（通常较快 0.1-1s）
| 行号 | API | 用途 | 预估耗时 |
|------|-----|------|---------|
| 207 | `stock_hk_hist` | 港股历史K线 | ~0.5s |
| 225 | `fund_etf_hist_em` | ETF历史K线 | ~0.3s |
| 438 | `stock_zh_a_hist` | A股历史K线（单股） | **~0.03s** ✅ 极快 |
| 1077 | `index_stock_cons_weight_csindex` | 指数成分股 | ~0.1s |
| 1369 | `stock_financial_report_sina` | 财务报表 | ~0.5s |
| 1397 | `stock_financial_analysis_indicator` | 财务指标 | ~0.3s |

### 2. 筹码/实时数据类（中等 0.3-3s）
| 行号 | API | 用途 | 预估耗时 |
|------|-----|------|---------|
| 356 | `stock_cyq_em` | 筹码分布 | ~0.5s |
| 476 | `stock_individual_info_em` | 个股信息 | **~0.2s** ✅ 快 |
| 644 | `stock_market_activity_legu` | 市场活动统计 | **~0.5s** ✅ 已优化 |

### 3. 全量实时行情类（慢 10-30s）⚠️
| 行号 | API | 用途 | 预估耗时 | 状态 |
|------|-----|------|---------|------|
| 501 | `stock_zh_a_spot_em` | A股全量实时 | ~19s | fallback 备用 |
| 510 | `stock_zh_a_spot` | A股全量实时(Sina) | ~13-30s | fallback 备用 |
| 681 | `stock_zh_a_spot_em` | 市场概览fallback | ~19s | fallback 备用 |
| 689 | `stock_zh_a_spot` | 市场概览fallback | ~13-30s | fallback 备用 |
| 1156-1164 | `stock_*_a_spot_em` | 分市场全量 | ~5-15s each | fallback 备用 |
| 1174 | `stock_zh_a_spot` | 股票池fallback | ~13-30s | fallback 备用 |

### 4. 指数/期货类（中等 1-5s）
| 行号 | API | 用途 | 预估耗时 | 状态 |
|------|-----|------|---------|------|
| 577 | `stock_zh_index_spot_sina` | 指数行情 | ~1-3s | 有15s超时保护 ✅ |
| 586 | `stock_zh_index_spot_em` | 指数行情(EM) | ~0.5s | fallback |
| 993 | `futures_main_sina` | 期货主力 | ~0.2s | 有5s超时保护 ✅ |

### 5. 板块/行业类（中等 0.5-3s）
| 行号 | API | 用途 | 预估耗时 | 状态 |
|------|-----|------|---------|------|
| 718 | `stock_board_industry_name_em` | 行业列表 | ~3s | fallback 备用 |
| 727 | `stock_board_industry_name_ths` | 行业列表(THS) | **~0.3s** ✅ 主用 |
| 1251 | `stock_board_industry_cons_em` | 行业成分股 | ~1s | 主用 |
| 1260 | `stock_board_industry_cons_ths` | 行业成分股(THS) | ~1s | fallback |
| 1310 | `stock_board_industry_name_em` | 行业列表 | ~3s | fallback |
| 1319 | `stock_board_industry_name_ths` | 行业列表(THS) | **~0.3s** ✅ 主用 |

### 6. 期权类（快 0.2-1s）
| 行号 | API | 用途 | 预估耗时 | 状态 |
|------|-----|------|---------|------|
| 753 | `option_risk_indicator_sse` | 期权风险指标 | ~0.2s | 主用 |
| 817 | `option_current_em` | 期权实时(EM) | ~0.5s | fallback |
| 824 | `option_sse_spot_price_sina` | 期权实时(Sina) | ~0.1s | fallback 备用 |

## 风险点分析

### 🔴 高风险（可能长时间阻塞）
1. **stock_zh_a_spot / stock_zh_a_spot_em 系列**
   - 用途：全量A股实时行情
   - 现状：仅作为 fallback 使用
   - 风险：如果主要数据源都失败，用户会经历 13-30s 等待
   - 建议：保持现状，已添加超时保护

### 🟡 中风险（偶发慢）
2. **stock_zh_index_spot_sina**
   - 现状：已添加 15s 超时保护
   - 风险：超时后切换到 EM 源

3. **stock_board_industry_cons_em**
   - 用途：获取行业成分股
   - 风险：如果行业名称不匹配可能失败
   - 现状：有 THS 源作为 fallback

### 🟢 低风险（已优化或本来很快）
4. **stock_zh_a_hist** - 单股查询，极快
5. **stock_individual_info_em** - 单股查询，快
6. **stock_market_activity_legu** - 已优化，0.5s
7. **futures_main_sina** - 有5s超时
8. **option_risk_indicator_sse** - 本来很快

## 结论

当前代码中**主要耗时调用**（全量接口）都已作为 fallback，正常使用不会触发。

核心功能路径：
- 个股实时行情 → `stock_zh_a_hist` (0.03s) ✅
- 市场概览 → `stock_market_activity_legu` (0.5s) ✅
- 股票池 → 指数成分股 (0.1s) ✅
- 行业板块 → THS 源 (0.3s) ✅

剩余潜在优化空间：
1. 为 `_get_sector_rankings` 添加缓存
2. 为 `_get_industry_list` 添加缓存
