# Stockton Cloud V2 使用说明

## 新特性

- **指数分表存储**：沪深300和中证500成分股分别存储（简化命名）
  - `data_if300`: 沪深300成分股
  - `data_ic500`: 中证500成分股
- **ETF统一表**：所有ETF数据存储在单一表中（简化命名）
  - `data_etf`: 包含 510050, 510300, 588000, 159915, 510500
- **本地缓存**：先保存到本地SQLite，再同步到Workers
- **增量更新**：
  - 首次获取：从2023年1月1日开始获取全部历史数据
  - 后续获取：自动从数据库最新日期的下一天开始获取，避免重复
  - 数据已最新时自动跳过
- **指数成分股本地缓存**：
  - 本地SQLite存储指数成分股信息（`data_index_components`表）
  - 自动每月更新一次（检查数据是否超过30天）
  - 优先从本地读取，减少网络请求
- **多数据源支持**：当前支持akshare，可扩展妙想、QMT等其他数据源

## 目录结构

```
workers/python-fetcher/
├── cron_v2.py           # V2主入口
├── src/
│   ├── local_db.py      # 本地SQLite管理（支持指数分表+ETF统一表）
│   ├── fetcher_v2.py    # 数据获取
│   └── sync_v2.py       # 同步到Workers
└── ...
```

## 快速开始

### 1. 初始化数据库

**本地数据库**（自动创建）：
```bash
cd workers/python-fetcher
python cron.py --fetch-only
# 数据将保存在 ./data/stock_data.db
```

**Workers D1 数据库**：
```bash
cd workers
npx wrangler d1 execute stockton-db --file=./database/schema_v2.sql
```

### 2. 配置环境变量

```bash
# Workers 地址和密钥
export WORKERS_URL="https://your-worker.workers.dev"
export API_KEY="your-secret-api-key"

# 可选配置
export INDICES="000300,000905"  # 要获取的指数
```

### 3. 运行数据同步

#### 仅获取数据到本地
```bash
python cron.py --fetch-only
```

#### 仅同步本地数据到Workers
```bash
python cron.py --sync-only
```

#### 完整流程
```bash
python cron_v2.py
```

## API 使用

### 查询指数成分股数据

```bash
# 查询沪深300表中的股票
curl "https://your-worker.workers.dev/api/stock/000001?table=data_if300&limit=30"

# 查询中证500表中的股票
curl "https://your-worker.workers.dev/api/stock/000001?table=data_ic500&limit=30"
```

### 查询ETF数据

```bash
# 查询ETF数据（统一表）
curl "https://your-worker.workers.dev/api/stock/510300?table=etf_data_table&limit=30"

# 获取所有ETF列表
curl "https://your-worker.workers.dev/api/etfs"
```

### 查询最新数据

```bash
# 最新数据（指定表）
curl "https://your-worker.workers.dev/api/stock/000001/latest?table=data_if300"

# ETF最新数据
curl "https://your-worker.workers.dev/api/stock/510300/latest?table=data_etf"
```

### 查询数据库状态

```bash
curl -H "Authorization: Bearer your-api-key" \
  "https://your-worker.workers.dev/api/db_status"
```

## 数据表说明

### 指数成分股表（分表）

| 表名 | 说明 | 数据量估算 |
|------|------|-----------|
| `stock_data_if300` | 沪深300成分股日线 | ~300只 × 500天 = 15万条 |
| `stock_data_ic500` | 中证500成分股日线 | ~500只 × 500天 = 25万条 |

### ETF表（统一表）

| 表名 | 说明 | 数据量估算 |
|------|------|-----------|
| `etf_data_table` | 所有ETF日线统一存储 | ~5只 × 500天 = 2500条 |

### ETF包含代码

| 代码 | 名称 | 说明 |
|------|------|------|
| 510050 | 上证50ETF | 华夏上证50ETF |
| 510300 | 沪深300ETF | 华泰柏瑞沪深300ETF |
| 588000 | 科创50ETF | 华夏上证科创板50ETF |
| 159915 | 创业板ETF | 易方达创业板ETF |
| 510500 | 中证500ETF | 南方中证500ETF |

