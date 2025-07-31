"""
招标项目存储服务
基于MinIO的招标项目数据存储管理
"""
import json
import io
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
from app.models.tender import (
    TenderProject,
    ProjectMetadata,
    AnalysisResult,
    OutlineStructure,
    ChapterContent,
    DocumentInfo
)
from app.utils.minio_client import minio_client as default_minio_client, MINIO_BUCKET

logger = logging.getLogger(__name__)


class TenderStorageService:
    """基于MinIO的招标项目存储服务"""
    
    def __init__(self, minio_client: Minio = None, bucket_name: str = None):
        self.minio_client = minio_client or default_minio_client
        self.bucket_name = bucket_name or MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"创建MinIO存储桶: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"创建存储桶失败: {str(e)}")
            raise
    
    def get_project_path(self, tenant_id: str, project_id: str) -> str:
        """获取项目存储路径"""
        return f"tenants/{tenant_id}/projects/{project_id}"
    
    async def save_project_metadata(self, project: TenderProject, metadata: ProjectMetadata):
        """保存项目元数据"""
        path = f"{project.get_storage_path()}/metadata.json"
        await self._save_json(path, metadata.dict())
        logger.info(f"保存项目元数据: {path}")
    
    async def load_project_metadata(self, project: TenderProject) -> ProjectMetadata:
        """加载项目元数据"""
        path = f"{project.get_storage_path()}/metadata.json"
        data = await self._load_json(path)
        return ProjectMetadata(**data)
    
    async def save_analysis_result(self, project: TenderProject, analysis: AnalysisResult):
        """保存分析结果"""
        path = f"{project.get_storage_path()}/analysis.json"
        await self._save_json(path, analysis.dict())
        logger.info(f"保存分析结果: {path}")
    
    async def load_analysis_result(self, project: TenderProject) -> AnalysisResult:
        """加载分析结果"""
        path = f"{project.get_storage_path()}/analysis.json"
        data = await self._load_json(path)
        
        # 验证数据完整性
        self._validate_analysis_data(data)
        
        return AnalysisResult(**data)
    
    async def save_outline(self, project: TenderProject, outline: OutlineStructure):
        """保存大纲结构"""
        path = f"{project.get_storage_path()}/outline.json"
        await self._save_json(path, outline.model_dump())
        logger.info(f"保存大纲结构: {path}")
    
    async def load_outline(self, project: TenderProject) -> OutlineStructure:
        """加载大纲结构"""
        path = f"{project.get_storage_path()}/outline.json"
        data = await self._load_json(path)
        return OutlineStructure(**data)
    
    async def save_chapter_content(self, project: TenderProject, chapter: ChapterContent):
        """保存章节内容"""
        path = f"{project.get_storage_path()}/content/chapter_{chapter.chapter_id}.json"
        await self._save_json(path, chapter.dict())
        logger.info(f"保存章节内容: {path}")
    
    async def load_chapter_content(self, project: TenderProject, chapter_id: str) -> ChapterContent:
        """加载章节内容"""
        path = f"{project.get_storage_path()}/content/chapter_{chapter_id}.json"
        data = await self._load_json(path)
        return ChapterContent(**data)
    
    async def load_all_chapters(self, project: TenderProject) -> List[ChapterContent]:
        """加载所有章节内容"""
        content_path = f"{project.get_storage_path()}/content/"
        chapters = []
        
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name, 
                prefix=content_path,
                recursive=True
            )
            
            for obj in objects:
                if obj.object_name.endswith('.json') and 'chapter_' in obj.object_name:
                    try:
                        data = await self._load_json(obj.object_name)
                        chapters.append(ChapterContent(**data))
                    except Exception as e:
                        logger.warning(f"加载章节内容失败 {obj.object_name}: {str(e)}")
                        continue
            
            # 按章节ID排序
            chapters.sort(key=lambda x: x.chapter_id)
            return chapters
            
        except S3Error as e:
            logger.error(f"加载章节内容列表失败: {str(e)}")
            return []
    
    async def save_document(self, project: TenderProject, document_type: str, content: bytes, filename: str = None) -> str:
        """保存生成的文档"""
        if not filename:
            filename = f"final.{document_type.lower()}"
        
        path = f"{project.get_storage_path()}/documents/{filename}"
        
        try:
            self.minio_client.put_object(
                self.bucket_name,
                path,
                io.BytesIO(content),
                len(content),
                content_type=self._get_content_type(document_type)
            )
            logger.info(f"保存文档: {path}")
            return path
        except S3Error as e:
            logger.error(f"保存文档失败: {str(e)}")
            raise
    
    async def get_document_download_url(self, document_path: str, expires: int = 3600) -> str:
        """获取文档下载链接"""
        try:
            return self.minio_client.presigned_get_object(
                self.bucket_name,
                document_path,
                expires=timedelta(seconds=expires)
            )
        except S3Error as e:
            logger.error(f"生成下载链接失败: {str(e)}")
            raise
    
    async def list_project_documents(self, project: TenderProject) -> List[DocumentInfo]:
        """列出项目的所有文档"""
        documents_path = f"{project.get_storage_path()}/documents/"
        documents = []
        
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name,
                prefix=documents_path,
                recursive=True
            )
            
            for obj in objects:
                if not obj.object_name.endswith('/'):  # 排除目录
                    filename = obj.object_name.split('/')[-1]
                    document_type = filename.split('.')[-1].lower()
                    
                    document_info = DocumentInfo(
                        document_id=obj.etag,
                        document_type=document_type,
                        filename=filename,
                        file_size=obj.size,
                        minio_path=obj.object_name,
                        created_at=obj.last_modified
                    )
                    documents.append(document_info)
            
            return documents
            
        except S3Error as e:
            logger.error(f"列出项目文档失败: {str(e)}")
            return []
    
    async def delete_project_data(self, project: TenderProject):
        """删除项目的所有数据"""
        project_path = f"{project.get_storage_path()}/"
        
        try:
            # 列出项目下的所有对象
            objects = self.minio_client.list_objects(
                self.bucket_name,
                prefix=project_path,
                recursive=True
            )
            
            # 删除所有对象
            object_names = [obj.object_name for obj in objects]
            if object_names:
                errors = self.minio_client.remove_objects(
                    self.bucket_name,
                    object_names
                )
                
                # 检查删除错误
                for error in errors:
                    logger.error(f"删除对象失败: {error}")
            
            logger.info(f"删除项目数据: {project_path}")
            
        except S3Error as e:
            logger.error(f"删除项目数据失败: {str(e)}")
            raise
    
    async def check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        try:
            self.minio_client.stat_object(self.bucket_name, file_path)
            return True
        except S3Error:
            return False
    
    async def _save_json(self, path: str, data: dict):
        """保存JSON数据到MinIO"""
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2, default=self._json_serializer)
            json_bytes = json_str.encode('utf-8')
            
            self.minio_client.put_object(
                self.bucket_name,
                path,
                io.BytesIO(json_bytes),
                len(json_bytes),
                content_type='application/json'
            )
        except S3Error as e:
            logger.error(f"保存JSON数据失败 {path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"序列化JSON数据失败 {path}: {str(e)}")
            raise
    
    async def _load_json(self, path: str) -> dict:
        """从MinIO加载JSON数据"""
        try:
            response = self.minio_client.get_object(self.bucket_name, path)
            content = response.read().decode('utf-8')
            return json.loads(content)
        except S3Error as e:
            logger.error(f"加载JSON数据失败 {path}: {str(e)}")
            raise FileNotFoundError(f"无法加载文件 {path}: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON数据失败 {path}: {str(e)}")
            raise ValueError(f"JSON格式错误 {path}: {str(e)}")
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    def _json_serializer(self, obj):
        """JSON序列化器，处理特殊类型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _get_content_type(self, document_type: str) -> str:
        """根据文档类型获取Content-Type"""
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain',
            'json': 'application/json'
        }
        return content_types.get(document_type.lower(), 'application/octet-stream')
    
    def _validate_analysis_data(self, data: Dict[str, Any]) -> None:
        """
        验证分析结果数据完整性
        
        Args:
            data: 分析结果数据
            
        Raises:
            ValueError: 数据验证失败
        """
        required_fields = [
            'project_info', 'technical_requirements', 
            'evaluation_criteria', 'submission_requirements', 'extracted_at'
        ]
        
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                raise ValueError(f"分析结果缺少必需字段: {field}")
        
        # 验证字段类型
        if not isinstance(data['project_info'], dict):
            raise ValueError("project_info 必须是字典类型")
        
        if not isinstance(data['technical_requirements'], dict):
            raise ValueError("technical_requirements 必须是字典类型")
        
        if not isinstance(data['evaluation_criteria'], dict):
            raise ValueError("evaluation_criteria 必须是字典类型")
        
        if not isinstance(data['submission_requirements'], dict):
            raise ValueError("submission_requirements 必须是字典类型")
        
        # 验证时间戳格式
        try:
            extracted_at = data['extracted_at']
            if isinstance(extracted_at, datetime):
                # 如果已经是datetime对象，直接通过验证
                pass
            elif isinstance(extracted_at, str):
                # 如果是字符串，尝试解析
                datetime.fromisoformat(extracted_at.replace('Z', '+00:00'))
            else:
                raise ValueError("extracted_at 必须是datetime对象或ISO格式字符串")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"extracted_at 时间格式无效: {str(e)}")
        
        logger.debug("分析结果数据验证通过")
    
    async def update_analysis_result_field(
        self, 
        project: TenderProject, 
        field_name: str, 
        field_value: Any
    ) -> AnalysisResult:
        """
        更新分析结果的特定字段
        
        Args:
            project: 项目对象
            field_name: 字段名称
            field_value: 字段值
            
        Returns:
            AnalysisResult: 更新后的分析结果
        """
        try:
            # 加载现有分析结果
            analysis = await self.load_analysis_result(project)
        except FileNotFoundError:
            # 如果文件不存在，创建新的分析结果
            analysis = AnalysisResult(
                project_info={},
                technical_requirements={},
                evaluation_criteria={},
                submission_requirements={},
                extracted_at=datetime.utcnow()
            )
        
        # 更新指定字段
        if hasattr(analysis, field_name):
            setattr(analysis, field_name, field_value)
        else:
            raise ValueError(f"无效的字段名称: {field_name}")
        
        # 保存更新后的结果
        await self.save_analysis_result(project, analysis)
        
        logger.info(f"更新分析结果字段 {field_name}，项目ID: {project.id}")
        return analysis
    
    async def get_analysis_result_summary(self, project: TenderProject) -> Dict[str, Any]:
        """
        获取分析结果摘要信息
        
        Args:
            project: 项目对象
            
        Returns:
            Dict: 分析结果摘要
        """
        try:
            analysis = await self.load_analysis_result(project)
            
            # 统计各部分的信息数量
            project_info_count = len(analysis.project_info) if analysis.project_info else 0
            tech_req_count = sum(
                len(v) if isinstance(v, (list, dict)) else 1 
                for v in analysis.technical_requirements.values()
            ) if analysis.technical_requirements else 0
            eval_criteria_count = len(analysis.evaluation_criteria) if analysis.evaluation_criteria else 0
            submission_req_count = len(analysis.submission_requirements) if analysis.submission_requirements else 0
            
            return {
                'project_id': project.id,
                'extracted_at': analysis.extracted_at,
                'project_info_fields': project_info_count,
                'technical_requirements_items': tech_req_count,
                'evaluation_criteria_fields': eval_criteria_count,
                'submission_requirements_fields': submission_req_count,
                'total_fields': project_info_count + tech_req_count + eval_criteria_count + submission_req_count,
                'has_complete_data': all([
                    analysis.project_info,
                    analysis.technical_requirements,
                    analysis.evaluation_criteria,
                    analysis.submission_requirements
                ])
            }
            
        except FileNotFoundError:
            return {
                'project_id': project.id,
                'extracted_at': None,
                'project_info_fields': 0,
                'technical_requirements_items': 0,
                'evaluation_criteria_fields': 0,
                'submission_requirements_fields': 0,
                'total_fields': 0,
                'has_complete_data': False
            }
    
    async def backup_analysis_result(self, project: TenderProject, backup_suffix: str = None) -> str:
        """
        备份分析结果
        
        Args:
            project: 项目对象
            backup_suffix: 备份后缀，默认使用时间戳
            
        Returns:
            str: 备份文件路径
        """
        if backup_suffix is None:
            backup_suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 原始文件路径
        original_path = f"{project.get_storage_path()}/analysis.json"
        
        # 备份文件路径
        backup_path = f"{project.get_storage_path()}/backups/analysis_{backup_suffix}.json"
        
        try:
            # 检查原始文件是否存在
            if not await self.check_file_exists(original_path):
                raise FileNotFoundError(f"原始分析结果文件不存在: {original_path}")
            
            # 读取原始文件内容
            original_data = await self._load_json(original_path)
            
            # 保存备份文件
            await self._save_json(backup_path, original_data)
            
            logger.info(f"分析结果备份完成: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"备份分析结果失败: {str(e)}")
            raise
    
    async def restore_analysis_result(self, project: TenderProject, backup_path: str) -> AnalysisResult:
        """
        从备份恢复分析结果
        
        Args:
            project: 项目对象
            backup_path: 备份文件路径
            
        Returns:
            AnalysisResult: 恢复的分析结果
        """
        try:
            # 检查备份文件是否存在
            if not await self.check_file_exists(backup_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            # 读取备份文件内容
            backup_data = await self._load_json(backup_path)
            
            # 验证数据完整性
            self._validate_analysis_data(backup_data)
            
            # 创建分析结果对象
            analysis = AnalysisResult(**backup_data)
            
            # 保存为当前分析结果
            await self.save_analysis_result(project, analysis)
            
            logger.info(f"分析结果恢复完成，从备份: {backup_path}")
            return analysis
            
        except Exception as e:
            logger.error(f"恢复分析结果失败: {str(e)}")
            raise
    
    async def list_analysis_backups(self, project: TenderProject) -> List[Dict[str, Any]]:
        """
        列出项目的分析结果备份
        
        Args:
            project: 项目对象
            
        Returns:
            List[Dict]: 备份文件列表
        """
        backups_path = f"{project.get_storage_path()}/backups/"
        backups = []
        
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name,
                prefix=backups_path,
                recursive=True
            )
            
            for obj in objects:
                if obj.object_name.endswith('.json') and 'analysis_' in obj.object_name:
                    filename = obj.object_name.split('/')[-1]
                    backup_info = {
                        'filename': filename,
                        'path': obj.object_name,
                        'size': obj.size,
                        'created_at': obj.last_modified,
                        'backup_suffix': filename.replace('analysis_', '').replace('.json', '')
                    }
                    backups.append(backup_info)
            
            # 按创建时间倒序排列
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
            
        except S3Error as e:
            logger.error(f"列出分析结果备份失败: {str(e)}")
            return []
    
    async def delete_analysis_result(self, project: TenderProject) -> bool:
        """
        删除分析结果
        
        Args:
            project: 项目对象
            
        Returns:
            bool: 删除是否成功
        """
        analysis_path = f"{project.get_storage_path()}/analysis.json"
        
        try:
            # 检查文件是否存在
            if not await self.check_file_exists(analysis_path):
                logger.warning(f"分析结果文件不存在: {analysis_path}")
                return True  # 文件不存在视为删除成功
            
            # 删除文件
            self.minio_client.remove_object(self.bucket_name, analysis_path)
            
            logger.info(f"分析结果删除完成: {analysis_path}")
            return True
            
        except S3Error as e:
            logger.error(f"删除分析结果失败: {str(e)}")
            return False
    
    # 大纲版本管理功能
    
    async def backup_outline(self, project: TenderProject, backup_suffix: str = None) -> str:
        """
        备份大纲结构
        
        Args:
            project: 项目对象
            backup_suffix: 备份后缀，默认使用时间戳
            
        Returns:
            str: 备份文件路径
        """
        if backup_suffix is None:
            backup_suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 原始文件路径
        original_path = f"{project.get_storage_path()}/outline.json"
        
        # 备份文件路径
        backup_path = f"{project.get_storage_path()}/backups/outline_{backup_suffix}.json"
        
        try:
            # 检查原始文件是否存在
            if not await self.check_file_exists(original_path):
                raise FileNotFoundError(f"原始大纲文件不存在: {original_path}")
            
            # 读取原始文件内容
            original_data = await self._load_json(original_path)
            
            # 保存备份文件
            await self._save_json(backup_path, original_data)
            
            logger.info(f"大纲备份完成: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"备份大纲失败: {str(e)}")
            raise
    
    async def restore_outline(self, project: TenderProject, backup_path: str) -> OutlineStructure:
        """
        从备份恢复大纲结构
        
        Args:
            project: 项目对象
            backup_path: 备份文件路径
            
        Returns:
            OutlineStructure: 恢复的大纲结构
        """
        try:
            # 检查备份文件是否存在
            if not await self.check_file_exists(backup_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            # 读取备份文件内容
            backup_data = await self._load_json(backup_path)
            
            # 验证数据完整性
            self._validate_outline_data(backup_data)
            
            # 创建大纲结构对象
            outline = OutlineStructure(**backup_data)
            
            # 保存为当前大纲
            await self.save_outline(project, outline)
            
            logger.info(f"大纲恢复完成，从备份: {backup_path}")
            return outline
            
        except Exception as e:
            logger.error(f"恢复大纲失败: {str(e)}")
            raise
    
    async def list_outline_backups(self, project: TenderProject) -> List[Dict[str, Any]]:
        """
        列出项目的大纲备份
        
        Args:
            project: 项目对象
            
        Returns:
            List[Dict]: 备份文件列表
        """
        backups_path = f"{project.get_storage_path()}/backups/"
        backups = []
        
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name,
                prefix=backups_path,
                recursive=True
            )
            
            for obj in objects:
                if obj.object_name.endswith('.json') and 'outline_' in obj.object_name:
                    filename = obj.object_name.split('/')[-1]
                    backup_info = {
                        'filename': filename,
                        'path': obj.object_name,
                        'size': obj.size,
                        'created_at': obj.last_modified,
                        'backup_suffix': filename.replace('outline_', '').replace('.json', '')
                    }
                    backups.append(backup_info)
            
            # 按创建时间倒序排列
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
            
        except S3Error as e:
            logger.error(f"列出大纲备份失败: {str(e)}")
            return []
    
    async def delete_outline(self, project: TenderProject) -> bool:
        """
        删除大纲结构
        
        Args:
            project: 项目对象
            
        Returns:
            bool: 删除是否成功
        """
        outline_path = f"{project.get_storage_path()}/outline.json"
        
        try:
            # 检查文件是否存在
            if not await self.check_file_exists(outline_path):
                logger.warning(f"大纲文件不存在: {outline_path}")
                return True  # 文件不存在视为删除成功
            
            # 删除文件
            self.minio_client.remove_object(self.bucket_name, outline_path)
            
            logger.info(f"大纲删除完成: {outline_path}")
            return True
            
        except S3Error as e:
            logger.error(f"删除大纲失败: {str(e)}")
            return False
    
    async def update_outline_field(
        self, 
        project: TenderProject, 
        field_name: str, 
        field_value: Any
    ) -> OutlineStructure:
        """
        更新大纲的特定字段
        
        Args:
            project: 项目对象
            field_name: 字段名称
            field_value: 字段值
            
        Returns:
            OutlineStructure: 更新后的大纲结构
        """
        try:
            # 加载现有大纲
            outline = await self.load_outline(project)
        except FileNotFoundError:
            # 如果文件不存在，创建新的大纲结构
            outline = OutlineStructure(
                chapters=[],
                chapter_count=0,
                generated_at=datetime.utcnow()
            )
        
        # 更新指定字段
        if hasattr(outline, field_name):
            setattr(outline, field_name, field_value)
        else:
            raise ValueError(f"无效的字段名称: {field_name}")
        
        # 保存更新后的结果
        await self.save_outline(project, outline)
        
        logger.info(f"更新大纲字段 {field_name}，项目ID: {project.id}")
        return outline
    
    async def get_outline_summary(self, project: TenderProject) -> Dict[str, Any]:
        """
        获取大纲摘要信息
        
        Args:
            project: 项目对象
            
        Returns:
            Dict: 大纲摘要
        """
        try:
            outline = await self.load_outline(project)
            
            # 统计大纲信息
            total_subsections = sum(len(chapter.subsections) for chapter in outline.chapters)
            avg_subsections = total_subsections / outline.chapter_count if outline.chapter_count > 0 else 0
            
            return {
                'project_id': project.id,
                'generated_at': outline.generated_at,
                'chapter_count': outline.chapter_count,
                'total_subsections': total_subsections,
                'avg_subsections_per_chapter': avg_subsections,
                'has_outline': outline.chapter_count > 0,
                'chapter_titles': [chapter.title for chapter in outline.chapters]
            }
            
        except FileNotFoundError:
            return {
                'project_id': project.id,
                'generated_at': None,
                'chapter_count': 0,
                'total_subsections': 0,
                'avg_subsections_per_chapter': 0,
                'has_outline': False,
                'chapter_titles': []
            }
    
    def _validate_outline_data(self, data: Dict[str, Any]) -> None:
        """
        验证大纲数据完整性
        
        Args:
            data: 大纲数据
            
        Raises:
            ValueError: 数据验证失败
        """
        required_fields = ['chapters', 'chapter_count', 'generated_at']
        
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                raise ValueError(f"大纲数据缺少必需字段: {field}")
        
        # 验证字段类型
        if not isinstance(data['chapters'], list):
            raise ValueError("chapters 必须是列表类型")
        
        if not isinstance(data['chapter_count'], int):
            raise ValueError("chapter_count 必须是整数类型")
        
        # 验证章节数据
        for i, chapter in enumerate(data['chapters']):
            if not isinstance(chapter, dict):
                raise ValueError(f"第{i+1}个章节必须是字典类型")
            
            required_chapter_fields = ['chapter_id', 'title', 'description', 'subsections']
            for field in required_chapter_fields:
                if field not in chapter:
                    raise ValueError(f"第{i+1}个章节缺少必需字段: {field}")
            
            if not isinstance(chapter['subsections'], list):
                raise ValueError(f"第{i+1}个章节的subsections必须是列表类型")
        
        # 验证时间戳格式
        try:
            generated_at = data['generated_at']
            if isinstance(generated_at, datetime):
                # 如果已经是datetime对象，直接通过验证
                pass
            elif isinstance(generated_at, str):
                # 如果是字符串，尝试解析
                datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            else:
                raise ValueError("generated_at 必须是datetime对象或ISO格式字符串")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"generated_at 时间格式无效: {str(e)}")
        
        logger.debug("大纲数据验证通过")


# 全局存储服务实例将在需要时创建
def get_tender_storage_service() -> TenderStorageService:
    """获取招标存储服务实例"""
    return TenderStorageService()