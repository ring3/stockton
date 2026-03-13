# -*- coding: utf-8 -*-
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak
df = ak.stock_individual_info_em(symbol='000001')
print('stock_individual_info_em 返回数据:')
for _, row in df.iterrows():
    print(f'  {row["item"]}: {row["value"]}')
