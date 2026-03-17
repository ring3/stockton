#!/bin/bash
# Stockton Cloud 一键部署脚本

set -e

echo "=========================================="
echo "Stockton Cloud 部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. 部署 Cloudflare Workers
deploy_workers() {
    echo -e "\n${YELLOW}[1/2] 部署 Cloudflare Workers...${NC}"
    
    if ! command_exists npx; then
        echo -e "${RED}错误: 需要安装 Node.js 和 npm${NC}"
        exit 1
    fi
    
    # 安装依赖
    echo "安装依赖..."
    npm install
    
    # 检查是否已登录
    echo "检查 Cloudflare 登录状态..."
    npx wrangler whoami || npx wrangler login
    
    # 创建 D1 数据库（如果不存在）
    echo "检查 D1 数据库..."
    if ! npx wrangler d1 list | grep -q "stockton-db"; then
        echo "创建 D1 数据库..."
        npx wrangler d1 create stockton-db
        echo -e "${YELLOW}请编辑 wrangler.toml，将 database_id 替换为上方输出的 ID${NC}"
        exit 1
    fi
    
    # 执行数据库迁移
    echo "执行数据库迁移..."
    npx wrangler d1 execute stockton-db --file=./database/schema.sql --local
    
    # 设置 secrets
    echo "设置 API Key..."
    read -s -p "请输入 API Key (用于验证 Python fetcher): " API_KEY
    echo
    echo "$API_KEY" | npx wrangler secret put API_KEY
    
    # 部署
    echo "部署 Workers..."
    npx wrangler deploy
    
    echo -e "${GREEN}Workers 部署完成!${NC}"
    echo -e "${YELLOW}请记录 Workers URL，用于配置 Python fetcher${NC}"
}

# 2. 部署 Python Fetcher
deploy_python_fetcher() {
    echo -e "\n${YELLOW}[2/2] 部署 Python Fetcher...${NC}"
    
    cd python-fetcher
    
    # 配置环境变量
    echo "配置环境变量..."
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${YELLOW}请编辑 .env 文件，填入 WORKERS_URL 和 API_KEY${NC}"
        
        # 提示用户输入
        read -p "Workers URL (如 https://stockton.xxx.workers.dev): " WORKERS_URL
        read -s -p "API Key: " API_KEY
        echo
        
        # 写入 .env
        sed -i "s|WORKERS_URL=.*|WORKERS_URL=$WORKERS_URL|" .env
        sed -i "s|API_KEY=.*|API_KEY=$API_KEY|" .env
    fi
    
    # 检查部署平台
    if command_exists railway; then
        echo "使用 Railway 部署..."
        railway login
        railway init
        railway up
        echo -e "${GREEN}Railway 部署完成!${NC}"
        
    elif command_exists render; then
        echo "请使用 Render 手动部署:"
        echo "1. 访问 https://dashboard.render.com"
        echo "2. 创建新的 Background Worker"
        echo "3. 连接 GitHub 仓库"
        echo "4. 设置环境变量"
        
    else
        echo -e "${YELLOW}未检测到 Railway CLI，请手动部署:${NC}"
        echo "1. Railway (推荐): https://railway.app"
        echo "   - 导入 GitHub 仓库"
        echo "   - 设置环境变量"
        echo "   - 配置定时任务 (cron: 0 19 * * *)"
        echo ""
        echo "2. 或本地手动运行:"
        echo "   cd python-fetcher && pip install -r requirements.txt && python cron.py"
    fi
    
    cd ..
}

# 主菜单
main() {
    echo -e "\n请选择部署选项:"
    echo "1) 部署 Cloudflare Workers (API 服务)"
    echo "2) 部署 Python Fetcher (数据拉取)"
    echo "3) 部署全部"
    echo "4) 仅测试本地运行"
    read -p "输入选项 [1-4]: " choice
    
    case $choice in
        1)
            deploy_workers
            ;;
        2)
            deploy_python_fetcher
            ;;
        3)
            deploy_workers
            deploy_python_fetcher
            ;;
        4)
            echo "测试本地运行..."
            cd python-fetcher
            pip install -r requirements.txt
            python cron.py
            ;;
        *)
            echo "无效选项"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}部署流程完成!${NC}"
}

main
