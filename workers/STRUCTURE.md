# Workers 项目结构

Stockton Cloud 的完整项目结构说明。

## 部署架构

```
OpenClaw 定时任务
    │
    ▼
┌─────────────────────┐
│ Python Data Fetcher │  ← 通过 OpenClaw 定时触发
│ (workers/python-)   │     本地运行，推送数据到 Workers
└──────────┬──────────┘
           │ HTTP POST
           ▼
┌─────────────────────┐
│ Cloudflare Workers  │  ← 全球边缘节点，提供 REST API
│ (TypeScript)        │     使用 D1 存储，KV 缓存
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Cloudflare D1       │  ← SQLite 数据库 (500MB 免费)
│ Cloudflare KV       │  ← 键值缓存 (1GB 免费)
└─────────────────────┘
```

## 目录结构

```
workers/
├── README.md                       # 主文档
├── OPENCLAW_INTEGRATION.md         # OpenClaw 集成指南
├── STRUCTURE.md                    # 本文件
├──
├── src/                            # Workers TypeScript 源代码
│   ├── index.ts                   # 入口：路由分发
│   ├── router.ts                  # 路由实现
│   ├── types.ts                   # TypeScript 类型定义
│   ├── stock.ts                   # 股票查询逻辑
│   ├── market.ts                  # 市场概览逻辑
│   ├── db.ts                      # D1 数据库操作
│   └── cache.ts                   # KV 缓存操作
│
├── database/
│   └── schema.sql                 # D1 数据库 Schema
│
├── python-fetcher/                # Python 数据拉取器
│   ├── cron.py                    # 主入口（OpenClaw 调用）
│   ├── requirements.txt           # Python 依赖
│   ├── .env.example               # 环境变量模板
│   │
│   └── src/                       # Python 源代码
│       ├── __init__.py
│       ├── fetcher.py            # akshare 数据拉取
│       ├── sync.py               # Workers 数据同步
│       └── cron_job.py           # 定时任务逻辑
│
├── client_example.py              # Python 客户端示例
│
├── wrangler.toml                  # Workers 配置
└── package.json                   # Node.js 依赖
```

## 数据流向

```
OpenClaw 定时触发 (19:00)
    │
    ├──→ 拉取沪深300成分股
    │       └──→ 每只股票获取60日历史
    │
    ├──→ 拉取中证500成分股
    │       └──→ 每只股票获取60日历史
    │
    └──→ HTTP POST /api/batch_update
            │
            └──→ D1 数据库存储
```

## 文件职责

### Workers 端 (TypeScript)

| 文件 | 职责 |
|------|------|
| `index.ts` | 入口，处理 HTTP 请求和定时清理 |
| `router.ts` | 路由解析和分发 |
| `stock.ts` | 股票数据查询（支持 KV 缓存） |
| `market.ts` | 市场概览统计 |
| `db.ts` | D1 数据库 CRUD 操作 |
| `cache.ts` | KV 缓存读写 |
| `types.ts` | TypeScript 接口定义 |

### Python Fetcher 端

| 文件 | 职责 |
|------|------|
| `cron.py` | OpenClaw 定时任务入口 |
| `src/cron_job.py` | 定时任务核心逻辑 |
| `src/fetcher.py` | akshare 数据拉取，计算技术指标 |
| `src/sync.py` | HTTP 客户端，批量推送到 Workers |

### 客户端

| 文件 | 职责 |
|------|------|
| `client_example.py` | Python SDK，封装 Workers API |

## API 端点

### 公开 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/stock/:code` | 股票历史数据 |
| GET | `/api/stock/:code/latest` | 最新数据 |
| GET | `/api/market/overview` | 市场概览 |

### 内部 API

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/batch_update` | 批量更新 | API_KEY |

## 缓存策略

| 数据类型 | 缓存层 | TTL |
|----------|--------|-----|
| 股票历史数据 | KV | 5分钟 |
| 最新数据 | KV | 1分钟 |
| 市场概览 | 内存 | 30秒 |
| 静态配置 | 内存 | 无限 |

## 数据库 Schema

```sql
-- 股票价格表
stock_prices (
    code TEXT,           -- 股票代码
    trade_date TEXT,     -- 交易日期
    open REAL,           -- 开盘价
    high REAL,           -- 最高价
    low REAL,            -- 最低价
    close REAL,          -- 收盘价
    volume INTEGER,      -- 成交量
    ma5 REAL,            -- 5日均线
    ma10 REAL,           -- 10日均线
    ma20 REAL,           -- 20日均线
    ma60 REAL,           -- 60日均线
    PRIMARY KEY (code, trade_date)
)

-- 市场概览表
market_overview (
    date TEXT PRIMARY KEY,
    up_count INTEGER,
    down_count INTEGER,
    flat_count INTEGER,
    limit_up_count INTEGER,
    limit_down_count INTEGER,
    updated_at TEXT
)
```

## 环境变量

### Workers Secrets

```
API_KEY=your-secret-api-key-here
```

### Python Fetcher（OpenClaw 环境变量）

```
WORKERS_URL=https://your-worker.workers.dev
API_KEY=your-secret-api-key-here
INDICES=000300,000905
HISTORY_DAYS=60
MAX_STOCKS_PER_RUN=100
```

## 扩展开发

### 添加新数据源

1. 修改 `src/fetcher.py`
2. 在 `StockDataFetcher` 类添加新方法
3. 更新 `cron_job.py` 调用逻辑

### 添加新 API 端点

1. 在 `src/router.ts` 添加路由
2. 在 `src/` 下添加处理逻辑（如 `newfeature.ts`）
3. 更新 `types.ts` 类型定义

### 添加新定时任务

1. 在 OpenClaw 配置中添加新的 schedule
2. 创建新的 Python 脚本入口
3. 调用 Workers 相应端点

## 本地开发

```bash
# Workers 本地开发
cd workers
npm install
npm run dev

# Python fetcher 测试
cd python-fetcher
pip install -r requirements.txt
export WORKERS_URL=http://localhost:8787
export API_KEY=test
python cron.py
```

## 部署流程

```bash
# 1. 部署 Workers
npx wrangler deploy

# 2. 配置 OpenClaw 定时任务
# 参考 OPENCLAW_INTEGRATION.md

# 3. 测试定时任务
openclaw run workers/python-fetcher/cron.py
```
