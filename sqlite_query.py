#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================
Stockton SQLite 查询工具
=========================================

一个通用的 SQLite 数据库查询工具，支持多数据库管理和常用查询快捷方式。

使用方法:
    # 交互式模式（推荐）
    python sqlite_query.py
    
    # 直接执行 SQL
    python sqlite_query.py -d skills/stockton/data/stock_data.db -q "SELECT * FROM stock_daily LIMIT 5"
    
    # 显示数据库统计
    python sqlite_query.py --stats
    
    # 导出查询结果为 CSV
    python sqlite_query.py -q "SELECT * FROM stock_daily WHERE code='600519'" -o output.csv

作者: Stockton AI
版本: 1.0.0
"""

import os
import sys
import json
import sqlite3
import argparse
import csv
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

# 默认数据库路径（按优先级排序）
DEFAULT_DB_PATHS = [
    r".\data\stock_data.db",          # 项目级数据目录（优先）
    r"data\stock_data.db",            # 兼容写法
    r"skills\stockton\data\stock_data.db",  # Skill 目录
    r".\data\stock_analysis.db",      # 分析数据库
]


@dataclass
class QueryResult:
    """查询结果封装"""
    columns: List[str]
    rows: List[Tuple]
    row_count: int
    execution_time: float
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [dict(zip(self.columns, row)) for row in self.rows]
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict_list(), ensure_ascii=False, indent=indent, default=str)
    
    def to_csv(self, filepath: str):
        """导出为 CSV"""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            writer.writerows(self.rows)
    
    def print_table(self, max_rows: int = 20):
        """打印表格格式"""
        if not self.rows:
            print("(无数据)")
            return
        
        # 限制显示行数
        display_rows = self.rows[:max_rows]
        if len(self.rows) > max_rows:
            show_count = len(display_rows)
            total_count = len(self.rows)
        else:
            show_count = total_count = len(self.rows)
        
        # 计算每列宽度
        col_widths = []
        for i, col in enumerate(self.columns):
            max_data_len = max([len(str(row[i])) for row in display_rows], default=0)
            col_widths.append(max(len(col), max_data_len, 8) + 2)
        
        # 分隔线
        separator = "+" + "+".join(["-" * w for w in col_widths]) + "+"
        
        # 打印表头
        print(separator)
        header = "|" + "|".join([f" {col:^{w-2}} " for col, w in zip(self.columns, col_widths)]) + "|"
        print(header)
        print(separator)
        
        # 打印数据
        for row in display_rows:
            row_str = "|" + "|".join([f" {str(val):^{w-2}} " for val, w in zip(row, col_widths)]) + "|"
            print(row_str)
        
        print(separator)
        print(f"共 {self.row_count} 行，显示 {show_count} 行，执行时间 {self.execution_time:.3f}s")
        
        if total_count > show_count:
            print(f"(还有 {total_count - show_count} 行未显示，使用 -o 导出查看全部)")


class SQLiteQueryTool:
    """SQLite 查询工具主类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化查询工具
        
        Args:
            db_path: 数据库路径，None 则自动查找
        """
        self.conn: Optional[sqlite3.Connection] = None
        self.db_path: Optional[str] = None
        self._db_paths: List[str] = []
        
        if db_path:
            self.connect(db_path)
        else:
            self._find_databases()
    
    def _find_databases(self):
        """自动查找项目中的数据库文件"""
        self._db_paths = []
        for path in DEFAULT_DB_PATHS:
            if os.path.exists(path):
                self._db_paths.append(os.path.abspath(path))
        
        # 递归查找其他 .db 文件
        for root, dirs, files in os.walk("."):
            # 跳过一些目录
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.venv']]
            for file in files:
                if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                    full_path = os.path.abspath(os.path.join(root, file))
                    if full_path not in self._db_paths:
                        self._db_paths.append(full_path)
    
    def list_databases(self) -> List[str]:
        """列出所有找到的数据库"""
        return self._db_paths
    
    def connect(self, db_path: str) -> bool:
        """
        连接到指定数据库
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            是否连接成功
        """
        try:
            if not os.path.exists(db_path):
                print(f"错误: 数据库文件不存在: {db_path}")
                return False
            
            self.conn = sqlite3.connect(db_path)
            self.db_path = db_path
            print(f"[OK] 已连接到数据库: {db_path}")
            return True
            
        except sqlite3.Error as e:
            print(f"连接数据库失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.db_path = None
    
    def get_tables(self) -> List[Dict[str, Any]]:
        """获取数据库中的所有表"""
        if not self.conn:
            print("错误: 未连接到数据库")
            return []
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        result = []
        for (table_name,) in tables:
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
            count = cursor.fetchone()[0]
            result.append({
                'name': table_name,
                'row_count': count
            })
        
        return result
    
    def get_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表的 schema 信息
        
        Args:
            table_name: 表名
            
        Returns:
            列信息列表
        """
        if not self.conn:
            print("错误: 未连接到数据库")
            return []
        
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
        columns = cursor.fetchall()
        
        return [{
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default_value': col[4],
            'pk': col[5]
        } for col in columns]
    
    def execute(self, sql: str, params: Tuple = ()) -> Optional[QueryResult]:
        """
        执行 SQL 查询
        
        Args:
            sql: SQL 语句
            params: 查询参数
            
        Returns:
            QueryResult 对象
        """
        if not self.conn:
            print("错误: 未连接到数据库")
            return None
        
        import time
        start_time = time.time()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            
            # 获取列名
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            else:
                columns = []
                rows = []
            
            # 提交非查询语句
            if not cursor.description:
                self.conn.commit()
                affected = cursor.rowcount
                print(f"[OK] 执行成功，影响 {affected} 行")
                return None
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time=execution_time
            )
            
        except sqlite3.Error as e:
            print(f"SQL 执行失败: {e}")
            print(f"  执行的 SQL: {sql[:100]}{'...' if len(sql) > 100 else ''}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        if not self.conn:
            print("错误: 未连接到数据库")
            return {}
        
        stats = {
            'database': self.db_path,
            'file_size': os.path.getsize(self.db_path),
            'tables': []
        }
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # 记录数
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
            row_count = cursor.fetchone()[0]
            
            # 列信息
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            columns = cursor.fetchall()
            
            # 日期范围（如果有 date 列）
            date_range = None
            date_cols = [c[1] for c in columns if 'date' in c[1].lower()]
            if date_cols and row_count > 0:
                try:
                    date_col = date_cols[0]
                    cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM \"{table_name}\"")
                    min_date, max_date = cursor.fetchone()
                    date_range = {'min': min_date, 'max': max_date}
                except:
                    pass
            
            stats['tables'].append({
                'name': table_name,
                'row_count': row_count,
                'column_count': len(columns),
                'date_range': date_range
            })
        
        return stats
    
    # ============ 快捷查询方法 ============
    
    def quick_stock_data(self, code: str, days: int = 10, table_name: str = 'stock_daily') -> Optional[QueryResult]:
        """快速查询股票数据"""
        # 获取表的实际列名，避免查询不存在的列
        schema = self.get_schema(table_name)
        if not schema:
            print(f"错误: 表 {table_name} 不存在")
            return None
        
        col_names = [col['name'] for col in schema]
        
        # 构建查询列（只查询存在的列）
        desired_cols = ['code', 'name', 'date', 'open', 'high', 'low', 'close', 
                       'volume', 'amount', 'pct_chg', 'change_pct', 'turnover_rate']
        select_cols = [c for c in desired_cols if c in col_names]
        
        if not select_cols:
            select_cols = ['*']
        
        sql = f"""
            SELECT {', '.join(select_cols)}
            FROM {table_name}
            WHERE code = ? 
            ORDER BY date DESC 
            LIMIT ?
        """
        return self.execute(sql, (code, days))
    
    def quick_stock_list(self, table_name: str = 'stock_daily') -> Optional[QueryResult]:
        """快速查询股票列表"""
        # 获取表的实际列名
        schema = self.get_schema(table_name)
        if not schema:
            print(f"错误: 表 {table_name} 不存在")
            return None
        
        col_names = [col['name'] for col in schema]
        has_name = 'name' in col_names
        
        if has_name:
            sql = f"""
                SELECT DISTINCT code, name,
                    COUNT(*) as data_days,
                    MIN(date) as start_date,
                    MAX(date) as end_date
                FROM {table_name}
                GROUP BY code, name
                ORDER BY data_days DESC
            """
        else:
            sql = f"""
                SELECT DISTINCT code,
                    COUNT(*) as data_days,
                    MIN(date) as start_date,
                    MAX(date) as end_date
                FROM {table_name}
                GROUP BY code
                ORDER BY data_days DESC
            """
        return self.execute(sql)
    
    def quick_latest_date(self) -> Optional[QueryResult]:
        """查询最新数据日期"""
        sql = """
            SELECT MAX(date) as latest_date, COUNT(*) as total_records
            FROM stock_daily
        """
        return self.execute(sql)
    
    def quick_index_components(self, index_code: str) -> Optional[QueryResult]:
        """查询指数成分股"""
        sql = """
            SELECT stock_code, stock_name, weight
            FROM index_components
            WHERE index_code = ?
            ORDER BY weight DESC
        """
        return self.execute(sql, (index_code,))


