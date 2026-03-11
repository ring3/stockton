# -*- coding: utf-8 -*-
"""
===================================
数据预加载模块 - 用于定时任务
===================================

职责：
1. 批量预加载指数成分股的历史K线数据
2. 更新指数成分股缓存
3. 用于定时任务（如每晚收盘后执行）

使用方式：
    # 在OpenClaw中设置定时任务调用
    from skills.stockton.scripts.preload_data import preload_index_data
    
    # 预加载沪深300和中证500
    result = preload_index_data(['沪深300', '中证500'], days=60)

OpenClaw 定时任务配置示例（每晚 19:00 执行）：
    {
        "name": "preload-stock-data",
        "schedule": "0 19 * * 1-5",
        "command": "python -c 'from skills.stockton.scripts.preload_data import preload_index_data; preload_index_data([\"沪深300\", \"中证500\"], days=60)'"
    }
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 指数代码映射
INDEX_CODE_MAP = {
    '沪深300': '000300',
    '中证500': '000905',
    '中证1000': '000852',
    '上证50': '000016',
}


def preload_index_data(
    indices: List[str] = None,
    days: int = 60,
    max_stocks: int = None
) -> Dict[str, Any]:
    """
    预加载指数成分股的历史数据
    
    用于定时任务，在收盘后批量获取数据，为第二天的选股做准备。
    
    Args:
        indices: 指数名称列表，如 ['沪深300', '中证500']，默认全部
        days: 获取历史数据天数，默认60天
        max_stocks: 最多处理的股票数量（用于测试），默认不限制
        
    Returns:
        加载结果统计
        
    Example:
        >>> from skills.stockton.scripts.preload_data import preload_index_data
        >>> result = preload_index_data(['沪深300', '中证500'], days=60)
        >>> print(f"成功加载 {result['success_count']} 只股票")
    """
    if indices is None:
        indices = list(INDEX_CODE_MAP.keys())
    
    start_time = datetime.now()
    
    result = {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'indices': indices,
        'days': days,
        'total_stocks': 0,
        'success_count': 0,
        'failed_count': 0,
        'failed_stocks': [],
        'details': {}
    }
    
    try:
        try:
            from .storage import DatabaseManager
            from .data_fetcher import get_stock_data
            from .data_provider import DataFetcherManager
        except ImportError:
            from storage import DatabaseManager
            from data_fetcher import get_stock_data
            from data_provider import DataFetcherManager
        
        db = DatabaseManager.get_instance()
        data_manager = DataFetcherManager()
        
        for index_name in indices:
            if index_name not in INDEX_CODE_MAP:
                logger.warning(f"未知指数: {index_name}")
                continue
            
            index_code = INDEX_CODE_MAP[index_name]
            logger.info(f"[预加载] 开始处理 {index_name}({index_code})...")
            
            try:
                # 获取指数成分股（使用统一数据源接口）
                df, source = data_manager.get_index_components(index_code)
                if df is None or df.empty:
                    logger.error(f"[预加载] 获取 {index_name} 成分股失败")
                    continue
                
                logger.info(f"[预加载] 从 {source} 获取 {index_name} 成分股: {len(df)} 只")
                stock_codes = df['stock_code'].tolist()
                if max_stocks:
                    stock_codes = stock_codes[:max_stocks]
                
                index_success = 0
                index_failed = 0
                
                # 逐个获取历史数据
                for i, code in enumerate(stock_codes, 1):
                    try:
                        # 检查数据库是否已有最新数据
                        if db.has_today_data(code):
                            logger.debug(f"[{code}] 今日数据已存在，跳过")
                            index_success += 1
                            continue
                        
                        # 获取数据（会自动保存到数据库）
                        logger.info(f"[{index_name}] ({i}/{len(stock_codes)}) 获取 {code} 数据...")
                        data = get_stock_data(code, days=days)
                        
                        if data.get('success'):
                            index_success += 1
                        else:
                            index_failed += 1
                            result['failed_stocks'].append(f"{index_name}:{code}")
                            
                    except Exception as e:
                        logger.error(f"[{code}] 获取数据失败: {e}")
                        index_failed += 1
                        result['failed_stocks'].append(f"{index_name}:{code}")
                
                # 更新指数成分股缓存
                try:
                    components = []
                    for _, row in df.iterrows():
                        components.append({
                            'stock_code': row.get('stock_code', ''),
                            'stock_name': row.get('stock_name', ''),
                            'weight': row.get('weight', 0)
                        })
                    db.save_index_components(index_code, index_name, components)
                    logger.info(f"[预加载] {index_name} 成分股缓存已更新: {len(components)} 只")
                except Exception as e:
                    logger.error(f"[预加载] 保存 {index_name} 成分股缓存失败: {e}")
                
                result['details'][index_name] = {
                    'total': len(stock_codes),
                    'success': index_success,
                    'failed': index_failed
                }
                
                result['total_stocks'] += len(stock_codes)
                result['success_count'] += index_success
                result['failed_count'] += index_failed
                
            except Exception as e:
                logger.error(f"[预加载] 处理 {index_name} 失败: {e}")
                result['details'][index_name] = {'error': str(e)}
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
        result['duration_seconds'] = duration
        
        logger.info(f"[预加载] 完成！共处理 {result['total_stocks']} 只股票，"
                   f"成功 {result['success_count']}，失败 {result['failed_count']}，"
                   f"耗时 {duration:.1f} 秒")
        
    except Exception as e:
        logger.error(f"[预加载] 执行失败: {e}")
        result['error'] = str(e)
    
    return result


def preload_single_stock(stock_code: str, days: int = 60) -> bool:
    """
    预加载单只股票的历史数据
    
    Args:
        stock_code: 股票代码
        days: 历史数据天数
        
    Returns:
        是否成功
    """
    try:
        try:
            from .storage import DatabaseManager
            from .data_fetcher import get_stock_data
        except ImportError:
            from storage import DatabaseManager
            from data_fetcher import get_stock_data
        
        db = DatabaseManager.get_instance()
        
        # 检查是否已有最新数据
        if db.has_today_data(stock_code):
            logger.debug(f"[{stock_code}] 今日数据已存在，跳过")
            return True
        
        # 获取数据
        data = get_stock_data(stock_code, days=days)
        return data.get('success', False)
        
    except Exception as e:
        logger.error(f"[{stock_code}] 预加载失败: {e}")
        return False


def check_preload_status(indices: List[str] = None) -> Dict[str, Any]:
    """
    检查预加载状态
    
    检查指定指数成分股的数据在数据库中的覆盖情况。
    
    Args:
        indices: 指数名称列表，默认全部
        
    Returns:
        状态统计
        
    Example:
        >>> check_preload_status(['沪深300'])
        {
            '沪深300': {
                'total': 300,
                'has_data': 280,
                'missing': 20,
                'coverage': '93.3%'
            }
        }
    """
    if indices is None:
        indices = list(INDEX_CODE_MAP.keys())
    
    result = {}
    
    try:
        try:
            from .storage import DatabaseManager
            from .data_provider import DataFetcherManager
        except ImportError:
            from storage import DatabaseManager
            from data_provider import DataFetcherManager
        
        db = DatabaseManager.get_instance()
        data_manager = DataFetcherManager()
        
        for index_name in indices:
            if index_name not in INDEX_CODE_MAP:
                continue
            
            index_code = INDEX_CODE_MAP[index_name]
            
            try:
                # 获取指数成分股（使用统一数据源接口）
                df, source = data_manager.get_index_components(index_code)
                if df is None or df.empty:
                    continue
                
                stock_codes = df['stock_code'].tolist()
                
                # 检查每只股票是否有数据
                has_data_count = 0
                missing_stocks = []
                
                for code in stock_codes:
                    if db.has_today_data(code):
                        has_data_count += 1
                    else:
                        missing_stocks.append(code)
                
                coverage = (has_data_count / len(stock_codes) * 100) if stock_codes else 0
                
                result[index_name] = {
                    'total': len(stock_codes),
                    'has_data': has_data_count,
                    'missing': len(stock_codes) - has_data_count,
                    'coverage': f"{coverage:.1f}%",
                    'missing_stocks': missing_stocks[:10]  # 只显示前10个缺失的
                }
                
            except Exception as e:
                result[index_name] = {'error': str(e)}
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


# 命令行入口
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='预加载股票数据')
    parser.add_argument('--indices', nargs='+', default=['沪深300', '中证500'],
                       help='要预加载的指数，如：沪深300 中证500')
    parser.add_argument('--days', type=int, default=60,
                       help='历史数据天数，默认60天')
    parser.add_argument('--max-stocks', type=int, default=None,
                       help='最多处理的股票数量（用于测试）')
    parser.add_argument('--check', action='store_true',
                       help='仅检查预加载状态，不执行加载')
    
    args = parser.parse_args()
    
    if args.check:
        # 检查状态
        status = check_preload_status(args.indices)
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        # 执行预加载
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        result = preload_index_data(args.indices, args.days, args.max_stocks)
        print(json.dumps(result, ensure_ascii=False, indent=2))
