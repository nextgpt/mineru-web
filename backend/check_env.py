#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# 尝试加载不同的环境文件
env_files = ['env.docker', '.env', 'env.example']
loaded_env = None

for env_file in env_files:
    if os.path.exists(env_file):
        print(f"📁 找到环境文件: {env_file}")
        load_dotenv(env_file)
        loaded_env = env_file
        break

if not loaded_env:
    print("⚠️ 未找到环境配置文件，使用系统环境变量")

print("\n🔍 当前环境变量:")
print("=" * 50)

# MinIO配置
minio_vars = [
    'MINIO_ENDPOINT',
    'MINIO_ACCESS_KEY', 
    'MINIO_SECRET_KEY',
    'MINIO_BUCKET',
    'MINIO_SECURE'
]

print("📦 MinIO配置:")
for var in minio_vars:
    value = os.getenv(var, '未设置')
    if var in ['MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY']:
        # 隐藏敏感信息
        if value != '未设置':
            value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
    print(f"  {var}: {value}")

print("\n🌐 网络配置:")
network_vars = [
    'HOST',
    'PORT', 
    'SERVER_URL',
    'MINERU_API_URL',
    'LLM_API_URL'
]

for var in network_vars:
    value = os.getenv(var, '未设置')
    print(f"  {var}: {value}")

print("\n🗄️ 数据库配置:")
db_vars = [
    'DATABASE_URL',
    'REDIS_HOST',
    'REDIS_PORT',
    'REDIS_DB'
]

for var in db_vars:
    value = os.getenv(var, '未设置')
    print(f"  {var}: {value}")

print("\n🤖 LLM配置:")
llm_vars = [
    'LLM_API_KEY',
    'LLM_MODEL_NAME',
    'BACKEND'
]

for var in llm_vars:
    value = os.getenv(var, '未设置')
    if var == 'LLM_API_KEY':
        if value != '未设置':
            value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
    print(f"  {var}: {value}")

print("\n" + "=" * 50)
if loaded_env:
    print(f"✅ 已加载环境文件: {loaded_env}")
else:
    print("⚠️ 建议创建环境配置文件") 