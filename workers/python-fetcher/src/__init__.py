# -*- coding: utf-8 -*-
"""
Stockton Python Fetcher - 股票数据获取模块
支持多数据源（akshare、efinance）自动故障切换
"""

from .local_db import LocalDatabase
from .fetcher import StockDataFetcher
from .data_source import (
    DataSourceManager, 
    AkshareEastmoneyAdapter, 
    AkshareSinaAdapter,
    AkshareTencentAdapter,
    BaostockAdapter,
    is_hk_stock_code
)
from .sync import WorkersSync

__all__ = [
    'LocalDatabase',
    'StockDataFetcher', 
    'DataSourceManager',
    'AkshareEastmoneyAdapter',
    'AkshareSinaAdapter',
    'AkshareTencentAdapter',
    'BaostockAdapter',
    'is_hk_stock_code',
    'WorkersSync',
]
