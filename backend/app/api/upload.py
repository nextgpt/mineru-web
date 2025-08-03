import traceback
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.file import File as FileModel, FileStatus, BackendType as FileBackendType
from app.models.settings import Settings, BackendType
from app.utils.minio_client import upload_file
from app.utils.user_dep import get_user_id
from app.services.parser import ParserService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid
from datetime import datetime
from typing import List

router = APIRouter()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mineru.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_user_id)
):
    db = SessionLocal()
    results = []
    
    for file in files:
        try:
            # 生成唯一文件名
            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            # 保存到 MinIO（如果失败会自动回退到本地存储）
            minio_path = upload_file(
                file.file,
                unique_filename,
                file.content_type
            )
            settings = db.query(Settings).filter(Settings.user_id == user_id).first()
            backend = FileBackendType.PIPELINE
            if settings:
            
                if settings.backend == BackendType.PIPELINE:
                    backend = FileBackendType.PIPELINE
                else:
                    backend = FileBackendType.VLM

            
            # 保存到数据库
            db_file = FileModel(
                user_id=user_id,
                filename=file.filename,
                size=file.size,
                status=FileStatus.PENDING,
                upload_time=datetime.utcnow(),
                minio_path=minio_path,  # 使用实际返回的路径
                content_type=file.content_type,
                backend=backend
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            
            # 将解析任务加入队列（如果Redis可用）
            try:
                parser_service = ParserService(db)
                parser_service.queue_parse_file(db_file, user_id)
                print(f"✅ 解析任务已加入队列: {db_file.filename}")
            except Exception as e:
                print(f"⚠️ 无法加入解析队列，但文件上传成功: {str(e)}")
                # 不抛出异常，让文件上传继续完成
            
            results.append(db_file.to_dict())
            
        except Exception as e:
            db.rollback()
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"文件 {file.filename} 上传失败: {str(e)}")
    
    db.close()
    return {
        "total": len(results),
        "files": results
    } 