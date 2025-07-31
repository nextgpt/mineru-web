#!/bin/bash

export MINERU_MODEL_SOURCE=local

# 等待依赖服务启动
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    
    echo "等待 $service_name 服务启动..."
    while ! nc -z $host $port; do
        echo "等待 $service_name ($host:$port) 启动..."
        sleep 2
    done
    echo "$service_name 服务已启动"
}

# 等待Redis和MinIO服务
if [ "$REDIS_HOST" ]; then
    wait_for_service $REDIS_HOST 6379 "Redis"
fi

if [ "$MINIO_ENDPOINT" ]; then
    MINIO_HOST=$(echo $MINIO_ENDPOINT | cut -d':' -f1)
    MINIO_PORT=$(echo $MINIO_ENDPOINT | cut -d':' -f2)
    wait_for_service $MINIO_HOST $MINIO_PORT "MinIO"
fi

# 初始化数据库
echo "初始化数据库..."
python scripts/init_db.py

if [ "$1" = "python" ]; then
  exec "$@"
else
  # 运行数据库迁移
  echo "运行数据库迁移..."
  alembic upgrade head
  
  # 启动应用
  exec "$@"
fi 