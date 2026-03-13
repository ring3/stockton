# -*- coding: utf-8 -*-
import os
import time
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak

print('测试 stock_market_activity_legu 响应时间...')
start = time.time()
df = ak.stock_market_activity_legu()
elapsed = time.time() - start

print(f'耗时: {elapsed:.3f}s')
print()
print('数据内容:')
for _, row in df.iterrows():
    print(f'  {row["item"]}: {row["value"]}')
