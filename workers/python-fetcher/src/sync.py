# -*- coding: utf-8 -*-
"""
与 Cloudflare Workers 同步模块
"""
import logging
import requests
import time
from typing import List, Dict

logger = logging.getLogger(__name__)


class WorkersSync:
    """Workers 数据同步器"""
    
    def __init__(self, workers_url: str, api_key: str):
        """
        初始化
        
        Args:
            workers_url: Workers 服务地址
            api_key: API 密钥
        """
        self.workers_url = workers_url.rstrip('/')
        self.api_key = api_key
        self.batch_size = 100  # 每批发送100条
        self.timeout = 30
    
    def sync_prices(self, prices: List[Dict]) -> bool:
        """
        同步价格数据到 Workers
        
        Args:
            prices: 价格数据列表
            
        Returns:
            是否成功
        """
        if not prices:
            logger.info("无价格数据需要同步")
            return True
        
        total = len(prices)
        logger.info(f"开始同步 {total} 条价格数据...")
        
        # 分批发送
        for i in range(0, total, self.batch_size):
            batch = prices[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            
            try:
                logger.info(f"发送批次 {batch_num}/{total_batches}: {len(batch)} 条")
                
                response = requests.post(
                    f"{self.workers_url}/api/batch_update",
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={'prices': batch},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"批次 {batch_num} 同步成功")
                    else:
                        logger.warning(f"批次 {batch_num} 同步失败: {result.get('error')}")
                        return False
                else:
                    logger.error(f"批次 {batch_num} HTTP错误: {response.status_code} - {response.text}")
                    return False
                
                # 短暂延迟，避免请求过快
                if i + self.batch_size < total:
                    time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"批次 {batch_num} 请求异常: {e}")
                return False
            except Exception as e:
                logger.error(f"批次 {batch_num} 处理异常: {e}")
                return False
        
        logger.info(f"所有 {total} 条价格数据同步完成")
        return True
    
    def sync_market_stats(self, stats: Dict) -> bool:
        """
        同步市场统计数据
        
        Args:
            stats: 市场统计数据
            
        Returns:
            是否成功
        """
        if not stats:
            logger.info("无市场统计数据需要同步")
            return True
        
        try:
            logger.info("同步市场统计数据...")
            
            response = requests.post(
                f"{self.workers_url}/api/batch_update",
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={'stats': stats},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("市场统计数据同步成功")
                    return True
                else:
                    logger.warning(f"市场统计数据同步失败: {result.get('error')}")
                    return False
            else:
                logger.error(f"市场统计 HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"同步市场统计数据异常: {e}")
            return False
    
    def sync_all(self, prices: List[Dict], stats: Dict) -> Dict:
        """
        同步所有数据
        
        Args:
            prices: 价格数据
            stats: 市场统计数据
            
        Returns:
            同步结果统计
        """
        result = {
            'prices_total': len(prices),
            'prices_success': False,
            'stats_success': False,
        }
        
        # 同步价格数据
        result['prices_success'] = self.sync_prices(prices)
        
        # 同步市场统计
        result['stats_success'] = self.sync_market_stats(stats)
        
        return result
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否正常
        """
        try:
            response = requests.get(
                f"{self.workers_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
