# OpenClaw 定时任务集成方案

将 Python Fetcher 改为通过 OpenClaw 定时任务触发，无需部署到 Railway。

## 架构更新

```
┌─────────────────────────────────────────────────────────────────┐
│  OpenClaw 定时任务调度器                                         │
│  ──────────────────────                                         │
│  触发时间: 每天 19:00 (收盘后)                                    │
│  执行方式: Python 脚本                                           │
│  脚本位置: workers/python-fetcher/cron.py                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ 调用执行
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Python Fetcher (本地/OpenClaw 环境运行)                         │
│  ─────────────────────────────────────                          │
│  功能: 从 akshare 拉取数据 → 推送到 Workers                      │
│  配置: .env 文件存储 WORKERS_URL 和 API_KEY                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cloudflare Workers (API 服务)                                   │
│  Cloudflare D1 (SQLite 数据库)                                   │
└─────────────────────────────────────────────────────────────────┘
```

## OpenClaw 定时任务配置

### 方式1: 使用 OpenClaw 的 schedule 功能（如果支持）

在 OpenClaw 配置中添加定时任务：

```json
{
  "name": "stockton-data-fetch",
  "schedule": "0 19 * * 1-5",
  "script": "workers/python-fetcher/cron.py",
  "environment": {
    "WORKERS_URL": "https://your-worker.workers.dev",
    "API_KEY": "your-api-key"
  }
}
```

### 方式2: 通过 OpenClaw 函数调用（推荐）

在 OpenClaw 中定义一个任务函数：

```python
# openclaw_task.py
import os
import sys

# 添加 stockton 路径
sys.path.insert(0, 'workers/python-fetcher')

from cron import fetch_and_sync

def stockton_daily_fetch():
    """
    OpenClaw 定时任务入口
    每天收盘后拉取股票数据
    """
    # 设置环境变量（从 OpenClaw 配置读取）
    os.environ['WORKERS_URL'] = os.getenv('STOCKTON_WORKERS_URL')
    os.environ['API_KEY'] = os.getenv('STOCKTON_API_KEY')
    os.environ['INDICES'] = '000300,000905'
    os.environ['HISTORY_DAYS'] = '60'
    
    # 执行拉取
    result = fetch_and_sync()
    
    return {
        'success': result.get('success'),
        'stocks_processed': result.get('stocks_processed'),
        'prices_total': result.get('prices_total'),
        'duration': result.get('duration_seconds')
    }

# OpenClaw 定时任务注册
# schedule: 0 19 * * 1-5 (工作日19:00)
STOCKTON_FETCH_TASK = {
    'name': 'stockton_daily_fetch',
    'function': stockton_daily_fetch,
    'schedule': '0 19 * * 1-5',
    'timezone': 'Asia/Shanghai'
}
```

### 方式3: 系统级 Cron + OpenClaw CLI（最可靠）

如果 OpenClaw 提供 CLI 工具：

```bash
# Linux/Mac crontab
0 19 * * 1-5 cd /path/to/stockton && openclaw run workers/python-fetcher/cron.py

# Windows 任务计划程序
schtasks /create /tn "StocktonFetch" /tr "openclaw run workers/python-fetcher/cron.py" /sc weekly /d MON,TUE,WED,THU,FRI /st 19:00
```

## 配置步骤

### 1. 配置 Workers（已部署）

确保 Workers 已部署并获得 URL：
```bash
cd workers
npx wrangler deploy
# 记录 URL: https://stockton.xxx.workers.dev
```

### 2. 在 OpenClaw 中配置环境变量

```bash
# OpenClaw 环境变量设置
openclaw env set STOCKTON_WORKERS_URL https://your-worker.workers.dev
openclaw env set STOCKTON_API_KEY your-secret-api-key
```

### 3. 测试手动执行

```bash
# 手动运行一次测试
openclaw run workers/python-fetcher/cron.py --env STOCKTON_WORKERS_URL=https://xxx --env STOCKTON_API_KEY=xxx

# 或进入目录执行
cd workers/python-fetcher
python cron.py
```

### 4. 设置定时任务

根据 OpenClaw 支持的定时任务方式选择：

**如果 OpenClaw 支持 `schedule` 配置：**

```yaml
# openclaw.yaml
skills:
  stockton:
    schedule:
      - name: daily-fetch
        cron: "0 19 * * 1-5"
        script: "workers/python-fetcher/cron.py"
        env:
          WORKERS_URL: "${STOCKTON_WORKERS_URL}"
          API_KEY: "${STOCKTON_API_KEY}"
```

**如果 OpenClaw 支持函数注册：**

```python
# 在 skill 初始化时注册
from workers.python-fetcher.cron import fetch_and_sync

@openclaw.schedule(cron="0 19 * * 1-5")
def stockton_data_fetch():
    return fetch_and_sync()
```

## 数据流向

```
OpenClaw 定时触发
    ↓
执行 cron.py
    ↓
从 akshare 获取沪深300/中证500数据
    ↓
计算技术指标 (MA5/MA10/MA20/MA60)
    ↓
HTTP POST 到 Workers /api/batch_update
    ↓
数据存入 D1 数据库
    ↓
客户端通过 API 查询
```

## 监控和日志

### 查看执行日志

```bash
# 如果 OpenClaw 提供日志查看
openclaw logs stockton-daily-fetch

# 或查看本地日志文件
tail -f workers/python-fetcher/fetcher.log
```

### 健康检查

```bash
# 手动检查 Workers 健康
curl https://your-worker.workers.dev/health

# 检查数据更新状态
curl https://your-worker.workers.dev/api/market/overview
```

## 故障处理

### 如果定时任务失败

1. **检查环境变量**
   ```python
   import os
   print(os.getenv('WORKERS_URL'))
   print(os.getenv('API_KEY'))
   ```

2. **手动重试**
   ```bash
   cd workers/python-fetcher
   python cron.py
   ```

3. **检查 Workers 状态**
   ```bash
   curl https://your-worker.workers.dev/health
   ```

## 优点

| 方面 | 说明 |
|------|------|
| **简化架构** | 无需 Railway/Render 第三方平台 |
| **统一调度** | 所有定时任务由 OpenClaw 管理 |
| **环境复用** | 复用 OpenClaw 的 Python 环境 |
| **日志集中** | 所有日志在 OpenClaw 中查看 |
| **免费** | 无额外托管成本 |

## 注意事项

1. **执行时长**: 拉取300只股票约需 5-10 分钟，确保 OpenClaw 任务超时时间 > 15 分钟
2. **并发控制**: akshare 有请求频率限制，cron.py 中已添加延时
3. **失败重试**: 建议配置失败通知（邮件/Slack）
4. **数据备份**: Workers D1 数据定期导出（虽然 D1 有持久化）
