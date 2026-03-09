---
name: stockton
description: A鑲¤鎯呮暟鎹幏鍙栦笌鍒嗘瀽宸ュ叿锛堝熀浜巃kshare锛夛紝鎻愪緵涓偂鍘嗗彶K绾裤€佸疄鏃惰鎯呫€佹妧鏈寚鏍囪绠椼€佽秼鍔垮垎鏋愶紝浠ュ強澶х洏甯傚満姒傝鏁版嵁锛堟寚鏁拌鎯呫€佹定璺岀粺璁°€佹澘鍧楁定璺屾锛夈€傛墍鏈夌粨鏋滄敮鎸佸瓧鍏?JSON鏍煎紡锛屼究浜庝紶缁橪LM杩涗竴姝ュ垎鏋愩€俇se when Kimi needs to get Chinese A-stock market data, analyze stock trends, get market overview data (indices, sectors, statistics), or provide trading decision support with structured data output for LLM processing.
---

# Stockton - A鑲¤鎯呮暟鎹伐鍏凤紙Akshare鐗堬級

Stockton 鎻愪緵 A 鑲″競鍦虹殑瀹屾暣鏁版嵁鑾峰彇鍜屽垎鏋愯兘鍔涳紝鍖呮嫭**涓偂鏁版嵁**鍜?*澶х洏甯傚満鏁版嵁**锛屽熀浜?**akshare** 鏁版嵁婧愶紝鎵€鏈夌粨鏋滃潎鍙浆鎹负 **JSON 鏍煎紡**锛屼究浜庝紶缁?LLM 杩涗竴姝ュ垎鏋愩€?

## 鏍稿績鍔熻兘

### 涓偂鏁版嵁
1. **鍘嗗彶琛屾儏鏁版嵁鑾峰彇** - 鏃ョ嚎鏁版嵁锛圤HLCV锛夈€佸墠澶嶆潈澶勭悊銆佹妧鏈寚鏍囷紙MA銆侀噺姣旂瓑锛?
2. **瀹炴椂琛屾儏鏁版嵁** - 鏈€鏂颁环鏍笺€佹定璺屽箙銆侀噺姣斻€佹崲鎵嬬巼銆佸競鐩堢巼銆佸競鍑€鐜?
3. **绛圭爜鍒嗗竷鏁版嵁**锛堜粎A鑲★級- 鑾峰埄姣斾緥銆佸钩鍧囨垚鏈€佺鐮侀泦涓害
4. **瓒嬪娍浜ゆ槗鍒嗘瀽** - 澶氬ご鎺掑垪鍒ゆ柇銆佷拱鍏ヤ俊鍙风敓鎴愩€佺患鍚堣瘎鍒?

### 澶х洏甯傚満鏁版嵁
1. **涓昏鎸囨暟琛屾儏** - 涓婅瘉鎸囨暟銆佹繁璇佹垚鎸囥€佸垱涓氭澘鎸囥€佺鍒?0銆佹勃娣?00绛?
2. **甯傚満娑ㄨ穼缁熻** - 涓婃定/涓嬭穼瀹舵暟銆佹定鍋滆穼鍋滄暟銆佷袱甯傛垚浜ら
3. **鏉垮潡娑ㄨ穼姒?* - 棰嗘定/棰嗚穼鏉垮潡鎺掑悕
4. **甯傚満鎯呯华鍒嗘瀽** - 鍩轰簬鏁版嵁璁＄畻甯傚満鎯呯华鎸囨爣

## 蹇€熷紑濮?