def interactive_mode(tool: SQLiteQueryTool):
    """交互式查询模式"""
    print("\n" + "=" * 50)
    print("  Stockton SQLite 交互式查询工具")
    print("=" * 50)
    print("\n可用命令:")
    print("  .tables     - 列出所有表")
    print("  .schema <表> - 查看表结构")
    print("  .stats      - 数据库统计信息")
    print("  .db         - 列出所有数据库")
    print("  .use <路径>  - 切换数据库")
    print("  .stock <代码> [表名] - 快速查询股票数据")
    print("  .list [表名] - 列出所有股票")
    print("  .latest     - 查看最新数据日期")
    print("  .query <SQL> - 直接执行 SQL 语句")
    print("  .select <列> from <表> ... - 快捷 SELECT 查询")
    print("  .help       - 显示帮助")
    print("  .quit       - 退出")
    print("-" * 50)
    
    while True:
        try:
            command = input("\nsqlite> ").strip()
            
            if not command:
                continue
            
            if command == '.quit' or command == '.exit':
                break
            
            elif command == '.help':
                print("\n可用命令:")
                print("  .tables     - 列出所有表")
                print("  .schema <表> - 查看表结构")
                print("  .stats      - 数据库统计信息")
                print("  .db         - 列出所有数据库")
                print("  .use <路径>  - 切换数据库")
                print("  .stock <代码> [表名] - 快速查询股票数据 (如: .stock 600519)")
                print("  .list [表名] - 列出所有股票")
                print("  .latest     - 查看最新数据日期")
                print("  .query <SQL> - 直接执行 SQL 语句")
                print("  .select <列> from <表> ... - 快捷 SELECT 查询")
                print("  .help       - 显示帮助")
                print("  .quit       - 退出")
                print("\n或直接输入 SQL 语句:")
                print("  SELECT * FROM stock_daily LIMIT 5")
            
            elif command == '.tables':
                tables = tool.get_tables()
                if tables:
                    print("\n表列表:")
                    for t in tables:
                        print(f"  {t['name']:<30} ({t['row_count']} 行)")
                else:
                    print("(无表)")
            
            elif command.startswith('.schema '):
                table_name = command[8:].strip()
                schema = tool.get_schema(table_name)
                if schema:
                    print(f"\n表 {table_name} 的结构:")
                    print(f"{'列名':<20} {'类型':<15} {'非空':<6} {'主键':<6}")
                    print("-" * 50)
                    for col in schema:
                        notnull = "YES" if col['notnull'] else "NO"
                        pk = "YES" if col['pk'] else "NO"
                        print(f"{col['name']:<20} {col['type']:<15} {notnull:<6} {pk:<6}")
            
            elif command == '.stats':
                stats = tool.get_stats()
                if stats:
                    print(f"\n数据库: {stats['database']}")
                    print(f"文件大小: {stats['file_size'] / 1024 / 1024:.2f} MB")
                    print("\n表统计:")
                    for t in stats['tables']:
                        print(f"  {t['name']:<30} {t['row_count']:>10} 行  {t['column_count']:>3} 列", end="")
                        if t.get('date_range'):
                            print(f"  [{t['date_range']['min']} ~ {t['date_range']['max']}]")
                        else:
                            print()
            
            elif command == '.db':
                dbs = tool.list_databases()
                if dbs:
                    print("\n发现的数据库文件:")
                    for i, db in enumerate(dbs, 1):
                        size_mb = os.path.getsize(db) / 1024 / 1024
                        current = " (当前)" if db == tool.db_path else ""
                        print(f"  {i}. {db} ({size_mb:.2f} MB){current}")
                else:
                    print("未发现数据库文件")
            
            elif command.startswith('.use '):
                db_path = command[5:].strip()
                # 支持序号选择
                if db_path.isdigit():
                    dbs = tool.list_databases()
                    idx = int(db_path) - 1
                    if 0 <= idx < len(dbs):
                        db_path = dbs[idx]
                    else:
                        print(f"错误: 无效的数据库序号")
                        continue
                tool.close()
                tool.connect(db_path)
            
            elif command.startswith('.stock'):
                parts = command.split(maxsplit=2)
                code = parts[1] if len(parts) > 1 else ''
                table_name = parts[2] if len(parts) > 2 else 'stock_daily'
                if code:
                    result = tool.quick_stock_data(code, table_name=table_name)
                    if result:
                        result.print_table()
                else:
                    print("用法: .stock <股票代码> [表名]")
                    print("示例: .stock 600519")
                    print("      .stock 600519 stock_daily")
            
            elif command.startswith('.list'):
                parts = command.split(maxsplit=1)
                table_name = parts[1] if len(parts) > 1 else 'stock_daily'
                result = tool.quick_stock_list(table_name=table_name)
                if result:
                    result.print_table(max_rows=30)
            
            elif command == '.latest':
                result = tool.quick_latest_date()
                if result:
                    result.print_table()
            
            elif command.startswith('.query '):
                sql = command[7:].strip()
                if sql:
                    result = tool.execute(sql)
                    if result:
                        result.print_table()
                else:
                    print("用法: .query <SQL语句>")
                    print("示例: .query SELECT * FROM stock_daily LIMIT 5")
            
            elif command.startswith('.select'):
                sql_part = command[7:].strip()
                if sql_part:
                    # 自动添加 SELECT 前缀
                    sql = f"SELECT {sql_part}"
                    result = tool.execute(sql)
                    if result:
                        result.print_table()
                else:
                    print("用法: .select <列名> from <表名> [where ...] [order by ...] [limit ...]")
                    print("示例: .select code, date, close from stock_a_data limit 10")
                    print("      .select * from stock_a_data where code='000001' order by date desc limit 5")
            
            else:
                # 执行 SQL（直接输入）
                result = tool.execute(command)
                if result:
                    result.print_table()
                
        except KeyboardInterrupt:
            print("\n使用 .quit 退出")
        except Exception as e:
            print(f"错误: {e}")
    
    print("\n再见!")


