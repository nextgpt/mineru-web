"""
文档解析服务
使用已部署的MinerU API服务进行文档解析
"""
import os
from typing import List, Dict, Any, Union, Tuple
import sys
import json
import re
import copy
from io import StringIO
from pathlib import Path
from loguru import logger

from app.utils.minio_client import minio_client, MINIO_BUCKET
from app.models.parsed_content import ParsedContent
from app.models.file import File as FileModel, FileStatus
from sqlalchemy.orm import Session
from app.models.settings import Settings
from app.utils.redis_client import redis_client
from app.services.mineru_client import MinerUClient, mineru_client

# 支持的文件扩展名
PDF_EXTENSIONS = [".pdf"]
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

# Redis 频道名称
PARSER_CHANNEL = "file_parser_tasks"
PARSER_STREAM = "file_parser_stream"  # 统一使用这个名称
CONSUMER_GROUP = "parser_workers"

SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:30000")


class MemoryDataWriter:
    """内存数据写入器，用于临时存储解析结果"""

    def __init__(self):
        self.buffer = StringIO()

    def write(self, path: str, data: bytes) -> None:
        if isinstance(data, str):
            self.buffer.write(data)
        else:
            self.buffer.write(data.decode("utf-8"))

    def write_string(self, path: str, data: str) -> None:
        self.buffer.write(data)

    def get_value(self) -> str:
        return self.buffer.getvalue()

    def close(self):
        self.buffer.close()


def get_s3_image_url(image_path: str, bucket: str) -> str:
    """Get HTTP accessible image URL from S3"""
    # 这里需要根据您的MinIO配置来构建URL
    # 假设MinIO服务运行在192.168.30.54:9000
    endpoint = "http://192.168.30.54:9000"
    return f"{endpoint}/{bucket}/{image_path}"


def modify_markdown_image_urls(markdown_content: str, bucket: str) -> str:
    """修改Markdown内容中的图片URL为S3 HTTP URL"""
    # 匹配Markdown中的图片标签
    pattern = r'\!\[(?:[^\]]*)\]\(([^)]+)\)'

    def replace_url(match):
        image_path = match.group(1)
        # 如果已经是完整的URL，则跳过
        if image_path.startswith(('http://', 'https://')):
            return match.group(0)
        # 否则转换为S3 URL
        return f'![]({get_s3_image_url(image_path, bucket)})'

    # 应用替换
    return re.sub(pattern, replace_url, markdown_content)


