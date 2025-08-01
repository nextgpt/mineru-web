#!/bin/bash

# 快速修复 Docker 环境变量脚本
# 在远程服务器上运行此脚本

echo "🔧 修复 Docker 环境变量..."

# 设置 Redis 环境变量（使用 Docker 映射端口）
export REDIS_HOST=localhost
export REDIS_PORT=16379
export REDIS_DB=0
export REDIS_PASSWORD=

# 设置 MinIO 环境变量（使用 Docker 映射端口）
export MINIO_ENDPOINT=localhost:19000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
export MINIO_BUCKET=mineru-files

# 设置数据库环境变量（使用 Docker 映射端口）
export DATABASE_URL=postgresql://postgres:password@localhost:15432/bidgen

# 设置其他环境变量
export MINERU_API_URL=http://192.168.30.54:8088
export SERVER_URL=http://127.0.0.1:30000
export LLM_API_URL=http://192.168.30.54:3000/v1
export LLM_API_KEY=token-abc123
export LLM_MODEL_NAME=Qwen3-30B-A3B-FP8
export BACKEND=sglang-client

echo "✅ 环境变量设置完成"
echo "🚀 现在可以启动应用了："
echo "   uvicorn main:app --host 0.0.0.0 --port 8088 --reload" 