# -*- coding: utf-8 -*-
"""
使用 akshare 获取期权数据 - 增加延迟和重试
"""
import os
import time

# 清除代理
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak

# 在调用前等待一下，避免频繁请求
print('等待 2 秒...')
time.sleep(2)

print('开始获取数据...')
try:
    df = ak.option_value_analysis_em()
    print(f'成功！获取了 {len(df)} 条数据')
    print(df.head())
except Exception as e:
    print(f'失败: {e}')
