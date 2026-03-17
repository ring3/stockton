# -*- coding: utf-8 -*-
"""
股票数据拉取模块
使用 akshare 获取 A 股数据
"""
import logging
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# 指数代码映射
INDEX_MAP = {
    '000300': '沪深300',
    '000905': '中证500',
    '000852': '中证1000',
    '000016': '上证50',
}


class StockDataFetcher:
    """股票数据拉取器"""
    
    def __init__(self):
        self.indices = INDEX_MAP
    
    def get_index_components(self, index_code: str) -> List[str]:
        """
        获取指数成分股代码列表
        
        Args:
            index_code: 指数代码，如 '000300'
            
        Returns:
            成分股代码列表
        """
        try:
            logger.info(f"获取指数 {index_code} 成分股...")
            df = ak.index_stock_cons_weight_csindex(symbol=index_code)
            
            if df is None or df.empty:
                logger.warning(f"指数 {index_code} 返回空数据")
                return []
            
            codes = df['成分券代码'].tolist()
            logger.info(f"指数 {index_code} 成分股数量: {len(codes)}")
            return codes
            
        except Exception as e:
            logger.error(f"获取指数 {index_code} 成分股失败: {e}")
            return []
    
    def get_stock_history(self, code: str, days: int = 60) -> List[Dict]:
        """
        获取股票历史K线数据
        
        Args:
            code: 股票代码
            days: 历史天数
            
        Returns:
            K线数据列表
        """
        try:
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 20)  # 多取20天用于计算均线
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq"  # 前复权
            )
            
            if df is None or df.empty:
                logger.debug(f"股票 {code} 无历史数据")
                return []
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate',
            })
            
            # 计算技术指标
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            
            # 只保留最近的数据
            df = df.tail(days)
            
            # 转换为字典列表
            records = []
            for _, row in df.iterrows():
                records.append({
                    'code': code,
                    'date': row['date'],
                    'open': self._safe_float(row.get('open')),
                    'high': self._safe_float(row.get('high')),
                    'low': self._safe_float(row.get('low')),
                    'close': self._safe_float(row.get('close')),
                    'volume': int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                    'amount': self._safe_float(row.get('amount')),
                    'ma5': self._safe_float(row.get('ma5')),
                    'ma10': self._safe_float(row.get('ma10')),
                    'ma20': self._safe_float(row.get('ma20')),
                    'ma60': self._safe_float(row.get('ma60')),
                    'change_pct': self._safe_float(row.get('change_pct')),
                    'turnover_rate': self._safe_float(row.get('turnover_rate')),
                })
            
            return records
            
        except Exception as e:
            logger.error(f"获取股票 {code} 历史数据失败: {e}")
            return []
    
    def get_market_stats(self) -> Dict:
        """
        获取市场统计数据
        
        Returns:
            市场统计字典
        """
        try:
            logger.info("获取市场统计数据...")
            df = ak.stock_market_activity_legu()
            
            if df is None or df.empty:
                logger.warning("市场统计数据为空")
                return {}
            
            # 转换为字典
            stats = dict(zip(df['item'], df['value']))
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'up_count': int(stats.get('上涨', 0)),
                'down_count': int(stats.get('下跌', 0)),
                'flat_count': int(stats.get('平盘', 0)),
                'limit_up_count': int(stats.get('涨停', 0)),
                'limit_down_count': int(stats.get('跌停', 0)),
            }
            
        except Exception as e:
            logger.error(f"获取市场统计数据失败: {e}")
            return {}
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except:
            return None