```python
from skills.stockton.scripts.data_fetcher import get_stock_data, get_stock_data_for_llm
from skills.stockton.scripts.stock_analyzer import analyze_trend, analyze_for_llm
from skills.stockton.scripts.market_analyzer import get_market_overview, analyze_market_for_llm

# ========== 涓偂鏁版嵁 ==========
# 鑾峰彇涓偂鏁版嵁锛堝瓧鍏告牸寮忥級
stock_result = get_stock_data('600519', days=60)

# 涓偂瓒嬪娍鍒嗘瀽锛圠LM鏍煎紡锛?
stock_analysis = analyze_for_llm('600519', days=60)

# ========== 澶х洏鏁版嵁 ==========
# 鑾峰彇甯傚満姒傝锛堝瓧鍏告牸寮忥級
market_result = get_market_overview(format_type='dict')

# 澶х洏甯傚満鍒嗘瀽锛圠LM鏍煎紡锛?
market_analysis = analyze_market_for_llm()

# ========== 浼犵粰 LLM ==========
llm_input = f"""
{market_analysis}

---

{stock_analysis}

璇峰熀浜庝互涓婂ぇ鐩樺拰涓偂鏁版嵁锛岀粰鍑烘姇璧勫缓璁€?
"""
```

## 鏁版嵁婧?