def main():
    parser = argparse.ArgumentParser(
        description='Stockton SQLite 查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 交互式模式
  %(prog)s --stats                   # 显示数据库统计
  %(prog)s -q "SELECT * FROM stock_daily LIMIT 5"
  %(prog)s -d data/stock_data.db -q "SELECT code, name FROM stock_daily"
  %(prog)s --stock 600519            # 查询茅台数据
  %(prog)s --stock 000001 --table stock_a_data  # 指定表名查询
  %(prog)s --list --table stock_a_data           # 列出指定表的股票
  %(prog)s -q "SELECT * FROM stock_daily" -o result.csv
        """
    )
    
    parser.add_argument('-d', '--database', 
                        help='指定数据库路径')
    parser.add_argument('-q', '--query', 
                        help='执行 SQL 查询')
    parser.add_argument('-o', '--output',
                        help='导出结果到文件 (支持 .csv 和 .json)')
    parser.add_argument('--stats', action='store_true',
                        help='显示数据库统计信息')
    parser.add_argument('--tables', action='store_true',
                        help='列出所有表')
    parser.add_argument('--schema',
                        help='显示指定表的 schema')
    parser.add_argument('--stock',
                        help='快速查询股票数据 (如: --stock 600519)')
    parser.add_argument('--table', default='stock_daily',
                        help='指定表名 (默认: stock_daily)')
    parser.add_argument('--list', action='store_true',
                        help='列出所有股票')
    parser.add_argument('--latest', action='store_true',
                        help='查看最新数据日期')
    
    args = parser.parse_args()
    
    # 创建工具实例
    tool = SQLiteQueryTool(args.database)
    
    # 如果没有指定数据库，使用找到的第一个
    if not args.database and not tool.db_path:
        dbs = tool.list_databases()
        if dbs:
            print(f"自动选择数据库: {dbs[0]}")
            tool.connect(dbs[0])
        else:
            print("错误: 未找到数据库文件")
            print(f"默认搜索路径: {DEFAULT_DB_PATHS}")
            sys.exit(1)
    
    # 处理命令
    if args.stats:
        stats = tool.get_stats()
        if stats:
            print(f"\n数据库: {stats['database']}")
            print(f"文件大小: {stats['file_size'] / 1024 / 1024:.2f} MB")
            print("\n表统计:")
            for t in stats['tables']:
                print(f"  {t['name']:<30} {t['row_count']:>10} 行  {t['column_count']:>3} 列", end="")
                if t.get('date_range'):
                    print(f"  [{t['date_range']['min']} ~ {t['date_range']['max']}]")
                else:
                    print()
    
    elif args.tables:
        tables = tool.get_tables()
        if tables:
            print("\n表列表:")
            for t in tables:
                print(f"  {t['name']:<30} ({t['row_count']} 行)")
    
    elif args.schema:
        schema = tool.get_schema(args.schema)
        if schema:
            print(f"\n表 {args.schema} 的结构:")
            print(f"{'列名':<20} {'类型':<15} {'非空':<6} {'主键':<6}")
            print("-" * 50)
            for col in schema:
                notnull = "YES" if col['notnull'] else "NO"
                pk = "YES" if col['pk'] else "NO"
                print(f"{col['name']:<20} {col['type']:<15} {notnull:<6} {pk:<6}")
    
    elif args.stock:
        result = tool.quick_stock_data(args.stock, table_name=args.table)
        if result:
            if args.output:
                if args.output.endswith('.csv'):
                    result.to_csv(args.output)
                    print(f"结果已导出到: {args.output}")
                elif args.output.endswith('.json'):
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(result.to_json())
                    print(f"结果已导出到: {args.output}")
            else:
                result.print_table()
    
    elif args.list:
        result = tool.quick_stock_list(table_name=args.table)
        if result:
            if args.output:
                if args.output.endswith('.csv'):
                    result.to_csv(args.output)
                    print(f"结果已导出到: {args.output}")
                else:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(result.to_json())
                    print(f"结果已导出到: {args.output}")
            else:
                result.print_table(max_rows=30)
    
    elif args.latest:
        result = tool.quick_latest_date()
        if result:
            result.print_table()
    
    elif args.query:
        result = tool.execute(args.query)
        if result:
            if args.output:
                if args.output.endswith('.csv'):
                    result.to_csv(args.output)
                    print(f"结果已导出到: {args.output}")
                elif args.output.endswith('.json'):
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(result.to_json())
                    print(f"结果已导出到: {args.output}")
                else:
                    print("不支持的导出格式，请使用 .csv 或 .json")
            else:
                result.print_table()
    
    else:
        # 进入交互模式
        interactive_mode(tool)
    
    tool.close()


if __name__ == '__main__':
    main()
