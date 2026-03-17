#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stockton Cloud - OpenClaw 定时任务入口

OpenClaw 定时任务配置示例:
```yaml
schedule:
  - name: stockton-daily-fetch
    cron: "0 19 * * 1-5"  # 工作日19:00
    script: "workers/python-fetcher/cron.py"
    environment:
      WORKERS_URL: "https://your-worker.workers.dev"
      API_KEY: "your-secret-api-key"
      INDICES: "000300,000905"
      HISTORY_DAYS: "60"
```

或系统级 Cron:
```bash
0 19 * * 1-5 cd /path/to/stockton && openclaw run workers/python-fetcher/cron.py
```

或 Windows 任务计划程序:
schtasks /create /tn "StocktonFetch" /tr "openclaw run workers/python-fetcher/cron.py" /sc weekly /d MON,TUE,WED,THU,FRI /st 19:00
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.fetcher import StockDataFetcher
from src.sync import WorkersSync
from src.cron_job import fetch_and_sync


def main():
    """OpenClaw 定时任务入口"""
    print("=" * 60)
    print("Stockton Cloud - OpenClaw 定时任务启动")
    print("=" * 60)
    
    result = fetch_and_sync()
    
    # 输出结果（OpenClaw 会捕获 stdout）
    if result.get('success'):
        print(f"✓ 成功处理 {result.get('stocks_processed')} 只股票")
        print(f"✓ 共 {result.get('prices_total')} 条价格记录")
        print(f"✓ 耗时: {result.get('duration_seconds', 0):.1f} 秒")
    else:
        print(f"✗ 执行失败: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
