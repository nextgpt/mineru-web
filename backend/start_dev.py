#!/usr/bin/env python3
"""
开发环境启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import sqlalchemy
        import redis
        import minio
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_services():
    """检查外部服务连接"""
    import redis
    import psycopg2
    from minio import Minio
    
    # 检查Redis连接
    try:
        r = redis.Redis(host='192.168.30.220', port=16379, decode_responses=True)
        r.ping()
        print("✅ Redis连接正常")
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False
    
    # 检查PostgreSQL连接
    try:
        conn = psycopg2.connect(
            host='192.168.30.220',
            port=15432,
            database='bidgen',
            user='postgres',
            password='password'
        )
        conn.close()
        print("✅ PostgreSQL连接正常")
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        return False
    
    # 检查MinIO连接
    try:
        client = Minio(
            '192.168.30.220:19000',
            access_key='minioadmin',
            secret_key='minioadmin',
            secure=False
        )
        # 尝试列出buckets
        list(client.list_buckets())
        print("✅ MinIO连接正常")
    except Exception as e:
        print(f"❌ MinIO连接失败: {e}")
        return False
    
    return True

def setup_database():
    """初始化数据库"""
    try:
        from app.database import create_tables
        create_tables()
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def main():
    print("🚀 启动标书生成系统后端服务...")
    
    # 设置工作目录
    os.chdir(Path(__file__).parent)
    
    # 加载环境变量
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载完成")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查外部服务
    print("\n🔍 检查外部服务连接...")
    if not check_services():
        print("❌ 外部服务连接失败，请检查服务状态")
        sys.exit(1)
    
    # 初始化数据库
    print("\n🗄️ 初始化数据库...")
    if not setup_database():
        sys.exit(1)
    
    print("\n🎉 所有检查通过，启动服务...")
    print("📍 服务地址: http://192.168.30.220:8000")
    print("📖 API文档: http://192.168.30.220:8000/docs")
    print("🔧 健康检查: http://192.168.30.220:8000/api/health")
    print("\n按 Ctrl+C 停止服务\n")
    
    # 启动服务
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")

if __name__ == "__main__":
    main()