#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stockton Cloud 数据同步 V3 主入口

功能：
1. 从多数据源获取沪深300、中证500成分股数据（支持自动故障切换）
2. 获取指定ETF数据
3. 保存到本地 SQLite
4. 同步到 Cloudflare Workers

数据源支持（自动故障切换）：
    - akshare_tx (腾讯): 速度最快，推荐首选
    - akshare_sina (新浪): 数据完整，有成交额和换手率
    - baostock: 稳定性好，但有17:30延迟
    - akshare_em (东财): 数据最全，但可能被代理阻止
    
    当首选数据源失败时，自动切换到下一个可用数据源

使用方法：
    # 仅获取数据到本地（自动选择数据源）
    python cron.py --fetch-only
    
    # 指定首选数据源（失败时自动切换）
    python cron.py --fetch-only --data-source akshare_tx
    python cron.py --fetch-only --data-source baostock
    
    # 仅同步本地数据到 Workers
    python cron.py --sync-only
    
    # 完整流程（获取+同步）
    python cron.py
    
    # 强制更新指数成分股（每月自动更新）
    python cron.py --update-components
    
    # 指定Workers地址和API Key
    python cron.py --url https://your-worker.workers.dev --api-key xxx
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from local_db import LocalDatabase
from fetcher import StockDataFetcher
from sync import WorkersSync

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'./data/sync_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Stockton Cloud 数据同步 V2')
    
    parser.add_argument('--fetch-only', action='store_true',
                        help='仅获取数据到本地，不同步到 Workers')
    parser.add_argument('--sync-only', action='store_true',
                        help='仅同步本地数据到 Workers，不获取新数据')
    
    parser.add_argument('--url', type=str, default=os.getenv('WORKERS_URL'),
                        help='Workers URL (也可通过 WORKERS_URL 环境变量设置)')
    parser.add_argument('--api-key', type=str, default=os.getenv('API_KEY'),
                        help='API Key (也可通过 API_KEY 环境变量设置)')
    
    parser.add_argument('--db-path', type=str, default='./data/stock_data.db',
                        help='本地数据库路径')
    
    parser.add_argument('--indices', type=str, default='000300,000905',
                        help='要获取的指数，逗号分隔 (默认: 000300,000905)')
    
    parser.add_argument('--update-components', action='store_true',
                        help='强制更新指数成分股数据（默认每月自动检查更新）')
    
    parser.add_argument('--skip-components-check', action='store_true',
                        help='跳过指数成分股更新检查')
    
    parser.add_argument('--data-source', type=str, 
                        default=os.getenv('DATA_SOURCE', 'akshare_tx'),
                        choices=['akshare_tx', 'akshare_sina', 'akshare_em', 'baostock', 'akshare', 'efinance'],
                        help='数据源选择 (默认: akshare_tx 腾讯，其他: akshare_sina 新浪, akshare_em 东财, baostock)')
    
    parser.add_argument('--skip-stock-info', action='store_true',
                        help='跳过更新股票基本信息')
    
    parser.add_argument('--update-stock-info-only', action='store_true',
                        help='仅更新股票基本信息，不获取价格数据')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    logger.info("=" * 80)
    logger.info("Stockton Cloud 数据同步 V3")
    logger.info("=" * 80)
    logger.info(f"本地数据库: {args.db_path}")
    logger.info(f"Workers URL: {args.url or '未设置'}")
    
    # 确定模式
    mode_str = '完整流程'
    if args.fetch_only:
        mode_str = '仅获取'
    elif args.sync_only:
        mode_str = '仅同步'
    elif args.update_stock_info_only:
        mode_str = '仅更新股票信息'
    
    logger.info(f"模式: {mode_str}")
    logger.info(f"数据源: {args.data_source}")
    if not args.skip_stock_info and not args.update_stock_info_only:
        logger.info("股票信息: 自动更新")
    logger.info("=" * 80)
    
    # 初始化本地数据库
    local_db = LocalDatabase(args.db_path)
    
    # 模式: 仅更新股票基本信息
    if args.update_stock_info_only:
        logger.info("\n[模式] 仅更新股票基本信息\n")
        
        fetcher = StockDataFetcher(local_db=local_db, preferred_source=args.data_source)
        
        # 收集需要更新的股票代码
        codes_to_update = set()
        
        # 从指数成分股收集
        indices = [x.strip() for x in args.indices.split(',') if x.strip()]
        for index_code in indices:
            components = local_db.get_index_components(index_code)
            for comp in components:
                codes_to_update.add(comp['stock_code'])
        
        # 从自选股收集
        watchlist = local_db.get_watchlist()
        for stock in watchlist:
            codes_to_update.add(stock['code'])
        
        # 从ETF收集
        for etf_code in fetcher.etfs.keys():
            codes_to_update.add(etf_code)
        
        logger.info(f"共收集到 {len(codes_to_update)} 只待更新股票")
        
        if codes_to_update:
            # 更新股票基本信息
            stats = fetcher.fetch_and_save_stock_basic_info(list(codes_to_update))
            
            # 更新自选股名称
            if stats.get('saved', 0) > 0:
                fetcher.update_watchlist_stock_names()
            
            logger.info("\n" + "=" * 80)
            logger.info("股票信息更新完成!")
            logger.info(f"总计: {stats['total']} 只")
            logger.info(f"成功: {stats['saved']} 只")
            logger.info(f"跳过: {stats['skipped']} 只")
            logger.info(f"失败: {stats['failed']} 只")
            logger.info("=" * 80)
        
        return
    
    # 检查/更新指数成分股（除非跳过）
    if not args.skip_components_check:
        logger.info("\n[检查] 指数成分股...")
        fetcher = StockDataFetcher(local_db=local_db)
        indices = [x.strip() for x in args.indices.split(',') if x.strip()]
        
        for index_code in indices:
            if args.update_components:
                # 强制更新
                fetcher.update_index_components(index_code)
            else:
                # 检查是否需要更新（每月一次）
                if local_db.needs_components_update(index_code):
                    fetcher.update_index_components(index_code)
                else:
                    logger.info(f"  指数 {index_code}: 成分股数据最新，无需更新")
    
    # 模式1: 仅获取数据
    if args.fetch_only:
        logger.info("\n[模式] 仅获取数据到本地数据库\n")
        
        fetcher = StockDataFetcher(local_db=local_db, preferred_source=args.data_source)
        
        # 解析指数列表
        indices = [x.strip() for x in args.indices.split(',') if x.strip()]
        
        # 获取数据（根据参数决定是否更新股票信息）
        stats = fetcher.fetch_all(
            indices=indices,
            update_stock_info=not args.skip_stock_info
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("获取完成!")
        logger.info(f"新增记录数: {stats['total_new_records']}")
        logger.info(f"耗时: {stats['duration_seconds']:.1f} 秒")
        logger.info("表统计:")
        for code, count in stats.get('table_stats', {}).items():
            logger.info(f"  {code}: {count} 条")
        if 'stock_info_stats' in stats:
            si_stats = stats['stock_info_stats']
            logger.info(f"股票信息: {si_stats.get('total_count', 0)} 只")
        logger.info("=" * 80)
        
        return
    
    # 模式2: 仅同步数据
    if args.sync_only:
        if not args.url or not args.api_key:
            logger.error("错误: 同步模式需要提供 --url 和 --api-key (或设置环境变量)")
            sys.exit(1)
        
        logger.info("\n[模式] 仅同步本地数据到 Workers\n")
        
        sync = WorkersSync(args.url, args.api_key)
        
        # 健康检查
        if not sync.health_check():
            logger.error("Workers 健康检查失败，请检查 URL 是否正确")
            sys.exit(1)
        
        logger.info("Workers 健康检查通过")
        
        # 执行同步
        results = sync.sync_from_local_db(local_db)
        
        logger.info("\n" + "=" * 80)
        logger.info("同步完成!")
        logger.info(f"成功: {len([t for t, r in results['tables'].items() if r['success']])} 个表")
        logger.info(f"失败: {len(results['failed_tables'])} 个表")
        if results['failed_tables']:
            logger.info(f"失败的表: {', '.join(results['failed_tables'])}")
        logger.info(f"总记录数: {results['total_prices']}")
        logger.info("=" * 80)
        
        return
    
    # 模式3: 完整流程 (获取 + 同步)
    if not args.url or not args.api_key:
        logger.error("错误: 完整流程需要提供 --url 和 --api-key (或设置环境变量)")
        sys.exit(1)
    
    logger.info("\n[模式] 完整流程: 获取数据 + 同步到 Workers\n")
    
    # 步骤1: 获取数据
    logger.info("步骤 1/2: 获取数据...")
    fetcher = StockDataFetcher(local_db=local_db, preferred_source=args.data_source)
    indices = [x.strip() for x in args.indices.split(',') if x.strip()]
    fetch_stats = fetcher.fetch_all(
        indices=indices,
        update_stock_info=not args.skip_stock_info
    )
    
    logger.info(f"获取完成: {fetch_stats['total_new_records']} 条记录")
    
    # 步骤2: 同步数据
    logger.info("\n步骤 2/2: 同步到 Workers...")
    sync = WorkersSync(args.url, args.api_key)
    
    if not sync.health_check():
        logger.error("Workers 健康检查失败")
        sys.exit(1)
    
    sync_results = sync.sync_from_local_db(local_db)
    
    # 汇总报告
    logger.info("\n" + "=" * 80)
    logger.info("执行完成!")
    logger.info("=" * 80)
    logger.info(f"获取数据: {fetch_stats['total_new_records']} 条")
    logger.info(f"同步数据: {sync_results['total_prices']} 条")
    logger.info(f"成功表数: {len([t for t, r in sync_results['tables'].items() if r['success']])}")
    if sync_results['failed_tables']:
        logger.warning(f"失败表数: {len(sync_results['failed_tables'])}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
