# stockton Skill 娴嬭瘯鎸囧崡

## 娴嬭瘯鏂囦欢璇存槑

### test_basic.py - 鍩虹鍔熻兘娴嬭瘯锛堟帹鑽愰鍏堣繍琛岋級
**鏃犻渶缃戠粶杩炴帴**锛屼粎娴嬭瘯浠ｇ爜缁撴瀯鍜屾暟鎹ā鍨嬨€?

```bash
cd skills/stockton/tests
python test_basic.py
```

### 鎵嬪姩娴嬭瘯

濡傛灉鑷姩鍖栨祴璇曢亣鍒伴棶棰橈紝鍙互鎵嬪姩娴嬭瘯鏍稿績鍔熻兘锛?

#### 1. 娴嬭瘯妯″潡瀵煎叆

```python
cd skills/stockton/tests
python -c "
import sys
sys.path.insert(0, '../scripts')

from data_fetcher import get_stock_data
from stock_analyzer import analyze_trend
from market_analyzer import get_market_overview

print('All modules imported successfully!')
"
```

#### 2. 娴嬭瘯鏁版嵁鑾峰彇

```python
python -c "
import sys
sys.path.insert(0, '../scripts')
from data_fetcher import get_stock_data

result = get_stock_data('600519', days=5)
print(f'Success: {result[\"success\"]}')
print(f'Code: {result[\"code\"]}')
print(f'Data count: {len(result[\"daily_data\"])}')
"
```

#### 3. 娴嬭瘯瓒嬪娍鍒嗘瀽

```python
python -c "
import sys
sys.path.insert(0, '../scripts')
from stock_analyzer import analyze_trend

result = analyze_trend('600519', days=5, format_type='dict')
print(f'Code: {result[\"code\"]}')
print(f'Signal: {result.get(\"buy_signal\", \"N/A\")}')
print(f'Score: {result.get(\"signal_score\", \"N/A\")}')
"
```

#### 4. 娴嬭瘯澶х洏鏁版嵁

```python
python -c "
import sys
sys.path.insert(0, '../scripts')
from market_analyzer import get_market_overview

result = get_market_overview(format_type='dict')
print(f'Date: {result[\"date\"]}')
print(f'Indices: {len(result[\"indices\"])}')
print(f'Up: {result[\"up_count\"]}, Down: {result[\"down_count\"]}')
"
```

## 缃戠粶闂鎺掓煡

濡傛灉閬囧埌 `ProxyError` 鎴?`Max retries exceeded` 閿欒锛?

### 1. 妫€鏌ョ綉缁滆繛鎺?
```bash
ping push2his.eastmoney.com
```

### 2. 娓呴櫎浠ｇ悊鐜鍙橀噺锛堝鏋滀笉浣跨敤浠ｇ悊锛?
```bash
# Windows CMD
set HTTP_PROXY=
set HTTPS_PROXY=

# Windows PowerShell
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
```

### 3. 鏇存柊 akshare
```bash
pip install -U akshare
```

### 4. 浣跨敤澶囩敤鎺ュ彛
浠ｇ爜宸插唴缃鎺ュ彛閲嶈瘯鏈哄埗锛屼細鑷姩灏濊瘯锛?
- 涓绘帴鍙? `stock_zh_a_hist`
- 澶囩敤鎺ュ彛1: `stock_zh_a_hist_em`
- 澶囩敤鎺ュ彛2: 涓嶅鏉冩暟鎹?

## 娉ㄦ剰浜嬮」

1. **瀹炴椂琛屾儏闄愬埗**: `stock_zh_a_spot_em` 杩斿洖鐨勮偂绁ㄥ垪琛ㄦ湁闄愶紝涓嶆槸鎵€鏈夎偂绁ㄩ兘鑳芥煡鍒板疄鏃惰鎯?
2. **璇锋眰棰戠巼**: akshare 鏈夐槻鐖満鍒讹紝浠ｇ爜宸插唴缃?2-5 绉掗殢鏈轰紤鐪?
3. **缂撳瓨**: 瀹炴椂琛屾儏鏁版嵁缂撳瓨 60 绉掞紝閬垮厤棰戠箒璇锋眰
4. **閿欒澶勭悊**: 鎵€鏈夋帴鍙ｉ兘鏈?try/except 淇濇姢锛屽け璐ユ椂杩斿洖绌烘暟鎹€屼笉鏄穿婧?

## 娴嬭瘯閫氳繃鏍囧噯

- `[OK]` 鎴?`[PASS]` 鏍囪琛ㄧず鎴愬姛
- 鍩虹娴嬭瘯涓嶉渶瑕佺綉缁?
- 缃戠粶娴嬭瘯闇€瑕佽兘璁块棶涓滄柟璐㈠瘜缃戠珯
- 閮ㄥ垎娴嬭瘯澶辫触涓嶅奖鍝嶅叾浠栧姛鑳戒娇鐢?
