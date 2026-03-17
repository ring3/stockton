# -*- coding: utf-8 -*-
"""
股票数据拉取模块 V3
支持增量更新：根据数据库已有数据智能确定获取范围
支持多数据源：akshare、efinance（自动故障切换）
"""
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

try:
    from .data_source import DataSourceManager
except ImportError:
    from data_source import DataSourceManager

logger = logging.getLogger(__name__)

# 指数代码映射
INDEX_MAP = {
    '000300': '沪深300',
    '000905': '中证500',
}

# ETF代码映射
ETF_MAP = {
    '510050': '上证50ETF',
    '510300': '沪深300ETF',
    '588000': '科创50ETF',
    '159915': '创业板ETF',
    '510500': '中证500ETF',
}

# 历史数据起始日期（全量获取的起始日期）
HISTORY_START_DATE = '20230101'


class StockDataFetcher:
    """股票数据拉取器 V3 - 支持增量更新和多数据源"""
    
    # 数据源名称映射（兼容旧名称）
    SOURCE_MAP = {
        'akshare': 'akshare_em',      # 旧名称映射到东财
        'eastmoney': 'akshare_em',
        'sina': 'akshare_sina',
        'tencent': 'akshare_tx',
    }
    
    def __init__(self, local_db=None, preferred_source: str = 'akshare_sina'):
        """
        初始化
        
        Args:
            local_db: 本地数据库实例 (LocalDatabase)
            preferred_source: 首选数据源名称 ('akshare_tx', 'akshare_sina', 'akshare_em')
        """
        self.indices = INDEX_MAP
        self.etfs = ETF_MAP
        self.local_db = local_db
        self.history_start = HISTORY_START_DATE
        
        # 映射旧名称
        mapped_source = self.SOURCE_MAP.get(preferred_source, preferred_source)
        
        # 初始化数据源管理器（自动故障切换）
        try:
            self.data_source = DataSourceManager(preferred_source=mapped_source)
            logger.info(f"使用数据源: {self.data_source.current_source_name}")
        except RuntimeError as e:
            logger.error(f"初始化数据源失败: {e}")
            raise
    
    def _get_date_range(self, table_name: str, code: str) -> Tuple[str, str]:
        """
        根据数据库已有数据确定获取日期范围
        
        直接从最新日期开始获取（覆盖更新），简化逻辑，支持盘中多次更新：
        - 首次获取：从2023-01-01获取到今天
        - 后续获取：从数据库最新日期获取到今天（覆盖已有数据）
        - 盘中更新：交易时间内可多次运行，每次都从当天开始获取最新数据
        
        Args:
            table_name: 表名
            code: 股票代码
            
        Returns:
            (start_date, end_date) 格式：YYYYMMDD
        """
        today = datetime.now().strftime('%Y%m%d')
        
        if not self.local_db:
            # 没有本地数据库，获取全部历史数据
            logger.info(f"  无本地数据库，使用默认起始日期: {self.history_start}")
            return (self.history_start, today)
        
        # 查询数据库中的最新日期
        latest_date = self.local_db.get_latest_date(table_name, code)
        
        if latest_date is None:
            # 数据库中没有该股票的数据，从2023-01-01开始获取
            logger.info(f"  数据库中无数据，从 {self.history_start} 开始获取")
            return (self.history_start, today)
        
        # 数据库中已有数据，直接从最新日期开始获取（覆盖更新）
        # 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
        if latest_date and '-' in latest_date:
            latest_date_fmt = latest_date.replace('-', '')
        else:
            latest_date_fmt = latest_date
        logger.info(f"  数据库最新日期: {latest_date}，从该日期开始获取到今天 ({today})")
        return (latest_date_fmt, today)
    
    def _fetch_from_source(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """
        从当前数据源获取股票历史数据
        
        注意：网络连接异常会直接抛出，不会返回空列表，以便调用者中断执行
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            K线数据列表（可能为空，表示无数据但不是错误）
            
        Raises:
            ConnectionError: 网络连接异常等错误直接抛出，不捕获
        """
        # 使用数据源管理器获取数据（直接从 start_date 开始，无需提前120天）
        records = self.data_source.get_stock_history(code, start_date, end_date)
        
        if not records:
            logger.debug(f"股票 {code} 无历史数据")
            return []
        
        return records
    
    def get_stock_history(self, code: str, table_name: str) -> List[Dict]:
        """
        获取股票历史数据（智能增量更新）
        
        Args:
            code: 股票代码
            table_name: 要保存到的表名（用于查询已有数据）
            
        Returns:
            K线数据列表
        """
        # 确定日期范围
        start_date, end_date = self._get_date_range(table_name, code)
        
        if start_date is None:
            # 数据已是最新，无需获取
            return []
        
        # 获取数据 - 失败时直接抛出异常
        return self._fetch_from_source(code, start_date, end_date)
    
    def get_index_components(self, index_code: str, 
                              use_cache: bool = True) -> List[str]:
        """
        获取指数成分股代码列表
        
        优先从本地数据库获取，如果没有数据或需要更新，则从数据源获取
        
        Args:
            index_code: 指数代码，如 '000300'
            use_cache: 是否使用本地缓存
            
        Returns:
            成分股代码列表
            
        Raises:
            RuntimeError: 无法获取成分股
        """
        # 1. 尝试从本地数据库获取
        if use_cache and self.local_db:
            components = self.local_db.get_index_components(index_code)
            
            if components:
                # 检查是否需要更新（超过30天）
                if not self.local_db.needs_components_update(index_code):
                    logger.info(f"指数 {index_code}: 从本地数据库获取 {len(components)} 只成分股")
                    return [c['stock_code'] for c in components]
                else:
                    logger.info(f"指数 {index_code}: 本地数据需要更新，从网络获取")
            else:
                logger.info(f"指数 {index_code}: 本地无数据，从网络获取")
        
        # 2. 从数据源获取
        return self._fetch_components_from_source(index_code)
    
    def _fetch_components_from_source(self, index_code: str) -> List[str]:
        """
        从数据源获取指数成分股（内部方法）
        
        Args:
            index_code: 指数代码
            
        Returns:
            成分股代码列表
            
        Raises:
            RuntimeError: 无法获取成分股
        """
        logger.info(f"从 {self.data_source.current_source_name} 获取指数 {index_code} 成分股...")
        
        components = self.data_source.get_index_components(index_code)
        
        if not components:
            raise RuntimeError(f"无法获取指数 {index_code} 成分股")
        
        codes = [c['stock_code'] for c in components]
        logger.info(f"指数 {index_code} 成分股数量: {len(codes)}")
        
        # 保存到本地数据库
        if self.local_db:
            index_name = self.indices.get(index_code, index_code)
            self.local_db.save_index_components(index_code, index_name, components)
        
        return codes
    
    def update_index_components(self, index_code: str) -> bool:
        """
        强制更新指数成分股数据
        
        Args:
            index_code: 指数代码
            
        Returns:
            是否成功
        """
        logger.info(f"强制更新指数 {index_code} 成分股...")
        codes = self._fetch_components_from_source(index_code)
        return len(codes) > 0
    
    def fetch_and_save_index_components(self, index_code: str, 
                                        batch_size: int = 50) -> Dict:
        """
        获取指数成分股数据并保存到本地数据库（增量更新）
        
        注意：网络连接异常会直接抛出中断执行，不会继续处理其他股票
        
        Args:
            index_code: 指数代码
            batch_size: 每批处理的股票数
            
        Returns:
            统计信息 dict
            
        Raises:
            ConnectionError: 网络连接异常等错误直接抛出，中断执行
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return {'total': 0, 'updated': 0, 'skipped': 0}
        
        table_name = self.local_db.get_index_table_name(index_code)
        if not table_name:
            logger.error(f"不支持的指数代码: {index_code}")
            return {'total': 0, 'updated': 0, 'skipped': 0}
        
        # 获取成分股列表
        stocks = self.get_index_components(index_code)
        if not stocks:
            return {'total': 0, 'updated': 0, 'skipped': 0}
        
        logger.info(f"\n开始处理指数 {index_code} ({self.indices.get(index_code)})")
        logger.info(f"成分股总数: {len(stocks)}")
        logger.info(f"保存到表: {table_name}")
        
        stats = {
            'total': len(stocks),
            'updated': 0,      # 有数据更新的股票数
            'skipped': 0,      # 数据已最新跳过的股票数
            'new_records': 0,  # 新增记录数
        }
        
        for i, code in enumerate(stocks):
            logger.info(f"[{i+1}/{len(stocks)}] 处理 {code}...")
            
            # 获取数据（自动判断增量或全量）
            # 注意：所有数据源都失败时会抛出异常，中断整个执行
            prices = self.get_stock_history(code, table_name)
            
            if prices:
                # 保存数据（使用 INSERT OR REPLACE 自动处理重复）
                saved = self.local_db.save_prices(table_name, prices)
                stats['updated'] += 1
                stats['new_records'] += saved
                logger.info(f"  [OK] 新增/更新 {saved} 条记录")
            else:
                # 数据已是最新，无需更新
                stats['skipped'] += 1
                logger.info(f"  [SKIP] 无新数据或已是最新")
            
            # 延时避免请求过快
            if (i + 1) % batch_size == 0:
                logger.info(f"已完成 {i+1}/{len(stocks)}，暂停一下...")
                import time
                time.sleep(2)
            else:
                import time
                time.sleep(0.3)
        
        logger.info(f"\n{index_code} 处理完成:")
        logger.info(f"  更新: {stats['updated']}, 跳过: {stats['skipped']}")
        logger.info(f"  新增记录: {stats['new_records']}")
        
        return stats
    
    def fetch_and_save_etfs(self) -> Dict:
        """
        获取所有ETF数据并保存到本地数据库（增量更新）
        
        注意：网络连接异常会直接抛出中断执行
        
        Returns:
            统计信息
            
        Raises:
            ConnectionError: 网络连接异常等错误直接抛出，中断执行
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return {'total': 0, 'updated': 0, 'new_records': 0}
        
        table_name = self.local_db.ETF_TABLE
        total_new_records = 0
        updated_etfs = 0
        skipped_etfs = 0
        
        for etf_code, etf_name in self.etfs.items():
            logger.info(f"\n处理 ETF {etf_code} ({etf_name})...")
            
            # 获取数据（自动判断增量或全量）
            # 注意：所有数据源都失败时会抛出异常，中断整个执行
            prices = self.get_stock_history(etf_code, table_name)
            
            if prices:
                # 添加ETF名称
                for p in prices:
                    p['name'] = etf_name
                
                # 保存到统一ETF表
                saved = self.local_db.save_etf_prices(prices)
                total_new_records += saved
                updated_etfs += 1
                logger.info(f"  [OK] 新增/更新 {saved} 条记录")
            else:
                skipped_etfs += 1
                logger.info(f"  [SKIP] 无新数据或已是最新")
        
        logger.info(f"\nETF处理完成:")
        logger.info(f"  更新: {updated_etfs}, 跳过: {skipped_etfs}")
        logger.info(f"  新增记录: {total_new_records}")
        
        return {
            'total': len(self.etfs),
            'updated': updated_etfs,
            'skipped': skipped_etfs,
            'new_records': total_new_records
        }
    
    def fetch_all(self, indices: List[str] = None) -> Dict:
        """
        获取所有数据并保存到本地数据库（增量更新）
        
        Args:
            indices: 要获取的指数列表，默认所有配置的指数
            
        Returns:
            统计信息
        """
        if indices is None:
            indices = list(self.indices.keys())
        
        start_time = datetime.now()
        stats = {
            'indices': {},
            'etfs': {},
            'total_stocks': 0,
            'total_updated': 0,
            'total_new_records': 0,
            'start_time': start_time.isoformat(),
        }
        
        # 获取指数成分股数据
        for index_code in indices:
            if index_code not in self.indices:
                logger.warning(f"跳过未知指数: {index_code}")
                continue
            
            index_stats = self.fetch_and_save_index_components(index_code)
            stats['indices'][index_code] = index_stats
            stats['total_stocks'] += index_stats['total']
            stats['total_updated'] += index_stats['updated']
            stats['total_new_records'] += index_stats['new_records']
        
        # 获取ETF数据
        etf_stats = self.fetch_and_save_etfs()
        stats['etfs'] = etf_stats
        stats['total_new_records'] += etf_stats['new_records']
        
        end_time = datetime.now()
        stats['end_time'] = end_time.isoformat()
        stats['duration_seconds'] = (end_time - start_time).total_seconds()
        
        # 获取表统计
        if self.local_db:
            stats['table_stats'] = self.local_db.get_table_stats()
        
        return stats
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except:
            return None
