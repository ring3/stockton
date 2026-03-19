#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT 策略配置文件示例

根据你的实际环境和需求修改此配置
"""

# ============================================================
# HTTP 推送模式配置
# ============================================================

HTTP_CONFIG = {
    # 数据接收服务地址
    # 如果是本机运行: 'http://127.0.0.1:8888'
    # 如果是局域网: 'http://192.168.1.100:8888'
    # 如果是公网: 'http://your-server.com:8888'
    'push_url': 'http://127.0.0.1:8888',
    
    # 推送间隔（秒）
    'quote_interval': 5,      # 行情推送间隔（建议 3-10 秒）
    'option_interval': 30,    # 期权推送间隔（建议 30-60 秒）
    'position_interval': 60,  # 持仓推送间隔（建议 60-300 秒）
    
    # 监控的股票列表（添加你关注的股票）
    'stock_codes': [
        # 银行股
        '000001.SZ',   # 平安银行
        '600036.SH',   # 招商银行
        
        # 消费股
        '600519.SH',   # 贵州茅台
        '000858.SZ',   # 五粮液
        '000333.SZ',   # 美的集团
        
        # 科技股
        '002415.SZ',   # 海康威视
        '000725.SZ',   # 京东方A
        
        # 医药股
        '600276.SH',   # 恒瑞医药
        '000538.SZ',   # 云南白药
        
        # 新能源
        '300750.SZ',   # 宁德时代
        '002594.SZ',   # 比亚迪
        
        # 金融股
        '600030.SH',   # 中信证券
        '601318.SH',   # 中国平安
    ],
    
    # 监控的期权标的（ETF）
    'option_underlyings': [
        '510050.SH',   # 50ETF
        '510300.SH',   # 300ETF
        '159915.SZ',   # 创业板ETF
        '588000.SH',   # 科创50ETF
    ],
    
    # 监控的指数
    'index_codes': [
        '000001.SH',   # 上证指数
        '399001.SZ',   # 深证成指
        '000300.SH',   # 沪深300
        '000905.SH',   # 中证500
        '000852.SH',   # 中证1000
        '399006.SZ',   # 创业板指
        '000016.SH',   # 上证50
    ],
    
    # 日志级别: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    'log_level': 'INFO',
    
    # 重试配置
    'max_retries': 3,
    'retry_delay': 1,
}


# ============================================================
# 本地文件模式配置
# ============================================================

FILE_CONFIG = {
    # 输出目录
    # Windows: 'D:/qmt_data' 或 'C:/Users/xxx/qmt_data'
    # Linux/Mac: '/home/xxx/qmt_data' 或 '/shared/qmt_data'
    'output_dir': 'D:/qmt_data',
    
    # 刷新间隔（秒）
    'quote_interval': 5,
    'option_interval': 30,
    
    # 监控的股票（可以只配置关注的几只）
    'stock_codes': [
        '000001.SZ',
        '600519.SH',
        '000333.SZ',
    ],
    
    # 监控的期权标的
    'option_underlyings': [
        '510050.SH',
        '510300.SH',
    ],
    
    'log_level': 'INFO',
}


# ============================================================
# 高级配置（根据需求调整）
# ============================================================

ADVANCED_CONFIG = {
    # 是否推送买卖盘数据（需要确认你的 QMT 支持）
    'push_order_book': False,
    
    # 买卖盘档位数（1-5档）
    'order_book_levels': 1,
    
    # 是否推送分笔数据（tick级别，数据量大）
    'push_tick_data': False,
    
    # 分笔数据推送间隔（秒，0表示每个tick都推）
    'tick_interval': 0,
    
    # 数据压缩（减少网络传输）
    'compress_data': False,
    
    # 批量推送阈值（累积多少条数据后推送）
    'batch_threshold': 10,
    
    # 批量推送超时（秒，超过此时间强制推送）
    'batch_timeout': 3,
}


# ============================================================
# 使用说明
# ============================================================
"""
1. 复制此配置文件
2. 重命名为 qmt_config.py
3. 根据你的需求修改配置
4. 在 QMT 策略中导入: from qmt_config import HTTP_CONFIG as CONFIG
"""

if __name__ == '__main__':
    import json
    print("HTTP 模式配置:")
    print(json.dumps(HTTP_CONFIG, indent=2, ensure_ascii=False))
    print("\n文件模式配置:")
    print(json.dumps(FILE_CONFIG, indent=2, ensure_ascii=False))
