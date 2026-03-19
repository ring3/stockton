# QMT 数据集成快速启动指南

## 5 分钟快速上手

### 场景：本机运行（最简单）

#### 第一步：启动接收服务（python-fetcher 端）

```bash
cd workers/python-fetcher

# Windows
cd qmt
start_qmt_server.bat

# Linux/Mac
cd qmt
chmod +x start_qmt_server.sh
./start_qmt_server.sh
```

看到以下输出表示服务已启动：
```
========================================
QMT 数据接收服务启动
监听地址: 0.0.0.0:8888
数据库: ./data/stock_data.db
========================================
```

#### 第二步：配置 QMT 客户端策略

1. 打开 QMT/iQuant 客户端
2. 点击"策略开发" → "新建策略"
3. 选择"Python 策略"
4. 将 `qmt/qmt_client_simple.py` 的内容复制到编辑器
5. 修改配置（只需改一行）：

```python
CONFIG = {
    'output_dir': 'D:/qmt_data',  # 改为你想要的目录
    'stock_codes': ['000001.SZ', '600519.SH'],  # 添加你关注的股票
}
```

6. 保存策略
7. 点击"运行"（选择"模拟"或"实盘"）

#### 第三步：验证数据

在 python-fetcher 目录下查看数据文件：

```bash
# 查看生成的文件
ls D:/qmt_data/
# 应有: realtime_quotes.json, metadata.json

# 查看内容
cat D:/qmt_data/realtime_quotes.json
```

#### 第四步：读取数据（python-fetcher）

```python
from qmt.qmt_client_simple import read_qmt_quote_file

quotes = read_qmt_quote_file('D:/qmt_data/realtime_quotes.json')
for quote in quotes:
    print(f"{quote['code']}: {quote['price']}")
```

---

## 局域网部署（多台机器）

### 网络拓扑

```
机器A (QMT客户端)           机器B (python-fetcher)
192.168.1.10    <------>   192.168.1.100:8888
```

### 配置步骤

#### 1. 服务端（机器B）

```bash
python src/qmt_pusher.py --port 8888 --host 0.0.0.0
```

> 注意：确保防火墙放行 8888 端口

#### 2. 客户端（机器A - QMT 内）

```python
CONFIG = {
    'push_url': 'http://192.168.1.100:8888',  # 改为机器B的IP
    # ... 其他配置
}
```

#### 3. 测试连接

在机器A上：
```bash
curl http://192.168.1.100:8888/health
```

返回 `{"status": "ok"}` 表示连接成功。

---

## 常见问题

### Q1: QMT 提示模块导入失败

**解决**：QMT 内置的 Python 环境可能缺少某些模块。

```python
# 在策略开头添加
try:
    import json
    import time
    # ... 其他导入
except ImportError as e:
    print(f"导入失败: {e}")
    # 使用 QMT 内置的替代方案
```

### Q2: 无法获取期权数据

**原因**：你的 QMT 版本可能不支持期权 API

**解决**：
1. 联系券商确认是否开通期权权限
2. 使用简化版仅获取股票数据
3. 在 python-fetcher 端用 akshare 补充期权数据

### Q3: 数据推送延迟高

**优化**：
```python
# 减小推送间隔
CONFIG = {
    'quote_interval': 3,  # 改为 3 秒
}
```

### Q4: 持仓数据为空

**原因**：需要登录交易账号且有实际持仓

**检查**：
1. QMT 是否已登录交易账号
2. 是否选择了正确的资金账号
3. 是否有实际持仓

---

## 进阶配置

### 监控更多股票

编辑配置：
```python
'stock_codes': [
    # 添加你想监控的股票代码
    '000001.SZ',
    '600519.SH',
    # ... 最多支持 100 只
]
```

### 保存到不同数据库

```bash
# 启动时指定数据库
python src/qmt_pusher.py --db-path ./data/qmt_2024.db
```

### 查看数据

```bash
# 进入数据库
sqlite3 data/stock_data.db

# 查询最新行情
SELECT code, name, price, change_pct, datetime(timestamp) 
FROM qmt_realtime_quotes 
ORDER BY timestamp DESC 
LIMIT 10;

# 查询期权数据
SELECT code, underlying, iv, delta, theta
FROM qmt_option_data
WHERE underlying = '510050'
ORDER BY timestamp DESC
LIMIT 10;
```

---

## 下一步

1. **数据融合**：将 QMT 数据与 akshare 数据合并
2. **实时分析**：基于 QMT 实时数据构建监控系统
3. **策略开发**：使用 QMT 数据进行策略回测

遇到问题？查看完整文档：`QMT_INTEGRATION_GUIDE.md`
