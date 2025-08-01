#!/usr/bin/env python3
"""
Docker 环境启动脚本
适用于远程服务器上的 Docker 部署
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import numpy
        print("✅ NumPy 已安装")
    except ImportError:
        print("❌ NumPy 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy>=1.21.0"])
        print("✅ NumPy 安装完成")

def setup_docker_environment():
    """设置 Docker 环境变量"""
    env_vars = {
        # Redis 配置 - 使用 Docker 容器端口
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "16379",  # Docker 映射端口
        "REDIS_DB": "0",
        "REDIS_PASSWORD": "",
        
        # MinIO 配置 - 使用 Docker 容器端口
        "MINIO_ENDPOINT": "localhost:19000",  # Docker 映射端口
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_BUCKET": "mineru-files",
        
        # 数据库配置 - 使用 Docker 容器端口
        "DATABASE_URL": "postgresql://postgres:password@localhost:15432/bidgen",  # Docker 映射端口
        
        # MinerU API 配置
        "MINERU_API_URL": "http://192.168.30.54:8088",
        "SERVER_URL": "http://127.0.0.1:30000",
        
        # LLM API 配置
        "LLM_API_URL": "http://192.168.30.54:3000/v1",
        "LLM_API_KEY": "token-abc123",
        "LLM_MODEL_NAME": "Qwen3-30B-A3B-FP8",
        
        # 后端配置
        "BACKEND": "sglang-client"
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"✅ 设置环境变量: {key}={value}")

def check_docker_services():
    """检查 Docker 服务状态"""
    print("🔍 检查 Docker 服务状态...")
    
    try:
        # 检查 Redis
        import redis
        r = redis.Redis(host='localhost', port=16379, db=0)
        r.ping()
        print("✅ Redis 连接正常")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print("💡 请确保 Docker 容器正在运行: docker ps | grep redis")
    
    try:
        # 检查 PostgreSQL
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=15432,
            database="bidgen",
            user="postgres",
            password="password"
        )
        conn.close()
        print("✅ PostgreSQL 连接正常")
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        print("💡 请确保 Docker 容器正在运行: docker ps | grep postgres")

def main():
    print("🚀 启动 MinerU Web 后端服务 (Docker 环境)...")
    
    # 检查依赖
    check_dependencies()
    
    # 设置环境变量
    setup_docker_environment()
    
    # 检查 Docker 服务
    check_docker_services()
    
    print("📋 环境变量设置完成")
    print("🔧 启动 uvicorn 服务器...")
    
    # 启动 uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8088", 
        "--reload"
    ])

if __name__ == "__main__":
    main() 