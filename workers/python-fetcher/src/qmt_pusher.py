#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================
QMT 数据接收服务
=========================================

接收来自 QMT 客户端推送的数据，存入本地 SQLite 数据库。

运行方式：
1. 独立服务模式: python qmt_pusher.py --server
2. 作为模块被导入使用

数据接收端点：
- POST /api/v1/prices      - 接收行情数据
- POST /api/v1/options     - 接收期权数据
- POST /api/v1/positions   - 接收持仓数据
- GET  /health             - 健康检查

作者: Stockton
版本: 1.0.0
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QMTDataReceiver:
    """
    QMT 数据接收器
    
    负责接收、验证、存储来自 QMT 客户端的数据
    """
    
    def __init__(self, db_path: str = './data/stock_data.db'):
        """
        初始化数据接收器
        
        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        self._ensure_directory()
        self._init_tables()
        self._lock = threading.Lock()
    
    def _ensure_directory(self):
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # QMT 实时行情数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qmt_realtime_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT,
                price REAL,
                change_pct REAL,
                volume INTEGER,
                amount REAL,
                bid1 REAL,
                ask1 REAL,
                bid_vol1 INTEGER,
                ask_vol1 INTEGER,
                timestamp TEXT NOT NULL,
                update_time TEXT NOT NULL,
                source TEXT DEFAULT 'qmt',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, timestamp)
            )
        ''')
        
        # QMT 期权数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qmt_option_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                underlying TEXT NOT NULL,
                option_type TEXT,  -- 'call' 或 'put'
                strike REAL,
                expiry_date TEXT,
                price REAL,
                iv REAL,  -- 隐含波动率
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                rho REAL,
                volume INTEGER,
                open_interest INTEGER,
                timestamp TEXT NOT NULL,
                source TEXT DEFAULT 'qmt',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, timestamp)
            )
        ''')
        
        # QMT 持仓数据表（用于期权持仓分析）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qmt_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                position_type TEXT,  -- 'stock', 'option', 'future'
                quantity INTEGER,
                available INTEGER,
                avg_cost REAL,
                market_value REAL,
                pnl REAL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account, code, timestamp)
            )
        ''')
        
        # 数据同步日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qmt_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,  -- 'quotes', 'options', 'positions'
                record_count INTEGER,
                timestamp TEXT,
                status TEXT,  -- 'success', 'error'
                message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_qmt_quotes_code_time 
            ON qmt_realtime_quotes(code, timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_qmt_options_code_time 
            ON qmt_option_data(code, timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_qmt_options_underlying 
            ON qmt_option_data(underlying)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("QMT 数据表初始化完成")
    
    def save_realtime_quotes(self, quotes: List[Dict]) -> Dict:
        """
        保存实时行情数据
        
        Args:
            quotes: 行情数据列表
            
        Returns:
            操作结果统计
        """
        if not quotes:
            return {'success': True, 'saved': 0}
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            saved = 0
            errors = 0
            
            try:
                for quote in quotes:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO qmt_realtime_quotes 
                            (code, name, price, change_pct, volume, amount,
                             bid1, ask1, bid_vol1, ask_vol1, timestamp, update_time, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            quote.get('code'),
                            quote.get('name'),
                            quote.get('price'),
                            quote.get('change_pct'),
                            quote.get('volume'),
                            quote.get('amount'),
                            quote.get('bid1'),
                            quote.get('ask1'),
                            quote.get('bid_vol1'),
                            quote.get('ask_vol1'),
                            quote.get('timestamp'),
                            quote.get('update_time', datetime.now().isoformat()),
                            quote.get('source', 'qmt')
                        ))
                        saved += 1
                    except Exception as e:
                        logger.error(f"保存行情数据失败 {quote.get('code')}: {e}")
                        errors += 1
                
                conn.commit()
                
                # 记录同步日志
                self._log_sync('quotes', saved, 'success' if saved > 0 else 'error')
                
                return {
                    'success': errors == 0,
                    'saved': saved,
                    'errors': errors
                }
                
            except Exception as e:
                logger.error(f"批量保存行情数据失败: {e}")
                conn.rollback()
                self._log_sync('quotes', 0, 'error', str(e))
                return {'success': False, 'saved': 0, 'error': str(e)}
            finally:
                conn.close()
    
    def save_option_data(self, options: List[Dict]) -> Dict:
        """
        保存期权数据
        
        Args:
            options: 期权数据列表
            
        Returns:
            操作结果统计
        """
        if not options:
            return {'success': True, 'saved': 0}
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            saved = 0
            errors = 0
            
            try:
                for opt in options:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO qmt_option_data 
                            (code, underlying, option_type, strike, expiry_date,
                             price, iv, delta, gamma, theta, vega, rho,
                             volume, open_interest, timestamp, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            opt.get('code'),
                            opt.get('underlying'),
                            opt.get('option_type'),
                            opt.get('strike'),
                            opt.get('expiry_date'),
                            opt.get('price'),
                            opt.get('iv'),
                            opt.get('delta'),
                            opt.get('gamma'),
                            opt.get('theta'),
                            opt.get('vega'),
                            opt.get('rho'),
                            opt.get('volume'),
                            opt.get('open_interest'),
                            opt.get('timestamp'),
                            opt.get('source', 'qmt')
                        ))
                        saved += 1
                    except Exception as e:
                        logger.error(f"保存期权数据失败 {opt.get('code')}: {e}")
                        errors += 1
                
                conn.commit()
                self._log_sync('options', saved, 'success' if saved > 0 else 'error')
                
                return {
                    'success': errors == 0,
                    'saved': saved,
                    'errors': errors
                }
                
            except Exception as e:
                logger.error(f"批量保存期权数据失败: {e}")
                conn.rollback()
                self._log_sync('options', 0, 'error', str(e))
                return {'success': False, 'saved': 0, 'error': str(e)}
            finally:
                conn.close()
    
    def save_positions(self, positions: List[Dict]) -> Dict:
        """
        保存持仓数据
        
        Args:
            positions: 持仓数据列表
            
        Returns:
            操作结果统计
        """
        if not positions:
            return {'success': True, 'saved': 0}
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            saved = 0
            errors = 0
            
            try:
                for pos in positions:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO qmt_positions 
                            (account, code, name, position_type, quantity, available,
                             avg_cost, market_value, pnl, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            pos.get('account'),
                            pos.get('code'),
                            pos.get('name'),
                            pos.get('position_type'),
                            pos.get('quantity'),
                            pos.get('available'),
                            pos.get('avg_cost'),
                            pos.get('market_value'),
                            pos.get('pnl'),
                            pos.get('timestamp')
                        ))
                        saved += 1
                    except Exception as e:
                        logger.error(f"保存持仓数据失败 {pos.get('code')}: {e}")
                        errors += 1
                
                conn.commit()
                self._log_sync('positions', saved, 'success' if saved > 0 else 'error')
                
                return {
                    'success': errors == 0,
                    'saved': saved,
                    'errors': errors
                }
                
            except Exception as e:
                logger.error(f"批量保存持仓数据失败: {e}")
                conn.rollback()
                self._log_sync('positions', 0, 'error', str(e))
                return {'success': False, 'saved': 0, 'error': str(e)}
            finally:
                conn.close()
    
    def _log_sync(self, data_type: str, count: int, status: str, message: str = ''):
        """记录同步日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO qmt_sync_log (data_type, record_count, timestamp, status, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (data_type, count, datetime.now().isoformat(), status, message))
        
        conn.commit()
        conn.close()
    
    def get_latest_quotes(self, code: str = None, limit: int = 100) -> List[Dict]:
        """获取最新行情数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if code:
            cursor.execute('''
                SELECT * FROM qmt_realtime_quotes 
                WHERE code = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (code, limit))
        else:
            cursor.execute('''
                SELECT * FROM qmt_realtime_quotes 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_option_chain(self, underlying: str, timestamp: str = None) -> List[Dict]:
        """获取期权链数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if timestamp:
            cursor.execute('''
                SELECT * FROM qmt_option_data 
                WHERE underlying = ? AND timestamp = ?
                ORDER BY strike
            ''', (underlying, timestamp))
        else:
            # 获取最新的
            cursor.execute('''
                SELECT * FROM qmt_option_data 
                WHERE underlying = ?
                ORDER BY timestamp DESC, strike
            ''', (underlying,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


class QMTRequestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    receiver = None  # 类变量，由外部设置
    
    def log_message(self, format, *args):
        """重写日志方法"""
        logger.info(f"{self.client_address[0]} - {format % args}")
    
    def _send_json_response(self, data: Dict, status_code: int = 200):
        """发送 JSON 响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/health':
            self._send_json_response({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'service': 'qmt-data-receiver'
            })
        else:
            self._send_json_response({'error': 'Not found'}, 404)
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self._send_json_response({'error': 'Invalid JSON'}, 400)
            return
        
        if path == '/api/v1/prices':
            result = self.receiver.save_realtime_quotes(data.get('quotes', []))
            self._send_json_response(result)
            
        elif path == '/api/v1/options':
            result = self.receiver.save_option_data(data.get('options', []))
            self._send_json_response(result)
            
        elif path == '/api/v1/positions':
            result = self.receiver.save_positions(data.get('positions', []))
            self._send_json_response(result)
            
        else:
            self._send_json_response({'error': 'Not found'}, 404)
    
    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server(host: str = '0.0.0.0', port: int = 8888, db_path: str = './data/stock_data.db'):
    """
    启动 HTTP 服务器
    
    Args:
        host: 监听地址
        port: 监听端口
        db_path: 数据库路径
    """
    receiver = QMTDataReceiver(db_path)
    QMTRequestHandler.receiver = receiver
    
    server = HTTPServer((host, port), QMTRequestHandler)
    
    logger.info(f"=" * 60)
    logger.info("QMT 数据接收服务启动")
    logger.info(f"监听地址: {host}:{port}")
    logger.info(f"数据库: {db_path}")
    logger.info(f"=" * 60)
    logger.info("API 端点:")
    logger.info(f"  GET  /health")
    logger.info(f"  POST /api/v1/prices")
    logger.info(f"  POST /api/v1/options")
    logger.info(f"  POST /api/v1/positions")
    logger.info(f"=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务已停止")
        server.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='QMT 数据接收服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8888, help='监听端口')
    parser.add_argument('--db-path', default='./data/stock_data.db', help='数据库路径')
    
    args = parser.parse_args()
    
    run_server(args.host, args.port, args.db_path)
