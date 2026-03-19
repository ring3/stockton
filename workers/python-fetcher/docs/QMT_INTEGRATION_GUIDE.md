# QMT 数据集成方案指南

## 方案概述

由于 QMT 只能在客户端运行，我们采用**"客户端拉取 + 服务接收"** 或 **"本地文件共享"** 的架构。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             QMT 客户端                                   │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │  策略1: HTTP推送    │     │  策略2: 文件写入    │                    │
│  │  qmt_client_strategy │     │  qmt_client_simple  │                    │
│  │                     │     │                     │                    │
│  │  - 拉取实时行情      │     │  - 拉取实时行情      │                    │
│  │  - 拉取期权数据      │     │  - 写入本地文件      │                    │
│  │  - HTTP推送         │     │  - 定时刷新         │                    │
│  └──────────┬──────────┘     └──────────┬──────────┘                    │
│             │                           │                               │
│             ▼                           ▼                               │
│      ┌──────────────┐          ┌──────────────┐                        │
│      │ HTTP POST    │          │ 本地JSON文件  │                        │
│      │ 实时推送     │          │ 定时写入     │                        │
│      └──────────────┘          └──────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
             │                           │
             │                           │ (文件共享/同步)
             ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         python-fetcher 服务端                            │
│  ┌─────────────────────┐     ┌─────────────────────┐                    │
│  │  HTTP接收服务       │     │  文件读取器         │                    │
│  │  qmt_pusher.py      │     │  (集成在fetcher中)  │                    │
│  │                     │     │                     │                    │
│  │  - 接收行情数据      │     │  - 扫描文件变化      │                    │
│  │  - 接收期权数据      │     │  - 读取并入库        │                    │
│  │  - 接收持仓数据      │     │  - 清理过期文件      │                    │
│  └──────────┬──────────┘     └──────────┬──────────┘                    │
│             │                           │                               │
│             └───────────┬───────────────┘                               │
│                         ▼                                               │
│              ┌─────────────────────┐                                    │
│              │    SQLite 数据库    │                                    │
│              │  (stock_data.db)    │                                    │
│              └─────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Cloudflare Workers                               │
│                     (云端数据同步 - 可选)                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 方案对比

| 特性 | HTTP 推送模式 | 本地文件模式 |
|------|--------------|-------------|
| **实时性** | 高（秒级） | 中（5-30秒） |
| **网络依赖** | 需要网络连接 | 本地即可 |
| **部署复杂度** | 需要启动接收服务 | 简单文件共享 |
| **适用场景** | 同机器/局域网 | 跨机器/网络不稳定 |
| **容错性** | 自动重试 | 文件覆盖机制 |

## 方案一：HTTP 推送模式

### 1. 服务端部署（python-fetcher）

```bash
cd workers/python-fetcher

# 启动 QMT 数据接收服务
python qmt/start_qmt_server.bat  # Windows
# 或
python qmt/start_qmt_server.sh    # Linux/Mac

# 或使用指定数据库
python qmt/start_qmt_server.bat  # Windows
# 或
python qmt/start_qmt_server.sh    # Linux/Mac --db-path ./data/qmt_data.db
```

服务启动后会监听以下端点：
- `GET  /health` - 健康检查
- `POST /api/v1/prices` - 接收行情数据
- `POST /api/v1/options` - 接收期权数据
- `POST /api/v1/positions` - 接收持仓数据

### 2. 客户端配置（QMT 内）

1. 打开 QMT/iQuant 客户端
2. 新建 Python 策略
3. 将 `qmt/qmt_client_strategy.py` 的内容复制到策略编辑器
4. 修改配置：

```python
CONFIG = {
    # 数据接收服务地址（如果是本机使用 127.0.0.1，如果是局域网使用服务IP）
    'push_url': 'http://192.168.1.100:8888',
    
    # 推送间隔
    'quote_interval': 5,      # 行情每5秒推送一次
    'option_interval': 30,    # 期权每30秒推送一次
    'position_interval': 60,  # 持仓每分钟推送一次
    
    # 监控的股票
    'stock_codes': [
        '000001.SZ',
        '600519.SH',
        # ... 添加你的股票
    ],
    
    # 监控的期权标的
    'option_underlyings': [
        '510050.SH',   # 50ETF
        '510300.SH',   # 300ETF
    ],
}
```

5. 运行策略（选择"实盘"或"模拟"模式）

## 方案二：本地文件模式

### 1. 客户端配置（QMT 内）

1. 新建 Python 策略
2. 将 `qmt/qmt_client_simple.py` 的内容复制到策略编辑器
3. 修改配置：

```python
CONFIG = {
    # 输出目录（可以是共享文件夹）
    'output_dir': 'D:/qmt_data',  # Windows
    # 'output_dir': '/shared/qmt_data',  # Linux/Mac
    
    # 刷新间隔
    'quote_interval': 5,
    'option_interval': 30,
    
    # 监控的股票
    'stock_codes': ['000001.SZ', '600519.SH'],
}
```

4. 运行策略

### 2. 服务端读取（python-fetcher）

在 `fetcher.py` 中添加文件扫描逻辑：

