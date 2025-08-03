#!/usr/bin/env python3
import requests
import json

def diagnose_minio():
    """诊断MinIO服务状态"""
    print("🔍 诊断MinIO服务...")
    
    # 测试基本连接
    try:
        response = requests.get("http://192.168.30.220:19000", timeout=5)
        print(f"✅ MinIO服务响应: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ MinIO服务连接失败: {e}")
        return
    
    # 测试不同的访问密钥组合
    test_keys = [
        ("minioadmin", "minioadmin"),
        ("cqIORnWCvvtCeRYr", "eErd1bjLIDEw0jrZA7htfoJ8e3RgSgBh"),
        ("admin", "admin"),
        ("root", "root"),
    ]
    
    for access_key, secret_key in test_keys:
        print(f"\n🧪 测试密钥: {access_key}")
        try:
            from minio import Minio
            minio_client = Minio(
                "192.168.30.220:19000",
                access_key=access_key,
                secret_key=secret_key,
                secure=False
            )
            
            # 尝试列出buckets
            buckets = minio_client.list_buckets()
            print(f"✅ 密钥有效! 找到 {len(list(buckets))} 个buckets")
            
            # 测试创建bucket
            test_bucket = "test-bucket-123"
            if not minio_client.bucket_exists(test_bucket):
                minio_client.make_bucket(test_bucket)
                print(f"✅ 成功创建bucket: {test_bucket}")
                minio_client.remove_bucket(test_bucket)
                print(f"✅ 成功删除bucket: {test_bucket}")
            
            print(f"🎉 推荐使用密钥: {access_key}")
            return access_key, secret_key
            
        except Exception as e:
            print(f"❌ 密钥无效: {str(e)}")
    
    print("\n❌ 所有测试的密钥都无效")
    print("💡 建议:")
    print("1. 检查MinIO服务配置")
    print("2. 查看MinIO容器日志")
    print("3. 重新初始化MinIO服务")

if __name__ == "__main__":
    diagnose_minio() 