"""
内容管理功能集成测试
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.content_management import (
    ContentManagementService,
    ContentVersion,
    ContentEditHistory,
    ContentSearchResult,
    ContentStatistics
)
from app.models.tender import TenderProject, TenderStatus, ChapterContent, OutlineStructure, ChapterInfo


class TestContentManagementIntegration:
    """内容管理功能集成测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def mock_storage_service(self):
        """模拟存储服务"""
        return Mock()
    
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
    
    # ==================== 基础功能测试 ====================
    
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
    async def test_get_content_statistics_success(
        self, content_service, mock_db, mock_storage_service, mock_project, sample_chapter_content
    ):
        """测试获取内容统计成功"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 创建示例大纲
        chapters = [
            ChapterInfo(
                chapter_id="1.1",
                title="项目理解",
                description="对项目的理解和分析",
                subsections=[]
            ),
            ChapterInfo(
                chapter_id="1.2",
                title="技术方案",
                description="技术实施方案",
                subsections=[]
            )
        ]
        
        sample_outline = OutlineStructure(
            chapters=chapters,
            chapter_count=2,
            generated_at=datetime.utcnow()
        )
        
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
    
    # ==================== 错误处理测试 ====================
    
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


if __name__ == "__main__":
    pytest.main([__file__])