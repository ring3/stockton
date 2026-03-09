# -*- coding: utf-8 -*-
"""
数据源策略层 - 包初始化

本包实现策略模式管理多个数据源，实现：
1. 统一的数据获取接口
2. 自动故障切换
3. 防封禁流控策略

数据源优先级：
1. EfinanceFetcher (Priority 0) - 可选增强，来自 efinance 库
2. AkshareFetcher (Priority 1) - 主要数据源，来自 akshare 库
   - 支持多源切换：东方财富 → 新浪 → 腾讯 → 网易
"""

from .base import BaseFetcher, DataFetcherManager

# 可选的 efinance 数据源（严格检查，确保库可用）
try:
    from .efinance_fetcher import EfinanceFetcher
    import efinance as _  # 验证库可用
except Exception:
    EfinanceFetcher = None

# 主要的 akshare 数据源（必需）
try:
    from .akshare_fetcher import AkshareFetcher
except ImportError:
    AkshareFetcher = None
    raise ImportError("请安装 akshare: pip install akshare")

__all__ = [
    'BaseFetcher',
    'DataFetcherManager',
    'EfinanceFetcher',
    'AkshareFetcher',
]
