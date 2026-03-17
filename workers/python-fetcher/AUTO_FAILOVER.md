# 数据源自动故障切换指南

## 功能概述

系统支持**请求级别的自动故障切换** - 当某个数据源请求失败时，自动切换到下一个可用数据源重试，直到成功或所有数据源都失败。

## 故障切换策略

### 1. 初始化策略

```
按优先级测试各数据源 → 选择第一个可用的作为主数据源
```

### 2. 请求失败时的故障切换

```
当前数据源请求失败
    ↓
记录失败，尝试下一个数据源
    ↓
成功 → 更新当前数据源，返回结果
失败 → 继续尝试下一个
    ↓
所有数据源都失败 → 抛出异常
```

### 3. 指数成分股获取策略

```
优先使用 akshare_em（支持最好）
    ↓
失败 → 尝试当前数据源
    ↓
失败 → 尝试其他数据源
    ↓
都失败 → 返回空列表（非致命）
```

## 默认优先级

```python
['akshare_tx', 'akshare_sina', 'baostock', 'akshare_em']
```

1. **akshare_tx** (腾讯) - 速度最快
2. **akshare_sina** (新浪) - 数据完整
3. **baostock** - 稳定性好
4. **akshare_em** (东财) - 数据最全但可能被代理阻止

## 使用示例

### 基本使用（自动故障切换）

```python
from src.data_source import DataSourceManager

# 初始化 - 自动选择可用数据源
manager = DataSourceManager()

# 获取数据 - 如果当前数据源失败，自动切换
records = manager.get_stock_history('000001', '20250301', '20250315')

# 获取指数成分股 - 自动选择最佳数据源
components = manager.get_index_components('000300')
```

### 指定首选数据源

```python
# 首选 baostock，失败时自动切换到其他
manager = DataSourceManager(preferred_source='baostock')

# 或自定义完整优先级
manager = DataSourceManager(
    preferred_source='akshare_sina',
    priority=['akshare_sina', 'akshare_tx', 'baostock', 'akshare_em']
)
```

### 命令行使用

```bash
# 使用默认自动故障切换
python cron.py --fetch-only

# 指定首选数据源（失败时自动切换）
python cron.py --fetch-only --data-source akshare_tx
python cron.py --fetch-only --data-source baostock
```

## 日志输出示例

### 正常情况

```
[INFO] 注册适配器: akshare_tx
[INFO] 注册适配器: akshare_sina
[INFO] 注册适配器: baostock
[INFO] 选择数据源: akshare_tx
[INFO] 使用 akshare_tx 获取 000001 数据
[INFO] 成功获取 10 条记录
```

### 故障切换情况

```
[INFO] 选择数据源: akshare_em
[WARNING] akshare_em 获取 000001 失败: ProxyError(...)
[INFO] 切换到 akshare_tx 重试获取 000001
[INFO] 故障切换成功: 切换到 akshare_tx
[INFO] 成功获取 10 条记录
```

### 部分数据源不可用

```
[WARNING] 无法注册 baostock 适配器: baostock not installed
[INFO] 注册适配器: akshare_tx
[INFO] 注册适配器: akshare_sina
[INFO] 选择数据源: akshare_tx
```

## 故障切换场景测试

### 场景1：东财被代理阻止

```python
# 首选东财，但网络不通
manager = DataSourceManager(preferred_source='akshare_em')
# 实际使用: akshare_tx (自动切换)

records = manager.get_stock_history('000001', '20250301', '20250315')
# 东财请求失败 → 自动切换到腾讯 → 成功
```

### 场景2：某只股票在特定数据源失败

```python
# 获取 ETF 数据（某些数据源可能不支持）
records = manager.get_stock_history('510300', '20250301', '20250315')
# akshare_tx 失败 → 切换到 akshare_sina → 切换到 baostock → 成功
```

### 场景3：指数成分股获取

```python
# 使用腾讯作为主数据源（不支持成分股）
manager = DataSourceManager(preferred_source='akshare_tx')

# 获取成分股时自动使用东财
components = manager.get_index_components('000300')
# 优先使用 akshare_em → 失败则尝试其他
```

## 配置建议

### 推荐配置1：速度优先

```python
# 首选腾讯，失败时依次尝试新浪、baostock、东财
manager = DataSourceManager(preferred_source='akshare_tx')
```

### 推荐配置2：数据完整优先

```python
# 首选新浪（有成交额和换手率）
manager = DataSourceManager(preferred_source='akshare_sina')
```

### 推荐配置3：稳定性优先

```python
# 首选 baostock（API 限制少）
manager = DataSourceManager(preferred_source='baostock')
```

## 故障排除

### 问题1：所有数据源都失败

**症状：**
```
RuntimeError: 所有数据源都无法获取 000001 数据。已尝试: akshare_tx, akshare_sina, baostock, akshare_em
```

**解决方案：**
1. 检查网络连接
2. 检查股票代码是否正确
3. 检查日期格式是否正确 (YYYYMMDD)
4. 查看日志中的具体错误信息

### 问题2：某个数据源频繁失败

**症状：**
```
[WARNING] akshare_tx 获取 XXX 失败: ...
[INFO] 切换到 akshare_sina 重试获取 XXX
```

**解决方案：**
- 这是正常现象，系统已自动处理
- 可以调整优先级避免使用该数据源

### 问题3：指数成分股获取失败

**症状：**
```
[ERROR] 所有数据源都无法获取指数 000300 成分股
```

**解决方案：**
- 指数成分股获取失败不会中断程序
- 系统会使用本地缓存的数据（如果有）
- 手动更新成分股：`python cron.py --update-components`

## 性能考虑

### 故障切换开销

- **首次故障切换**：需要尝试其他数据源，有一定延迟
- **后续请求**：使用已成功切换的数据源，无额外开销

### 优化建议

1. **批量请求前预热**：先请求一只股票确认数据源可用
2. **合理设置优先级**：将最稳定的数据源放在前面
3. **监控日志**：关注频繁故障切换的股票/数据源

## 高级用法

### 自定义故障切换逻辑

```python
from src.data_source import DataSourceManager

class CustomDataManager(DataSourceManager):
    def _get_fallback_adapters(self, exclude_names):
        # 自定义备选数据源选择逻辑
        # 例如：优先选择响应速度快的
        pass
```

### 监控故障切换事件

```python
import logging

# 启用 DEBUG 日志查看详细切换过程
logging.basicConfig(level=logging.DEBUG)

manager = DataSourceManager()
records = manager.get_stock_history('000001', '20250301', '20250315')
# 查看日志中的故障切换详情
```

## 总结

- ✅ **自动故障切换**：无需手动干预，系统自动处理
- ✅ **智能指数成分股获取**：优先使用最佳数据源
- ✅ **状态保持**：成功切换后，后续请求使用新数据源
- ✅ **完整日志**：详细记录每次故障切换过程
- ✅ **非致命错误**：指数成分股失败不会中断程序
