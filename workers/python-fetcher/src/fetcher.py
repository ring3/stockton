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
    from .data_source import DataSourceManager, is_hk_stock_code
    from .local_db import LocalDatabase
except ImportError:
    from data_source import DataSourceManager, is_hk_stock_code
    from local_db import LocalDatabase

try:
    import akshare as ak
except ImportError:
    ak = None

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
        
        数据统一保存到 stock_a_data 表，不再按指数分开存放
        
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
        
        # 获取成分股列表
        stocks = self.get_index_components(index_code)
        if not stocks:
            return {'total': 0, 'updated': 0, 'skipped': 0}
        
        # 统一使用 stock_a_data 表
        table_name = self.local_db.STOCK_A_TABLE
        
        logger.info(f"\n开始处理指数 {index_code} ({self.indices.get(index_code)})")
        logger.info(f"成分股总数: {len(stocks)}")
        logger.info(f"统一保存到表: {table_name}")
        
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
                # 保存数据到统一表（使用 INSERT OR REPLACE 自动处理重复）
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
        
        ETF数据统一保存到 stock_a_data 表，不再单独存放
        
        注意：网络连接异常会直接抛出中断执行
        
        Returns:
            统计信息
            
        Raises:
            ConnectionError: 网络连接异常等错误直接抛出，中断执行
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return {'total': 0, 'updated': 0, 'new_records': 0}
        
        # 统一使用 stock_a_data 表
        table_name = self.local_db.STOCK_A_TABLE
        total_new_records = 0
        updated_etfs = 0
        skipped_etfs = 0
        
        for etf_code, etf_name in self.etfs.items():
            logger.info(f"\n处理 ETF {etf_code} ({etf_name})...")
            
            # 获取数据（自动判断增量或全量）
            # 注意：所有数据源都失败时会抛出异常，中断整个执行
            prices = self.get_stock_history(etf_code, table_name)
            
            if prices:
                # 保存到统一表 stock_a_data
                saved = self.local_db.save_prices(table_name, prices)
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
    
    def fetch_all(self, indices: List[str] = None, 
                  update_stock_info: bool = True) -> Dict:
        """
        获取所有数据并保存到本地数据库（增量更新）
        
        Args:
            indices: 要获取的指数列表，默认所有配置的指数
            update_stock_info: 是否更新股票基本信息
            
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
        
        # 获取自选股数据
        logger.info(f"\n{'='*60}")
        logger.info("开始处理自选股列表")
        logger.info(f"{'='*60}")
        watchlist_stats = self.fetch_and_save_watchlist()
        stats['watchlist'] = watchlist_stats
        if watchlist_stats.get('success'):
            stats['total_new_records'] += watchlist_stats.get('new_records', 0)
        
        # 更新股票基本信息
        if update_stock_info and self.local_db:
            logger.info(f"\n{'='*60}")
            logger.info("开始更新股票基本信息")
            logger.info(f"{'='*60}")
            
            # 收集需要更新的股票代码
            codes_to_update = set()
            
            # 从指数成分股收集
            for index_code in indices:
                components = self.local_db.get_index_components(index_code)
                for comp in components:
                    codes_to_update.add(comp['stock_code'])
            
            # 从自选股收集
            watchlist = self.local_db.get_watchlist()
            for stock in watchlist:
                codes_to_update.add(stock['code'])
            
            # 从ETF收集
            for etf_code in self.etfs.keys():
                codes_to_update.add(etf_code)
            
            if codes_to_update:
                stock_info_stats = self.fetch_and_save_stock_basic_info(list(codes_to_update))
                stats['stock_info'] = stock_info_stats
                
                # 更新自选股名称
                if stock_info_stats.get('saved', 0) > 0:
                    name_update_stats = self.update_watchlist_stock_names()
                    stats['watchlist_name_update'] = name_update_stats
            else:
                logger.info("没有需要更新股票基本信息的代码")
        
        end_time = datetime.now()
        stats['end_time'] = end_time.isoformat()
        stats['duration_seconds'] = (end_time - start_time).total_seconds()
        
        # 获取表统计
        if self.local_db:
            stats['table_stats'] = self.local_db.get_table_stats()
            stats['stock_info_stats'] = self.local_db.get_stock_info_stats()
        
        return stats
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except:
            return None
    
    # ============================================================
    # 股票基本信息相关方法
    # ============================================================
    
    def fetch_and_save_stock_basic_info(self, codes: List[str]) -> Dict:
        """
        批量获取并保存股票基本信息
        
        Args:
            codes: 股票代码列表
            
        Returns:
            统计信息字典
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return {'success': False, 'error': 'No local_db provided'}
        
        if not codes:
            logger.info("股票代码列表为空")
            return {'success': True, 'total': 0, 'saved': 0}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始获取股票基本信息，共 {len(codes)} 只")
        logger.info(f"{'='*60}")
        
        stats = {
            'success': True,
            'total': len(codes),
            'saved': 0,
            'failed': 0,
            'skipped': 0,
            'info_list': []
        }
        
        for i, code in enumerate(codes):
            logger.info(f"[{i+1}/{len(codes)}] 获取 {code} 基本信息...")
            
            # 检查是否已存在且近期更新过（7天内）
            existing = self.local_db.get_stock_basic_info(code)
            if existing and existing.get('updated_at'):
                from datetime import datetime, timedelta
                updated_at = datetime.fromisoformat(existing['updated_at'])
                if datetime.now() - updated_at < timedelta(days=7):
                    logger.info(f"  [SKIP] {code} 信息已存在且7天内更新过")
                    stats['skipped'] += 1
                    continue
            
            try:
                # 从数据源获取
                info = self.data_source.get_stock_basic_info(code)
                
                if info and info.get('name'):
                    # 保存到本地数据库
                    success = self.local_db.save_stock_basic_info(
                        info, 
                        data_source=self.data_source.current_source_name
                    )
                    if success:
                        stats['saved'] += 1
                        stats['info_list'].append(info)
                        logger.info(f"  [OK] {code} - {info.get('name')}")
                    else:
                        stats['failed'] += 1
                        logger.warning(f"  [FAIL] {code} 保存失败")
                else:
                    stats['failed'] += 1
                    logger.warning(f"  [FAIL] {code} 获取不到数据")
                
                # 延时避免请求过快
                if i < len(codes) - 1:
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                stats['failed'] += 1
                logger.error(f"  [ERROR] {code} 获取失败: {e}")
        
        logger.info(f"\n股票基本信息获取完成:")
        logger.info(f"  总计: {stats['total']} 只")
        logger.info(f"  成功保存: {stats['saved']} 只")
        logger.info(f"  跳过: {stats['skipped']} 只")
        logger.info(f"  失败: {stats['failed']} 只")
        
        return stats
    
    def update_watchlist_stock_names(self) -> Dict:
        """
        更新自选股列表中的股票名称
        
        从 stock_basic_info 表中获取名称，更新到 watchlist 表
        
        Returns:
            统计信息字典
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return {'success': False, 'error': 'No local_db provided'}
        
        # 获取自选股列表
        watchlist = self.local_db.get_watchlist()
        if not watchlist:
            logger.info("自选股列表为空")
            return {'success': True, 'total': 0, 'updated': 0}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始更新自选股名称，共 {len(watchlist)} 只")
        logger.info(f"{'='*60}")
        
        stats = {
            'success': True,
            'total': len(watchlist),
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }
        
        for stock in watchlist:
            code = stock['code']
            current_name = stock['name']
            
            # 从股票信息表获取名称
            info = self.local_db.get_stock_basic_info(code)
            if info and info.get('name'):
                new_name = info['name']
                if new_name and new_name != current_name:
                    # 更新 watchlist
                    if self.local_db.add_to_watchlist(code, new_name, stock['market_type']):
                        logger.info(f"  [UPDATE] {code}: {current_name} -> {new_name}")
                        stats['updated'] += 1
                    else:
                        stats['failed'] += 1
                else:
                    stats['skipped'] += 1
            else:
                logger.debug(f"  [SKIP] {code} 未找到股票信息")
                stats['skipped'] += 1
        
        logger.info(f"\n自选股名称更新完成:")
        logger.info(f"  总计: {stats['total']} 只")
        logger.info(f"  更新: {stats['updated']} 只")
        logger.info(f"  跳过: {stats['skipped']} 只")
        logger.info(f"  失败: {stats['failed']} 只")
        
        return stats
    
    # ============================================================
    # 自选股相关方法
    # ============================================================
    
    def _search_stock_code(self, keyword: str) -> Optional[Dict]:
        """
        通过关键词（名称或代码）搜索股票代码
        
        Args:
            keyword: 股票名称或代码
            
        Returns:
            股票信息字典 {'code': str, 'name': str, 'market_type': str}，未找到返回None
        """
        if ak is None:
            logger.error("akshare 未安装，无法搜索股票")
            return None
        
        # 先判断是否为港股代码格式
        if is_hk_stock_code(keyword):
            # 尝试获取港股名称
            try:
                df = ak.stock_hk_spot_em()
                # 去除hk前缀进行匹配
                search_code = keyword.lower().replace('hk', '')
                match = df[df['代码'].astype(str).str.zfill(5) == search_code.zfill(5)]
                if not match.empty:
                    return {
                        'code': search_code.zfill(5),
                        'name': match.iloc[0]['名称'],
                        'market_type': 'H'
                    }
            except Exception as e:
                logger.warning(f"搜索港股 {keyword} 失败: {e}")
            
            # 如果无法获取名称，直接返回代码
            code = keyword.lower().replace('hk', '').zfill(5)
            return {'code': code, 'name': None, 'market_type': 'H'}
        
        # 判断是否为A股代码格式（6位数字）
        if len(keyword) == 6 and keyword.isdigit():
            # 尝试获取A股名称
            try:
                df = ak.stock_zh_a_spot_em()
                match = df[df['代码'] == keyword]
                if not match.empty:
                    return {
                        'code': keyword,
                        'name': match.iloc[0]['名称'],
                        'market_type': 'A'
                    }
            except Exception as e:
                logger.warning(f"搜索A股 {keyword} 失败: {e}")
            
            # 如果无法获取名称，根据代码规则判断市场
            if keyword.startswith('6'):
                return {'code': keyword, 'name': None, 'market_type': 'A'}
            elif keyword.startswith('0') or keyword.startswith('3'):
                return {'code': keyword, 'name': None, 'market_type': 'A'}
            elif keyword.startswith('68') or keyword.startswith('8') or keyword.startswith('4'):
                return {'code': keyword, 'name': None, 'market_type': 'A'}
        
        # 按名称搜索A股
        try:
            df = ak.stock_zh_a_spot_em()
            match = df[df['名称'].str.contains(keyword, case=False, na=False)]
            if not match.empty:
                return {
                    'code': match.iloc[0]['代码'],
                    'name': match.iloc[0]['名称'],
                    'market_type': 'A'
                }
        except Exception as e:
            logger.warning(f"按名称搜索A股 {keyword} 失败: {e}")
        
        # 按名称搜索港股
        try:
            df = ak.stock_hk_spot_em()
            match = df[df['名称'].str.contains(keyword, case=False, na=False)]
            if not match.empty:
                code = match.iloc[0]['代码']
                if isinstance(code, int):
                    code = str(code).zfill(5)
                else:
                    code = str(code).zfill(5)
                return {
                    'code': code,
                    'name': match.iloc[0]['名称'],
                    'market_type': 'H'
                }
        except Exception as e:
            logger.warning(f"按名称搜索港股 {keyword} 失败: {e}")
        
        logger.warning(f"未找到股票: {keyword}")
        return None
    
    def update_watch_list(self, code: str, name: str = None) -> Optional[Dict]:
        """
        更新自选股列表
        
        将指定股票添加到自选股列表。根据代码自动判断是A股还是港股。
        如果股票已存在，则更新信息。
        
        Args:
            code: 股票代码（如 '000001' 或 '00700'，港股可带'hk'前缀如'hk00700'）
            name: 股票名称（可选）
            
        Returns:
            股票信息字典 {'code': str, 'name': str, 'market_type': str, 'added': bool}
            added=True 表示新添加，added=False 表示已存在
            失败返回None
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return None
        
        if not code:
            logger.error("股票代码不能为空")
            return None
        
        # 判断是A股还是港股
        if is_hk_stock_code(code):
            market_type = 'H'
            # 标准化港股代码（去除hk前缀）
            code = code.lower().replace('hk', '').zfill(5)
        else:
            market_type = 'A'
        
        logger.info(f"更新自选股: {code} ({name}) [{market_type}股]")
        
        # 检查是否已在自选股列表
        is_existing = self.local_db.is_in_watchlist(code)
        
        # 添加到自选股列表
        success = self.local_db.add_to_watchlist(code, name, market_type)
        
        if success:
            result = {
                'code': code,
                'name': name,
                'market_type': market_type,
                'added': not is_existing
            }
            if is_existing:
                logger.info(f"股票已在自选股列表中: {code} ({name}) [{market_type}股]")
            else:
                logger.info(f"成功添加到自选股: {code} ({name}) [{market_type}股]")
            return result
        else:
            logger.error(f"添加到自选股失败: {code}")
            return None
    
    def fetch_and_save_watchlist(self) -> Dict:
        """
        拉取并保存自选股列表中所有股票的数据
        
        根据股票的类型（A股或港股）使用不同的数据源适配器，
        并将数据保存到对应的表中（stock_a_data 或 stock_h_data）。
        
        Returns:
            统计信息字典
        """
        if not self.local_db:
            logger.error("未设置本地数据库")
            return {'success': False, 'error': 'No local_db provided'}
        
        # 获取自选股列表
        watchlist = self.local_db.get_watchlist()
        if not watchlist:
            logger.info("自选股列表为空")
            return {'success': True, 'total': 0, 'updated': 0, 'skipped': 0, 'new_records': 0}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始处理自选股列表，共 {len(watchlist)} 只股票")
        logger.info(f"{'='*60}")
        
        stats = {
            'success': True,
            'total': len(watchlist),
            'updated': 0,
            'skipped': 0,
            'new_records': 0,
            'A': {'updated': 0, 'skipped': 0, 'new_records': 0},
            'H': {'updated': 0, 'skipped': 0, 'new_records': 0},
        }
        
        for i, stock in enumerate(watchlist):
            code = stock['code']
            name = stock['name'] or code
            market_type = stock['market_type']
            
            logger.info(f"[{i+1}/{len(watchlist)}] 处理 {code} ({name}) [{market_type}股]...")
            
            try:
                # 根据市场类型选择表名和适配器
                if market_type == 'H':
                    table_name = self.local_db.STOCK_H_TABLE
                    # 港股使用港股适配器
                    prices = self._fetch_hk_stock_history(code)
                else:
                    table_name = self.local_db.STOCK_A_TABLE
                    # A股使用普通方法
                    prices = self.get_stock_history(code, table_name)
                
                if prices:
                    # 保存数据
                    saved = self.local_db.save_prices(table_name, prices)
                    stats['updated'] += 1
                    stats['new_records'] += saved
                    stats[market_type]['updated'] += 1
                    stats[market_type]['new_records'] += saved
                    
                    # 更新最后同步日期
                    today = datetime.now().strftime('%Y-%m-%d')
                    self.local_db.update_watchlist_sync_date(code, today)
                    
                    logger.info(f"  [OK] 新增/更新 {saved} 条记录")
                else:
                    stats['skipped'] += 1
                    stats[market_type]['skipped'] += 1
                    logger.info(f"  [SKIP] 无新数据或已是最新")
                
                # 延时避免请求过快
                if i < len(watchlist) - 1:
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"  [ERROR] 处理 {code} 失败: {e}")
                stats['success'] = False
        
        logger.info(f"\n自选股处理完成:")
        logger.info(f"  总计: {stats['total']} 只")
        logger.info(f"  更新: {stats['updated']} 只, 跳过: {stats['skipped']} 只")
        logger.info(f"  新增记录: {stats['new_records']} 条")
        logger.info(f"  A股: 更新 {stats['A']['updated']}, 新增记录 {stats['A']['new_records']}")
        logger.info(f"  港股: 更新 {stats['H']['updated']}, 新增记录 {stats['H']['new_records']}")
        
        return stats
    
    def _fetch_hk_stock_history(self, code: str) -> List[Dict]:
        """
        获取港股历史数据
        
        Args:
            code: 港股代码
            
        Returns:
            历史数据列表
        """
        if not ak:
            logger.error("akshare 未安装")
            return []
        
        try:
            # 获取日期范围
            table_name = self.local_db.STOCK_H_TABLE
            start_date, end_date = self._get_date_range(table_name, code)
            
            logger.info(f"  获取港股数据: {code}, 范围: {start_date} ~ {end_date}")
            
            # 使用akshare获取港股数据
            df = ak.stock_hk_hist(symbol=code, period="daily", 
                                  start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df is None or df.empty:
                logger.info(f"  无新数据")
                return []
            
            # 转换列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'change_pct',
                '换手率': 'turnover_rate',
            })
            
            # 计算均线
            df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean().round(3)
            df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean().round(3)
            df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean().round(3)
            df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean().round(3)
            
            # 构建记录列表
            records = []
            for _, row in df.iterrows():
                records.append({
                    'code': code,
                    'date': row['date'],
                    'open': self._safe_float(row['open']),
                    'high': self._safe_float(row['high']),
                    'low': self._safe_float(row['low']),
                    'close': self._safe_float(row['close']),
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                    'amount': self._safe_float(row['amount']),
                    'ma5': self._safe_float(row['ma5']),
                    'ma10': self._safe_float(row['ma10']),
                    'ma20': self._safe_float(row['ma20']),
                    'ma60': self._safe_float(row['ma60']),
                    'change_pct': self._safe_float(row['change_pct']),
                    'turnover_rate': self._safe_float(row['turnover_rate']),
                })
            
            return records
            
        except Exception as e:
            logger.error(f"  获取港股数据失败 {code}: {e}")
            return []
