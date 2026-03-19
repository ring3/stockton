#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================
QMT 客户端数据推送策略（简化版 - 本地文件模式）
=========================================

此脚本运行在 QMT/iQuant 客户端内，将数据写入本地文件，
然后通过文件同步到 python-fetcher。

适用于：
- 网络推送不稳定的环境
- 需要离线缓存的场景
- 简单的本地文件共享

配置方法：
1. 在 QMT 客户端中新建 Python 策略
2. 将此代码粘贴到策略编辑器
3. 修改 CONFIG 中的输出目录
4. 运行策略（实盘/模拟模式）

作者: Stockton
版本: 1.0.0
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============================================================
# 配置区域
# ============================================================
CONFIG = {
    # 输出目录（共享目录或本地目录）
    'output_dir': 'D:/qmt_data',  # 修改为实际路径
    
    # 数据刷新间隔（秒）
    'quote_interval': 5,     # 行情刷新间隔
    'option_interval': 30,   # 期权数据刷新间隔
    
    # 监控的股票列表
    'stock_codes': [
        '000001.SZ',
        '600519.SH',
    ],
    
    # 监控的期权标的
    'option_underlyings': [
        '510050.SH',
    ],
    
    # 日志级别
    'log_level': 'INFO',
}


# ============================================================
# 日志工具
# ============================================================
class Logger:
    LEVELS = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
    
    def __init__(self, level: str = 'INFO'):
        self.level = self.LEVELS.get(level, 1)
    
    def _log(self, level: str, msg: str):
        if self.LEVELS.get(level, 99) >= self.level:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            print(f"[{timestamp}] [{level}] {msg}")
    
    def debug(self, msg: str): self._log('DEBUG', msg)
    def info(self, msg: str): self._log('INFO', msg)
    def warning(self, msg: str): self._log('WARNING', msg)
    def error(self, msg: str): self._log('ERROR', msg)


logger = Logger(CONFIG['log_level'])


# ============================================================
# 数据管理器
# ============================================================
class LocalDataManager:
    """本地数据管理器 - 写入文件"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self._ensure_directory()
        
        # 文件路径
        self.quote_file = os.path.join(output_dir, 'realtime_quotes.json')
        self.option_file = os.path.join(output_dir, 'option_data.json')
        self.meta_file = os.path.join(output_dir, 'metadata.json')
    
    def _ensure_directory(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建输出目录: {self.output_dir}")
    
    def save_quotes(self, quotes: List[Dict]):
        """保存行情数据到文件"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(quotes),
            'quotes': quotes
        }
        
        with open(self.quote_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"保存行情数据: {len(quotes)} 条")
    
    def save_options(self, options: List[Dict]):
        """保存期权数据到文件"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(options),
            'options': options
        }
        
        with open(self.option_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"保存期权数据: {len(options)} 条")
    
    def update_metadata(self, **kwargs):
        """更新元数据"""
        metadata = {
            'last_update': datetime.now().isoformat(),
        }
        metadata.update(kwargs)
        
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


# ============================================================
# 简化版数据获取
# ============================================================
class SimpleQMTFetcher:
    """简化版 QMT 数据获取器"""
    
    def __init__(self, context_info):
        self.ctx = context_info
    
    def get_quote(self, code: str) -> Optional[Dict]:
        """获取行情数据"""
        try:
            # 获取最新价
            price = self.ctx.get_last_price(code)
            
            # 获取昨收计算涨跌幅
            history = self.ctx.get_history_data(2, '1d', 
                                                field_list=['close'], 
                                                stock_code=code)
            
            if len(history) >= 2:
                prev_close = history['close'][0]
                change_pct = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
            else:
                change_pct = 0
            
            return {
                'code': code.split('.')[0],
                'name': self.ctx.get_stock_name(code),
                'price': price,
                'change_pct': round(change_pct, 3),
                'volume': self.ctx.get_last_volume(code),
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"获取 {code} 失败: {e}")
            return None


# ============================================================
# QMT 策略函数
# ============================================================

# 全局变量
data_mgr = None
fetcher = None
last_quote_time = 0
last_option_time = 0


def init(ContextInfo):
    """初始化"""
    global data_mgr, fetcher
    
    logger.info("=" * 60)
    logger.info("QMT 本地文件推送策略启动")
    logger.info("=" * 60)
    
    data_mgr = LocalDataManager(CONFIG['output_dir'])
    fetcher = SimpleQMTFetcher(ContextInfo)
    
    # 设置股票池
    ContextInfo.set_universe(CONFIG['stock_codes'] + CONFIG['option_underlyings'])
    
    logger.info(f"输出目录: {CONFIG['output_dir']}")
    logger.info(f"监控股票: {CONFIG['stock_codes']}")
    logger.info("=" * 60)


def handlebar(ContextInfo):
    """主循环"""
    global data_mgr, fetcher, last_quote_time, last_option_time
    
    now = time.time()
    
    # 推送行情
    if now - last_quote_time >= CONFIG['quote_interval']:
        last_quote_time = now
        
        quotes = []
        for code in CONFIG['stock_codes']:
            quote = fetcher.get_quote(code)
            if quote:
                quotes.append(quote)
        
        if quotes:
            data_mgr.save_quotes(quotes)
            logger.info(f"更新行情: {len(quotes)} 条")
    
    # 推送期权（示例，实际需要根据你的 QMT API 调整）
    if now - last_option_time >= CONFIG['option_interval']:
        last_option_time = now
        # 期权数据获取逻辑...
        logger.debug("检查期权数据...")


# ============================================================
# 文件读取器（用于 python-fetcher 端读取）
# ============================================================
def read_qmt_quote_file(file_path: str) -> List[Dict]:
    """
    读取 QMT 输出的行情文件
    
    在 python-fetcher 中使用此函数读取数据
    """
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('quotes', [])
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return []


if __name__ == '__main__':
    print("此脚本应在 QMT 客户端内运行")
