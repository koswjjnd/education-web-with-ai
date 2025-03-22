FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install IPython
RUN pip install llama-index-vector-stores-pinecone
RUN pip install llama-index-storage-chat-store-postgres
ENV PYTHONUNBUFFERED=1
# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"]

