#!/usr/bin/env python3
import os
from minio import Minio
from minio.error import S3Error

# MinIO配置 - 使用默认密钥
MINIO_ENDPOINT = '192.168.30.220:19000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_BUCKET = 'mineru-files'
MINIO_SECURE = False

def test_minio_connection():
    try:
        print(f"正在连接MinIO: {MINIO_ENDPOINT}")
        print(f"使用访问密钥: {MINIO_ACCESS_KEY}")
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        print("✅ MinIO连接成功")
        
        # 检查bucket是否存在
        if minio_client.bucket_exists(MINIO_BUCKET):
            print(f"✅ Bucket '{MINIO_BUCKET}' 已存在")
        else:
            print(f"❌ Bucket '{MINIO_BUCKET}' 不存在，正在创建...")
            minio_client.make_bucket(MINIO_BUCKET)
            print(f"✅ Bucket '{MINIO_BUCKET}' 创建成功")
        
        # 列出所有buckets
        buckets = minio_client.list_buckets()
        print("📦 所有Buckets:")
        for bucket in buckets:
            print(f"  - {bucket.name}")
            
        # 测试上传一个小文件
        print("\n🧪 测试文件上传...")
        test_content = b"Hello MinIO!"
        from io import BytesIO
        test_file = BytesIO(test_content)
        
        minio_client.put_object(
            MINIO_BUCKET,
            "test.txt",
            test_file,
            length=len(test_content),
            content_type="text/plain"
        )
        print("✅ 测试文件上传成功")
        
        # 清理测试文件
        minio_client.remove_object(MINIO_BUCKET, "test.txt")
        print("✅ 测试文件清理完成")
            
    except S3Error as e:
        print(f"❌ MinIO S3错误: code={e.code}, message={e.message}")
        if e.code == 'InvalidAccessKeyId':
            print("💡 建议: 检查MinIO访问密钥是否正确")
        elif e.code == 'NoSuchBucket':
            print("💡 建议: 检查bucket名称是否正确")
        elif e.code == 'AccessDenied':
            print("💡 建议: 检查用户权限是否正确")
    except Exception as e:
        print(f"❌ MinIO连接错误: {str(e)}")

if __name__ == "__main__":
    test_minio_connection()