## 定时任务配置（OpenClaw）

```yaml
# openclaw.yaml
schedule:
  - name: stockton-fetch-data
    cron: "0 19 * * 1-5"  # 工作日19:00执行
    script: "workers/python-fetcher/cron_v2.py"
    environment:
      WORKERS_URL: "https://your-worker.workers.dev"
      API_KEY: "your-secret-api-key"
      INDICES: "000300,000905"
```

## 存储空间估算

| 数据类型 | 数量 | 单条大小 | 总计 |
|----------|------|----------|------|
| 沪深300成分股 | 300只 × 500天 | 200字节 | ~30 MB |
| 中证500成分股 | 500只 × 500天 | 200字节 | ~50 MB |
| ETF统一表 | 5只 × 500天 | 220字节 | ~0.5 MB |
| **总计** | - | - | **~80 MB** |

远低于 Cloudflare D1 的 500MB 限制。

## 数据重复说明

- **指数成分股**：分表存储，同一只股票可能在多个指数表中出现
- **ETF数据**：统一表存储，按代码区分，无重复

## 增量更新说明

### 股票价格数据

1. **首次获取**：数据库为空时，从 `2023-01-01` 获取全部历史数据
2. **增量更新**：数据库已有数据时，从最新日期的**下一天**开始获取
3. **数据已最新**：如果最新日期已经是今天，自动跳过该股票
4. **数据合并**：使用 `INSERT OR REPLACE` 自动处理重复数据

示例：
```
股票 000001 在数据库中的最新日期是 2024-03-15
今天日期是 2024-03-20
→ 自动获取 2024-03-16 到 2024-03-20 的数据
```

### 指数成分股数据

指数成分股存储在 `data_index_components` 表中：

1. **首次获取**：本地无数据时，从akshare获取并保存到SQLite
2. **自动更新**：每月检查一次，超过30天自动更新
3. **强制更新**：使用 `--update-components` 参数强制更新
4. **优先本地**：获取股票价格前，优先从本地读取成分股列表

```bash
# 强制更新所有指数成分股
python cron.py --update-components --fetch-only

# 跳过成分股检查（快速模式）
python cron.py --skip-components-check --fetch-only
```

## 故障排查

### 检查本地数据库

```bash
# 查看表统计
sqlite3 ./data/stock_data.db "SELECT 'data_if300' as table, COUNT(*) FROM data_if300 UNION SELECT 'data_ic500', COUNT(*) FROM data_ic500 UNION SELECT 'data_etf', COUNT(*) FROM data_etf;"

# 查看某股票的最新日期
sqlite3 ./data/stock_data.db "SELECT code, MAX(date) as latest_date FROM data_if300 WHERE code='000001' GROUP BY code;"

# 查看ETF列表
sqlite3 ./data/stock_data.db "SELECT DISTINCT code, name FROM data_etf ORDER BY code;"

# 检查数据完整性（某股票的数据条数）
sqlite3 ./data/stock_data.db "SELECT code, COUNT(*) as count FROM data_if300 WHERE code='000001' GROUP BY code;"
```

### 检查Workers状态

```bash
# 健康检查
curl https://your-worker.workers.dev/health

# 数据库状态
curl -H "Authorization: Bearer your-api-key" https://your-worker.workers.dev/api/db_status
```

### 指数成分股表查询

```bash
# 查看指数成分股
sqlite3 ./data/stock_data.db "SELECT index_code, stock_code, stock_name, weight FROM data_index_components WHERE index_code='000300' ORDER BY weight DESC LIMIT 10;"

# 查看成分股更新日期
sqlite3 ./data/stock_data.db "SELECT index_code, COUNT(*) as count, MAX(update_date) as latest_date FROM data_index_components GROUP BY index_code;"
```

## 从 V1 迁移到 V2

1. 备份 V1 数据（可选）
2. 部署新的 Workers 代码（`index_v2.ts`）
3. 执行新的 schema（`schema_v2.sql`）
4. 运行 V2 数据获取脚本
5. 验证数据正确性
6. 更新客户端使用新的 API 端点
