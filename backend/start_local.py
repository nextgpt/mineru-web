#!/usr/bin/env python3
"""
本地开发启动脚本
解决 NumPy 和 Redis 连接问题
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

def setup_environment():
    """设置环境变量"""
    env_vars = {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379", 
        "REDIS_DB": "0",
        "REDIS_PASSWORD": "",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_BUCKET": "mineru-files",
        "DATABASE_URL": "postgresql://postgres:password@localhost:5432/bidgen",
        "MINERU_API_URL": "http://192.168.30.54:8088",
        "SERVER_URL": "http://127.0.0.1:30000",
        "LLM_API_URL": "http://192.168.30.54:3000/v1",
        "LLM_API_KEY": "token-abc123",
        "LLM_MODEL_NAME": "Qwen3-30B-A3B-FP8",
        "BACKEND": "sglang-client"
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"✅ 设置环境变量: {key}={value}")

def main():
    print("🚀 启动 MinerU Web 后端服务...")
    
    # 检查依赖
    check_dependencies()
    
    # 设置环境变量
    setup_environment()
    
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