# Stockton Cloud - 股票数据云服务

基于 Cloudflare Workers + OpenClaw 定时任务的股票数据服务架构。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│  OpenClaw 定时任务                                               │
│  - 每天 19:00 触发（收盘后）                                      │
│  - 执行 workers/python-fetcher/cron.py                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ 执行 Python 脚本
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Python Fetcher (OpenClaw 环境运行)                              │
│  - 使用 akshare 拉取股票数据                                      │
│  - 计算技术指标 (MA5/MA10/MA20/MA60)                              │
│  - 推送到 Cloudflare Workers                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cloudflare Workers + D1 + KV                                   │
│  - REST API 查询接口                                             │
│  - D1 SQLite 数据库存储 (500MB)                                  │
│  - KV 缓存热点数据                                               │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP GET
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  客户端 (stockton skill / 其他应用)                              │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 部署 Cloudflare Workers

```bash
cd workers
npm install

# 创建 D1 数据库
npx wrangler d1 create stockton-db
# 复制输出的 database_id 到 wrangler.toml

# 执行数据库迁移
npx wrangler d1 execute stockton-db --file=./database/schema.sql

# 设置 API Key (用于验证 Python fetcher)
echo "your-secret-api-key" | npx wrangler secret put API_KEY

# 部署
npx wrangler deploy

# 记录 Workers URL: https://stockton.xxx.workers.dev
```

### 2. 配置 OpenClaw 定时任务

在 OpenClaw 配置中添加定时任务（选择适合的方式）：

**方式1: 使用 OpenClaw schedule 配置（推荐）**

```yaml
# openclaw.yaml
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

**方式2: 系统级 Cron 调用 OpenClaw**

```bash
# Linux/Mac crontab
crontab -e
# 添加:
0 19 * * 1-5 cd /path/to/stockton && openclaw run workers/python-fetcher/cron.py

# Windows 任务计划程序
schtasks /create /tn "StocktonFetch" /tr "openclaw run workers/python-fetcher/cron.py" /sc weekly /d MON,TUE,WED,THU,FRI /st 19:00
```

**方式3: 手动执行（测试用）**

```bash
cd workers/python-fetcher

# 配置环境变量
export WORKERS_URL=https://your-worker.workers.dev
export API_KEY=your-secret-api-key

# 执行一次
python cron.py
```

### 3. 验证部署

```bash
# 检查 Workers 健康
curl https://your-worker.workers.dev/health

# 手动触发数据拉取
python workers/python-fetcher/cron.py

# 查询数据
curl https://your-worker.workers.dev/api/stock/000001?limit=30
```

## API 文档

### GET /api/stock/:code
查询股票历史数据

参数:
- `start` - 开始日期 (YYYY-MM-DD)
- `end` - 结束日期 (YYYY-MM-DD)
- `limit` - 返回条数 (默认 100)

示例:
```bash
curl https://your-worker.workers.dev/api/stock/000001?limit=30&start=2024-01-01
```

### GET /api/stock/:code/latest
查询最新数据

### GET /api/market/overview
市场概览统计

### POST /api/batch_update (内部)
批量更新数据（由 Python fetcher 调用）

## Python 客户端使用

```python
from workers.client_example import StocktonCloudClient

client = StocktonCloudClient('https://your-worker.workers.dev')

# 查询历史数据
history = client.get_stock_history('000001', limit=60)

# 查询最新数据
latest = client.get_latest('000001')

# 查询市场概览
overview = client.get_market_overview()
```

## 目录结构

```
workers/
├── README.md                 # 本文件
├── OPENCLAW_INTEGRATION.md   # OpenClaw 集成详细说明
├── src/                      # Workers 源代码
│   ├── index.ts             # API 路由
│   ├── router.ts            # 路由实现
│   └── types.ts             # 类型定义
├── database/
│   └── schema.sql           # D1 数据库 Schema
├── python-fetcher/          # Python 数据拉取
│   ├── cron.py              # 主入口
│   ├── src/
│   │   ├── fetcher.py       # akshare 拉取逻辑
│   │   └── sync.py          # Workers 同步
│   ├── requirements.txt     # Python 依赖
│   └── .env.example         # 环境变量模板
└── client_example.py        # Python 客户端示例
```

## 环境变量配置

### Workers 端 (Secrets)

```
API_KEY=your-secret-api-key-here
```

### Python Fetcher 端 (OpenClaw 环境变量)

```
WORKERS_URL=https://your-worker.workers.dev
API_KEY=your-secret-api-key-here
INDICES=000300,000905
HISTORY_DAYS=60
MAX_STOCKS_PER_RUN=100
LOG_LEVEL=INFO
```

## 免费额度

| 服务 | 免费额度 | 预估使用 |
|------|---------|---------|
| **Cloudflare Workers** | 100,000 请求/天 | ~1,000/天 ✅ |
| **Cloudflare D1** | 500MB + 5M 读/天 | ~200MB ✅ |
| **Cloudflare KV** | 1GB 存储 | ~100MB ✅ |
| **OpenClaw** | 内置定时任务 | 免费 ✅ |

**总成本: $0/月**

## 故障排查

### 定时任务未执行

1. 检查 OpenClaw 日志
2. 手动执行测试: `python workers/python-fetcher/cron.py`
3. 检查环境变量配置

### 数据未更新

1. 检查 Workers URL 和 API_KEY 是否正确
2. 检查 Workers 健康状态: `curl /health`
3. 检查 D1 数据库是否有数据: `wrangler d1 execute stockton-db --command="SELECT COUNT(*) FROM stock_prices"`

### akshare 请求失败

1. 检查网络连接
2. 降低请求频率（已内置延时）
3. 更换数据源（东财/新浪切换）

## 相关文档

- [OPENCLAW_INTEGRATION.md](./OPENCLAW_INTEGRATION.md) - OpenClaw 集成详细说明
- [STRUCTURE.md](./STRUCTURE.md) - 项目结构说明

## License

MIT
