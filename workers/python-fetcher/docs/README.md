# python-fetcher 文档目录

此目录包含 python-fetcher 项目的相关文档。

## 文件说明

| 文件 | 说明 |
|------|------|
| `AUTO_FAILOVER.md` | 自动故障切换说明 |
| `DATA_INTEGRITY_REPORT.md` | 数据完整性报告 |
| `DATA_SOURCE.md` | 数据源 V1 说明 |
| `DATA_SOURCE_V2.md` | 数据源 V2 说明 |
| `DATA_SOURCE_V3.md` | 数据源 V3 说明 |
| `DATA_VERIFICATION_SUMMARY.md` | 数据验证总结 |
| `QMT_INTEGRATION_GUIDE.md` | QMT 集成完整指南 |
| `QMT_QUICKSTART.md` | QMT 快速上手指南 |
| `README_FAILOVER.md` | 故障切换说明（旧版） |
| `STOCK_INFO_README.md` | 股票基本信息功能文档 |

## 目录结构

```
python-fetcher/
├── docs/                    # 文档目录（当前目录）
├── src/                     # 源代码目录
│   ├── data_source.py      # 数据源适配器
│   ├── fetcher.py          # 数据获取器
│   ├── local_db.py         # 本地数据库
│   ├── sync.py             # 同步模块
│   └── qmt_pusher.py       # QMT 数据接收服务
├── tests/                   # 测试脚本目录
├── data/                    # 数据存储目录
├── cron.py                  # 主入口脚本
└── requirements.txt         # 依赖清单
```

## 快速链接

- [QMT 集成指南](QMT_INTEGRATION_GUIDE.md) - QMT 数据集成完整说明
- [数据源文档](DATA_SOURCE_V3.md) - 数据源适配器说明
