from minio import Minio
from minio.error import S3Error
import os
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:19000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'mineru-files')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

logger.info(f"MinIO配置: endpoint={MINIO_ENDPOINT}, access_key={MINIO_ACCESS_KEY}, bucket={MINIO_BUCKET}, secure={MINIO_SECURE}")

# 创建MinIO客户端
try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )
    # 测试连接
    minio_client.list_buckets()
    logger.info("✅ MinIO连接成功")
    MINIO_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ MinIO连接失败，将使用本地存储: {str(e)}")
    MINIO_AVAILABLE = False

def ensure_bucket():
    if not MINIO_AVAILABLE:
        logger.warning("MinIO不可用，跳过bucket检查")
        return
        
    try:
        logger.info(f"检查bucket是否存在: {MINIO_BUCKET}")
        if not minio_client.bucket_exists(MINIO_BUCKET):
            logger.info(f"创建bucket: {MINIO_BUCKET}")
            minio_client.make_bucket(MINIO_BUCKET)
        else:
            logger.info(f"Bucket已存在: {MINIO_BUCKET}")
    except S3Error as e:
        logger.error(f"MinIO S3错误: code={e.code}, message={e.message}, resource={e.resource}")
        raise
    except Exception as e:
        logger.error(f"MinIO连接错误: {str(e)}")
        raise


def upload_file(file_obj, filename, content_type=None):
    if MINIO_AVAILABLE:
        try:
            ensure_bucket()
            minio_path = filename
            minio_client.put_object(
                MINIO_BUCKET,
                minio_path,
                file_obj,
                length=-1,
                part_size=10*1024*1024,
                content_type=content_type
            )
            logger.info(f"文件已上传到MinIO: {minio_path}")
            return minio_path
        except Exception as e:
            logger.error(f"MinIO上传失败，回退到本地存储: {str(e)}")
    
    # 回退到本地存储
    logger.info("使用本地存储")
    import os
    upload_dir = "/tmp/mineru_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        file_obj.seek(0)
        f.write(file_obj.read())
    
    logger.info(f"文件已保存到本地: {file_path}")
    return filename


def get_file_url(minio_path, expires=3600):
    if MINIO_AVAILABLE:
        try:
            return minio_client.presigned_get_object(MINIO_BUCKET, minio_path, expires=timedelta(seconds=expires))
        except Exception as e:
            logger.error(f"获取MinIO文件URL失败: {str(e)}")
    
    # 回退到本地文件路径
    upload_dir = "/tmp/mineru_uploads"
    file_path = os.path.join(upload_dir, minio_path)
    if os.path.exists(file_path):
        return f"file://{file_path}"
    else:
        return None
