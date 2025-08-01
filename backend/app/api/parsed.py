import traceback
from fastapi import APIRouter, Query, HTTPException, Body, Response, Depends, Request
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from app.models.parsed_content import ParsedContent
from app.models.file import File as FileModel, FileStatus
from app.services.parser import ParserService
from app.utils.minio_client import minio_client, MINIO_BUCKET
from app.utils.user_dep import get_user_id
import os
import io
import json
from pathlib import Path

router = APIRouter()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mineru.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

@router.get("/files/{file_id}/parsed_content")
def get_parsed_content(
    file_id: int,
    user_id: str = Depends(get_user_id)
):
    db = SessionLocal()
    try:
        # 检查文件是否存在
        file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == user_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 使用解析服务获取内容
        parser = ParserService(db)
        content = parser.get_parsed_content(file_id, user_id)
        
        
        return content
    finally:
        db.close()

@router.post("/files/{file_id}/parse")
def parse_file(
    request: Request,
    file_id: int,
    user_id: str = Depends(get_user_id)
):
    db = SessionLocal()
    try:
        # 检查文件是否存在
        file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == user_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查文件状态
        if file.status == FileStatus.PARSED:
            return {"msg": "文件已解析完成"}
        elif file.status == FileStatus.PARSING:
            return {"msg": "文件正在解析中"}
        
        # 执行解析
        parser = ParserService(db)
        result = parser.parse_file(file, user_id)
        
        return {
            "msg": "解析完成",
            "file_id": file_id,
            "details": result
        }
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/files/{file_id}/parse/status")
def get_parse_status(
    file_id: int,
    user_id: str = Depends(get_user_id)
):
    db = SessionLocal()
    try:
        file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == user_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "file_id": file_id,
            "status": file.status.value,
            "message": {
                FileStatus.PENDING.value: "等待解析",
                FileStatus.PARSING.value: "正在解析",
                FileStatus.PARSED.value: "解析完成",
                FileStatus.PARSE_FAILED.value: "解析失败"
            }.get(file.status.value, "未知状态")
        }
    finally:
        db.close()

@router.get("/files/{file_id}/export")
def export_content(
    file_id: int,
    format: str = Query('markdown', description="导出格式：markdown 或 markdown_page"),
    user_id: str = Depends(get_user_id)
):
    """导出文件内容
    
    Args:
        file_id: 文件ID
        format: 导出格式，支持 markdown 和 markdown_page
        user_id: 用户ID
        
    Returns:
        dict: 包含下载URL的响应
    """
    db = SessionLocal()
    try:
        # 检查文件是否存在
        file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == user_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 使用默认的markdown bucket
        mds_bucket = "mds"  # 默认markdown文件存储的bucket
        print(f"Using bucket: {mds_bucket}")
        
        # 构建文件名
        file_name = Path(file.minio_path).stem
        if format == 'markdown_page':
            file_name = f"{file_name}_pages"
        output_path = f"{file_name}.md"
        
        # 检查文件是否存在于 MinIO
        try:
            minio_client.stat_object(mds_bucket, output_path)
        except Exception:
            raise HTTPException(status_code=404, detail="导出文件不存在")
        
        # 生成下载URL
        from datetime import timedelta
        download_url = minio_client.presigned_get_object(
            mds_bucket,
            output_path,
            expires=timedelta(hours=1)  # URL 有效期1小时
        )
        
        # 构建下载文件名
        original_filename = Path(file.filename).stem
        if format == 'markdown_page':
            download_filename = f"{original_filename}_pages.md"
        else:
            download_filename = f"{original_filename}.md"
        
        return {
            "status": "success",
            "download_url": download_url,
            "filename": download_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close() 