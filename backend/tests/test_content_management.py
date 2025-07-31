"""
内容管理服务测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.content_management import (
    ContentManagementService,
    ContentVersion,
    ContentEditHistory,
    ContentSearchResult,
    ContentStatistics
)
from app.models.tender import TenderProject, TenderStatus, ChapterContent, OutlineStructure, ChapterInfo
from app.services.tender_storage import TenderStorageService


class TestContentManagementService:
    """内容管理服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage_service(self):
        """模拟存储服务"""
        return Mock(spec=TenderStorageService)
    
    @pytest.fixture
    def mock_project(self):
        """模拟项目对象"""
        project = Mock(spec=TenderProject)
        project.id = "test-project-id"
        project.tenant_id = "test-tenant"
        project.user_id = "test-user"
        project.project_name = "测试项目"
        project.status = TenderStatus.GENERATED
        project.get_storage_path.return_value = "tenants/test-tenant/projects/test-project-id"
        return project
    
    @pytest.fixture
    def content_service(self, mock_db, mock_storage_service):
        """内容管理服务实例"""
        with patch('app.services.content_management.default_minio_client'), \
             patch('app.services.content_management.MINIO_BUCKET', 'test-bucket'):
            service = ContentManagementService(mock_db, mock_storage_service)
            return service
    
    @pytest.fixture
    def sample_chapter_content(self):
        """示例章节内容"""
        return ChapterContent(
            chapter_id="1.1",
            chapter_title="项目理解",
            content="这是项目理解的内容，包含了对招标项目的深入分析和理解。",
            word_count=25,
            generated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_outline(self):
        """示例大纲结构"""
        chapters = [
            ChapterInfo(
                chapter_id="1.1",
                title="项目理解",
                description="对项目的理解和分析",
                subsections=[
                    {"id": "1.1.1", "title": "项目背景"},
                    {"id": "1.1.2", "title": "需求分析"}
                ]
            ),
            ChapterInfo(
                chapter_id="1.2",
                title="技术方案",
                description="技术实施方案",
                subsections=[
                    {"id": "1.2.1", "title": "架构设计"},
                    {"id": "1.2.2", "title": "技术选型"}
                ]
            )
        ]
        
        return OutlineStructure(
            chapters=chapters,
            chapter_count=2,
            generated_at=datetime.utcnow()
        )
    
    # ==================== 内容数据操作接口测试 ====================
    
    @pytest.mark.asyncio
    async def test_create_chapter_content_success(
        self, content_service, mock_db, mock_storage_service, mock_project
    ):
        """测试创建章节内容成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.save_chapter_content = AsyncMock()
        
        # 模拟MinIO操作
        with patch.object(content_service, '_create_content_version', new_callable=AsyncMock) as mock_create_version, \
             patch.object(content_service, '_record_edit_history', new_callable=AsyncMock) as mock_record_history:
            
            # 执行测试
            result = await content_service.create_chapter_content(
                project_id="test-project-id",
                chapter_id="1.1",
                chapter_title="项目理解",
                content="测试内容",
                user_id="test-user",
                version_note="初始创建"
            )
            
            # 验证结果
            assert result.chapter_id == "1.1"
            assert result.chapter_title == "项目理解"
            assert result.content == "测试内容"
            assert result.word_count == 4
            
            # 验证调用
            mock_storage_service.save_chapter_content.assert_called_once()
            mock_create_version.assert_called_once()
            mock_record_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_chapter_content_project_not_found(
        self, content_service, mock_db
    ):
        """测试创建章节内容时项目不存在"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="项目 .* 不存在"):
            await content_service.create_chapter_content(
                project_id="nonexistent-project",
                chapter_id="1.1",
                chapter_title="测试章节",
                content="测试内容",
                user_id="test-user"
            )
    
    @pytest.mark.asyncio
    async def test_update_chapter_content_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_chapter_content
    ):
        """测试更新章节内容成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_chapter_content = AsyncMock(return_value=sample_chapter_content)
        mock_storage_service.save_chapter_content = AsyncMock()
        
        # 模拟其他操作
        with patch.object(content_service, '_backup_current_version', new_callable=AsyncMock), \
             patch.object(content_service, '_create_content_version', new_callable=AsyncMock), \
             patch.object(content_service, '_record_edit_history', new_callable=AsyncMock):
            
            # 执行测试
            result = await content_service.update_chapter_content(
                project_id="test-project-id",
                chapter_id="1.1",
                content="更新后的内容",
                user_id="test-user",
                version_note="内容更新"
            )
            
            # 验证结果
            assert result.chapter_id == "1.1"
            assert result.content == "更新后的内容"
            assert result.word_count == 6
            
            # 验证调用
            mock_storage_service.load_chapter_content.assert_called_once()
            mock_storage_service.save_chapter_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_chapter_content_not_found(
        self, content_service, mock_db, mock_storage_service, mock_project
    ):
        """测试更新不存在的章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_chapter_content = AsyncMock(side_effect=FileNotFoundError())
        
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="章节 .* 不存在"):
            await content_service.update_chapter_content(
                project_id="test-project-id",
                chapter_id="nonexistent-chapter",
                content="更新内容",
                user_id="test-user"
            )
    
    @pytest.mark.asyncio
    async def test_delete_chapter_content_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_chapter_content
    ):
        """测试删除章节内容成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_chapter_content = AsyncMock(return_value=sample_chapter_content)
        
        # 模拟MinIO客户端
        mock_minio_client = Mock()
        content_service.minio_client = mock_minio_client
        
        with patch.object(content_service, '_backup_deleted_content', new_callable=AsyncMock), \
             patch.object(content_service, '_record_edit_history', new_callable=AsyncMock):
            
            # 执行测试
            result = await content_service.delete_chapter_content(
                project_id="test-project-id",
                chapter_id="1.1",
                user_id="test-user",
                delete_note="删除测试"
            )
            
            # 验证结果
            assert result is True
            
            # 验证调用
            mock_storage_service.load_chapter_content.assert_called_once()
            mock_minio_client.remove_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_chapter_content
    ):
        """测试获取章节内容成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_chapter_content = AsyncMock(return_value=sample_chapter_content)
        
        # 执行测试
        result = await content_service.get_chapter_content("test-project-id", "1.1")
        
        # 验证结果
        assert result == sample_chapter_content
        mock_storage_service.load_chapter_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_not_found(
        self, content_service, mock_db, mock_storage_service, mock_project
    ):
        """测试获取不存在的章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_chapter_content = AsyncMock(side_effect=FileNotFoundError())
        
        # 执行测试
        result = await content_service.get_chapter_content("test-project-id", "nonexistent")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_chapter_contents_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_chapter_content
    ):
        """测试列出章节内容成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_all_chapters = AsyncMock(return_value=[sample_chapter_content])
        
        # 执行测试
        result = await content_service.list_chapter_contents("test-project-id")
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_chapter_content
        mock_storage_service.load_all_chapters.assert_called_once()
    
    # ==================== 版本控制功能测试 ====================
    
    @pytest.mark.asyncio
    async def test_get_content_versions_success(self, content_service, mock_db, mock_project):
        """测试获取内容版本成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟MinIO对象列表
        mock_object = Mock()
        mock_object.object_name = "tenants/test-tenant/projects/test-project-id/versions/1.1/v_20240101_120000_1.1.json"
        
        mock_minio_client = Mock()
        mock_minio_client.list_objects.return_value = [mock_object]
        content_service.minio_client = mock_minio_client
        
        # 模拟版本数据
        version_data = {
            "version_id": "v_20240101_120000_1.1",
            "chapter_id": "1.1",
            "chapter_title": "项目理解",
            "content": "版本内容",
            "word_count": 4,
            "created_at": "2024-01-01T12:00:00",
            "created_by": "test-user",
            "version_note": "测试版本",
            "is_current": True
        }
        
        with patch.object(content_service.storage_service, '_load_json', new_callable=AsyncMock) as mock_load_json:
            mock_load_json.return_value = version_data
            
            # 执行测试
            result = await content_service.get_content_versions("test-project-id", "1.1")
            
            # 验证结果
            assert len(result) == 1
            version = result[0]
            assert isinstance(version, ContentVersion)
            assert version.version_id == "v_20240101_120000_1.1"
            assert version.chapter_id == "1.1"
            assert version.is_current is True
    
    @pytest.mark.asyncio
    async def test_restore_content_version_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_chapter_content
    ):
        """测试恢复内容版本成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_chapter_content = AsyncMock(return_value=sample_chapter_content)
        mock_storage_service.save_chapter_content = AsyncMock()
        
        # 模拟版本数据
        version_data = {
            "chapter_id": "1.1",
            "chapter_title": "项目理解",
            "content": "恢复的内容",
            "word_count": 5
        }
        
        with patch.object(content_service.storage_service, '_load_json', new_callable=AsyncMock) as mock_load_json, \
             patch.object(content_service, '_backup_current_version', new_callable=AsyncMock), \
             patch.object(content_service, '_create_content_version', new_callable=AsyncMock), \
             patch.object(content_service, '_record_edit_history', new_callable=AsyncMock):
            
            mock_load_json.return_value = version_data
            
            # 执行测试
            result = await content_service.restore_content_version(
                project_id="test-project-id",
                chapter_id="1.1",
                version_id="v_20240101_120000_1.1",
                user_id="test-user",
                restore_note="恢复测试"
            )
            
            # 验证结果
            assert result.chapter_id == "1.1"
            assert result.content == "恢复的内容"
            assert result.word_count == 5
            
            # 验证调用
            mock_storage_service.save_chapter_content.assert_called_once()
    
    # ==================== 编辑历史功能测试 ====================
    
    @pytest.mark.asyncio
    async def test_get_edit_history_success(self, content_service, mock_db, mock_project):
        """测试获取编辑历史成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟MinIO对象列表
        mock_object = Mock()
        mock_object.object_name = "tenants/test-tenant/projects/test-project-id/history/edit_20240101_120000_1.1.json"
        
        mock_minio_client = Mock()
        mock_minio_client.list_objects.return_value = [mock_object]
        content_service.minio_client = mock_minio_client
        
        # 模拟历史数据
        history_data = {
            "edit_id": "edit_20240101_120000_1.1",
            "chapter_id": "1.1",
            "action": "update",
            "old_content": "旧内容",
            "new_content": "新内容",
            "word_count_change": 1,
            "edited_at": "2024-01-01T12:00:00",
            "edited_by": "test-user",
            "edit_note": "测试编辑"
        }
        
        with patch.object(content_service.storage_service, '_load_json', new_callable=AsyncMock) as mock_load_json:
            mock_load_json.return_value = history_data
            
            # 执行测试
            result = await content_service.get_edit_history("test-project-id")
            
            # 验证结果
            assert len(result) == 1
            history = result[0]
            assert isinstance(history, ContentEditHistory)
            assert history.edit_id == "edit_20240101_120000_1.1"
            assert history.action == "update"
            assert history.word_count_change == 1
    
    # ==================== 内容搜索功能测试 ====================
    
    @pytest.mark.asyncio
    async def test_search_content_text_search(
        self, content_service, mock_db, mock_storage_service, mock_project
    ):
        """测试文本搜索功能"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 创建包含搜索关键词的内容
        search_content = ChapterContent(
            chapter_id="1.1",
            chapter_title="项目理解",
            content="这是一个关于项目理解的详细分析，包含了项目的背景和需求分析。",
            word_count=25,
            generated_at=datetime.utcnow()
        )
        
        mock_storage_service.load_all_chapters = AsyncMock(return_value=[search_content])
        
        # 执行测试
        result = await content_service.search_content(
            project_id="test-project-id",
            query="项目",
            search_type="text",
            case_sensitive=False
        )
        
        # 验证结果
        assert len(result) == 1
        search_result = result[0]
        assert isinstance(search_result, ContentSearchResult)
        assert search_result.chapter_id == "1.1"
        assert search_result.match_count == 2  # "项目"出现2次
        assert search_result.relevance_score > 0
    
    @pytest.mark.asyncio
    async def test_search_content_regex_search(
        self, content_service, mock_db, mock_storage_service, mock_project
    ):
        """测试正则表达式搜索功能"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 创建包含数字的内容
        search_content = ChapterContent(
            chapter_id="1.1",
            chapter_title="技术方案",
            content="系统支持1000个并发用户，处理速度达到500ms以内。",
            word_count=20,
            generated_at=datetime.utcnow()
        )
        
        mock_storage_service.load_all_chapters = AsyncMock(return_value=[search_content])
        
        # 执行测试 - 搜索数字
        result = await content_service.search_content(
            project_id="test-project-id",
            query=r"\d+",
            search_type="regex",
            case_sensitive=False
        )
        
        # 验证结果
        assert len(result) == 1
        search_result = result[0]
        assert search_result.match_count == 2  # 匹配到 "1000" 和 "500"
    
    # ==================== 内容统计功能测试 ====================
    
    @pytest.mark.asyncio
    async def test_get_content_statistics_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_outline, sample_chapter_content
    ):
        """测试获取内容统计成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_storage_service.load_outline = AsyncMock(return_value=sample_outline)
        mock_storage_service.load_all_chapters = AsyncMock(return_value=[sample_chapter_content])
        
        # 执行测试
        result = await content_service.get_content_statistics("test-project-id")
        
        # 验证结果
        assert isinstance(result, ContentStatistics)
        assert result.project_id == "test-project-id"
        assert result.total_chapters == 2
        assert result.completed_chapters == 1
        assert result.completion_rate == 50.0
        assert result.total_words == 25
        assert result.average_words_per_chapter == 25
        assert len(result.chapter_stats) == 2
    
    @pytest.mark.asyncio
    async def test_get_project_content_summary_success(
        self, content_service, mock_db, mock_storage_service, mock_project
    ):
        """测试获取项目内容摘要成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟统计数据
        mock_stats = ContentStatistics(
            project_id="test-project-id",
            total_chapters=2,
            completed_chapters=1,
            total_words=100,
            average_words_per_chapter=100,
            completion_rate=50.0,
            last_updated=datetime.utcnow(),
            chapter_stats=[]
        )
        
        with patch.object(content_service, 'get_content_statistics', new_callable=AsyncMock) as mock_get_stats, \
             patch.object(content_service, 'get_edit_history', new_callable=AsyncMock) as mock_get_history:
            
            mock_get_stats.return_value = mock_stats
            mock_get_history.return_value = []
            
            # 执行测试
            result = await content_service.get_project_content_summary("test-project-id")
            
            # 验证结果
            assert result["project_id"] == "test-project-id"
            assert "statistics" in result
            assert "recent_activities" in result
            assert "chapter_overview" in result
            assert result["statistics"]["total_chapters"] == 2
            assert result["statistics"]["completion_rate"] == 50.0
    
    @pytest.mark.asyncio
    async def test_get_content_analytics_success(
        self, content_service, mock_db, mock_project
    ):
        """测试获取内容分析数据成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 模拟编辑历史
        mock_history = [
            ContentEditHistory(
                edit_id="edit1",
                chapter_id="1.1",
                action="create",
                old_content=None,
                new_content="新内容",
                word_count_change=10,
                edited_at=datetime.utcnow(),
                edited_by="user1",
                edit_note="创建"
            ),
            ContentEditHistory(
                edit_id="edit2",
                chapter_id="1.2",
                action="update",
                old_content="旧内容",
                new_content="更新内容",
                word_count_change=5,
                edited_at=datetime.utcnow() - timedelta(days=1),
                edited_by="user2",
                edit_note="更新"
            )
        ]
        
        with patch.object(content_service, 'get_edit_history', new_callable=AsyncMock) as mock_get_history:
            mock_get_history.return_value = mock_history
            
            # 执行测试
            result = await content_service.get_content_analytics("test-project-id", days=30)
            
            # 验证结果
            assert result["project_id"] == "test-project-id"
            assert result["total_edits"] == 2
            assert result["total_word_change"] == 15
            assert "activity_by_day" in result
            assert "activity_by_user" in result
            assert "activity_by_action" in result
            assert result["activity_by_user"]["user1"] == 1
            assert result["activity_by_user"]["user2"] == 1
            assert result["activity_by_action"]["create"] == 1
            assert result["activity_by_action"]["update"] == 1
    
    # ==================== 辅助方法测试 ====================
    
    def test_search_in_content_text_search(self, content_service):
        """测试文本搜索辅助方法"""
        content = "这是一个测试内容，包含多个测试关键词。"
        query = "测试"
        
        matches = content_service._search_in_content(content, query, "text", False)
        
        assert len(matches) == 2
        assert matches[0][1] == "测试"
        assert matches[1][1] == "测试"
    
    def test_search_in_content_regex_search(self, content_service):
        """测试正则表达式搜索辅助方法"""
        content = "价格为1000元，数量为50个。"
        query = r"\d+"
        
        matches = content_service._search_in_content(content, query, "regex", False)
        
        assert len(matches) == 2
        assert matches[0][1] == "1000"
        assert matches[1][1] == "50"
    
    def test_generate_content_snippet(self, content_service):
        """测试生成内容摘要方法"""
        content = "这是一个很长的内容，" * 20 + "关键词在这里，" + "后面还有更多内容。" * 10
        query = "关键词"
        
        snippet = content_service._generate_content_snippet(content, query, False, 50)
        
        assert "关键词" in snippet
        assert len(snippet) <= 100  # 考虑省略号
        assert snippet.startswith("...")
        assert snippet.endswith("...")
    
    def test_calculate_relevance_score(self, content_service):
        """测试计算相关性分数方法"""
        content = "短内容"
        query = "内容"
        match_count = 1
        
        score = content_service._calculate_relevance_score(content, query, match_count)
        
        assert isinstance(score, float)
        assert score > 0
        
        # 测试更多匹配的情况
        score_more_matches = content_service._calculate_relevance_score(content, query, 3)
        assert score_more_matches > score


if __name__ == "__main__":
    pytest.main([__file__])