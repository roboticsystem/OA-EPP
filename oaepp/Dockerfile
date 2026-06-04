FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY oaepp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY oaepp/ ./oaepp/

WORKDIR /app/oaepp

# 编译前端（生成静态资源）
RUN reflex export --no-zip

EXPOSE 8000

# 运行Reflex应用
CMD ["reflex", "run", "--env", "prod", "--loglevel", "warning"]
