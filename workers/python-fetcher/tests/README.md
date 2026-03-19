# python-fetcher 测试脚本目录

此目录包含 python-fetcher 项目的各种测试脚本。

## 文件说明

| 文件 | 说明 |
|------|------|
| `test_simple.py` | 简单测试 - 只测试股票数据获取 |
| `test_datasource.py` | 测试数据源适配器 |
| `test_stock_info.py` | 股票基本信息功能测试 |
| `test_auto_failover.py` | 数据源自动故障切换测试 |
| `test_baostock.py` | Baostock 数据源详细测试 |
| `test_baostock_simple.py` | Baostock 数据源简单测试 |
| `test_data_integrity.py` | 数据完整性检查 |
| `test_latest_date.py` | 最新日期查询测试 |
| `test_new_adapter.py` | 新适配器测试 |
| `test_qmt_receiver.py` | QMT 数据接收服务测试 |
| `test_akshare_alternatives.py` | Akshare 备选接口测试 |

## 使用方法

所有测试脚本都已配置正确的路径，可以直接运行：

```bash
cd workers/python-fetcher

# 运行简单测试
python tests/test_simple.py

# 运行数据源测试
python tests/test_datasource.py

# 运行股票信息测试
python tests/test_stock_info.py

# 运行 QMT 接收服务测试
python tests/test_qmt_receiver.py
```

## 路径说明

测试脚本中已自动配置好导入路径：

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 现在可以正常导入 src 下的模块
from src.data_source import DataSourceManager
from src.local_db import LocalDatabase
from src.fetcher import StockDataFetcher
```

## 目录结构

```
python-fetcher/
├── tests/                   # 测试目录（当前目录）
├── src/                     # 源代码目录
│   ├── data_source.py
│   ├── fetcher.py
│   ├── local_db.py
│   └── ...
├── docs/                    # 文档目录
└── data/                    # 数据存储目录
```
