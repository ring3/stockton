# -*- coding: utf-8 -*-
import os
os.environ['NO_PROXY'] = '*'

for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

import urllib3
urllib3.disable_warnings()

import requests

# 使用 http/1.1 并禁用 keep-alive
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

class HTTP11Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['headers'] = {'Connection': 'close'}
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', HTTP11Adapter())
session.mount('http://', HTTP11Adapter())

headers = {
    'Host': 'push2.eastmoney.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://data.eastmoney.com/other/valueAnal.html',
    'Connection': 'close',
}

url = 'https://push2.eastmoney.com/api/qt/clist/get?fid=f301&po=1&pz=100&pn=1&np=1&fltt=2&invt=2&ut=b2884a393a59ad64002292a3e90d46a5&fields=f1,f2,f12,f14,f298,f301&fs=m:10'

try:
    resp = session.get(url, headers=headers, timeout=30)
    print(f'Status: {resp.status_code}')
    print(f'Headers: {dict(resp.headers)}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'Total: {data.get("data", {}).get("total", 0)}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
