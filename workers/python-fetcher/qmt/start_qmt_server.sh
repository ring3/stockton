#!/bin/bash

echo "========================================"
echo "QMT 数据接收服务启动器"
echo "========================================"
echo ""

# 设置默认参数
PORT=${1:-8888}
DB_PATH=${2:-"./data/stock_data.db"}

echo "服务端口: $PORT"
echo "数据库路径: $DB_PATH"
echo ""

# 确保目录存在
mkdir -p data

# 启动服务
echo "正在启动 QMT 数据接收服务..."
echo "按 Ctrl+C 停止服务"
echo ""

python3 ../src/qmt_pusher.py --port "$PORT" --db-path "$DB_PATH"
