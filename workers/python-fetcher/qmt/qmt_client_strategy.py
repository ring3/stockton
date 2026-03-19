#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================
QMT 客户端数据推送策略
=========================================

此脚本运行在 QMT/iQuant 客户端内，负责：
1. 拉取实时行情数据
2. 拉取期权数据（包括 Greeks、IV）
3. 拉取持仓数据
4. 通过 HTTP 推送到数据接收服务

配置方法：
1. 在 QMT 客户端中新建 Python 策略
2. 将此代码粘贴到策略编辑器
3. 修改 CONFIG 中的推送地址
4. 运行策略（实盘/模拟模式）

作者: Stockton
版本: 1.0.0
"""

import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============================================================
# 配置区域（根据你的环境修改）
# ============================================================
CONFIG = {
    # 数据接收服务地址
    'push_url': 'http://127.0.0.1:8888',  # 如果本机运行，改为你的服务IP
    
    # 推送间隔（秒）
    'quote_interval': 5,      # 行情推送间隔
    'option_interval': 30,    # 期权数据推送间隔
    'position_interval': 60,  # 持仓数据推送间隔
    
    # 监控的股票列表
    'stock_codes': [
        '000001.SZ',   # 平安银行
        '600519.SH',   # 贵州茅台
        '000333.SZ',   # 美的集团
    ],
    
    # 监控的期权标的
    'option_underlyings': [
        '510050.SH',   # 50ETF
        '510300.SH',   # 300ETF
        '159915.SZ',   # 创业板ETF
    ],
    
    # 监控的指数
    'index_codes': [
        '000001.SH',   # 上证指数
        '399001.SZ',   # 深证成指
        '000300.SH',   # 沪深300
        '000905.SH',   # 中证500
    ],
    
    # 日志级别: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    'log_level': 'INFO',
    
    # 重试配置
    'max_retries': 3,
    'retry_delay': 1,
}

# ============================================================
# 日志工具
# ============================================================
class Logger:
    """简单的日志工具"""
    
    LEVELS = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
    
    def __init__(self, level: str = 'INFO'):
        self.level = self.LEVELS.get(level, 1)
    
    def _log(self, level: str, msg: str):
        if self.LEVELS.get(level, 99) >= self.level:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            print(f"[{timestamp}] [{level}] {msg}")
    
    def debug(self, msg: str):
        self._log('DEBUG', msg)
    
    def info(self, msg: str):
        self._log('INFO', msg)
    
    def warning(self, msg: str):
        self._log('WARNING', msg)
    
    def error(self, msg: str):
        self._log('ERROR', msg)


logger = Logger(CONFIG['log_level'])

# ============================================================
# HTTP 请求工具（QMT 内置 urllib）
# ============================================================
try:
    import urllib.request as urllib2
    import urllib.parse as urlparse
except ImportError:
    import urllib2
    import urlparse


def http_post(url: str, data: Dict, timeout: int = 10) -> Dict:
    """
    发送 POST 请求
    
    Args:
        url: 请求地址
        data: 请求数据
        timeout: 超时时间
        
    Returns:
        响应数据
    """
    headers = {
        'Content-Type': 'application/json',
    }
    
    request = urllib2.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    
    try:
        response = urllib2.urlopen(request, timeout=timeout)
        result = json.loads(response.read().decode('utf-8'))
        return {'success': True, 'data': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============================================================
# QMT 数据获取封装
# ============================================================
class QMTDataFetcher:
    """QMT 数据获取器"""
    
    def __init__(self, context_info):
        """
        初始化
        
        Args:
            context_info: QMT 的 ContextInfo 对象
        """
        self.ctx = context_info
    
    def get_realtime_quote(self, code: str) -> Optional[Dict]:
        """
        获取实时行情
        
        Args:
            code: 股票代码，如 '000001.SZ'
            
        Returns:
            行情数据字典
        """
        try:
            # 使用 QMT API 获取行情数据
            # 注意：实际 API 可能需要根据你的 QMT 版本调整
            
            # 获取最新价格
            price = self.ctx.get_last_price(code)
            
            # 获取涨跌幅（需要计算或从其他 API 获取）
            # 这里使用历史数据计算
            history = self.ctx.get_history_data(2, '1d', 
                                                field_list=['close'], 
                                                stock_code=code)
            
            if len(history) >= 2:
                prev_close = history['close'][0]
                change_pct = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
            else:
                change_pct = 0
            
            # 获取买卖盘（需要确认 QMT 是否有此 API）
            # 这里使用简化版本
            return {
                'code': code.split('.')[0],
                'name': self.ctx.get_stock_name(code),
                'price': price,
                'change_pct': round(change_pct, 3),
                'volume': self.ctx.get_last_volume(code),
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"获取 {code} 行情失败: {e}")
            return None
    
    def get_option_data(self, underlying: str) -> List[Dict]:
        """
        获取期权数据
        
        Args:
            underlying: 标的代码，如 '510050.SH'
            
        Returns:
            期权数据列表
        """
        options = []
        
        try:
            # 获取期权合约列表
            # 注意：需要确认你的 QMT 版本是否支持这些 API
            
            # 假设 QMT 有获取期权链的 API
            option_codes = self._get_option_codes(underlying)
            
            for opt_code in option_codes:
                try:
                    # 获取期权价格
                    price = self.ctx.get_last_price(opt_code)
                    
                    # 获取期权 Greeks（需要确认 API）
                    greeks = self._get_option_greeks(opt_code)
                    
                    # 解析期权代码获取信息
                    # 期权代码格式示例：10002544.SH (50ETF购3月2500)
                    opt_info = self._parse_option_code(opt_code)
                    
                    options.append({
                        'code': opt_code.split('.')[0],
                        'underlying': underlying.split('.')[0],
                        'option_type': opt_info.get('type', 'call'),
                        'strike': opt_info.get('strike', 0),
                        'expiry_date': opt_info.get('expiry', ''),
                        'price': price,
                        'iv': greeks.get('iv', 0),
                        'delta': greeks.get('delta', 0),
                        'gamma': greeks.get('gamma', 0),
                        'theta': greeks.get('theta', 0),
                        'vega': greeks.get('vega', 0),
                        'rho': greeks.get('rho', 0),
                        'volume': self.ctx.get_last_volume(opt_code),
                        'timestamp': datetime.now().isoformat(),
                    })
                except Exception as e:
                    logger.debug(f"获取期权 {opt_code} 数据失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"获取期权数据失败 {underlying}: {e}")
        
        return options
    
    def _get_option_codes(self, underlying: str) -> List[str]:
        """
        获取期权合约代码列表
        
        注意：这需要确认你的 QMT 是否支持此 API
        如果不支持，可能需要从其他方式获取
        """
        # 示例：假设 QMT 有获取期权链的 API
        # 实际使用时需要根据你的 QMT 版本调整
        
        # 如果 QMT 没有此 API，可以：
        # 1. 使用 akshare 获取期权列表
        # 2. 使用本地配置文件
        # 3. 使用固定的期权代码列表
        
        # 这里返回示例代码
        return []
    
    def _get_option_greeks(self, option_code: str) -> Dict:
        """
        获取期权 Greeks
        
        注意：这需要确认你的 QMT 是否支持此 API
        """
        # 示例结构
        return {
            'iv': 0.2,
            'delta': 0.5,
            'gamma': 0.01,
            'theta': -0.01,
            'vega': 0.1,
            'rho': 0.01,
        }
    
    def _parse_option_code(self, code: str) -> Dict:
        """解析期权代码获取信息"""
        # 上交所期权代码格式：10002544.SH
        # 需要根据实际情况解析
        return {
            'type': 'call',
            'strike': 2.5,
            'expiry': '2024-03'
        }
    
    def get_positions(self) -> List[Dict]:
        """
        获取持仓数据
        
        Returns:
            持仓数据列表
        """
        positions = []
        
        try:
            # 使用 QMT 交易 API 获取持仓
            # 注意：这需要在交易时间且有持仓
            
            # 获取交易明细数据
            trade_data = get_trade_detail_data('position')
            
            for pos in trade_data:
                positions.append({
                    'account': pos.account_id,
                    'code': pos.stock_code.split('.')[0],
                    'name': pos.stock_name,
                    'position_type': 'option' if self._is_option_code(pos.stock_code) else 'stock',
                    'quantity': pos.hold_amount,
                    'available': pos.enable_amount,
                    'avg_cost': pos.avg_price,
                    'market_value': pos.market_value,
                    'pnl': pos.floating_pnl,
                    'timestamp': datetime.now().isoformat(),
                })
        except Exception as e:
            logger.error(f"获取持仓数据失败: {e}")
        
        return positions
    
    def _is_option_code(self, code: str) -> bool:
        """判断是否为期权代码"""
        # 上交所期权代码以 1 开头
        # 深交所期权代码以 9 开头
        prefix = code.split('.')[0]
        return prefix.startswith(('1', '9'))


# ============================================================
# 数据推送器
# ============================================================
class DataPusher:
    """数据推送器"""
    
    def __init__(self, base_url: str):
        """
        初始化
        
        Args:
            base_url: 数据接收服务地址
        """
        self.base_url = base_url.rstrip('/')
        self.last_quote_time = 0
        self.last_option_time = 0
        self.last_position_time = 0
    
    def push_quotes(self, quotes: List[Dict], max_retries: int = 3) -> bool:
        """推送行情数据"""
        if not quotes:
            return True
        
        url = f"{self.base_url}/api/v1/prices"
        
        for attempt in range(max_retries):
            result = http_post(url, {'quotes': quotes})
            if result['success']:
                logger.debug(f"推送 {len(quotes)} 条行情数据成功")
                return True
            else:
                logger.warning(f"推送行情失败 (尝试 {attempt+1}/{max_retries}): {result.get('error')}")
                time.sleep(1)
        
        logger.error("推送行情数据最终失败")
        return False
    
    def push_options(self, options: List[Dict], max_retries: int = 3) -> bool:
        """推送期权数据"""
        if not options:
            return True
        
        url = f"{self.base_url}/api/v1/options"
        
        for attempt in range(max_retries):
            result = http_post(url, {'options': options})
            if result['success']:
                logger.debug(f"推送 {len(options)} 条期权数据成功")
                return True
            else:
                logger.warning(f"推送期权失败 (尝试 {attempt+1}/{max_retries}): {result.get('error')}")
                time.sleep(1)
        
        logger.error("推送期权数据最终失败")
        return False
    
    def push_positions(self, positions: List[Dict], max_retries: int = 3) -> bool:
        """推送持仓数据"""
        if not positions:
            return True
        
        url = f"{self.base_url}/api/v1/positions"
        
        for attempt in range(max_retries):
            result = http_post(url, {'positions': positions})
            if result['success']:
                logger.debug(f"推送 {len(positions)} 条持仓数据成功")
                return True
            else:
                logger.warning(f"推送持仓失败 (尝试 {attempt+1}/{max_retries}): {result.get('error')}")
                time.sleep(1)
        
        logger.error("推送持仓数据最终失败")
        return False
    
    def should_push_quote(self) -> bool:
        """检查是否应该推送行情"""
        now = time.time()
        if now - self.last_quote_time >= CONFIG['quote_interval']:
            self.last_quote_time = now
            return True
        return False
    
    def should_push_option(self) -> bool:
        """检查是否应该推送期权数据"""
        now = time.time()
        if now - self.last_option_time >= CONFIG['option_interval']:
            self.last_option_time = now
            return True
        return False
    
    def should_push_position(self) -> bool:
        """检查是否应该推送持仓"""
        now = time.time()
        if now - self.last_position_time >= CONFIG['position_interval']:
            self.last_position_time = now
            return True
        return False


# ============================================================
# QMT 策略主函数
# ============================================================

# 全局变量
pusher = None
fetcher = None


def init(ContextInfo):
    """
    QMT 策略初始化函数
    
    在策略加载时调用一次
    """
    global pusher, fetcher
    
    logger.info("=" * 60)
    logger.info("QMT 数据推送策略初始化")
    logger.info("=" * 60)
    
    # 初始化数据获取器
    fetcher = QMTDataFetcher(ContextInfo)
    
    # 初始化推送器
    pusher = DataPusher(CONFIG['push_url'])
    
    # 设置股票池
    all_codes = CONFIG['stock_codes'] + CONFIG['option_underlyings'] + CONFIG['index_codes']
    ContextInfo.set_universe(all_codes)
    
    logger.info(f"监控股票: {len(CONFIG['stock_codes'])} 只")
    logger.info(f"监控期权标的: {len(CONFIG['option_underlyings'])} 只")
    logger.info(f"监控指数: {len(CONFIG['index_codes'])} 个")
    logger.info(f"推送地址: {CONFIG['push_url']}")
    logger.info("=" * 60)


def handlebar(ContextInfo):
    """
    QMT 策略主函数
    
    每根 K 线调用一次（或每个 tick，取决于设置）
    """
    global pusher, fetcher
    
    if pusher is None or fetcher is None:
        logger.error("初始化失败，跳过")
        return
    
    try:
        # 1. 推送行情数据
        if pusher.should_push_quote():
            quotes = []
            
            # 获取股票行情
            for code in CONFIG['stock_codes']:
                quote = fetcher.get_realtime_quote(code)
                if quote:
                    quotes.append(quote)
            
            # 获取指数行情
            for code in CONFIG['index_codes']:
                quote = fetcher.get_realtime_quote(code)
                if quote:
                    quotes.append(quote)
            
            if quotes:
                success = pusher.push_quotes(quotes)
                if success:
                    logger.info(f"推送行情: {len(quotes)} 条")
        
        # 2. 推送期权数据
        if pusher.should_push_option():
            all_options = []
            
            for underlying in CONFIG['option_underlyings']:
                options = fetcher.get_option_data(underlying)
                all_options.extend(options)
            
            if all_options:
                success = pusher.push_options(all_options)
                if success:
                    logger.info(f"推送期权: {len(all_options)} 条")
        
        # 3. 推送持仓数据
        if pusher.should_push_position():
            positions = fetcher.get_positions()
            
            if positions:
                success = pusher.push_positions(positions)
                if success:
                    logger.info(f"推送持仓: {len(positions)} 条")
    
    except Exception as e:
        logger.error(f"handlebar 执行异常: {e}")
        logger.error(traceback.format_exc())


# ============================================================
# 如果需要在策略外测试，可以运行此部分
# ============================================================
if __name__ == '__main__':
    print("此脚本应在 QMT 客户端内运行")
    print("配置信息:")
    print(json.dumps(CONFIG, indent=2))