class ParserService:
    def __init__(self, db: Session):
        self.db = db
        self.mineru_client = MinerUClient()

    def parse_file(self, file: FileModel, user_id: str, parse_method: str = "auto") -> Dict[str, Any]:
        """使用MinerU API解析文件"""
        try:
            # 获取用户设置，如果没有则使用默认配置
            user_settings = self.db.query(Settings).filter(Settings.user_id == user_id).first()
            if not user_settings:
                user_settings = Settings(
                    user_id=user_id,
                    force_ocr=False,
                    ocr_lang='ch',
                    formula_recognition=True,
                    table_recognition=True
                )
            settings = user_settings.to_dict()
            logger.info(f"User settings: {settings}")
            
            if settings.get('force_ocr', False):
                parse_method = 'ocr'
            
            # 更新文件状态为解析中
            file.status = FileStatus.PARSING
            self.db.commit()

            # 从MinIO获取文件
            response = minio_client.get_object(MINIO_BUCKET, file.minio_path)
            file_bytes = response.read()
            file_extension = Path(file.minio_path).suffix.lower()
            file_name = Path(file.minio_path).name
            
            # 检查文件类型是否支持
            if file_extension not in PDF_EXTENSIONS + IMAGE_EXTENSIONS:
                raise ValueError(f"不支持的文件类型: {file_extension}")

            # 使用MinerU API解析文档
            logger.info(f"Starting document parsing for file: {file_name}")
            
            parse_result = self.mineru_client.parse_document_sync(
                file_path=file_name,
                file_bytes=file_bytes,
                parse_method=parse_method,
                lang=settings.get('ocr_lang', 'ch'),
                formula_enable=settings.get('formula_recognition', True),
                table_enable=settings.get('table_recognition', True)
            )
            
            logger.info("Document parsing completed successfully")
            
            # 提取解析结果
            if 'content' in parse_result:
                markdown_content = parse_result['content']
            elif 'markdown' in parse_result:
                markdown_content = parse_result['markdown']
            else:
                # 如果没有找到标准字段，尝试其他可能的字段
                markdown_content = str(parse_result)
            
            # 保存解析结果到数据库
            parsed_content = ParsedContent(
                user_id=user_id,
                file_id=file.id,
                content=markdown_content
            )
            self.db.add(parsed_content)

            # 更新文件状态为已解析
            file.status = FileStatus.PARSED
            self.db.commit()

            return {
                "status": "success",
                "content": markdown_content,
                "file_id": file.id
            }

        except Exception as e:
            # 发生错误时回滚并更新状态
            self.db.rollback()
            file.status = FileStatus.PARSE_FAILED
            self.db.commit()
            logger.error(f"Document parsing failed: {str(e)}")
            raise Exception(f"解析失败: {str(e)}")

    def get_parsed_content(self, file_id: int, user_id: str):
        """获取已解析的内容"""
        query = self.db.query(ParsedContent).filter(
            ParsedContent.file_id == file_id,
            ParsedContent.user_id == user_id
        )

        content_obj = query.first()

        return content_obj.content if content_obj else ""

    def queue_parse_file(self, file: FileModel, user_id: str, parse_method: str = "auto") -> Dict[str, Any]:
        """
        将文件解析任务发布到 Redis Stream
        Args:
            file (FileModel): 文件模型实例
            user_id (str): 用户ID
            parse_method (str): 解析方法，可选值：auto, ocr, txt
        Returns:
            Dict[str, Any]: 包含任务状态的字典
        """
        try:
            # 更新文件状态为等待解析
            file.status = FileStatus.PENDING
            self.db.commit()

            # 准备任务数据
            task_data = {
                "file_id": file.id,
                "user_id": user_id,
                "parse_method": parse_method
            }

            # 发布任务到 Redis Stream
            logger.info(f"Publishing task to stream {PARSER_STREAM}: {task_data}")
            redis_client.publish_task(PARSER_STREAM, task_data)

            return {
                "status": "queued",
                "message": "File parsing task has been queued",
                "file_id": file.id
            }

        except Exception as e:
            # 发生错误时回滚并更新状态
            self.db.rollback()
            file.status = FileStatus.PARSE_FAILED
            self.db.commit()
            raise Exception(f"Failed to queue parsing task: {str(e)}")

    async def parse_file_async(self, file: FileModel, user_id: str, parse_method: str = "auto") -> Dict[str, Any]:
        """异步解析文件"""
        try:
            # 获取用户设置
            user_settings = self.db.query(Settings).filter(Settings.user_id == user_id).first()
            if not user_settings:
                user_settings = Settings(
                    user_id=user_id,
                    force_ocr=False,
                    ocr_lang='ch',
                    formula_recognition=True,
                    table_recognition=True
                )
            settings = user_settings.to_dict()
            
            if settings.get('force_ocr', False):
                parse_method = 'ocr'
            
            # 更新文件状态为解析中
            file.status = FileStatus.PARSING
            self.db.commit()

            # 从MinIO获取文件
            response = minio_client.get_object(MINIO_BUCKET, file.minio_path)
            file_bytes = response.read()
            file_name = Path(file.minio_path).name
            
            # 使用MinerU API异步解析文档
            async with MinerUClient() as client:
                parse_result = await client.parse_document_async(
                    file_path=file_name,
                    file_bytes=file_bytes,
                    parse_method=parse_method,
                    lang=settings.get('ocr_lang', 'ch'),
                    formula_enable=settings.get('formula_recognition', True),
                    table_enable=settings.get('table_recognition', True)
                )
            
            # 提取解析结果
            if 'content' in parse_result:
                markdown_content = parse_result['content']
            elif 'markdown' in parse_result:
                markdown_content = parse_result['markdown']
            else:
                markdown_content = str(parse_result)
            
            # 保存解析结果到数据库
            parsed_content = ParsedContent(
                user_id=user_id,
                file_id=file.id,
                content=markdown_content
            )
            self.db.add(parsed_content)

            # 更新文件状态为已解析
            file.status = FileStatus.PARSED
            self.db.commit()

            return {
                "status": "success",
                "content": markdown_content,
                "file_id": file.id
            }

        except Exception as e:
            # 发生错误时回滚并更新状态
            self.db.rollback()
            file.status = FileStatus.PARSE_FAILED
            self.db.commit()
            logger.error(f"Async document parsing failed: {str(e)}")
            raise Exception(f"异步解析失败: {str(e)}")


if __name__ == "__main__":
    # 测试代码
    print("ParserService module loaded successfully")
