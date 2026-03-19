# -*- coding: utf-8 -*-
"""
与 Cloudflare Workers 同步模块 V2
支持分表同步
"""
import logging
import requests
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class WorkersSync:
    """Workers 数据同步器 - 统一使用 stock_a_data 表"""
    
    # 统一数据表
    STOCK_A_TABLE = 'stock_a_data'
    
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
    
    def sync_table(self, table_name: str, prices: List[Dict], 
                   code: str = None, code_type: str = None) -> bool:
        """
        同步指定表的数据到 Workers
        
        Args:
            table_name: 本地表名（如 'stock_prices_000300'）
            prices: 价格数据列表
            code: 指数/ETF代码（可选）
            code_type: 类型（可选）
            
        Returns:
            是否成功
        """
        if not prices:
            logger.info(f"表 {table_name}: 无数据需要同步")
            return True
        
        # 获取代码和类型信息
        if not code or not code_type:
            code_info = self.INDEX_TABLE_MAP.get(table_name, (None, None))
            code, code_type = code_info
        
        total = len(prices)
        logger.info(f"开始同步表 {table_name} ({code}, {code_type}): {total} 条数据...")
        
        # 分批发送
        for i in range(0, total, self.batch_size):
            batch = prices[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            
            try:
                logger.info(f"  批次 {batch_num}/{total_batches}: {len(batch)} 条")
                
                response = requests.post(
                    f"{self.workers_url}/api/batch_update_v2",
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'table': table_name,  # 指定目标表
                        'code': code,         # 指数/ETF代码
                        'code_type': code_type,  # 'index' 或 'etf'
                        'prices': batch
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"  ✓ 批次 {batch_num} 同步成功")
                    else:
                        logger.warning(f"  ✗ 批次 {batch_num} 同步失败: {result.get('error')}")
                        return False
                else:
                    logger.error(f"  ✗ 批次 {batch_num} HTTP错误: {response.status_code}")
                    logger.error(f"     响应: {response.text[:200]}")
                    return False
                
                # 短暂延迟
                if i + self.batch_size < total:
                    time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"  ✗ 批次 {batch_num} 请求异常: {e}")
                return False
            except Exception as e:
                logger.error(f"  ✗ 批次 {batch_num} 处理异常: {e}")
                return False
        
        logger.info(f"✓ 表 {table_name} 同步完成 ({total} 条)")
        return True
    
    def sync_from_local_db(self, local_db) -> Dict:
        """
        从本地数据库同步 stock_a_data 表数据到 Workers
        
        Args:
            local_db: 本地数据库实例 (LocalDatabase)
            
        Returns:
            同步结果统计
        """
        if not local_db:
            logger.error("未提供本地数据库实例")
            return {'success': False, 'error': 'No local_db provided'}
        
        results = {
            'success': True,
            'table': self.STOCK_A_TABLE,
            'total_prices': 0,
            'error': None,
        }
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"同步统一数据表: {self.STOCK_A_TABLE}")
            logger.info(f"{'='*60}")
            
            # 从本地数据库读取数据
            prices = local_db.get_all_prices_for_sync(self.STOCK_A_TABLE)
            
            if not prices:
                logger.info(f"表 {self.STOCK_A_TABLE} 无数据，跳过")
                results['success'] = True
                results['count'] = 0
                return results
            
            logger.info(f"从本地读取 {len(prices)} 条记录")
            
            # 同步到 Workers
            success = self.sync_table(self.STOCK_A_TABLE, prices)
            
            if success:
                results['success'] = True
                results['count'] = len(prices)
                results['total_prices'] = len(prices)
            else:
                results['success'] = False
                results['count'] = 0
                results['error'] = 'Sync failed'
            
        except Exception as e:
            logger.error(f"同步表 {self.STOCK_A_TABLE} 异常: {e}")
            results['success'] = False
            results['count'] = 0
            results['error'] = str(e)
        
        return results
    
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
    
    def check_workers_db(self) -> Optional[Dict]:
        """
        检查 Workers 端数据库状态
        
        Returns:
            数据库状态信息
        """
        try:
            response = requests.get(
                f"{self.workers_url}/api/db_status",
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"检查数据库状态失败: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"检查数据库状态异常: {e}")
            return None
