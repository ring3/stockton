# -*- coding: utf-8 -*-
import subprocess
import os

os.environ['NO_PROXY'] = '*'

result = subprocess.run([
    'curl', '-v', '-s',
    '-H', 'User-Agent: Mozilla/5.0',
    '-H', 'Accept: application/json',
    'https://push2.eastmoney.com/api/qt/clist/get?fid=f301&po=1&pz=10&pn=1&np=1&fltt=2&invt=2&ut=b2884a393a59ad64002292a3e90d46a5&fields=f1,f2,f12,f14&fs=m:10'
], capture_output=True, text=True, timeout=30)

print('STDOUT:', result.stdout[:500])
print('STDERR:', result.stderr[:500])
print('Return code:', result.returncode)
