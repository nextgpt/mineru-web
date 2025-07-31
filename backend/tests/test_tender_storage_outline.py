"""
大纲存储和版本管理测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.tender_storage import TenderStorageService
from app.models.tender import (
    TenderProject, 
    OutlineStructure, 
    ChapterInfo
)


class TestTenderStorageOutline:
    """大纲存储和版本管理测试"""
    
    @pytest.fixture
    def mock_minio_client(self):
        """模拟MinIO客户端"""
        client = Mock()
        client.bucket_exists.return_value = True
        client.stat_object.return_value = Mock()
        client.get_object.return_value = Mock()
        client.put_object.return_value = Mock()
        client.remove_object.return_value = Mock()
        client.list_objects.return_value = []
        return client
    
    @pytest.fixture
    def storage_service(self, mock_minio_client):
        """创建存储服务实例"""
        return TenderStorageService(minio_client=mock_minio_client, bucket_name="test-bucket")
    
    @pytest.fixture
    def sample_project(self):
        """示例项目"""
        return TenderProject(
            id="test-project-id",
            tenant_id="test-tenant",
            user_id="test-user",
            project_name="测试项目",
            source_file_id=1,
            minio_path="tenants/test-tenant/projects/test-project-id"
        )
    
    @pytest.fixture
    def sample_outline(self):
        """示例大纲"""
        return OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="项目理解",
                    description="对项目的深入理解",
                    subsections=[
                        {"id": "1.1", "title": "项目背景"},
                        {"id": "1.2", "title": "需求分析"}
                    ]
                ),
                ChapterInfo(
                    chapter_id="2",
                    title="技术方案",
                    description="详细的技术方案",
                    subsections=[
                        {"id": "2.1", "title": "架构设计"},
                        {"id": "2.2", "title": "技术选型"}
                    ]
                )
            ],
            chapter_count=2,
            generated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_save_and_load_outline(self, storage_service, sample_project, sample_outline):
        """测试保存和加载大纲"""
        # 模拟保存操作
        with patch.object(storage_service, '_save_json', new_callable=AsyncMock) as mock_save:
            await storage_service.save_outline(sample_project, sample_outline)
            mock_save.assert_called_once()
            
            # 验证保存路径
            expected_path = f"{sample_project.get_storage_path()}/outline.json"
            mock_save.assert_called_with(expected_path, sample_outline.dict())
    
    @pytest.mark.asyncio
    async def test_backup_outline_success(self, storage_service, sample_project, sample_outline):
        """测试成功备份大纲"""
        # 模拟文件存在和数据加载
        storage_service.check_file_exists = AsyncMock(return_value=True)
        storage_service._load_json = AsyncMock(return_value=sample_outline.dict())
        storage_service._save_json = AsyncMock()
        
        # 执行备份
        backup_path = await storage_service.backup_outline(sample_project, "test_backup")
        
        # 验证结果
        expected_backup_path = f"{sample_project.get_storage_path()}/backups/outline_test_backup.json"
        assert backup_path == expected_backup_path
        
        # 验证调用
        storage_service.check_file_exists.assert_called_once()
        storage_service._load_json.assert_called_once()
        storage_service._save_json.assert_called_once_with(expected_backup_path, sample_outline.dict())
    
    @pytest.mark.asyncio
    async def test_backup_outline_file_not_exists(self, storage_service, sample_project):
        """测试备份不存在的大纲文件"""
        # 模拟文件不存在
        storage_service.check_file_exists = AsyncMock(return_value=False)
        
        # 执行备份并验证异常
        with pytest.raises(FileNotFoundError, match="原始大纲文件不存在"):
            await storage_service.backup_outline(sample_project, "test_backup")
    
    @pytest.mark.asyncio
    async def test_restore_outline_success(self, storage_service, sample_project, sample_outline):
        """测试成功恢复大纲"""
        backup_path = f"{sample_project.get_storage_path()}/backups/outline_test.json"
        
        # 模拟备份文件存在和数据
        storage_service.check_file_exists = AsyncMock(return_value=True)
        storage_service._load_json = AsyncMock(return_value=sample_outline.dict())
        storage_service.save_outline = AsyncMock()
        
        # 执行恢复
        result = await storage_service.restore_outline(sample_project, backup_path)
        
        # 验证结果
        assert isinstance(result, OutlineStructure)
        assert result.chapter_count == sample_outline.chapter_count
        assert len(result.chapters) == len(sample_outline.chapters)
        
        # 验证调用
        storage_service.check_file_exists.assert_called_once_with(backup_path)
        storage_service._load_json.assert_called_once_with(backup_path)
        storage_service.save_outline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_outline_backup_not_exists(self, storage_service, sample_project):
        """测试恢复不存在的备份文件"""
        backup_path = f"{sample_project.get_storage_path()}/backups/outline_nonexistent.json"
        
        # 模拟备份文件不存在
        storage_service.check_file_exists = AsyncMock(return_value=False)
        
        # 执行恢复并验证异常
        with pytest.raises(FileNotFoundError, match="备份文件不存在"):
            await storage_service.restore_outline(sample_project, backup_path)
    
    @pytest.mark.asyncio
    async def test_list_outline_backups(self, storage_service, sample_project):
        """测试列出大纲备份"""
        # 模拟MinIO对象列表
        mock_objects = [
            Mock(
                object_name=f"{sample_project.get_storage_path()}/backups/outline_20240101_120000.json",
                size=1024,
                last_modified=datetime(2024, 1, 1, 12, 0, 0)
            ),
            Mock(
                object_name=f"{sample_project.get_storage_path()}/backups/outline_20240102_130000.json",
                size=2048,
                last_modified=datetime(2024, 1, 2, 13, 0, 0)
            )
        ]
        storage_service.minio_client.list_objects.return_value = mock_objects
        
        # 执行列出备份
        backups = await storage_service.list_outline_backups(sample_project)
        
        # 验证结果
        assert len(backups) == 2
        assert backups[0]['backup_suffix'] == '20240102_130000'  # 按时间倒序
        assert backups[1]['backup_suffix'] == '20240101_120000'
        
        # 验证备份信息结构
        for backup in backups:
            assert 'filename' in backup
            assert 'path' in backup
            assert 'size' in backup
            assert 'created_at' in backup
            assert 'backup_suffix' in backup
    
    @pytest.mark.asyncio
    async def test_delete_outline_success(self, storage_service, sample_project):
        """测试成功删除大纲"""
        # 模拟文件存在
        storage_service.check_file_exists = AsyncMock(return_value=True)
        
        # 执行删除
        result = await storage_service.delete_outline(sample_project)
        
        # 验证结果
        assert result is True
        
        # 验证调用
        storage_service.check_file_exists.assert_called_once()
        storage_service.minio_client.remove_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_outline_file_not_exists(self, storage_service, sample_project):
        """测试删除不存在的大纲文件"""
        # 模拟文件不存在
        storage_service.check_file_exists = AsyncMock(return_value=False)
        
        # 执行删除
        result = await storage_service.delete_outline(sample_project)
        
        # 验证结果 - 文件不存在也视为删除成功
        assert result is True
        
        # 验证没有调用删除操作
        storage_service.minio_client.remove_object.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_outline_field(self, storage_service, sample_project, sample_outline):
        """测试更新大纲字段"""
        # 模拟加载现有大纲
        storage_service.load_outline = AsyncMock(return_value=sample_outline)
        storage_service.save_outline = AsyncMock()
        
        # 执行字段更新
        new_chapters = [
            ChapterInfo(
                chapter_id="1",
                title="更新后的项目理解",
                description="更新后的描述",
                subsections=[]
            )
        ]
        
        result = await storage_service.update_outline_field(
            sample_project, 
            "chapters", 
            new_chapters
        )
        
        # 验证结果
        assert isinstance(result, OutlineStructure)
        assert result.chapters == new_chapters
        
        # 验证调用
        storage_service.load_outline.assert_called_once()
        storage_service.save_outline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_outline_field_invalid_field(self, storage_service, sample_project, sample_outline):
        """测试更新无效字段"""
        # 模拟加载现有大纲
        storage_service.load_outline = AsyncMock(return_value=sample_outline)
        
        # 执行更新无效字段并验证异常
        with pytest.raises(ValueError, match="无效的字段名称"):
            await storage_service.update_outline_field(
                sample_project, 
                "invalid_field", 
                "some_value"
            )
    
    @pytest.mark.asyncio
    async def test_get_outline_summary(self, storage_service, sample_project, sample_outline):
        """测试获取大纲摘要"""
        # 模拟加载大纲
        storage_service.load_outline = AsyncMock(return_value=sample_outline)
        
        # 执行获取摘要
        summary = await storage_service.get_outline_summary(sample_project)
        
        # 验证结果
        assert summary['project_id'] == sample_project.id
        assert summary['chapter_count'] == 2
        assert summary['total_subsections'] == 4  # 每个章节2个子章节
        assert summary['avg_subsections_per_chapter'] == 2.0
        assert summary['has_outline'] is True
        assert len(summary['chapter_titles']) == 2
        assert "项目理解" in summary['chapter_titles']
        assert "技术方案" in summary['chapter_titles']
    
    @pytest.mark.asyncio
    async def test_get_outline_summary_no_outline(self, storage_service, sample_project):
        """测试获取不存在大纲的摘要"""
        # 模拟大纲不存在
        storage_service.load_outline = AsyncMock(side_effect=FileNotFoundError())
        
        # 执行获取摘要
        summary = await storage_service.get_outline_summary(sample_project)
        
        # 验证结果
        assert summary['project_id'] == sample_project.id
        assert summary['generated_at'] is None
        assert summary['chapter_count'] == 0
        assert summary['total_subsections'] == 0
        assert summary['avg_subsections_per_chapter'] == 0
        assert summary['has_outline'] is False
        assert summary['chapter_titles'] == []
    
    def test_validate_outline_data_valid(self, storage_service):
        """测试有效大纲数据验证"""
        valid_data = {
            'chapters': [
                {
                    'chapter_id': '1',
                    'title': '测试章节',
                    'description': '测试描述',
                    'subsections': [
                        {'id': '1.1', 'title': '子章节1'},
                        {'id': '1.2', 'title': '子章节2'}
                    ]
                }
            ],
            'chapter_count': 1,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # 验证不应抛出异常
        storage_service._validate_outline_data(valid_data)
    
    def test_validate_outline_data_missing_fields(self, storage_service):
        """测试缺少必需字段的数据验证"""
        invalid_data = {
            'chapters': [],
            # 缺少 chapter_count 和 generated_at
        }
        
        # 验证应抛出异常
        with pytest.raises(ValueError, match="大纲数据缺少必需字段"):
            storage_service._validate_outline_data(invalid_data)
    
    def test_validate_outline_data_invalid_chapter_structure(self, storage_service):
        """测试无效章节结构的数据验证"""
        invalid_data = {
            'chapters': [
                {
                    'chapter_id': '1',
                    'title': '测试章节',
                    # 缺少 description 和 subsections
                }
            ],
            'chapter_count': 1,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # 验证应抛出异常
        with pytest.raises(ValueError, match="第1个章节缺少必需字段"):
            storage_service._validate_outline_data(invalid_data)
    
    def test_validate_outline_data_invalid_subsections(self, storage_service):
        """测试无效子章节结构的数据验证"""
        invalid_data = {
            'chapters': [
                {
                    'chapter_id': '1',
                    'title': '测试章节',
                    'description': '测试描述',
                    'subsections': "not a list"  # 应该是列表
                }
            ],
            'chapter_count': 1,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # 验证应抛出异常
        with pytest.raises(ValueError, match="第1个章节的subsections必须是列表类型"):
            storage_service._validate_outline_data(invalid_data)


if __name__ == "__main__":
    pytest.main([__file__])