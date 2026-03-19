# QMT 数据集成模块

此目录包含与 QMT (iQuant) 客户端集成的相关代码。

## 文件说明

### 客户端策略（运行在 QMT 内）

| 文件 | 说明 |
|------|------|
| `qmt_client_strategy.py` | QMT 客户端数据推送策略（HTTP 模式） |
| `qmt_client_simple.py` | QMT 客户端数据推送策略（本地文件模式） |
| `qmt_config_example.py` | 配置文件示例 |

### 启动脚本

| 文件 | 说明 |
|------|------|
| `start_qmt_server.bat` | Windows 启动脚本（启动接收服务） |
| `start_qmt_server.sh` | Linux/Mac 启动脚本（启动接收服务） |

## 使用方式

### 1. HTTP 推送模式

**服务端（python-fetcher）启动接收服务：**

```bash
# Windows
cd workers/python-fetcher/qmt
start_qmt_server.bat

# Linux/Mac
./start_qmt_server.sh
```

**客户端（QMT 内）配置：**

1. 复制 `qmt_client_strategy.py` 到 QMT 策略编辑器
2. 修改 `CONFIG['push_url']` 为接收服务地址
3. 运行策略

### 2. 本地文件模式

**客户端（QMT 内）配置：**

1. 复制 `qmt_client_simple.py` 到 QMT 策略编辑器
2. 修改 `CONFIG['output_dir']` 为输出目录
3. 运行策略

**服务端读取文件：**

```python
from qmt.qmt_client_simple import read_qmt_quote_file

quotes = read_qmt_quote_file('D:/qmt_data/realtime_quotes.json')
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                         QMT 客户端                           │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │ qmt_client_strategy  │      │ qmt_client_simple    │    │
│  │    (HTTP 推送)        │      │    (文件写入)         │    │
│  └──────────┬───────────┘      └──────────┬───────────┘    │
│             │                              │               │
│             ▼                              ▼               │
│      HTTP POST 推送                   写入本地文件          │
└─────────────────────────────────────────────────────────────┘
              │                              │
              │                              │ (文件读取)
              ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     python-fetcher                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           src/qmt_pusher.py (接收服务)                │  │
│  │  - 接收 HTTP 推送的数据                                │  │
│  │  - 保存到 SQLite 数据库                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 注意事项

1. **QMT 客户端策略**是运行在券商 QMT 软件内的，不是 python-fetcher 的一部分
2. **接收服务**（qmt_pusher.py）是运行在 python-fetcher 端的
3. 两者通过 HTTP 或文件系统进行数据交换
4. 由于 QMT 只能在 Windows 客户端运行，推送/文件模式是最佳方案

## 详细文档

- [QMT 集成指南](../docs/QMT_INTEGRATION_GUIDE.md)
- [QMT 快速上手](../docs/QMT_QUICKSTART.md)
