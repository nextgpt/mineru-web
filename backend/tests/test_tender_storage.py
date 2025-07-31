"""
招标存储服务单元测试
"""
import pytest
import json
import io
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from minio.error import S3Error
from app.services.tender_storage import TenderStorageService
from app.models.tender import (
    TenderProject,
    TenderStatus,
    ProjectMetadata,
    AnalysisResult,
    OutlineStructure,
    ChapterContent,
    ChapterInfo,
    DocumentInfo
)


@pytest.fixture
def mock_minio_client():
    """模拟MinIO客户端"""
    client = Mock()
    client.bucket_exists.return_value = True
    client.make_bucket.return_value = None
    client.put_object.return_value = None
    client.get_object.return_value = Mock()
    client.list_objects.return_value = []
    client.stat_object.return_value = Mock()
    client.presigned_get_object.return_value = "http://example.com/download"
    client.remove_objects.return_value = []
    return client


@pytest.fixture
def storage_service(mock_minio_client):
    """创建存储服务实例"""
    return TenderStorageService(minio_client=mock_minio_client, bucket_name="test-bucket")


@pytest.fixture
def sample_project():
    """创建示例项目"""
    return TenderProject(
        id="test-project-123",
        tenant_id="tenant_12345678",
        user_id="user123",
        project_name="测试项目",
        source_file_id=1,
        status=TenderStatus.ANALYZING,
        minio_path="tenants/tenant_12345678/projects/test-project-123"
    )