**涓昏鏁版嵁婧?*: [akshare](https://www.akshare.xyz/) - 寮€婧愯储缁忔暟鎹帴鍙ｅ簱

| 浼樺厛绾?| 鏁版嵁婧?| 璇存槑 |
|--------|--------|------|
| 1 | 涓滄柟璐㈠瘜 (akshare) | A鑲′富鎺ュ彛 `stock_zh_a_hist` |
| 2 | 鏂版氮璐㈢粡 (akshare) | A鑲″鐢?`stock_zh_a_daily` |
| 3 | 鑵捐璐㈢粡 (akshare) | A鑲″鐢?`stock_zh_a_hist_tx` |
| 4 | 缃戞槗璐㈢粡 (akshare) | A鑲″鐢?`stock_zh_a_hist_163` |
| 5 | 涓滄柟璐㈠瘜 (efinance) | 鍙€夊寮猴紝瀹夎鍚庝紭鍏堜娇鐢?|

**鑷姩鍒囨崲**: 褰撲富鏁版嵁婧愯繛鎺ュけ璐ユ椂锛堝浠ｇ悊閿欒锛夛紝鑷姩鍒囨崲鍒版柊娴?鑵捐/缃戞槗绛夊叾浠栨暟鎹簮銆?

---

## OpenClaw 宸ュ叿鎺ュ彛

### 馃搳 澶х洏甯傚満鏁版嵁宸ュ叿

#### 宸ュ叿 1: get_market_overview

鑾峰彇瀹屾暣鐨勫競鍦烘瑙堟暟鎹紝鍖呮嫭鎸囨暟琛屾儏銆佹定璺岀粺璁°€佹澘鍧楁定璺屾銆?

```python
def get_market_overview(
    format_type: str = "dict"  # "dict", "json", "prompt"
) -> Union[Dict[str, Any], str]:
    """
    Returns (format_type="dict"):
        {
            'date': '2024-01-15',
            'fetch_time': '2024-01-15 10:30:00',
            'data_source': 'akshare',
            'indices': [              # 涓昏鎸囨暟鍒楄〃
                {
                    'code': 'sh000001',
                    'name': '涓婅瘉鎸囨暟',
                    'current': 2850.50,
                    'change': 15.30,
                    'change_pct': 0.54,
                    'open': 2835.20,
                    'high': 2860.80,
                    'low': 2830.50,
                    'volume': 350000000,
                    'amount': 450000000000,
                    'amplitude': 1.07
                },
                ...
            ],
            'up_count': 3200,         # 涓婃定瀹舵暟
            'down_count': 1500,       # 涓嬭穼瀹舵暟
            'flat_count': 200,        # 骞崇洏瀹舵暟
            'limit_up_count': 80,     # 娑ㄥ仠瀹舵暟
            'limit_down_count': 20,   # 璺屽仠瀹舵暟
            'total_amount': 8500.5,   # 涓ゅ競鎴愪氦棰濓紙浜垮厓锛?
            'top_sectors': [          # 棰嗘定鏉垮潡锛圱op 5锛?
                {'name': '鍗婂浣?, 'change_pct': 3.5},
                {'name': '鏂拌兘婧?, 'change_pct': 2.8},
                ...
            ],
            'bottom_sectors': [       # 棰嗚穼鏉垮潡锛圱op 5锛?
                {'name': '閾惰', 'change_pct': -1.2},
                {'name': '鍦颁骇', 'change_pct': -0.8},
                ...
            ]
        }
    """
```

**Prompt 鏍煎紡杈撳嚭绀轰緥**:
```markdown
# A鑲″競鍦烘瑙?- 2024-01-15
鏁版嵁鑾峰彇鏃堕棿: 2024-01-15 10:30:00

## 涓昏鎸囨暟琛屾儏
- **涓婅瘉鎸囨暟** (sh000001): 2850.50 鈫?+15.30 (+0.54%) | 楂? 2860.80 浣? 2830.50
- **娣辫瘉鎴愭寚** (sz399001): 8900.30 鈫?+45.20 (+0.51%) | 楂? 8950.60 浣? 8850.20
...

## 甯傚満娑ㄨ穼缁熻
- 涓婃定瀹舵暟: 3200 馃搱
- 涓嬭穼瀹舵暟: 1500 馃搲
- 娑ㄥ仠瀹舵暟: 80 馃煡
- 璺屽仠瀹舵暟: 20 馃煩
- 涓ゅ競鎴愪氦棰? 8500 浜垮厓

## 棰嗘定鏉垮潡 (Top 5)
1. 鍗婂浣? +3.5%
2. 鏂拌兘婧? +2.8%
...

## 甯傚満鎯呯华
- 鏁翠綋姘涘洿: 鏅定鏍煎眬 馃搱
- 娑ㄨ穼姣? 3200:1500
```

#### 宸ュ叿 2: get_main_indices

鑾峰彇涓昏鎸囨暟琛屾儏銆?

```python
def get_main_indices(
    format_type: str = "dict"
) -> Union[List[Dict], str]:
    """
    Returns (format_type="dict"):
        [
            {
                'code': 'sh000001',
                'name': '涓婅瘉鎸囨暟',
                'current': 2850.50,
                'change_pct': 0.54,
                ...
            },
            ...
        ]
    """
```

#### 宸ュ叿 3: get_sector_rankings

鑾峰彇鏉垮潡娑ㄨ穼姒溿€?

```python
def get_sector_rankings(
    format_type: str = "dict"
) -> Union[Dict[str, List], str]:
    """
    Returns:
        {
            'date': '2024-01-15',
            'top_sectors': [
                {'name': '鍗婂浣?, 'change_pct': 3.5},
                ...
            ],
            'bottom_sectors': [
                {'name': '閾惰', 'change_pct': -1.2},
                ...
            ]
        }
    """
```

#### 宸ュ叿 4: analyze_market_for_llm

鑾峰彇瀹屾暣鐨勫競鍦哄垎鏋愭暟鎹紝鏍煎紡鍖栦负 LLM 鎻愮ず璇嶃€?

```python
def analyze_market_for_llm() -> str:
    """
    Returns:
        瀹屾暣鐨勫競鍦哄垎鏋愭枃鏈紝鍖呭惈锛?
        1. 涓昏鎸囨暟琛屾儏
        2. 甯傚満娑ㄨ穼缁熻
        3. 鏉垮潡娑ㄨ穼姒?
        4. 甯傚満鎯呯华鍒ゆ柇
        5. 鍒嗘瀽璇锋眰锛堜緵LLM鍥炵瓟锛?
        
        鍙洿鎺ヤ綔涓?LLM 鐨勮緭鍏ャ€?
    """
```

---

### 馃搱 涓偂鏁版嵁宸ュ叿

#### 宸ュ叿 5: get_stock_data

鑾峰彇鑲＄エ瀹屾暣鏁版嵁銆?

```python
def get_stock_data(
    stock_code: str,           # 鑲＄エ浠ｇ爜锛屽 "600519"
    days: int = 60,            # 鍘嗗彶鏁版嵁澶╂暟
    include_realtime: bool = True,
    include_chip: bool = True
) -> Dict[str, Any]:
    """
    Returns:
        {
            'success': True,
            'code': '600519',
            'name': '璐靛窞鑼呭彴',
            'daily_data': [...],      # 鍘嗗彶鏃ョ嚎鏁版嵁鍒楄〃
            'realtime_quote': {...},  # 瀹炴椂琛屾儏
            'chip_distribution': {...},  # 绛圭爜鍒嗗竷
            'fetch_time': '2024-01-15 10:30:00'
        }
    """
```

#### 宸ュ叿 6: get_stock_data_for_llm

鑾峰彇鑲＄エ鏁版嵁骞舵牸寮忓寲涓?LLM 鍙敤鐨勬牸寮忋€?

```python
def get_stock_data_for_llm(
    stock_code: str,
    days: int = 60,
    format_type: str = "prompt"  # "prompt", "json", "dict"
) -> str:
    """
    format_type:
    - "prompt": 鏍煎紡鍖栫殑鎻愮ず璇嶆枃鏈紙榛樿锛?
    - "json": JSON 瀛楃涓?
    - "dict": Python 瀛楀吀
    """
```

#### 宸ュ叿 7: analyze_trend

鎵ц瓒嬪娍鍒嗘瀽銆?

```python
def analyze_trend(
    stock_code: str,
    days: int = 60,
    format_type: str = "dict"  # "dict", "json", "prompt"
) -> Union[Dict[str, Any], str]:
    """
    Returns (format_type="dict"):
        {
            'code': '600519',
            'name': '璐靛窞鑼呭彴',
            'trend_status': '寮哄娍澶氬ご',
            'buy_signal': '寮虹儓涔板叆',
            'signal_score': 93,
            'indicators': {
                'current_price': 1695.0,
                'ma5': 1685.0,
                'bias_ma5': 0.59,
                'volume_ratio_5d': 1.1,
                ...
            },
            'signal_reasons': [...],
            'risk_factors': [...]
        }
    """
```

#### 宸ュ叿 8: analyze_for_llm

鑾峰彇瀹屾暣鐨勮偂绁ㄥ垎鏋愶紙鏁版嵁 + 鎶€鏈垎鏋愶級銆?

```python
def analyze_for_llm(stock_code: str, days: int = 60) -> str:
    """
    杩斿洖瀹屾暣鐨勫垎鏋愭枃鏈紝鍙洿鎺ヤ綔涓?LLM 杈撳叆
    """
```

#### 宸ュ叿 9: batch_analyze

鎵归噺鍒嗘瀽澶氬彧鑲＄エ銆?

```python
def batch_analyze(
    stock_codes: List[str],
    days: int = 60,
    max_workers: int = 3
) -> List[Dict[str, Any]]:
    """
    杩斿洖姣忓彧鑲＄エ鐨勫垎鏋愮粨鏋滃垪琛紝鎸夎瘎鍒嗘帓搴?
    """
```

---

## 浣跨敤绀轰緥

### 绀轰緥 1: 鑾峰彇澶х洏鏁版嵁骞朵紶缁?LLM

```python
from skills.stockton.scripts.market_analyzer import analyze_market_for_llm

# 鑾峰彇瀹屾暣鐨勫競鍦哄垎鏋?
market_data = analyze_market_for_llm()

# 浼犵粰 LLM
llm_prompt = f"""
{market_data}

璇峰垎鏋愪粖鏃ュ競鍦鸿蛋鍔匡紝骞剁粰鍑烘槑鏃ユ搷浣滃缓璁€?
"""
```

### 绀轰緥 2: 澶х洏 + 涓偂缁煎悎鍒嗘瀽

```python
from skills.stockton.scripts.market_analyzer import get_market_overview
from skills.stockton.scripts.stock_analyzer import analyze_for_llm

# 鑾峰彇澶х洏鏁版嵁
market = get_market_overview(format_type='prompt')

# 鑾峰彇涓偂鍒嗘瀽
stock = analyze_for_llm('600519', days=60)

# 鍚堝苟浼犵粰 LLM
full_prompt = f"""
# 甯傚満鐜

{market}

---

# 涓偂鍒嗘瀽

{stock}

---

璇风粨鍚堝綋鍓嶅競鍦虹幆澧冿紝鍒嗘瀽璇ヨ偂绁ㄧ殑鎶曡祫浠峰€笺€?
"""
```

### 绀轰緥 3: 鐩戞帶鐗瑰畾鏉垮潡

```python
from skills.stockton.scripts.market_analyzer import get_sector_rankings

# 鑾峰彇鏉垮潡娑ㄨ穼姒?
sectors = get_sector_rankings(format_type='dict')

print("浠婃棩棰嗘定鏉垮潡:")
for s in sectors['top_sectors']:
    print(f"  {s['name']}: +{s['change_pct']:.2f}%")

print("\n浠婃棩棰嗚穼鏉垮潡:")
for s in sectors['bottom_sectors']:
    print(f"  {s['name']}: {s['change_pct']:.2f}%")
```

### 绀轰緥 4: 鎵归噺鍒嗘瀽鑲＄エ骞舵帓搴?

```python
from skills.stockton.scripts.stock_analyzer import batch_analyze

# 鎵归噺鍒嗘瀽
stock_codes = ['600519', '300750', '002594', '000001', '601318']
results = batch_analyze(stock_codes, days=60)

# 杈撳嚭璇勫垎鎺掑悕
print("鑲＄エ璇勫垎鎺掑悕锛?)
for r in results:
    if 'signal_score' in r:
        signal = r['buy_signal']
        score = r['signal_score']
        print(f"{r['code']}: {signal} (璇勫垎: {score})")
```

---

## 浜ゆ槗鐞嗗康

鏈妧鑳藉熀浜庝互涓嬭秼鍔夸氦鏄撶悊蹇佃繘琛屽垎鏋愶細

### 涓ヨ繘绛栫暐锛堜笉杩介珮锛?
- **涔栫鐜?> 5%** 鍧氬喅涓嶄拱鍏?
- **涔栫鐜?< 2%** 鏈€浣充拱鐐瑰尯闂?
- **浠锋牸鍥炶俯 MA5** 鏀拺鏃朵粙鍏?

### 瓒嬪娍浜ゆ槗锛堥『鍔胯€屼负锛?
- **澶氬ご鎺掑垪**: MA5 > MA10 > MA20
- **鍙仛澶氬ご鎺掑垪**鐨勮偂绁?
- **瓒嬪娍寮哄害**鍒ゆ柇锛氱湅鍧囩嚎闂磋窛

### 缁煎悎璇勫垎绯荤粺

| 缁村害 | 鏉冮噸 | 璇存槑 |
|------|------|------|
| 瓒嬪娍 | 40% | 澶氬ご鎺掑垪寰楀垎楂?|
| 涔栫鐜?| 30% | 鎺ヨ繎 MA5 寰楀垎楂?|
| 閲忚兘 | 20% | 缂╅噺鍥炶皟寰楀垎楂?|
| 鏀拺 | 10% | 鑾峰緱鍧囩嚎鏀拺寰楀垎楂?|

**涔板叆淇″彿绛夌骇**:
- 90-100鍒? 寮虹儓涔板叆
- 65-89鍒? 涔板叆
- 50-64鍒? 鎸佹湁
- 35-49鍒? 瑙傛湜
- <35鍒? 鍗栧嚭/绌轰粨

---

## 娴嬭瘯

鎶€鑳藉寘鍚畬鏁寸殑娴嬭瘯濂椾欢锛屼綅浜?`skills/stockton/tests/` 鐩綍銆?

### 瀹夎渚濊禆

```bash
pip install akshare pandas numpy
```

### 杩愯娴嬭瘯

```bash
cd skills/stockton/tests

# 蹇€熸祴璇曪紙鍙祴璇曟牳蹇冨姛鑳斤級
python run_all_tests.py --quick

# 瀹屾暣娴嬭瘯濂椾欢
python run_all_tests.py

# 杩愯鍗曚釜娴嬭瘯
python test_data_fetcher.py
python test_stock_analyzer.py
python test_market_analyzer.py
python test_llm_integration.py
```

### 娴嬭瘯鍐呭

| 娴嬭瘯鏂囦欢 | 娴嬭瘯鍐呭 |
|----------|----------|
| `test_data_fetcher.py` | 鏁版嵁鑾峰彇銆佸疄鏃惰鎯呫€佺鐮佸垎甯冦€丒TF鏁版嵁 |
| `test_stock_analyzer.py` | 瓒嬪娍鍒嗘瀽銆佷拱鍏ヤ俊鍙枫€佺患鍚堣瘎鍒嗐€佹壒閲忓垎鏋?|
| `test_market_analyzer.py` | 鎸囨暟琛屾儏銆佹定璺岀粺璁°€佹澘鍧楁定璺屾 |
| `test_llm_integration.py` | Prompt鏍煎紡銆丣SON鏍煎紡銆佹暟鎹竴鑷存€?|
| `run_all_tests.py` | 涓€閿繍琛屾墍鏈夋祴璇?|

---

## 鍙傝€冩枃妗?

- **鏁版嵁婧愯鎯?*: [references/data_provider.md](references/data_provider.md)
- **浜ゆ槗绛栫暐璇﹁В**: [references/trading_strategy.md](references/trading_strategy.md)

---

## 渚濊禆瑕佹眰

```bash
pip install pandas numpy akshare
```

**鍙€夛紙澧炲己浣撻獙锛?*:
```bash
pip install efinance
```

**璇存槑**: 
- akshare 鏄繀闇€鐨勪富瑕佹暟鎹簮
- efinance 鏄彲閫夌殑锛屽畨瑁呭悗浼氫紭鍏堜娇鐢紙鏇寸ǔ瀹氾級
- 濡傛灉 efinance 鏈畨瑁咃紝鍙娇鐢?akshare 涔熻兘姝ｅ父宸ヤ綔

---

## 鏁呴殰鎺掗櫎

### 浠ｇ悊閿欒 (Windows Proxy Error)

濡傛灉閬囧埌 `ProxyError: Unable to connect to proxy`锛岃鏄庣郴缁熶唬鐞嗚缃共鎵颁簡 akshare 鐨勮繛鎺ャ€?

**蹇€熶慨澶?(PowerShell 绠＄悊鍛?**:
```powershell
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name ProxyEnable -Value 0
ipconfig /flushdns
```
鐒跺悗閲嶆柊鎵撳紑缁堢锛岃繍琛?`python tests/check_proxy.py` 楠岃瘉銆?

**瀹屾暣鎸囧崡**: 瑙?`tests/PROXY_FIX.md`

**鏇夸唬鏂规**: 濡傛灉鏃犳硶淇敼绯荤粺浠ｇ悊锛屽彲鍦ㄦ棤浠ｇ悊鐨勭幆澧冿紙濡傜Щ鍔ㄧ儹鐐癸級涓祴璇曘€傛妧鑳戒唬鐮佹纭紝鍦ㄦ棤浠ｇ悊鐜涓嬪彲姝ｅ父宸ヤ綔銆?

---

## 娉ㄦ剰浜嬮」

1. **闃插皝绂佺瓥鐣?*:
   - 姣忔璇锋眰鍓嶆湁闅忔満浼戠湢锛?-5绉掞級
   - 寤鸿浣跨敤浣庡苟鍙戯紙max_workers=3锛?
   - 瀹炴椂琛屾儏鏁版嵁缂撳瓨 60 绉?

2. **鏁版嵁闄愬埗**:
   - 绛圭爜鍒嗗竷浠呮敮鎸?A 鑲★紙涓嶆敮鎸?ETF銆佹腐鑲★級
   - 瀹炴椂琛屾儏鏁版嵁鏉ヨ嚜涓滄柟璐㈠瘜锛屽彲鑳芥湁寤惰繜

3. **閿欒澶勭悊**:
   - 鎵€鏈夊伐鍏峰嚱鏁伴兘杩斿洖鍖呭惈 `success` 瀛楁鐨勫瓧鍏?
   - 澶辫触鏃?`error_message` 瀛楁鍖呭惈閿欒淇℃伅
