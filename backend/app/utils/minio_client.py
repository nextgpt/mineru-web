from minio import Minio
from minio.error import S3Error
import os
from datetime import timedelta

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:19000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'mineru-files')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def ensure_bucket():
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)


def upload_file(file_obj, filename, content_type=None):
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
    return minio_path


def get_file_url(minio_path, expires=3600):
    return minio_client.presigned_get_object(MINIO_BUCKET, minio_path, expires=timedelta(seconds=expires)) 
