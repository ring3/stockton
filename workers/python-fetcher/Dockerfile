# Stockton Python Fetcher Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY cron.py .
COPY .env.example .

# 环境变量
ENV PYTHONUNBUFFERED=1

# 默认执行一次数据拉取
CMD ["python", "cron.py"]
