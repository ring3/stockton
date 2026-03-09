# 鏁版嵁婧愯缁嗘枃妗?

鏈枃妗ｈ缁嗕粙缁?Stockton 鎶€鑳戒娇鐢ㄧ殑 akshare 鏁版嵁婧愬強鍏?API 璇存槑銆?

## Akshare 绠€浠?

[Akshare](https://www.akshare.xyz/) 鏄竴涓紑婧愮殑 Python 璐㈢粡鏁版嵁鎺ュ彛搴擄紝鎻愪緵鑲＄エ銆佹湡璐с€佹湡鏉冦€佸熀閲戙€佸姹囩瓑閲戣瀺鏁版嵁銆?

### 鐗圭偣

- **鍏嶈垂寮€婧?*: 鏃犻渶 API Key锛屽畬鍏ㄥ厤璐?
- **鏁版嵁涓板瘜**: 瑕嗙洊 A鑲°€佹腐鑲°€佺編鑲°€丒TF銆佹湡璐х瓑
- **瀹炴椂鎬уソ**: 瀹炴椂琛屾儏鏁版嵁鏉ヨ嚜涓滄柟璐㈠瘜
- **鏇存柊鍙婃椂**: 绀惧尯娲昏穬锛屾帴鍙ｆ寔缁淮鎶?

### 瀹夎

```bash
pip install akshare
```

## 澶氭暟鎹簮鑷姩鍒囨崲

Stockton 鎶€鑳芥敮鎸佸鏁版嵁婧愯嚜鍔ㄥ垏鎹€傚綋涓绘暟鎹簮锛堜笢鏂硅储瀵岋級杩炴帴澶辫触鏃讹紝浼氳嚜鍔ㄥ垏鎹㈠埌澶囩敤鏁版嵁婧愶紙鏂版氮銆佽吘璁€佺綉鏄擄級銆?

### 鏁版嵁婧愪紭鍏堢骇锛圓鑲″巻鍙叉暟鎹級

| 浼樺厛绾?| 鏁版嵁婧?| akshare API | 浠ｇ爜鏍煎紡 |
|--------|--------|-------------|----------|
| 1 | 涓滄柟璐㈠瘜 | `stock_zh_a_hist` | 600519 |
| 2 | 鏂版氮璐㈢粡 | `stock_zh_a_daily` | sh600519 / sz000001 |
| 3 | 鑵捐璐㈢粡 | `stock_zh_a_hist_tx` | sh600519 / sz000001 |
| 4 | 缃戞槗璐㈢粡 | `stock_zh_a_hist_163` | 0600519 / 1000001 |

### 杩炴帴閿欒鑷姩鍒囨崲

褰撴娴嬪埌浠ヤ笅杩炴帴閿欒鏃讹紝鑷姩灏濊瘯涓嬩竴涓暟鎹簮锛?
- `ProxyError` - 浠ｇ悊閿欒
- `Max retries exceeded` - 杩炴帴瓒呮椂
- `Remote end closed` - 杩滅▼杩炴帴鍏抽棴
- `SSL` / `443` - SSL 杩炴帴閿欒

### 鏌ョ湅鏁版嵁鏉ユ簮

鏁版嵁杩斿洖鍚庝細鏍囪瀹為檯浣跨敤鐨勬暟鎹簮锛?

```python
result = get_stock_data('600519', days=60)
print(result['data_source'])  # "akshare(eastmoney)" 鎴?"akshare(sina)" 绛?
```

## 涓昏 API 璇存槑

### 1. A鑲″巻鍙茶鎯?

```python
import akshare as ak

# 鑾峰彇A鑲″巻鍙睰绾挎暟鎹?
df = ak.stock_zh_a_hist(
    symbol='600519',           # 鑲＄エ浠ｇ爜
    period='daily',            # 鍛ㄦ湡: daily, weekly, monthly
    start_date='20240101',     # 寮€濮嬫棩鏈?(YYYYMMDD)
    end_date='20240301',       # 缁撴潫鏃ユ湡 (YYYYMMDD)
    adjust='qfq'               # 澶嶆潈: qfq=鍓嶅鏉? hfq=鍚庡鏉? 绌?涓嶅鏉?
)

# 杩斿洖鍒楀悕
# 鏃ユ湡, 寮€鐩? 鏀剁洏, 鏈€楂? 鏈€浣? 鎴愪氦閲? 鎴愪氦棰? 鎸箙, 娑ㄨ穼骞? 娑ㄨ穼棰? 鎹㈡墜鐜?
```

### 2. ETF 鍩洪噾鏁版嵁

```python
# 鑾峰彇ETF鍘嗗彶鏁版嵁
df = ak.fund_etf_hist_em(
    symbol='512400',           # ETF浠ｇ爜
    period='daily',
    start_date='20240101',
    end_date='20240301',
    adjust='qfq'
)
```

### 3. 娓偂鏁版嵁

```python
# 鑾峰彇娓偂鍘嗗彶鏁版嵁
df = ak.stock_hk_hist(
    symbol='00700',            # 娓偂浠ｇ爜锛?浣嶆暟瀛楋級
    period='daily',
    start_date='20240101',
    end_date='20240301',
    adjust='qfq'
)
```

### 4. 瀹炴椂琛屾儏

```python
# A鑲″疄鏃惰鎯咃紙鍏ㄩ儴A鑲★級
df = ak.stock_zh_a_spot_em()

# 杩斿洖鍒楀悕锛堥儴鍒嗭級:
# 浠ｇ爜, 鍚嶇О, 鏈€鏂颁环, 娑ㄨ穼骞? 娑ㄨ穼棰? 鎴愪氦閲? 鎴愪氦棰? 鎸箙, 
# 鏈€楂? 鏈€浣? 浠婂紑, 鏄ㄦ敹, 閲忔瘮, 鎹㈡墜鐜? 甯傜泩鐜?鍔ㄦ€? 甯傚噣鐜?
# 鎬诲競鍊? 娴侀€氬競鍊? 60鏃ユ定璺屽箙, 骞村垵鑷充粖娑ㄨ穼骞? 52鍛ㄦ渶楂? 52鍛ㄦ渶浣?

# ETF瀹炴椂琛屾儏
df = ak.fund_etf_spot_em()

# 娓偂瀹炴椂琛屾儏
df = ak.stock_hk_spot_em()
```

### 5. 绛圭爜鍒嗗竷

```python
# 鑾峰彇涓偂绛圭爜鍒嗗竷锛堜粎A鑲★級
df = ak.stock_cyq_em(symbol='600519')

# 杩斿洖鍒楀悕:
# 鏃ユ湡, 鑾峰埄姣斾緥, 骞冲潎鎴愭湰, 90鎴愭湰-浣? 90鎴愭湰-楂? 90闆嗕腑搴? 
# 70鎴愭湰-浣? 70鎴愭湰-楂? 70闆嗕腑搴?
```

## 浠ｇ爜绫诲瀷鍒ゆ柇

### ETF 浠ｇ爜瑙勫垯

| 绫诲瀷 | 浠ｇ爜瑙勫垯 | 绀轰緥 |
|------|----------|------|
| 涓婁氦鎵€ ETF | 51xxxx, 52xxxx, 56xxxx, 58xxxx | 512400 (鏈夎壊ETF) |
| 娣变氦鎵€ ETF | 15xxxx, 16xxxx, 18xxxx | 159883 (鍖荤枟鍣ㄦETF) |

```python
def is_etf_code(stock_code: str) -> bool:
    etf_prefixes = ('51', '52', '56', '58', '15', '16', '18')
    return stock_code.startswith(etf_prefixes) and len(stock_code) == 6
```

### 娓偂浠ｇ爜瑙勫垯

| 绫诲瀷 | 浠ｇ爜瑙勫垯 | 绀轰緥 |
|------|----------|------|
| 娓偂 | 5浣嶆暟瀛楋紝鎴栧甫 hk 鍓嶇紑 | 00700, hk00700 (鑵捐鎺ц偂) |

```python
def is_hk_code(stock_code: str) -> bool:
    code = stock_code.lower()
    if code.startswith('hk'):
        numeric_part = code[2:]
        return numeric_part.isdigit() and 1 <= len(numeric_part) <= 5
    return code.isdigit() and len(code) == 5
```

## 鎶€鏈寚鏍囪绠?

### 绉诲姩骞冲潎绾?(MA)

```python
df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()
```

### 涔栫鐜?(Bias)

```python
# 涔栫鐜?= (鐜颁环 - 鍧囩嚎) / 鍧囩嚎 * 100%
df['bias_ma5'] = (df['close'] - df['ma5']) / df['ma5'] * 100
df['bias_ma10'] = (df['close'] - df['ma10']) / df['ma10'] * 100
```

### 閲忔瘮

```python
# 閲忔瘮 = 褰撴棩鎴愪氦閲?/ 5鏃ュ钩鍧囨垚浜ら噺
avg_volume_5 = df['volume'].rolling(window=5, min_periods=1).mean()
df['volume_ratio'] = df['volume'] / avg_volume_5.shift(1)
```

## 闃插皝绂佺瓥鐣?

### 1. 璇锋眰棰戠巼鎺у埗

```python
import time
import random

# 闅忔満浼戠湢锛?-5绉掞級
time.sleep(random.uniform(2.0, 5.0))

# 閫熺巼闄愬埗鍣?
class RateLimiter:
    def __init__(self, min_interval=2.0):
        self.min_interval = min_interval
        self.last_request_time = None
    
    def sleep(self):
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        
        # 棰濆闅忔満浼戠湢
        time.sleep(random.uniform(2.0, 5.0))
        self.last_request_time = time.time()
```

### 2. 缂撳瓨绛栫暐

```python
import time
from typing import Dict, Any

# 瀹炴椂琛屾儏缂撳瓨锛?0绉掞級
_realtime_cache: Dict[str, Any] = {
    'data': None,
    'timestamp': 0,
    'ttl': 60
}

def get_cached_realtime():
    current_time = time.time()
    if (_realtime_cache['data'] is not None and 
        current_time - _realtime_cache['timestamp'] < _realtime_cache['ttl']):
        return _realtime_cache['data']
    
    # 閲嶆柊鑾峰彇鏁版嵁
    df = ak.stock_zh_a_spot_em()
    _realtime_cache['data'] = df
    _realtime_cache['timestamp'] = current_time
    return df
```

### 3. 骞跺彂鎺у埗

```python
from concurrent.futures import ThreadPoolExecutor

# 寤鸿淇濇寔浣庡苟鍙戯紙3涓互鍐咃級
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(fetch_func, stock_codes))
```

## 閿欒澶勭悊

### 甯歌閿欒

```python
import akshare as ak

try:
    df = ak.stock_zh_a_hist(symbol='600519', ...)
except Exception as e:
    error_msg = str(e).lower()
    
    # 鍙嶇埇灏佺
    if any(kw in error_msg for kw in ['banned', 'blocked', '棰戠巼', 'rate', '闄愬埗']):
        print("琚弽鐖皝绂侊紝璇风◢鍚庡啀璇?)
    
    # 缃戠粶閿欒
    elif any(kw in error_msg for kw in ['connection', 'timeout', '缃戠粶']):
        print("缃戠粶閿欒锛岃妫€鏌ヨ繛鎺?)
    
    # 鏁版嵁涓嶅瓨鍦?
    elif 'empty' in error_msg or 'none' in error_msg:
        print("鏁版嵁涓嶅瓨鍦ㄦ垨涓虹┖")
    
    else:
        print(f"鏈煡閿欒: {e}")
```

### 閲嶈瘯鏈哄埗

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def fetch_with_retry(symbol):
    return ak.stock_zh_a_hist(symbol=symbol, ...)
```

## 鏁版嵁鏍囧噯鍖?

### 鍒楀悕鏄犲皠

```python
# akshare 涓枃鍒楀悕 -> 鏍囧噯鑻辨枃鍒楀悕
column_mapping = {
    '鏃ユ湡': 'date',
    '寮€鐩?: 'open',
    '鏀剁洏': 'close',
    '鏈€楂?: 'high',
    '鏈€浣?: 'low',
    '鎴愪氦閲?: 'volume',
    '鎴愪氦棰?: 'amount',
    '娑ㄨ穼骞?: 'pct_chg',
    '鎹㈡墜鐜?: 'turnover_rate',
}

df = df.rename(columns=column_mapping)
```

### 鏁版嵁绫诲瀷杞崲

```python
# 鏁板€煎垪绫诲瀷杞崲
numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 鏃ユ湡杞崲
df['date'] = pd.to_datetime(df['date'])

# 鎺掑簭
df = df.sort_values('date').reset_index(drop=True)
```

## 鍏朵粬鏁版嵁婧愶紙澶囬€夛級

铏界劧 Stockton 鎶€鑳戒富瑕佷娇鐢?akshare锛屼絾涔熷彲浠ユ牴鎹渶瑕侀泦鎴愬叾浠栨暟鎹簮锛?

### Efinance锛堝閫夛級

```python
import efinance as ef

# 鍘嗗彶鏁版嵁
df = ef.stock.get_quote_history(
    stock_codes='600519',
    beg='20240101',
    end='20240301',
    klt=101,  # 鏃ョ嚎
    fqt=1     # 鍓嶅鏉?
)
```

### Tushare锛堝閫夛紝闇€瑕?Token锛?

```python
import tushare as ts

ts.set_token('your_token')
pro = ts.pro_api()

# 鏃ョ嚎鏁版嵁
df = pro.daily(ts_code='600519.SH', start_date='20240101')
```

## 鐩稿叧閾炬帴

- [Akshare 瀹樻柟鏂囨。](https://www.akshare.xyz/)
- [Akshare GitHub](https://github.com/akfamily/akshare)
- [涓滄柟璐㈠瘜](https://www.eastmoney.com/)
