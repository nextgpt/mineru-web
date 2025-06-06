import os
from typing import List, Dict, Any, Union, Tuple
import sys
import json
import re
import tempfile
from io import StringIO
from pathlib import Path
from loguru import logger

# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# sys.path.append(PROJECT_ROOT)

from app.utils.minio_client import minio_client, MINIO_BUCKET
from app.models.parsed_content import ParsedContent
from app.models.file import File as FileModel, FileStatus
from sqlalchemy.orm import Session

from magic_pdf.data.read_api import read_local_images, read_local_office
import magic_pdf.model as model_config
from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.data_reader_writer import DataWriter
from magic_pdf.data.data_reader_writer.s3 import S3DataWriter
from magic_pdf.data.dataset import ImageDataset, PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.operators.models import InferenceResult
from magic_pdf.operators.pipes import PipeResult
from magic_pdf.libs.config_reader import get_bucket_name, get_s3_config, read_config
from magic_pdf.dict2md.ocr_mkcontent import ocr_mk_markdown_with_para_core_v2
from magic_pdf.config.make_content_config import DropMode
from app.models.settings import Settings
from app.utils.redis_client import redis_client

# 设置使用内置模型
model_config.__use_inside_model__ = True

# 支持的文件扩展名
PDF_EXTENSIONS = [".pdf"]
OFFICE_EXTENSIONS = [".ppt", ".pptx", ".doc", ".docx"]
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

# Redis 频道名称
PARSER_CHANNEL = "file_parser_tasks"
PARSER_STREAM = "file_parser_stream"  # 统一使用这个名称
CONSUMER_GROUP = "parser_workers"


class MemoryDataWriter(DataWriter):
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
    # 获取S3配置
    _, _, endpoint = get_s3_config(bucket)

    # 直接使用endpoint和image_path构建URL
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
        print(image_path, '---')
        return f'![]({get_s3_image_url(image_path, bucket)})'
    
    # 应用替换
    return re.sub(pattern, replace_url, markdown_content)

def get_buckets() -> list[str]:
    """获取默认bucket"""
    config = read_config()
    bucket_info = config.get('bucket_info', {})
    if not bucket_info:
        raise Exception('未找到bucket配置信息')
    # 默认[images, mds],分别存储图片和解析后的markdown文件
    return list(bucket_info.keys())

