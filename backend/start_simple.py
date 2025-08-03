#!/usr/bin/env python3
"""
简化的开发环境启动脚本
"""
import os
import sys

def main():
    print("🚀 启动标书生成系统后端服务...")
    
    # 设置环境变量
    os.environ.update({
        'DATABASE_URL': 'postgresql://postgres:password@192.168.30.220:15432/bidgen',
        'REDIS_HOST': '192.168.30.220',
        'REDIS_PORT': '16379',
        'MINIO_ENDPOINT': '192.168.30.220:19000',
        'MINIO_ACCESS_KEY': 'minioadmin',
        'MINIO_SECRET_KEY': 'minioadmin',
        'MINIO_SECURE': 'false',
        'MINERU_API_URL': 'http://192.168.30.54:8088',
        'LLM_API_URL': 'http://192.168.30.54:3000/v1',
        'LLM_API_KEY': 'token-abc123',
        'LLM_MODEL_NAME': 'Qwen3-30B-A3B-FP8',
        'DEBUG': 'true',
        'HOST': '0.0.0.0',
        'PORT': '8088',
        'PRELOAD_MODEL': 'false'
    })
    
    print("✅ 环境变量设置完成")
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
            port=8088,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
