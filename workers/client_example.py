#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stockton Cloud Python 客户端

用法:
```python
from workers.client_example import StocktonCloudClient

client = StocktonCloudClient('https://your-worker.workers.dev')

# 查询历史数据
history = client.get_stock_history('000001', limit=60)

# 查询最新数据
latest = client.get_latest('000001')

# 查询市场概览
overview = client.get_market_overview()
```
"""

import requests
from typing import Optional, Dict, Any, List


class StocktonCloudClient:
    """
    Stockton Cloud Workers API 客户端
    
    用于从 Python 代码访问 Cloudflare Workers 上的股票数据
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def _request(self, method: str, path: str, **kwargs) -> Optional[Dict]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def get_stock_history(
        self, 
        code: str, 
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100
    ) -> Optional[Dict]:
        """
        获取股票历史数据
        
        Args:
            code: 股票代码 (如 '000001')
            start: 开始日期 (YYYY-MM-DD)
            end: 结束日期 (YYYY-MM-DD)
            limit: 最大返回条数
        
        Returns:
            Dict: {'code': str, 'prices': List[Dict]}
        """
        params = {'limit': limit}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        return self._request('GET', f'/api/stock/{code}', params=params)
    
    def get_latest(self, code: str) -> Optional[Dict]:
        """
        获取股票最新数据
        
        Args:
            code: 股票代码
        
        Returns:
            Dict: 最新价格数据
        """
        return self._request('GET', f'/api/stock/{code}/latest')
    
    def get_market_overview(self) -> Optional[Dict]:
        """
        获取市场概览
        
        Returns:
            Dict: 市场统计数据
        """
        return self._request('GET', '/api/market/overview')
    
    def health_check(self) -> bool:
        """
        检查服务健康状态
        
        Returns:
            bool: 服务是否正常
        """
        result = self._request('GET', '/health')
        return result is not None and result.get('status') == 'ok'


def demo():
    """客户端使用示例"""
    # 替换为你的 Workers URL
    client = StocktonCloudClient('https://stockton.xxx.workers.dev')
    
    # 检查健康状态
    if not client.health_check():
        print("服务不可用")
        return
    
    print("服务正常")
    
    # 查询市场概览
    overview = client.get_market_overview()
    if overview:
        print(f"\n市场概览:")
        print(f"  上涨: {overview.get('up_count', 0)}")
        print(f"  下跌: {overview.get('down_count', 0)}")
    
    # 查询个股数据
    code = '000001'  # 平安银行
    history = client.get_stock_history(code, limit=30)
    if history:
        prices = history.get('prices', [])
        if prices:
            latest = prices[0]
            print(f"\n{code} 最新数据:")
            print(f"  日期: {latest.get('trade_date')}")
            print(f"  收盘: {latest.get('close')}")
            print(f"  涨跌: {latest.get('pct_chg', 0):.2f}%")


if __name__ == '__main__':
    demo()