```python
import os
import json
from datetime import datetime

class QMTFileReader:
    """读取 QMT 输出的文件"""
    
    def __init__(self, watch_dir: str = './qmt_data'):
        self.watch_dir = watch_dir
        self.last_mtime = {}
    
    def read_quotes(self) -> List[Dict]:
        """读取行情数据"""
        file_path = os.path.join(self.watch_dir, 'realtime_quotes.json')
        
        if not os.path.exists(file_path):
            return []
        
        # 检查文件是否更新
        mtime = os.path.getmtime(file_path)
        if file_path in self.last_mtime and mtime <= self.last_mtime[file_path]:
            return []  # 文件未更新
        
        self.last_mtime[file_path] = mtime
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('quotes', [])
        except Exception as e:
            logger.error(f"读取 QMT 文件失败: {e}")
            return []
```

## QMT API 适配说明

### 关键 API 确认清单

在部署前，请确认你的 QMT 版本支持以下 API：

```python
# 1. 基础行情（通常都支持）
get_last_price(code)        # 获取最新价
get_stock_name(code)        # 获取股票名称
get_last_volume(code)       # 获取成交量

# 2. 历史数据（用于计算涨跌幅）
get_history_data(count, period, field_list, stock_code)

# 3. 期权相关（需要确认）
get_option_list(underlying)         # 获取期权合约列表
get_option_greeks(code)             # 获取 Greeks
get_option_iv(code)                 # 获取隐含波动率
get_option_oi(code)                 # 获取持仓量

# 4. 持仓数据（需要登录交易）
get_trade_detail_data('position')   # 获取持仓

# 5. 指数成分股（通常支持）
get_sector(code)                    # 获取指数成分股
```

### API 适配示例

如果你的 QMT 版本 API 不同，请修改 `qmt/qmt_client_strategy.py` 中的 `QMTDataFetcher` 类：

```python
class QMTDataFetcher:
    def get_realtime_quote(self, code: str) -> Optional[Dict]:
        """根据你的 QMT API 修改此函数"""
        
        # 示例1：如果 get_last_price 不存在，使用 get_market_data
        market_data = self.ctx.get_market_data(
            field_list=['lastPrice', 'volume'],
            stock_code=code
        )
        
        return {
            'code': code.split('.')[0],
            'price': market_data['lastPrice'],
            'volume': market_data['volume'],
            'timestamp': datetime.now().isoformat(),
        }
```

## 数据表结构

接收服务会自动创建以下表：

### qmt_realtime_quotes（实时行情）
```sql
CREATE TABLE qmt_realtime_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,           -- 股票代码
    name TEXT,                    -- 股票名称
    price REAL,                   -- 最新价
    change_pct REAL,              -- 涨跌幅
    volume INTEGER,               -- 成交量
    amount REAL,                  -- 成交额
    bid1 REAL,                    -- 买1价
    ask1 REAL,                    -- 卖1价
    bid_vol1 INTEGER,             -- 买1量
    ask_vol1 INTEGER,             -- 卖1量
    timestamp TEXT NOT NULL,      -- 时间戳
    source TEXT DEFAULT 'qmt',    -- 数据来源
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, timestamp)
);
```

### qmt_option_data（期权数据）
```sql
CREATE TABLE qmt_option_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,           -- 期权代码
    underlying TEXT NOT NULL,     -- 标的代码
    option_type TEXT,             -- call/put
    strike REAL,                  -- 行权价
    expiry_date TEXT,             -- 到期日
    price REAL,                   -- 期权价格
    iv REAL,                      -- 隐含波动率
    delta REAL,                   -- Delta
    gamma REAL,                   -- Gamma
    theta REAL,                   -- Theta
    vega REAL,                    -- Vega
    rho REAL,                     -- Rho
    volume INTEGER,               -- 成交量
    open_interest INTEGER,        -- 持仓量
    timestamp TEXT NOT NULL,
    source TEXT DEFAULT 'qmt',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, timestamp)
);
```

## 监控与调试

### 1. 检查数据接收

```bash
# 查看数据库中的最新数据
sqlite3 ./data/stock_data.db "SELECT * FROM qmt_realtime_quotes ORDER BY timestamp DESC LIMIT 5;"
```

### 2. 检查同步日志

```bash
sqlite3 ./data/stock_data.db "SELECT * FROM qmt_sync_log ORDER BY created_at DESC LIMIT 10;"
```

### 3. 健康检查

```bash
curl http://localhost:8888/health
```

### 4. QMT 策略日志

在 QMT 客户端的"策略日志"窗口查看输出。

## 故障排查

### 问题1：QMT 无法连接到接收服务

**排查**：
1. 检查接收服务是否启动：`curl http://<ip>:8888/health`
2. 检查防火墙是否放行端口
3. 确认 QMT 所在机器可以访问服务 IP

### 问题2：期权数据获取失败

**原因**：你的 QMT 版本可能不支持期权 API

**解决**：
1. 联系券商确认 API 支持情况
2. 使用 akshare 在 python-fetcher 端补充期权数据
3. 仅使用 QMT 获取基础行情

### 问题3：数据延迟

**优化**：
1. 调整 `quote_interval` 到更小的值（如 3 秒）
2. 检查网络延迟
3. 使用本地文件模式避免网络开销

## 下一步开发

1. **数据融合**：将 QMT 的实时数据与 python-fetcher 的历史数据合并
2. **期权策略**：基于 QMT 的 Greeks 数据进行期权策略计算
3. **实时监控**：构建基于 QMT 数据的实时监控系统
4. **交易对接**：接收 QMT 的持仓数据，进行风险分析

需要我帮你实现特定的 QMT API 适配代码吗？或者进一步细化某个模块？
