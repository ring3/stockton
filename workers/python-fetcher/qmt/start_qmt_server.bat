@echo off
chcp 65001
cls

echo ========================================
echo QMT 数据接收服务启动器
echo ========================================
echo.

:: 设置默认参数
set PORT=8888
set DB_PATH=./data/stock_data.db

:: 检查参数
if not "%~1"=="" set PORT=%~1
if not "%~2"=="" set DB_PATH=%~2

echo 服务端口: %PORT%
echo 数据库路径: %DB_PATH%
echo.

:: 确保目录存在
if not exist "data" mkdir data

:: 启动服务
echo 正在启动 QMT 数据接收服务...
echo 按 Ctrl+C 停止服务
echo.

python ..\src\qmt_pusher.py --port %PORT% --db-path %DB_PATH%

pause
