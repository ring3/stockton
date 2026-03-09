# Proxy Error Fix Guide

## Problem
Your system has proxy settings that are causing akshare to fail with:
```
ProxyError('Unable to connect to proxy', RemoteDisconnected(...))
```

## Solutions (Try in order)

### Solution 1: Disable Proxy in Windows Settings

1. Open Windows Settings
2. Go to Network & Internet 鈫?Proxy
3. Turn OFF "Automatically detect settings"
4. Turn OFF "Use a proxy server"
5. Click Save
6. Restart your terminal/command prompt
7. Run tests again

### Solution 2: Clear Proxy via Registry (PowerShell as Admin)

```powershell
# Run PowerShell as Administrator
# Then execute:

Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name ProxyServer -ErrorAction SilentlyContinue
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name ProxyEnable -Value 0

# Restart networking
ipconfig /flushdns
```

Then restart your terminal and run tests.

### Solution 3: Force Disable Proxy in Python

Create a test file that forces proxy disable:

```python
# test_with_no_proxy.py
import os

# CRITICAL: Must set BEFORE importing requests/akshare
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# Also disable for urllib3
os.environ['no_proxy'] = '*'

import sys
sys.path.insert(0, '../scripts')

from data_fetcher import get_stock_data

result = get_stock_data('600519', days=5)
print(f"Success: {result['success']}")
print(f"Data count: {len(result.get('daily_data', []))}")
```

### Solution 4: Check Windows Internet Options

1. Open Internet Options (inetcpl.cpl)
2. Go to Connections tab
3. Click LAN settings
4. Uncheck ALL boxes:
   - [ ] Automatically detect settings
   - [ ] Use automatic configuration script
   - [ ] Use a proxy server for your LAN
5. Click OK
6. Restart command prompt

### Solution 5: Use Mobile Hotspot (Bypass)

If your corporate network forces proxy, try:
1. Connect to mobile hotspot (4G/5G)
2. Run the tests
3. This bypasses corporate proxy

## Verification

After applying fix, verify with:

```bash
cd skills/stockton/tests
python check_proxy.py
```

You should see:
```
[OK] akshare request: OK (X rows)
```

Instead of:
```
[FAIL] akshare request: FAIL (Proxy error)
```

## Quick Test

Once proxy is fixed, run:

```bash
cd skills/stockton/tests
python test_basic.py      # Should pass - no network
python test_network.py    # Should pass - with network
```

## Alternative: Use Different Network

If you can't fix proxy settings, the skill code itself is correct. You can:

1. Test on a different machine without proxy
2. Test in a VM or Docker container
3. Test on cloud environment (Colab, etc.)

The skill will work fine in environments without forced proxy.
