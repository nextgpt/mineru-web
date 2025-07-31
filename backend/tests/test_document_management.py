"""
文档管理服务测试
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.document_management import (
    DocumentManagementService,
    DocumentAccessLevel,
    DocumentMetadata,
    DocumentVersion
)
from app.models.tender import TenderProject, TenderStatus
from app.services.tender_storage import TenderStorageService
from app.utils.tenant_manager import TenantManager


@pytest.fixture
def mock_storage_service():
    """模拟存储服务"""
    storage = Mock(spec=TenderStorageService)
    storage.minio_client = Mock()
    storage.bucket_name = "test-bucket"
    storage._save_json = AsyncMock()
    storage._load_json = AsyncMock()
    storage.save_document = AsyncMock(return_value="test/path/document.pdf")
    storage.get_document_download_url = AsyncMock(return_value="http://test.com/download")
    return storage


@pytest.fixture
def mock_tenant_manager():
    """模拟租户管理器"""
    tenant_manager = Mock(spec=TenantManager)
    return tenant_manager


@pytest.fixture
def document_service(mock_storage_service, mock_tenant_manager):
    """文档管理服务实例"""
    return DocumentManagementService(mock_storage_service, mock_tenant_manager)


@pytest.fixture
def sample_project():
    """示例项目"""
    return TenderProject(
        id="test-project-id",
        tenant_id="test-tenant",
        user_id="test-user",
        project_name="测试项目",
        source_file_id=1,
        status=TenderStatus.COMPLETED,
        minio_path="tenants/test-tenant/projects/test-project-id",
        progress=100
    )


@pytest.mark.asyncio
async def test_save_document_with_version(document_service, sample_project, mock_storage_service):
    """测试保存文档并创建版本"""
    # 准备测试数据
    document_content = b"test document content"
    filename = "test_document.pdf"
    document_type = "pdf"
    created_by = "test-user"
    description = "Initial version"
    
    # 执行测试
    metadata = await document_service.save_document_with_version(
        project=sample_project,
        document_content=document_content,
        filename=filename,
        document_type=document_type,
        created_by=created_by,
        description=description
    )
    
    # 验证结果
    assert metadata.project_id == sample_project.id
    assert metadata.tenant_id == sample_project.tenant_id
    assert metadata.document_type == document_type
    assert metadata.filename == filename
    assert metadata.created_by == created_by
    assert metadata.access_level == DocumentAccessLevel.TENANT
    assert len(metadata.versions) == 1
    assert metadata.versions[0].version_number == "1.0"
    assert metadata.versions[0].is_current is True
    
    # 验证存储服务调用
    mock_storage_service.save_document.assert_called_once()
    mock_storage_service._save_json.assert_called_once()


@pytest.mark.asyncio
async def test_add_document_version(document_service, sample_project, mock_storage_service):
    """测试添加文档版本"""
    # 准备现有文档元数据
    document_id = "test-doc-id"
    existing_metadata = {
        'document_id': document_id,
        'project_id': sample_project.id,
        'tenant_id': sample_project.tenant_id,
        'document_type': 'pdf',
        'filename': 'test.pdf',
        'access_level': 'tenant',
        'created_by': 'test-user',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'download_count': 0,
        'last_downloaded_at': None,
        'versions': [
            {
                'version_id': 'v1',
                'version_number': '1.0',
                'document_path': 'test/path/v1.pdf',
                'file_size': 1000,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': 'test-user',
                'description': 'Initial version',
                'is_current': True
            }
        ]
    }
    
    mock_storage_service._load_json.return_value = existing_metadata
    
    # 执行测试
    new_content = b"updated document content"
    new_version = await document_service.add_document_version(
        project=sample_project,
        document_id=document_id,
        document_content=new_content,
        created_by="test-user",
        description="Updated version"
    )
    
    # 验证结果
    assert new_version.version_number == "1.1"
    assert new_version.is_current is True
    assert new_version.description == "Updated version"
    
    # 验证存储服务调用
    mock_storage_service._load_json.assert_called_once()
    mock_storage_service.save_document.assert_called_once()
    mock_storage_service._save_json.assert_called()


@pytest.mark.asyncio
async def test_get_document_metadata_with_permission(document_service, sample_project, mock_storage_service):
    """测试获取文档元数据（有权限）"""
    # 准备测试数据
    document_id = "test-doc-id"
    user_id = "test-user"
    
    metadata_dict = {
        'document_id': document_id,
        'project_id': sample_project.id,
        'tenant_id': sample_project.tenant_id,
        'document_type': 'pdf',
        'filename': 'test.pdf',
        'access_level': 'tenant',
        'created_by': user_id,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'download_count': 0,
        'last_downloaded_at': None,
        'versions': []
    }
    
    mock_storage_service._load_json.return_value = metadata_dict
    
    # 执行测试
    metadata = await document_service.get_document_metadata(
        project=sample_project,
        document_id=document_id,
        user_id=user_id
    )
    
    # 验证结果
    assert metadata is not None
    assert metadata.document_id == document_id
    assert metadata.created_by == user_id


@pytest.mark.asyncio
async def test_get_document_metadata_without_permission(document_service, sample_project, mock_storage_service):
    """测试获取文档元数据（无权限）"""
    # 准备测试数据
    document_id = "test-doc-id"
    user_id = "other-user"
    
    metadata_dict = {
        'document_id': document_id,
        'project_id': sample_project.id,
        'tenant_id': sample_project.tenant_id,
        'document_type': 'pdf',
        'filename': 'test.pdf',
        'access_level': 'private',  # 私有文档
        'created_by': 'test-user',  # 不同的创建者
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'download_count': 0,
        'last_downloaded_at': None,
        'versions': []
    }
    
    mock_storage_service._load_json.return_value = metadata_dict
    
    # 执行测试
    metadata = await document_service.get_document_metadata(
        project=sample_project,
        document_id=document_id,
        user_id=user_id
    )
    
    # 验证结果
    assert metadata is None


@pytest.mark.asyncio
async def test_generate_secure_download_url(document_service, sample_project, mock_storage_service):
    """测试生成安全下载链接"""
    # 准备测试数据
    document_id = "test-doc-id"
    user_id = "test-user"
    
    metadata_dict = {
        'document_id': document_id,
        'project_id': sample_project.id,
        'tenant_id': sample_project.tenant_id,
        'document_type': 'pdf',
        'filename': 'test.pdf',
        'access_level': 'tenant',
        'created_by': user_id,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'download_count': 0,
        'last_downloaded_at': None,
        'versions': [
            {
                'version_id': 'v1',
                'version_number': '1.0',
                'document_path': 'test/path/document.pdf',
                'file_size': 1000,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id,
                'description': 'Test version',
                'is_current': True
            }
        ]
    }
    
    mock_storage_service._load_json.return_value = metadata_dict
    
    # 执行测试
    download_url = await document_service.generate_secure_download_url(
        project=sample_project,
        document_id=document_id,
        version_id=None,  # 使用当前版本
        user_id=user_id
    )
    
    # 验证结果
    assert download_url == "http://test.com/download"
    mock_storage_service.get_document_download_url.assert_called_once()


@pytest.mark.asyncio
async def test_delete_document(document_service, sample_project, mock_storage_service):
    """测试删除文档"""
    # 准备测试数据
    document_id = "test-doc-id"
    user_id = "test-user"
    
    metadata_dict = {
        'document_id': document_id,
        'project_id': sample_project.id,
        'tenant_id': sample_project.tenant_id,
        'document_type': 'pdf',
        'filename': 'test.pdf',
        'access_level': 'tenant',
        'created_by': user_id,  # 创建者有删除权限
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'download_count': 0,
        'last_downloaded_at': None,
        'versions': [
            {
                'version_id': 'v1',
                'version_number': '1.0',
                'document_path': 'test/path/document.pdf',
                'file_size': 1000,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id,
                'description': 'Test version',
                'is_current': True
            }
        ]
    }
    
    mock_storage_service._load_json.return_value = metadata_dict
    
    # 执行测试
    result = await document_service.delete_document(
        project=sample_project,
        document_id=document_id,
        user_id=user_id
    )
    
    # 验证结果
    assert result is True
    # 验证删除调用
    assert mock_storage_service.minio_client.remove_object.call_count >= 1


@pytest.mark.asyncio
async def test_get_document_stats(document_service, sample_project, mock_storage_service):
    """测试获取文档统计信息"""
    # 模拟list_objects返回
    mock_objects = [
        Mock(object_name="tenants/test-tenant/projects/test-project-id/documents_metadata/doc1_metadata.json"),
        Mock(object_name="tenants/test-tenant/projects/test-project-id/documents_metadata/doc2_metadata.json")
    ]
    mock_storage_service.minio_client.list_objects.return_value = mock_objects
    
    # 模拟文档元数据
    def mock_load_json(path):
        if "doc1_metadata.json" in path:
            return {
                'document_id': 'doc1',
                'project_id': sample_project.id,
                'tenant_id': sample_project.tenant_id,
                'document_type': 'pdf',
                'filename': 'test1.pdf',
                'access_level': 'tenant',
                'created_by': 'test-user',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'download_count': 5,
                'last_downloaded_at': None,
                'versions': [
                    {
                        'version_id': 'v1',
                        'version_number': '1.0',
                        'document_path': 'test/path/doc1.pdf',
                        'file_size': 1000,
                        'created_at': datetime.utcnow().isoformat(),
                        'created_by': 'test-user',
                        'description': 'Test version',
                        'is_current': True
                    }
                ]
            }
        elif "doc2_metadata.json" in path:
            return {
                'document_id': 'doc2',
                'project_id': sample_project.id,
                'tenant_id': sample_project.tenant_id,
                'document_type': 'docx',
                'filename': 'test2.docx',
                'access_level': 'tenant',
                'created_by': 'test-user',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'download_count': 3,
                'last_downloaded_at': None,
                'versions': [
                    {
                        'version_id': 'v1',
                        'version_number': '1.0',
                        'document_path': 'test/path/doc2.docx',
                        'file_size': 2000,
                        'created_at': datetime.utcnow().isoformat(),
                        'created_by': 'test-user',
                        'description': 'Test version',
                        'is_current': True
                    }
                ]
            }
    
    mock_storage_service._load_json.side_effect = mock_load_json
    
    # 执行测试
    stats = await document_service.get_document_stats(
        project=sample_project,
        user_id="test-user"
    )
    
    # 验证结果
    assert stats['total_documents'] == 2
    assert stats['documents_by_type']['pdf'] == 1
    assert stats['documents_by_type']['docx'] == 1
    assert stats['total_versions'] == 2
    assert stats['total_size'] == 3000
    assert stats['total_downloads'] == 8
    assert len(stats['recent_documents']) == 2


def test_document_access_level_enum():
    """测试文档访问级别枚举"""
    assert DocumentAccessLevel.PRIVATE.value == "private"
    assert DocumentAccessLevel.TENANT.value == "tenant"
    assert DocumentAccessLevel.PUBLIC.value == "public"


def test_document_version_dataclass():
    """测试文档版本数据类"""
    version = DocumentVersion(
        version_id="test-version",
        version_number="1.0",
        document_path="test/path",
        file_size=1000,
        created_at=datetime.utcnow(),
        created_by="test-user",
        description="Test version",
        is_current=True
    )
    
    assert version.version_id == "test-version"
    assert version.version_number == "1.0"
    assert version.is_current is True


def test_document_metadata_dataclass():
    """测试文档元数据数据类"""
    metadata = DocumentMetadata(
        document_id="test-doc",
        project_id="test-project",
        tenant_id="test-tenant",
        document_type="pdf",
        filename="test.pdf",
        access_level=DocumentAccessLevel.TENANT,
        created_by="test-user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        versions=[],
        download_count=0
    )
    
    assert metadata.document_id == "test-doc"
    assert metadata.access_level == DocumentAccessLevel.TENANT
    assert metadata.download_count == 0