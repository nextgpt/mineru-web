"""
文档管理服务
提供文档版本管理、访问控制和下载管理功能
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models.tender import TenderProject, DocumentInfo
from app.services.tender_storage import TenderStorageService
from app.utils.tenant_manager import TenantManager

logger = logging.getLogger(__name__)


class DocumentAccessLevel(Enum):
    """文档访问级别"""
    PRIVATE = "private"      # 仅项目创建者可访问
    TENANT = "tenant"        # 租户内可访问
    PUBLIC = "public"        # 公开访问（暂不支持）


@dataclass
class DocumentVersion:
    """文档版本信息"""
    version_id: str
    version_number: str
    document_path: str
    file_size: int
    created_at: datetime
    created_by: str
    description: str = ""
    is_current: bool = False


@dataclass
class DocumentMetadata:
    """文档元数据"""
    document_id: str
    project_id: str
    tenant_id: str
    document_type: str
    filename: str
    access_level: DocumentAccessLevel
    created_by: str
    created_at: datetime
    updated_at: datetime
    versions: List[DocumentVersion]
    download_count: int = 0
    last_downloaded_at: Optional[datetime] = None


class DocumentManagementService:
    """文档管理服务"""
    
    def __init__(self, storage_service: TenderStorageService, tenant_manager: TenantManager):
        self.storage = storage_service
        self.tenant_manager = tenant_manager
    
    async def save_document_with_version(
        self,
        project: TenderProject,
        document_content: bytes,
        filename: str,
        document_type: str,
        created_by: str,
        description: str = "",
        access_level: DocumentAccessLevel = DocumentAccessLevel.TENANT
    ) -> DocumentMetadata:
        """
        保存文档并创建版本记录
        
        Args:
            project: 项目对象
            document_content: 文档内容
            filename: 文件名
            document_type: 文档类型
            created_by: 创建者ID
            description: 版本描述
            access_level: 访问级别
            
        Returns:
            DocumentMetadata: 文档元数据
        """
        try:
            # 生成文档ID和版本ID
            document_id = str(uuid.uuid4())
            version_id = str(uuid.uuid4())
            
            # 生成版本化的文件路径
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            versioned_filename = f"{timestamp}_{version_id}_{filename}"
            document_path = await self.storage.save_document(
                project, document_type, document_content, versioned_filename
            )
            
            # 创建版本信息
            version = DocumentVersion(
                version_id=version_id,
                version_number="1.0",
                document_path=document_path,
                file_size=len(document_content),
                created_at=datetime.utcnow(),
                created_by=created_by,
                description=description,
                is_current=True
            )
            
            # 创建文档元数据
            metadata = DocumentMetadata(
                document_id=document_id,
                project_id=project.id,
                tenant_id=project.tenant_id,
                document_type=document_type,
                filename=filename,
                access_level=access_level,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                versions=[version],
                download_count=0
            )
            
            # 保存元数据
            await self._save_document_metadata(project, metadata)
            
            logger.info(f"文档保存成功: {document_id}, 项目: {project.id}")
            return metadata
            
        except Exception as e:
            logger.error(f"保存文档失败: {str(e)}")
            raise   
 
    async def add_document_version(
        self,
        project: TenderProject,
        document_id: str,
        document_content: bytes,
        created_by: str,
        description: str = ""
    ) -> DocumentVersion:
        """
        为现有文档添加新版本
        
        Args:
            project: 项目对象
            document_id: 文档ID
            document_content: 文档内容
            created_by: 创建者ID
            description: 版本描述
            
        Returns:
            DocumentVersion: 新版本信息
        """
        try:
            # 加载现有文档元数据
            metadata = await self._load_document_metadata(project, document_id)
            
            # 生成新版本ID
            version_id = str(uuid.uuid4())
            
            # 计算新版本号
            current_versions = [float(v.version_number) for v in metadata.versions]
            new_version_number = f"{max(current_versions) + 0.1:.1f}"
            
            # 生成版本化的文件路径
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            versioned_filename = f"{timestamp}_{version_id}_{metadata.filename}"
            document_path = await self.storage.save_document(
                project, metadata.document_type, document_content, versioned_filename
            )
            
            # 创建新版本
            new_version = DocumentVersion(
                version_id=version_id,
                version_number=new_version_number,
                document_path=document_path,
                file_size=len(document_content),
                created_at=datetime.utcnow(),
                created_by=created_by,
                description=description,
                is_current=True
            )
            
            # 更新现有版本状态
            for version in metadata.versions:
                version.is_current = False
            
            # 添加新版本
            metadata.versions.append(new_version)
            metadata.updated_at = datetime.utcnow()
            
            # 保存更新后的元数据
            await self._save_document_metadata(project, metadata)
            
            logger.info(f"文档版本添加成功: {document_id}, 版本: {new_version_number}")
            return new_version
            
        except Exception as e:
            logger.error(f"添加文档版本失败: {str(e)}")
            raise
    
    async def get_document_metadata(
        self,
        project: TenderProject,
        document_id: str,
        user_id: str
    ) -> Optional[DocumentMetadata]:
        """
        获取文档元数据（带权限检查）
        
        Args:
            project: 项目对象
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            DocumentMetadata: 文档元数据，如果无权限则返回None
        """
        try:
            metadata = await self._load_document_metadata(project, document_id)
            
            # 检查访问权限
            if not await self._check_document_access(metadata, user_id, project.tenant_id):
                logger.warning(f"用户 {user_id} 无权访问文档 {document_id}")
                return None
            
            return metadata
            
        except FileNotFoundError:
            logger.warning(f"文档元数据不存在: {document_id}")
            return None
        except Exception as e:
            logger.error(f"获取文档元数据失败: {str(e)}")
            raise
    
    async def list_project_documents(
        self,
        project: TenderProject,
        user_id: str,
        document_type: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """
        列出项目的所有文档（带权限过滤）
        
        Args:
            project: 项目对象
            user_id: 用户ID
            document_type: 文档类型过滤
            
        Returns:
            List[DocumentMetadata]: 文档元数据列表
        """
        try:
            # 获取项目下的所有文档元数据文件
            documents_path = f"{project.get_storage_path()}/documents_metadata/"
            documents = []
            
            try:
                objects = self.storage.minio_client.list_objects(
                    self.storage.bucket_name,
                    prefix=documents_path,
                    recursive=True
                )
                
                for obj in objects:
                    if obj.object_name.endswith('_metadata.json'):
                        try:
                            # 提取文档ID
                            filename = obj.object_name.split('/')[-1]
                            document_id = filename.replace('_metadata.json', '')
                            
                            # 加载元数据
                            metadata = await self._load_document_metadata(project, document_id)
                            
                            # 检查访问权限
                            if await self._check_document_access(metadata, user_id, project.tenant_id):
                                # 应用类型过滤
                                if document_type is None or metadata.document_type == document_type:
                                    documents.append(metadata)
                                    
                        except Exception as e:
                            logger.warning(f"加载文档元数据失败 {obj.object_name}: {str(e)}")
                            continue
                
                # 按创建时间倒序排列
                documents.sort(key=lambda x: x.created_at, reverse=True)
                return documents
                
            except Exception as e:
                logger.error(f"列出项目文档失败: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"列出项目文档失败: {str(e)}")
            return []    

    async def generate_secure_download_url(
        self,
        project: TenderProject,
        document_id: str,
        version_id: Optional[str],
        user_id: str,
        expires: int = 3600
    ) -> Optional[str]:
        """
        生成安全的文档下载链接
        
        Args:
            project: 项目对象
            document_id: 文档ID
            version_id: 版本ID，None表示当前版本
            user_id: 用户ID
            expires: 过期时间（秒）
            
        Returns:
            str: 下载链接，如果无权限则返回None
        """
        try:
            # 获取文档元数据并检查权限
            metadata = await self.get_document_metadata(project, document_id, user_id)
            if not metadata:
                return None
            
            # 找到指定版本
            target_version = None
            if version_id:
                target_version = next((v for v in metadata.versions if v.version_id == version_id), None)
            else:
                target_version = next((v for v in metadata.versions if v.is_current), None)
            
            if not target_version:
                logger.warning(f"文档版本不存在: {document_id}, 版本: {version_id}")
                return None
            
            # 生成下载链接
            download_url = await self.storage.get_document_download_url(
                target_version.document_path, expires
            )
            
            # 更新下载统计
            await self._update_download_stats(project, document_id)
            
            logger.info(f"生成下载链接: {document_id}, 用户: {user_id}")
            return download_url
            
        except Exception as e:
            logger.error(f"生成下载链接失败: {str(e)}")
            raise
    
    async def delete_document(
        self,
        project: TenderProject,
        document_id: str,
        user_id: str
    ) -> bool:
        """
        删除文档（软删除，保留元数据）
        
        Args:
            project: 项目对象
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 获取文档元数据并检查权限
            metadata = await self.get_document_metadata(project, document_id, user_id)
            if not metadata:
                return False
            
            # 检查删除权限（只有创建者或管理员可以删除）
            if metadata.created_by != user_id:
                logger.warning(f"用户 {user_id} 无权删除文档 {document_id}")
                return False
            
            # 删除所有版本的文件
            for version in metadata.versions:
                try:
                    self.storage.minio_client.remove_object(
                        self.storage.bucket_name, 
                        version.document_path
                    )
                except Exception as e:
                    logger.warning(f"删除文档文件失败 {version.document_path}: {str(e)}")
            
            # 删除元数据文件
            metadata_path = f"{project.get_storage_path()}/documents_metadata/{document_id}_metadata.json"
            try:
                self.storage.minio_client.remove_object(
                    self.storage.bucket_name, 
                    metadata_path
                )
            except Exception as e:
                logger.warning(f"删除元数据文件失败 {metadata_path}: {str(e)}")
            
            logger.info(f"文档删除成功: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    async def get_document_versions(
        self,
        project: TenderProject,
        document_id: str,
        user_id: str
    ) -> List[DocumentVersion]:
        """
        获取文档的所有版本
        
        Args:
            project: 项目对象
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            List[DocumentVersion]: 版本列表
        """
        try:
            metadata = await self.get_document_metadata(project, document_id, user_id)
            if not metadata:
                return []
            
            # 按版本号倒序排列
            versions = sorted(metadata.versions, key=lambda x: float(x.version_number), reverse=True)
            return versions
            
        except Exception as e:
            logger.error(f"获取文档版本失败: {str(e)}")
            return []
    
    async def set_current_version(
        self,
        project: TenderProject,
        document_id: str,
        version_id: str,
        user_id: str
    ) -> bool:
        """
        设置当前版本
        
        Args:
            project: 项目对象
            document_id: 文档ID
            version_id: 版本ID
            user_id: 用户ID
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 获取文档元数据并检查权限
            metadata = await self.get_document_metadata(project, document_id, user_id)
            if not metadata:
                return False
            
            # 检查编辑权限
            if metadata.created_by != user_id:
                logger.warning(f"用户 {user_id} 无权编辑文档 {document_id}")
                return False
            
            # 找到目标版本
            target_version = next((v for v in metadata.versions if v.version_id == version_id), None)
            if not target_version:
                logger.warning(f"版本不存在: {version_id}")
                return False
            
            # 更新版本状态
            for version in metadata.versions:
                version.is_current = (version.version_id == version_id)
            
            metadata.updated_at = datetime.utcnow()
            
            # 保存更新后的元数据
            await self._save_document_metadata(project, metadata)
            
            logger.info(f"设置当前版本成功: {document_id}, 版本: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"设置当前版本失败: {str(e)}")
            return False    
 
   async def _save_document_metadata(
        self,
        project: TenderProject,
        metadata: DocumentMetadata
    ):
        """保存文档元数据"""
        metadata_path = f"{project.get_storage_path()}/documents_metadata/{metadata.document_id}_metadata.json"
        
        # 转换为可序列化的字典
        metadata_dict = {
            'document_id': metadata.document_id,
            'project_id': metadata.project_id,
            'tenant_id': metadata.tenant_id,
            'document_type': metadata.document_type,
            'filename': metadata.filename,
            'access_level': metadata.access_level.value,
            'created_by': metadata.created_by,
            'created_at': metadata.created_at.isoformat(),
            'updated_at': metadata.updated_at.isoformat(),
            'download_count': metadata.download_count,
            'last_downloaded_at': metadata.last_downloaded_at.isoformat() if metadata.last_downloaded_at else None,
            'versions': [
                {
                    'version_id': v.version_id,
                    'version_number': v.version_number,
                    'document_path': v.document_path,
                    'file_size': v.file_size,
                    'created_at': v.created_at.isoformat(),
                    'created_by': v.created_by,
                    'description': v.description,
                    'is_current': v.is_current
                }
                for v in metadata.versions
            ]
        }
        
        await self.storage._save_json(metadata_path, metadata_dict)
    
    async def _load_document_metadata(
        self,
        project: TenderProject,
        document_id: str
    ) -> DocumentMetadata:
        """加载文档元数据"""
        metadata_path = f"{project.get_storage_path()}/documents_metadata/{document_id}_metadata.json"
        
        data = await self.storage._load_json(metadata_path)
        
        # 转换版本数据
        versions = [
            DocumentVersion(
                version_id=v['version_id'],
                version_number=v['version_number'],
                document_path=v['document_path'],
                file_size=v['file_size'],
                created_at=datetime.fromisoformat(v['created_at']),
                created_by=v['created_by'],
                description=v.get('description', ''),
                is_current=v.get('is_current', False)
            )
            for v in data['versions']
        ]
        
        return DocumentMetadata(
            document_id=data['document_id'],
            project_id=data['project_id'],
            tenant_id=data['tenant_id'],
            document_type=data['document_type'],
            filename=data['filename'],
            access_level=DocumentAccessLevel(data['access_level']),
            created_by=data['created_by'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            versions=versions,
            download_count=data.get('download_count', 0),
            last_downloaded_at=datetime.fromisoformat(data['last_downloaded_at']) if data.get('last_downloaded_at') else None
        )
    
    async def _check_document_access(
        self,
        metadata: DocumentMetadata,
        user_id: str,
        tenant_id: str
    ) -> bool:
        """检查文档访问权限"""
        # 创建者总是有权限
        if metadata.created_by == user_id:
            return True
        
        # 根据访问级别检查权限
        if metadata.access_level == DocumentAccessLevel.PRIVATE:
            return False
        elif metadata.access_level == DocumentAccessLevel.TENANT:
            return metadata.tenant_id == tenant_id
        elif metadata.access_level == DocumentAccessLevel.PUBLIC:
            return True  # 暂不支持公开访问
        
        return False
    
    async def _update_download_stats(
        self,
        project: TenderProject,
        document_id: str
    ):
        """更新下载统计"""
        try:
            metadata = await self._load_document_metadata(project, document_id)
            metadata.download_count += 1
            metadata.last_downloaded_at = datetime.utcnow()
            await self._save_document_metadata(project, metadata)
        except Exception as e:
            logger.warning(f"更新下载统计失败: {str(e)}")
    
    async def get_document_stats(
        self,
        project: TenderProject,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        Args:
            project: 项目对象
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        try:
            documents = await self.list_project_documents(project, user_id)
            
            stats = {
                'total_documents': len(documents),
                'documents_by_type': {},
                'total_versions': 0,
                'total_size': 0,
                'total_downloads': 0,
                'recent_documents': []
            }
            
            for doc in documents:
                # 按类型统计
                doc_type = doc.document_type
                if doc_type not in stats['documents_by_type']:
                    stats['documents_by_type'][doc_type] = 0
                stats['documents_by_type'][doc_type] += 1
                
                # 版本统计
                stats['total_versions'] += len(doc.versions)
                
                # 大小统计
                current_version = next((v for v in doc.versions if v.is_current), None)
                if current_version:
                    stats['total_size'] += current_version.file_size
                
                # 下载统计
                stats['total_downloads'] += doc.download_count
            
            # 最近文档（最多5个）
            stats['recent_documents'] = [
                {
                    'document_id': doc.document_id,
                    'filename': doc.filename,
                    'document_type': doc.document_type,
                    'created_at': doc.created_at.isoformat()
                }
                for doc in documents[:5]
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"获取文档统计失败: {str(e)}")
            return {
                'total_documents': 0,
                'documents_by_type': {},
                'total_versions': 0,
                'total_size': 0,
                'total_downloads': 0,
                'recent_documents': []
            }


def get_document_management_service() -> DocumentManagementService:
    """获取文档管理服务实例"""
    from app.services.tender_storage import get_tender_storage_service
    from app.utils.tenant_manager import get_tenant_manager
    
    storage_service = get_tender_storage_service()
    tenant_manager = get_tenant_manager()
    
    return DocumentManagementService(storage_service, tenant_manager)