#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务核心逻辑

供 OpenClaw 或本地定时任务调用
"""

import os
import time
import logging
from typing import List, Dict
from .fetcher import StockDataFetcher
from .sync import WorkersSync


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_and_sync() -> Dict:
    """
    执行数据拉取和同步（OpenClaw 定时任务入口）
    
    Returns:
        Dict: 执行结果统计
    """
    start_time = time.time()
    
    # 从环境变量读取配置
    workers_url = os.getenv('WORKERS_URL')
    api_key = os.getenv('API_KEY')
    indices_str = os.getenv('INDICES', '000300,000905')
    history_days = int(os.getenv('HISTORY_DAYS', '60'))
    max_stocks_per_run = int(os.getenv('MAX_STOCKS_PER_RUN', '100'))
    
    if not workers_url or not api_key:
        logger.error("错误: 请设置 WORKERS_URL 和 API_KEY 环境变量")
        return {
            'success': False,
            'error': 'Missing WORKERS_URL or API_KEY',
            'stocks_processed': 0,
            'prices_total': 0,
            'duration_seconds': 0
        }
    
    indices = [x.strip() for x in indices_str.split(',') if x.strip()]
    logger.info(f"索引列表: {indices}")
    logger.info(f"目标地址: {workers_url}")
    logger.info(f"历史天数: {history_days}")
    logger.info(f"每轮最大股票数: {max_stocks_per_run}")
    
    # 初始化组件
    fetcher = StockDataFetcher()
    sync = WorkersSync(workers_url, api_key)
    
    all_prices = []
    stocks_processed = 0
    
    try:
        for index_code in indices:
            logger.info(f"\n处理指数: {index_code}")
            
            # 获取成分股
            stocks = fetcher.get_index_components(index_code)
            logger.info(f"  成分股数量: {len(stocks)}")
            
            # 每轮只处理一部分（轮换）
            # 实际生产环境应该用数据库记录上次处理的位置
            stocks_to_process = stocks[:max_stocks_per_run]
            logger.info(f"  本次处理: {len(stocks_to_process)}")
            
            for i, code in enumerate(stocks_to_process):
                try:
                    logger.info(f"  [{i+1}/{len(stocks_to_process)}] 拉取 {code} 历史数据...")
                    prices = fetcher.get_stock_history(code, days=history_days)
                    
                    if prices:
                        all_prices.extend(prices)
                        stocks_processed += 1
                        logger.info(f"    ✓ 获取 {len(prices)} 条记录")
                    else:
                        logger.warning(f"    ✗ 无数据")
                    
                    # 延时避免请求过快
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"    ✗ 错误: {e}")
                    continue
        
        # 批量同步到 Workers
        if all_prices:
            logger.info(f"\n同步 {len(all_prices)} 条记录到 Workers...")
            success = sync.sync_prices(all_prices)
            
            if success:
                logger.info("✓ 同步成功")
            else:
                logger.error("✗ 同步失败")
        
        duration = time.time() - start_time
        
        return {
            'success': True,
            'stocks_processed': stocks_processed,
            'prices_total': len(all_prices),
            'duration_seconds': round(duration, 2)
        }
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'stocks_processed': stocks_processed,
            'prices_total': len(all_prices),
            'duration_seconds': round(time.time() - start_time, 2)
        }
