#!/usr/bin/env python3
from minio import Minio
from minio.error import S3Error
import os

# 从环境变量读取配置
MINIO_ENDPOINT = '192.168.30.220:19000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_SECURE = False

print(f"Testing MinIO connection to {MINIO_ENDPOINT}")
print(f"Access Key: {MINIO_ACCESS_KEY}")
print(f"Secret Key: {MINIO_SECRET_KEY}")
print(f"Secure: {MINIO_SECURE}")

try:
    # 创建 MinIO 客户端
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )
    
    # 测试连接
    print("\nTesting connection...")
    buckets = minio_client.list_buckets()
    print("Connection successful!")
    print("Existing buckets:")
    for bucket in buckets:
        print(f"  - {bucket.name} (created: {bucket.creation_date})")
        
    # 测试 bucket 存在性
    bucket_name = 'mineru-files'
    print(f"\nChecking if bucket '{bucket_name}' exists...")
    if minio_client.bucket_exists(bucket_name):
        print(f"Bucket '{bucket_name}' exists")
    else:
        print(f"Bucket '{bucket_name}' does not exist, creating...")
        minio_client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully")
        
except S3Error as e:
    print(f"S3 Error: {e}")
    print(f"Code: {e.code}")
    print(f"Message: {e.message}")
except Exception as e:
    print(f"Error: {e}")