class ParserService:
    def __init__(self, db: Session):
        self.db = db
        self.drop_mode = DropMode.NONE  # 默认使用 NONE 模式

    def convert_middle_json_to_markdown(self, middle_json: Dict[str, Any], keep_page: bool = True) -> str:
        """将 middle_json 转换为 markdown 格式
        
        Args:
            middle_json: 中间 JSON 数据
            keep_page: 是否保留页码信息
            
        Returns:
            str: 转换后的 markdown 内容
        """
        pdf_info_list = middle_json.get('pdf_info', [])
        output_content = []
        
        for page_info in pdf_info_list:
            drop_reason_flag = False
            drop_reason = None
            if page_info.get('need_drop', False):
                drop_reason = page_info.get('drop_reason')
                if self.drop_mode == DropMode.NONE:
                    pass
                elif self.drop_mode == DropMode.NONE_WITH_REASON:
                    drop_reason_flag = True
                elif self.drop_mode == DropMode.WHOLE_PDF:
                    raise Exception((f'drop_mode is {DropMode.WHOLE_PDF} ,'
                                    f'drop_reason is {drop_reason}'))
                elif self.drop_mode == DropMode.SINGLE_PAGE:
                    logger.warning((f'drop_mode is {DropMode.SINGLE_PAGE} ,'
                                    f'drop_reason is {drop_reason}'))
                    continue
                else:
                    raise Exception('drop_mode can not be null')

            paras_of_layout = page_info.get('para_blocks')
            page_idx = page_info.get('page_idx')
            if not paras_of_layout:
                continue
                
            page_markdown = ocr_mk_markdown_with_para_core_v2(
                paras_of_layout, 'mm', 'images')
            if keep_page:
                output_content.append(f"{{{page_idx}}}{'-'*48}")
            output_content.extend(page_markdown)

        return '\n\n'.join(output_content)

    def process_file(
        self,
        file_bytes: bytes,
        file_extension: str,
        parse_method: str,
        lang: str,
        formula_enable: bool,
        table_enable: bool,
        image_writer: DataWriter
    ) -> Tuple[InferenceResult, PipeResult]:
        """处理文件内容"""
        ds: Union[PymuDocDataset, ImageDataset] = None
        
        # 根据文件类型创建数据集
        if file_extension in PDF_EXTENSIONS:
            ds = PymuDocDataset(file_bytes, lang=lang)
        elif file_extension in OFFICE_EXTENSIONS:
            # Office 文件需要先保存到临时目录
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"temp_file{file_extension}")
            with open(temp_file, "wb") as f:
                f.write(file_bytes)
            ds = read_local_office(temp_dir)[0]
        elif file_extension in IMAGE_EXTENSIONS:
            # 图片文件需要先保存到临时目录
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"temp_file{file_extension}")
            with open(temp_file, "wb") as f:
                f.write(file_bytes)
            ds = read_local_images(temp_dir)[0]
        else:
            raise ValueError(f"不支持的文件类型: {file_extension}")

        # 执行解析
        if parse_method == "ocr":
            infer_result = ds.apply(doc_analyze, ocr=True, lang=ds._lang, formula_enable=formula_enable, table_enable=table_enable)
            pipe_result = infer_result.pipe_ocr_mode(image_writer, lang=ds._lang)
        elif parse_method == "txt":
            infer_result = ds.apply(doc_analyze, ocr=False, lang=ds._lang, formula_enable=formula_enable, table_enable=table_enable)
            pipe_result = infer_result.pipe_txt_mode(image_writer, lang=ds._lang)
        else:  # auto
            if ds.classify() == SupportedPdfParseMethod.OCR:
                infer_result = ds.apply(doc_analyze, ocr=True, lang=ds._lang, formula_enable=formula_enable, table_enable=table_enable)
                pipe_result = infer_result.pipe_ocr_mode(image_writer, lang=ds._lang)
            else:
                infer_result = ds.apply(doc_analyze, ocr=False, lang=ds._lang, formula_enable=formula_enable, table_enable=table_enable)
                pipe_result = infer_result.pipe_txt_mode(image_writer, lang=ds._lang)

        return infer_result, pipe_result

    def parse_file(self, file: FileModel, user_id: str, parse_method: str = "auto") -> Dict[str, Any]:
        """同步解析文件"""
        try:
            # 获取用户设置，如果没有则使用默认配置
            user_settings = self.db.query(Settings).filter(Settings.user_id == user_id).first()
            if not user_settings:
                user_settings = Settings(
                    user_id=user_id,
                    force_ocr=False,
                    ocr_lang='auto',
                    formula_recognition=True,
                    table_recognition=True
                )
            settings = user_settings.to_dict()
            print(settings)
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
            print(file_name)
            file_name_stem = Path(file_name).stem
            # 获取默认bucket配置
            buckets = get_buckets()
            mds_bucket = buckets[0]
            if not minio_client.bucket_exists(mds_bucket):
                minio_client.make_bucket(mds_bucket)
            ak, sk, endpoint = get_s3_config(mds_bucket)

            # 创建S3写入器用于图片
            image_writer = S3DataWriter(
                "images",  # 图片存储在images目录下
                bucket=mds_bucket,
                ak=ak,
                sk=sk,
                endpoint_url=endpoint
            )
            
            # 创建内存写入器用于其他内容
            content_list_writer = MemoryDataWriter()
            md_content_writer = MemoryDataWriter()
            md_content_writer_s3 = S3DataWriter(
                "",
                bucket=mds_bucket,
                ak=ak,
                sk=sk,
                endpoint_url=endpoint
            )
            middle_json_writer = MemoryDataWriter()
            
            try:
                # 处理文件
                infer_result, pipe_result = self.process_file(
                    file_bytes, 
                    file_extension, 
                    parse_method,
                    settings.get('ocr_lang', 'auto'),
                    settings.get('formula_recognition', True),
                    settings.get('table_recognition', True),
                    image_writer
                )

                # 导出各种格式的结果
                pipe_result.dump_content_list(content_list_writer, "", "images")
                pipe_result.dump_md(md_content_writer, "", "images")
                pipe_result.dump_middle_json(middle_json_writer, "")

                # 解析结果
                content_list = json.loads(content_list_writer.get_value())
                md_content = md_content_writer.get_value()
                middle_json = json.loads(middle_json_writer.get_value())
                model_json = infer_result.get_infer_res()


                # 使用新的转换函数生成 markdown
                md_content = modify_markdown_image_urls(md_content, mds_bucket)
                md_content_with_pages = self.convert_middle_json_to_markdown(middle_json, keep_page=True)
                md_content_with_pages = modify_markdown_image_urls(md_content_with_pages, mds_bucket)

                print(md_content_with_pages, '---')
                md_content_writer_s3.write_string(f"{file_name_stem}.md", md_content)
                md_content_writer_s3.write_string(f"{file_name_stem}_pages.md", md_content_with_pages)
                # 保存解析结果到数据库
                parsed_content = ParsedContent(
                    user_id=user_id,
                    file_id=file.id,
                    content=md_content
                )
                self.db.add(parsed_content)
                    
                
                # 更新文件状态为已解析
                file.status = FileStatus.PARSED
                self.db.commit()
                
                return {
                    "status": "success"
                }
            
            finally:
                # 清理内存写入器
                content_list_writer.close()
                middle_json_writer.close()
                md_content_writer.close()
            
        except Exception as e:
            # 发生错误时回滚并更新状态
            self.db.rollback()
            file.status = FileStatus.PARSE_FAILED
            self.db.commit()
            raise Exception(f"解析失败: {str(e)}")

    def get_parsed_content(self, file_id: int, user_id: str) -> List[Dict[str, Any]]:
        """获取已解析的内容"""
        query = self.db.query(ParsedContent).filter(
            ParsedContent.file_id == file_id,
            ParsedContent.user_id == user_id
        )
            
        content = query.first()
        
        return content.content if content else ""

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

if __name__ == "__main__":
    with open('/Users/lpdswing/projects/mineru-web/backend/tests/test.pdf', 'rb') as f:
        pdf_data = f.read()
    ds = PymuDocDataset(pdf_data)