@pytest.fixture
def sample_metadata():
    """创建示例元数据"""
    return ProjectMetadata(
        project_id="test-project-123",
        project_name="测试项目",
        tenant_id="tenant_12345678",
        user_id="user123",
        source_file_id=1,
        status=TenderStatus.ANALYZING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_analysis():
    """创建示例分析结果"""
    return AnalysisResult(
        project_info={"name": "测试项目", "budget": "100万"},
        technical_requirements={"tech": "Python"},
        evaluation_criteria={"technical": 70},
        submission_requirements={"format": "PDF"}
    )


@pytest.fixture
def sample_outline():
    """创建示例大纲"""
    chapter = ChapterInfo(
        chapter_id="1",
        title="项目理解",
        description="项目背景分析"
    )
    return OutlineStructure(
        chapters=[chapter],
        chapter_count=1
    )


@pytest.fixture
def sample_chapter():
    """创建示例章节内容"""
    return ChapterContent(
        chapter_id="1.1",
        chapter_title="项目背景",
        content="这是项目背景的详细内容...",
        word_count=500
    )


class TestTenderStorageService:
    """TenderStorageService测试类"""
    
    def test_init_with_defaults(self):
        """测试使用默认参数初始化"""
        with patch('app.services.tender_storage.default_minio_client') as mock_client:
            mock_client.bucket_exists.return_value = True
            service = TenderStorageService()
            assert service.minio_client == mock_client
    
    def test_ensure_bucket_exists(self, mock_minio_client):
        """测试确保存储桶存在"""
        mock_minio_client.bucket_exists.return_value = True
        service = TenderStorageService(minio_client=mock_minio_client, bucket_name="test-bucket")
        mock_minio_client.bucket_exists.assert_called_with("test-bucket")
        mock_minio_client.make_bucket.assert_not_called()
    
    def test_ensure_bucket_create(self, mock_minio_client):
        """测试创建不存在的存储桶"""
        mock_minio_client.bucket_exists.return_value = False
        service = TenderStorageService(minio_client=mock_minio_client, bucket_name="test-bucket")
        mock_minio_client.make_bucket.assert_called_with("test-bucket")
    
    def test_get_project_path(self, storage_service):
        """测试获取项目路径"""
        path = storage_service.get_project_path("tenant_123", "project_456")
        assert path == "tenants/tenant_123/projects/project_456"
    
    @pytest.mark.asyncio
    async def test_save_project_metadata(self, storage_service, sample_project, sample_metadata):
        """测试保存项目元数据"""
        await storage_service.save_project_metadata(sample_project, sample_metadata)
        
        # 验证调用了put_object
        storage_service.minio_client.put_object.assert_called_once()
        call_args = storage_service.minio_client.put_object.call_args
        
        assert call_args[0][0] == "test-bucket"  # bucket_name
        assert call_args[0][1] == "tenants/tenant_12345678/projects/test-project-123/metadata.json"  # path
        assert call_args[1]['content_type'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_load_project_metadata(self, storage_service, sample_project, sample_metadata):
        """测试加载项目元数据"""
        # 模拟返回的JSON数据
        json_data = sample_metadata.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.load_project_metadata(sample_project)
        
        assert isinstance(result, ProjectMetadata)
        assert result.project_id == sample_metadata.project_id
        assert result.project_name == sample_metadata.project_name
    
    @pytest.mark.asyncio
    async def test_save_analysis_result(self, storage_service, sample_project, sample_analysis):
        """测试保存分析结果"""
        await storage_service.save_analysis_result(sample_project, sample_analysis)
        
        storage_service.minio_client.put_object.assert_called_once()
        call_args = storage_service.minio_client.put_object.call_args
        
        assert "analysis.json" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_load_analysis_result(self, storage_service, sample_project, sample_analysis):
        """测试加载分析结果"""
        json_data = sample_analysis.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.load_analysis_result(sample_project)
        
        assert isinstance(result, AnalysisResult)
        assert result.project_info == sample_analysis.project_info
    
    @pytest.mark.asyncio
    async def test_save_outline(self, storage_service, sample_project, sample_outline):
        """测试保存大纲结构"""
        await storage_service.save_outline(sample_project, sample_outline)
        
        storage_service.minio_client.put_object.assert_called_once()
        call_args = storage_service.minio_client.put_object.call_args
        
        assert "outline.json" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_load_outline(self, storage_service, sample_project, sample_outline):
        """测试加载大纲结构"""
        json_data = sample_outline.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.load_outline(sample_project)
        
        assert isinstance(result, OutlineStructure)
        assert result.chapter_count == sample_outline.chapter_count
    
    @pytest.mark.asyncio
    async def test_save_chapter_content(self, storage_service, sample_project, sample_chapter):
        """测试保存章节内容"""
        await storage_service.save_chapter_content(sample_project, sample_chapter)
        
        storage_service.minio_client.put_object.assert_called_once()
        call_args = storage_service.minio_client.put_object.call_args
        
        assert "content/chapter_1.1.json" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_load_chapter_content(self, storage_service, sample_project, sample_chapter):
        """测试加载章节内容"""
        json_data = sample_chapter.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.load_chapter_content(sample_project, "1.1")
        
        assert isinstance(result, ChapterContent)
        assert result.chapter_id == sample_chapter.chapter_id
        assert result.content == sample_chapter.content
    
    @pytest.mark.asyncio
    async def test_load_all_chapters(self, storage_service, sample_project, sample_chapter):
        """测试加载所有章节内容"""
        # 模拟MinIO返回的对象列表
        mock_obj1 = Mock()
        mock_obj1.object_name = "tenants/tenant_12345678/projects/test-project-123/content/chapter_1.1.json"
        
        mock_obj2 = Mock()
        mock_obj2.object_name = "tenants/tenant_12345678/projects/test-project-123/content/chapter_1.2.json"
        
        storage_service.minio_client.list_objects.return_value = [mock_obj1, mock_obj2]
        
        # 模拟JSON数据
        json_data = sample_chapter.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.load_all_chapters(sample_project)
        
        assert len(result) == 2
        assert all(isinstance(chapter, ChapterContent) for chapter in result)
    
    @pytest.mark.asyncio
    async def test_save_document(self, storage_service, sample_project):
        """测试保存文档"""
        content = b"PDF content here"
        path = await storage_service.save_document(sample_project, "pdf", content)
        
        assert "documents/final.pdf" in path
        storage_service.minio_client.put_object.assert_called_once()
        call_args = storage_service.minio_client.put_object.call_args
        
        assert call_args[1]['content_type'] == 'application/pdf'
    
    @pytest.mark.asyncio
    async def test_get_document_download_url(self, storage_service):
        """测试获取文档下载链接"""
        url = await storage_service.get_document_download_url("test/path/document.pdf")
        
        assert url == "http://example.com/download"
        storage_service.minio_client.presigned_get_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_project_documents(self, storage_service, sample_project):
        """测试列出项目文档"""
        # 模拟MinIO返回的对象
        mock_obj = Mock()
        mock_obj.object_name = "tenants/tenant_12345678/projects/test-project-123/documents/final.pdf"
        mock_obj.etag = "test-etag"
        mock_obj.size = 1024
        mock_obj.last_modified = datetime.utcnow()
        
        storage_service.minio_client.list_objects.return_value = [mock_obj]
        
        result = await storage_service.list_project_documents(sample_project)
        
        assert len(result) == 1
        assert isinstance(result[0], DocumentInfo)
        assert result[0].document_type == "pdf"
        assert result[0].filename == "final.pdf"
    
    @pytest.mark.asyncio
    async def test_delete_project_data(self, storage_service, sample_project):
        """测试删除项目数据"""
        # 模拟要删除的对象
        mock_obj = Mock()
        mock_obj.object_name = "tenants/tenant_12345678/projects/test-project-123/metadata.json"
        
        storage_service.minio_client.list_objects.return_value = [mock_obj]
        storage_service.minio_client.remove_objects.return_value = []
        
        await storage_service.delete_project_data(sample_project)
        
        storage_service.minio_client.remove_objects.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_file_exists_true(self, storage_service):
        """测试文件存在检查 - 存在"""
        storage_service.minio_client.stat_object.return_value = Mock()
        
        result = await storage_service.check_file_exists("test/path")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_file_exists_false(self, storage_service):
        """测试文件存在检查 - 不存在"""
        storage_service.minio_client.stat_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        result = await storage_service.check_file_exists("test/path")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_load_json_file_not_found(self, storage_service):
        """测试加载不存在的JSON文件"""
        storage_service.minio_client.get_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        with pytest.raises(FileNotFoundError):
            await storage_service._load_json("nonexistent.json")
    
    @pytest.mark.asyncio
    async def test_load_json_invalid_format(self, storage_service):
        """测试加载格式错误的JSON文件"""
        mock_response = Mock()
        mock_response.read.return_value = b"invalid json content"
        storage_service.minio_client.get_object.return_value = mock_response
        
        with pytest.raises(ValueError):
            await storage_service._load_json("invalid.json")
    
    def test_get_content_type(self, storage_service):
        """测试获取内容类型"""
        assert storage_service._get_content_type("pdf") == "application/pdf"
        assert storage_service._get_content_type("docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert storage_service._get_content_type("unknown") == "application/octet-stream"
    
    def test_json_serializer(self, storage_service):
        """测试JSON序列化器"""
        now = datetime.utcnow()
        result = storage_service._json_serializer(now)
        assert result == now.isoformat()
        
        with pytest.raises(TypeError):
            storage_service._json_serializer(object())
    
    def test_validate_analysis_data_success(self, storage_service, sample_analysis):
        """测试分析数据验证成功"""
        data = sample_analysis.dict()
        # 不应该抛出异常
        storage_service._validate_analysis_data(data)
    
    def test_validate_analysis_data_missing_field(self, storage_service):
        """测试分析数据验证 - 缺少必需字段"""
        data = {
            "project_info": {},
            "technical_requirements": {},
            "evaluation_criteria": {},
            # 缺少 submission_requirements 和 extracted_at
        }
        
        with pytest.raises(ValueError, match="分析结果缺少必需字段"):
            storage_service._validate_analysis_data(data)
    
    def test_validate_analysis_data_wrong_type(self, storage_service):
        """测试分析数据验证 - 字段类型错误"""
        data = {
            "project_info": "not a dict",  # 应该是字典
            "technical_requirements": {},
            "evaluation_criteria": {},
            "submission_requirements": {},
            "extracted_at": datetime.utcnow().isoformat()
        }
        
        with pytest.raises(ValueError, match="project_info 必须是字典类型"):
            storage_service._validate_analysis_data(data)
    
    def test_validate_analysis_data_invalid_timestamp(self, storage_service):
        """测试分析数据验证 - 无效时间戳"""
        data = {
            "project_info": {},
            "technical_requirements": {},
            "evaluation_criteria": {},
            "submission_requirements": {},
            "extracted_at": "invalid timestamp"
        }
        
        with pytest.raises(ValueError, match="extracted_at 时间格式无效"):
            storage_service._validate_analysis_data(data)
    
    @pytest.mark.asyncio
    async def test_update_analysis_result_field_existing(self, storage_service, sample_project, sample_analysis):
        """测试更新现有分析结果字段"""
        # 模拟现有分析结果
        json_data = sample_analysis.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        # 更新字段
        new_project_info = {"name": "更新后的项目", "budget": "200万"}
        result = await storage_service.update_analysis_result_field(
            sample_project, "project_info", new_project_info
        )
        
        assert result.project_info == new_project_info
        # 验证保存操作被调用
        assert storage_service.minio_client.put_object.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_update_analysis_result_field_new(self, storage_service, sample_project):
        """测试更新不存在的分析结果字段（创建新的）"""
        # 模拟文件不存在
        storage_service.minio_client.get_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        # 更新字段
        new_project_info = {"name": "新项目", "budget": "300万"}
        result = await storage_service.update_analysis_result_field(
            sample_project, "project_info", new_project_info
        )
        
        assert result.project_info == new_project_info
        assert isinstance(result, AnalysisResult)
    
    @pytest.mark.asyncio
    async def test_update_analysis_result_field_invalid_field(self, storage_service, sample_project):
        """测试更新无效字段"""
        # 模拟文件不存在
        storage_service.minio_client.get_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        with pytest.raises(ValueError, match="无效的字段名称"):
            await storage_service.update_analysis_result_field(
                sample_project, "invalid_field", "value"
            )
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_summary_with_data(self, storage_service, sample_project, sample_analysis):
        """测试获取分析结果摘要 - 有数据"""
        json_data = sample_analysis.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.get_analysis_result_summary(sample_project)
        
        assert result['project_id'] == sample_project.id
        assert result['project_info_fields'] > 0
        assert result['has_complete_data'] is True
        assert 'total_fields' in result
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_summary_no_data(self, storage_service, sample_project):
        """测试获取分析结果摘要 - 无数据"""
        # 模拟文件不存在
        storage_service.minio_client.get_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        result = await storage_service.get_analysis_result_summary(sample_project)
        
        assert result['project_id'] == sample_project.id
        assert result['extracted_at'] is None
        assert result['total_fields'] == 0
        assert result['has_complete_data'] is False
    
    @pytest.mark.asyncio
    async def test_backup_analysis_result_success(self, storage_service, sample_project, sample_analysis):
        """测试备份分析结果成功"""
        # 模拟原始文件存在
        storage_service.minio_client.stat_object.return_value = Mock()
        
        json_data = sample_analysis.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        backup_path = await storage_service.backup_analysis_result(sample_project, "test_backup")
        
        assert "backups/analysis_test_backup.json" in backup_path
        # 验证保存操作被调用
        assert storage_service.minio_client.put_object.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_backup_analysis_result_file_not_found(self, storage_service, sample_project):
        """测试备份不存在的分析结果"""
        # 模拟原始文件不存在
        storage_service.minio_client.stat_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        with pytest.raises(FileNotFoundError, match="原始分析结果文件不存在"):
            await storage_service.backup_analysis_result(sample_project, "test_backup")
    
    @pytest.mark.asyncio
    async def test_restore_analysis_result_success(self, storage_service, sample_project, sample_analysis):
        """测试恢复分析结果成功"""
        backup_path = "tenants/tenant_12345678/projects/test-project-123/backups/analysis_backup.json"
        
        # 模拟备份文件存在
        storage_service.minio_client.stat_object.return_value = Mock()
        
        json_data = sample_analysis.dict()
        json_str = json.dumps(json_data, default=str)
        
        mock_response = Mock()
        mock_response.read.return_value = json_str.encode('utf-8')
        storage_service.minio_client.get_object.return_value = mock_response
        
        result = await storage_service.restore_analysis_result(sample_project, backup_path)
        
        assert isinstance(result, AnalysisResult)
        assert result.project_info == sample_analysis.project_info
        # 验证保存操作被调用
        assert storage_service.minio_client.put_object.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_restore_analysis_result_backup_not_found(self, storage_service, sample_project):
        """测试恢复不存在的备份"""
        backup_path = "nonexistent/backup.json"
        
        # 模拟备份文件不存在
        storage_service.minio_client.stat_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        with pytest.raises(FileNotFoundError, match="备份文件不存在"):
            await storage_service.restore_analysis_result(sample_project, backup_path)
    
    @pytest.mark.asyncio
    async def test_list_analysis_backups(self, storage_service, sample_project):
        """测试列出分析结果备份"""
        # 模拟备份文件
        mock_obj1 = Mock()
        mock_obj1.object_name = "tenants/tenant_12345678/projects/test-project-123/backups/analysis_20240101_120000.json"
        mock_obj1.size = 1024
        mock_obj1.last_modified = datetime(2024, 1, 1, 12, 0, 0)
        
        mock_obj2 = Mock()
        mock_obj2.object_name = "tenants/tenant_12345678/projects/test-project-123/backups/analysis_20240102_120000.json"
        mock_obj2.size = 2048
        mock_obj2.last_modified = datetime(2024, 1, 2, 12, 0, 0)
        
        storage_service.minio_client.list_objects.return_value = [mock_obj1, mock_obj2]
        
        result = await storage_service.list_analysis_backups(sample_project)
        
        assert len(result) == 2
        # 应该按时间倒序排列
        assert result[0]['backup_suffix'] == "20240102_120000"
        assert result[1]['backup_suffix'] == "20240101_120000"
        assert all('filename' in backup for backup in result)
        assert all('created_at' in backup for backup in result)
    
    @pytest.mark.asyncio
    async def test_list_analysis_backups_empty(self, storage_service, sample_project):
        """测试列出空的备份列表"""
        storage_service.minio_client.list_objects.return_value = []
        
        result = await storage_service.list_analysis_backups(sample_project)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_delete_analysis_result_success(self, storage_service, sample_project):
        """测试删除分析结果成功"""
        # 模拟文件存在
        storage_service.minio_client.stat_object.return_value = Mock()
        storage_service.minio_client.remove_object.return_value = None
        
        result = await storage_service.delete_analysis_result(sample_project)
        
        assert result is True
        storage_service.minio_client.remove_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_analysis_result_file_not_exists(self, storage_service, sample_project):
        """测试删除不存在的分析结果"""
        # 模拟文件不存在
        storage_service.minio_client.stat_object.side_effect = S3Error("NoSuchKey", "", "", "", "", "")
        
        result = await storage_service.delete_analysis_result(sample_project)
        
        assert result is True  # 文件不存在视为删除成功
        storage_service.minio_client.remove_object.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_analysis_result_error(self, storage_service, sample_project):
        """测试删除分析结果时发生错误"""
        # 模拟文件存在
        storage_service.minio_client.stat_object.return_value = Mock()
        # 模拟删除时发生错误
        storage_service.minio_client.remove_object.side_effect = S3Error("AccessDenied", "", "", "", "", "")
        
        result = await storage_service.delete_analysis_result(sample_project)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])