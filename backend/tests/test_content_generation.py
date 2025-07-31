"""
内容生成服务测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.content_generation import ContentGenerationService
from app.models.tender import (
    TenderProject, 
    TenderStatus, 
    AnalysisResult,
    OutlineStructure,
    ChapterInfo,
    ChapterContent
)
from app.services.tender_storage import TenderStorageService
from app.services.ai_client import AIResponse, AIServiceError


class TestContentGenerationService:
    """内容生成服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage(self):
        """模拟存储服务"""
        storage = Mock(spec=TenderStorageService)
        storage.load_outline = AsyncMock()
        storage.load_analysis_result = AsyncMock()
        storage.save_chapter_content = AsyncMock()
        storage.load_chapter_content = AsyncMock()
        storage.load_all_chapters = AsyncMock()
        storage._save_json = AsyncMock()
        return storage
    
    @pytest.fixture
    def mock_ai_client(self):
        """模拟AI客户端"""
        ai_client = Mock()
        ai_client.generate = AsyncMock()
        return ai_client
    
    @pytest.fixture
    def service(self, mock_db, mock_storage, mock_ai_client):
        """创建服务实例"""
        return ContentGenerationService(
            db=mock_db,
            storage_service=mock_storage,
            ai_client=mock_ai_client
        )
    
    @pytest.fixture
    def sample_project(self):
        """示例项目"""
        project = TenderProject(
            id="test-project-id",
            tenant_id="test-tenant",
            user_id="test-user",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.OUTLINED,
            minio_path="tenants/test-tenant/projects/test-project-id"
        )
        return project
    
    @pytest.fixture
    def sample_analysis(self):
        """示例分析结果"""
        return AnalysisResult(
            project_info={
                "project_name": "某某管理系统开发",
                "project_overview": "开发一套完整的管理系统",
                "budget": "100万元",
                "duration": "6个月"
            },
            technical_requirements={
                "functional_requirements": ["用户管理", "数据管理", "报表生成"],
                "performance_requirements": {"response_time": "< 3秒"},
                "security_requirements": ["数据加密", "用户认证"]
            },
            evaluation_criteria={
                "technical_score": {"weight": 70, "criteria": ["技术方案", "架构设计"]},
                "commercial_score": {"weight": 30, "criteria": ["价格", "服务"]}
            },
            submission_requirements={
                "document_format": "PDF",
                "required_documents": ["技术方案", "商务方案"]
            }
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
    async def test_generate_chapter_content_success(self, service, mock_db, mock_storage, mock_ai_client, sample_project, sample_analysis, sample_outline):
        """测试成功生成章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_analysis_result.return_value = sample_analysis
        mock_storage.load_outline.return_value = sample_outline
        
        # 模拟AI响应
        ai_response = AIResponse(
            content="这是生成的章节内容，包含了项目理解的详细分析...",
            model_type="mock",
            success=True,
            tokens_used=100,
            response_time=1.0
        )
        mock_ai_client.generate.return_value = ai_response
        
        # 执行测试
        result = await service.generate_chapter_content("test-project-id", "1")
        
        # 验证结果
        assert isinstance(result, ChapterContent)
        assert result.chapter_id == "1"
        assert result.chapter_title == "项目理解"
        assert result.content == ai_response.content
        assert result.word_count == len(ai_response.content)
        
        # 验证调用
        mock_storage.load_analysis_result.assert_called_once()
        mock_storage.load_outline.assert_called_once()
        mock_ai_client.generate.assert_called_once()
        mock_storage.save_chapter_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content_chapter_not_found(self, service, mock_db, mock_storage, sample_project, sample_analysis, sample_outline):
        """测试生成不存在的章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_analysis_result.return_value = sample_analysis
        mock_storage.load_outline.return_value = sample_outline
        
        # 执行测试 - 尝试生成不存在的章节
        result = await service.generate_chapter_content("test-project-id", "999")
        
        # 验证结果 - 应该返回None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content_ai_failure(self, service, mock_db, mock_storage, mock_ai_client, sample_project, sample_analysis, sample_outline):
        """测试AI生成失败的情况"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_analysis_result.return_value = sample_analysis
        mock_storage.load_outline.return_value = sample_outline
        
        # 模拟AI失败响应
        ai_response = AIResponse(
            content="",
            model_type="mock",
            success=False,
            error_message="AI服务不可用",
            tokens_used=0,
            response_time=1.0
        )
        mock_ai_client.generate.return_value = ai_response
        
        # 执行测试
        result = await service.generate_chapter_content("test-project-id", "1")
        
        # 验证结果 - 应该返回None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_all_content_success(self, service, mock_db, mock_storage, mock_ai_client, sample_project, sample_analysis, sample_outline):
        """测试成功生成所有内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_outline.return_value = sample_outline
        mock_storage.load_analysis_result.return_value = sample_analysis
        mock_storage.load_chapter_content.side_effect = FileNotFoundError()  # 模拟内容不存在
        
        # 模拟AI响应
        ai_response = AIResponse(
            content="生成的章节内容",
            model_type="mock",
            success=True,
            tokens_used=100,
            response_time=1.0
        )
        mock_ai_client.generate.return_value = ai_response
        
        # 执行测试
        result = await service.generate_all_content("test-project-id")
        
        # 验证结果
        assert result["total_chapters"] == 2
        assert result["generated_count"] == 2
        assert result["failed_count"] == 0
        assert result["success_rate"] == 100.0
        
        # 验证项目状态更新
        assert sample_project.status == TenderStatus.GENERATED
        assert sample_project.progress == 100
        
        # 验证AI调用次数
        assert mock_ai_client.generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_all_content_skip_existing(self, service, mock_db, mock_storage, mock_ai_client, sample_project, sample_analysis, sample_outline):
        """测试跳过已存在的内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_outline.return_value = sample_outline
        mock_storage.load_analysis_result.return_value = sample_analysis
        
        # 模拟第一个章节已存在内容
        existing_content = ChapterContent(
            chapter_id="1",
            chapter_title="项目理解",
            content="已存在的内容",
            word_count=100,
            generated_at=datetime.utcnow()
        )
        
        def mock_load_chapter_content(project, chapter_id):
            if chapter_id == "1":
                return existing_content
            else:
                raise FileNotFoundError()
        
        mock_storage.load_chapter_content.side_effect = mock_load_chapter_content
        
        # 模拟AI响应
        ai_response = AIResponse(
            content="新生成的章节内容",
            model_type="mock",
            success=True,
            tokens_used=100,
            response_time=1.0
        )
        mock_ai_client.generate.return_value = ai_response
        
        # 执行测试 - 不重新生成已存在的内容
        result = await service.generate_all_content("test-project-id", regenerate_existing=False)
        
        # 验证结果
        assert result["total_chapters"] == 2
        assert result["generated_count"] == 1  # 只生成了一个新章节
        assert result["skipped_count"] == 1    # 跳过了一个已存在的章节
        assert result["failed_count"] == 0
        
        # 验证AI只被调用一次（为第二个章节）
        assert mock_ai_client.generate.call_count == 1
    
    @pytest.mark.asyncio
    async def test_regenerate_chapter_with_backup(self, service, mock_db, mock_storage, mock_ai_client, sample_project):
        """测试重新生成章节并备份现有内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 模拟现有内容
        existing_content = ChapterContent(
            chapter_id="1",
            chapter_title="项目理解",
            content="现有的章节内容",
            word_count=100,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_chapter_content.return_value = existing_content
        
        # 模拟生成新内容的方法
        new_content = ChapterContent(
            chapter_id="1",
            chapter_title="项目理解",
            content="重新生成的章节内容",
            word_count=200,
            generated_at=datetime.utcnow()
        )
        
        with patch.object(service, 'generate_chapter_content', return_value=new_content) as mock_generate:
            # 执行测试
            result = await service.regenerate_chapter("test-project-id", "1")
            
            # 验证结果
            assert result == new_content
            
            # 验证备份被创建
            mock_storage._save_json.assert_called_once()
            
            # 验证重新生成被调用
            mock_generate.assert_called_once_with("test-project-id", "1")
    
    @pytest.mark.asyncio
    async def test_get_chapter_content(self, service, mock_db, mock_storage, sample_project):
        """测试获取章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        expected_content = ChapterContent(
            chapter_id="1",
            chapter_title="项目理解",
            content="章节内容",
            word_count=100,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_chapter_content.return_value = expected_content
        
        # 执行测试
        result = await service.get_chapter_content("test-project-id", "1")
        
        # 验证结果
        assert result == expected_content
        mock_storage.load_chapter_content.assert_called_once_with(sample_project, "1")
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_not_found(self, service, mock_db, mock_storage, sample_project):
        """测试获取不存在的章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_chapter_content.side_effect = FileNotFoundError()
        
        # 执行测试
        result = await service.get_chapter_content("test-project-id", "1")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_chapter_content(self, service, mock_db, mock_storage, sample_project):
        """测试更新章节内容"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        existing_content = ChapterContent(
            chapter_id="1",
            chapter_title="项目理解",
            content="原始内容",
            word_count=100,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_chapter_content.return_value = existing_content
        
        # 执行测试
        new_content_text = "更新后的章节内容"
        result = await service.update_chapter_content("test-project-id", "1", new_content_text)
        
        # 验证结果
        assert isinstance(result, ChapterContent)
        assert result.chapter_id == "1"
        assert result.chapter_title == "项目理解"
        assert result.content == new_content_text
        assert result.word_count == len(new_content_text)
        
        # 验证保存被调用
        mock_storage.save_chapter_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_content_statistics(self, service, mock_db, mock_storage, sample_project, sample_outline):
        """测试获取内容统计信息"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_outline.return_value = sample_outline
        
        # 模拟章节内容
        chapter_contents = [
            ChapterContent(
                chapter_id="1",
                chapter_title="项目理解",
                content="第一章内容",
                word_count=500,
                generated_at=datetime.utcnow()
            ),
            ChapterContent(
                chapter_id="2",
                chapter_title="技术方案",
                content="第二章内容",
                word_count=800,
                generated_at=datetime.utcnow()
            )
        ]
        mock_storage.load_all_chapters.return_value = chapter_contents
        
        # 执行测试
        result = await service.get_content_statistics("test-project-id")
        
        # 验证结果
        assert result["project_id"] == "test-project-id"
        assert result["total_chapters"] == 2
        assert result["generated_chapters"] == 2
        assert result["completion_rate"] == 100.0
        assert result["total_words"] == 1300
        assert result["average_words_per_chapter"] == 650.0
        assert len(result["chapter_statistics"]) == 2
        
        # 验证章节统计
        chapter_stats = result["chapter_statistics"]
        assert chapter_stats[0]["chapter_id"] == "1"
        assert chapter_stats[0]["has_content"] is True
        assert chapter_stats[0]["word_count"] == 500
    
    def test_build_content_generation_prompt(self, service, sample_analysis, sample_outline):
        """测试构建内容生成提示词"""
        chapter = sample_outline.chapters[0]  # 项目理解章节
        
        # 执行测试
        prompt = service._build_content_generation_prompt(chapter, sample_analysis, sample_outline)
        
        # 验证结果
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert chapter.title in prompt
        assert chapter.description in prompt
        assert sample_analysis.project_info["project_name"] in prompt
        
        # 验证包含子章节信息
        for subsection in chapter.subsections:
            assert subsection["title"] in prompt
        
        # 验证包含技术要求
        for req in sample_analysis.technical_requirements["functional_requirements"]:
            assert req in prompt


if __name__ == "__main__":
    pytest.main([__file__])


class TestAsyncTaskProcessing:
    """异步任务处理测试"""
    
    @pytest.fixture
    def mock_task_manager(self):
        """模拟任务管理器"""
        from app.services.task_manager import TaskType, TaskStatus, TaskInfo
        
        mock_manager = Mock()
        mock_manager.create_task = AsyncMock()
        mock_manager.start_task = AsyncMock()
        mock_manager.update_task_progress = AsyncMock()
        mock_manager.get_task_info = AsyncMock()
        mock_manager.complete_task = AsyncMock()
        mock_manager.fail_task = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def sample_task_info(self):
        """示例任务信息"""
        from app.services.task_manager import TaskType, TaskStatus, TaskInfo
        
        return TaskInfo(
            task_id="task-123",
            task_type=TaskType.CONTENT_GENERATION,
            status=TaskStatus.RUNNING,
            project_id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            title="生成标书内容",
            description="正在生成所有章节的标书内容...",
            progress=0,
            metadata={"operation": "generate_all", "regenerate_existing": False}
        )
    
    @pytest.mark.asyncio
    async def test_generate_all_content_async(self, mock_task_manager):
        """测试异步生成所有内容"""
        from app.services.content_generation import ContentGenerationService
        
        # 设置模拟
        mock_task_manager.create_task.return_value = "task-123"
        mock_task_manager.start_task.return_value = True
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(Mock(), Mock(), Mock())
            
            # 执行测试
            task_id = await service.generate_all_content_async(
                project_id="test-project-1",
                tenant_id="tenant_123",
                user_id="user_456",
                regenerate_existing=False
            )
            
            # 验证结果
            assert task_id == "task-123"
            
            # 验证任务创建
            mock_task_manager.create_task.assert_called_once()
            create_call = mock_task_manager.create_task.call_args
            assert create_call[1]["task_type"].value == "content_generation"
            assert create_call[1]["project_id"] == "test-project-1"
            assert create_call[1]["title"] == "生成标书内容"
            
            # 验证任务启动
            mock_task_manager.start_task.assert_called_once_with("task-123")
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content_async(self, mock_task_manager):
        """测试异步生成单个章节内容"""
        from app.services.content_generation import ContentGenerationService
        
        # 设置模拟
        mock_task_manager.create_task.return_value = "task-456"
        mock_task_manager.start_task.return_value = True
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(Mock(), Mock(), Mock())
            
            # 执行测试
            task_id = await service.generate_chapter_content_async(
                project_id="test-project-1",
                chapter_id="1",
                tenant_id="tenant_123",
                user_id="user_456"
            )
            
            # 验证结果
            assert task_id == "task-456"
            
            # 验证任务创建
            mock_task_manager.create_task.assert_called_once()
            create_call = mock_task_manager.create_task.call_args
            assert create_call[1]["metadata"]["chapter_id"] == "1"
            assert create_call[1]["metadata"]["operation"] == "generate_chapter"
    
    @pytest.mark.asyncio
    async def test_handle_generate_all_task_success(self, mock_task_manager, sample_task_info):
        """测试处理生成所有内容任务成功"""
        from app.services.content_generation import ContentGenerationService
        from app.models.tender import TenderProject, TenderStatus, AnalysisResult, OutlineStructure
        
        # 创建模拟对象
        mock_db = Mock()
        mock_storage = Mock()
        mock_ai_client = Mock()
        
        # 设置项目模拟
        sample_project = TenderProject(
            id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.OUTLINED
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 设置大纲模拟
        sample_outline = OutlineStructure(
            chapters=[
                {"chapter_id": "1", "title": "项目理解", "description": "项目理解描述"},
                {"chapter_id": "2", "title": "技术方案", "description": "技术方案描述"}
            ],
            chapter_count=2,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_outline = AsyncMock(return_value=sample_outline)
        
        # 设置分析结果模拟
        sample_analysis = AnalysisResult(
            project_info={"project_name": "测试项目"},
            technical_requirements={"functional_requirements": ["需求1", "需求2"]},
            evaluation_criteria={"technical_score": {"weight": 70}},
            submission_requirements={"document_format": "PDF"},
            extracted_at=datetime.utcnow()
        )
        mock_storage.load_analysis_result = AsyncMock(return_value=sample_analysis)
        
        # 设置章节内容不存在
        mock_storage.load_chapter_content = AsyncMock(side_effect=FileNotFoundError())
        mock_storage.save_chapter_content = AsyncMock()
        
        # 设置AI客户端模拟
        from app.services.ai_client import AIResponse, AIModelType
        mock_ai_client.generate = AsyncMock(return_value=AIResponse(
            content="生成的章节内容",
            model_type=AIModelType.MOCK,
            success=True,
            error_message=None
        ))
        
        # 设置任务管理器模拟
        mock_task_manager.get_task_info.return_value = sample_task_info
        mock_task_manager.update_task_progress = AsyncMock()
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(mock_db, mock_storage, mock_ai_client)
            
            # 执行测试
            result = await service._handle_generate_all_task(sample_task_info, mock_task_manager)
            
            # 验证结果
            assert result["total_chapters"] == 2
            assert result["generated_count"] == 2
            assert result["failed_count"] == 0
            assert result["success_rate"] == 100.0
            
            # 验证进度更新被调用
            assert mock_task_manager.update_task_progress.call_count >= 2
            
            # 验证AI生成被调用
            assert mock_ai_client.generate.call_count == 2
            
            # 验证项目状态更新
            assert sample_project.status == TenderStatus.GENERATED
    
    @pytest.mark.asyncio
    async def test_handle_generate_all_task_with_cancellation(self, mock_task_manager, sample_task_info):
        """测试任务取消处理"""
        from app.services.content_generation import ContentGenerationService
        from app.services.task_manager import TaskStatus
        from app.models.tender import TenderProject, TenderStatus, OutlineStructure
        
        # 创建模拟对象
        mock_db = Mock()
        mock_storage = Mock()
        mock_ai_client = Mock()
        
        # 设置项目模拟
        sample_project = TenderProject(
            id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.OUTLINED
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 设置大纲模拟
        sample_outline = OutlineStructure(
            chapters=[
                {"chapter_id": "1", "title": "项目理解", "description": "项目理解描述"}
            ],
            chapter_count=1,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_outline = AsyncMock(return_value=sample_outline)
        mock_storage.load_analysis_result = AsyncMock(return_value=Mock())
        
        # 模拟任务被取消
        cancelled_task = sample_task_info
        cancelled_task.status = TaskStatus.CANCELLED
        mock_task_manager.get_task_info.return_value = cancelled_task
        mock_task_manager.update_task_progress = AsyncMock()
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(mock_db, mock_storage, mock_ai_client)
            
            # 执行测试
            result = await service._handle_generate_all_task(sample_task_info, mock_task_manager)
            
            # 验证任务被中断
            assert result["generated_count"] == 0
            
            # 验证没有调用AI生成
            mock_ai_client.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_generate_chapter_task(self, mock_task_manager):
        """测试处理生成单个章节任务"""
        from app.services.content_generation import ContentGenerationService
        from app.services.task_manager import TaskType, TaskStatus, TaskInfo
        from app.models.tender import TenderProject, TenderStatus, AnalysisResult, OutlineStructure
        
        # 创建章节任务信息
        chapter_task_info = TaskInfo(
            task_id="task-456",
            task_type=TaskType.CONTENT_GENERATION,
            status=TaskStatus.RUNNING,
            project_id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            title="生成章节内容",
            description="正在生成章节 1 的内容...",
            progress=0,
            metadata={"operation": "generate_chapter", "chapter_id": "1"}
        )
        
        # 创建模拟对象
        mock_db = Mock()
        mock_storage = Mock()
        mock_ai_client = Mock()
        
        # 设置项目模拟
        sample_project = TenderProject(
            id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.OUTLINED
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 设置大纲和分析结果模拟
        sample_outline = OutlineStructure(
            chapters=[{"chapter_id": "1", "title": "项目理解", "description": "项目理解描述"}],
            chapter_count=1,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_outline = AsyncMock(return_value=sample_outline)
        mock_storage.load_analysis_result = AsyncMock(return_value=Mock())
        mock_storage.save_chapter_content = AsyncMock()
        
        # 设置AI客户端模拟
        from app.services.ai_client import AIResponse, AIModelType
        mock_ai_client.generate = AsyncMock(return_value=AIResponse(
            content="生成的项目理解章节内容",
            model_type=AIModelType.MOCK,
            success=True,
            error_message=None
        ))
        
        # 设置任务管理器模拟
        mock_task_manager.update_task_progress = AsyncMock()
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(mock_db, mock_storage, mock_ai_client)
            
            # 执行测试
            result = await service._handle_generate_chapter_task(chapter_task_info, mock_task_manager)
            
            # 验证结果
            assert result["chapter_id"] == "1"
            assert "generated_at" in result
            
            # 验证进度更新
            assert mock_task_manager.update_task_progress.call_count >= 2
            
            # 验证AI调用
            mock_ai_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_error_handling(self, mock_task_manager, sample_task_info):
        """测试任务错误处理"""
        from app.services.content_generation import ContentGenerationService
        
        # 创建模拟对象
        mock_db = Mock()
        mock_storage = Mock()
        mock_ai_client = Mock()
        
        # 设置项目不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(mock_db, mock_storage, mock_ai_client)
            
            # 执行测试并验证异常
            with pytest.raises(ValueError, match="项目 test-project-1 不存在"):
                await service._handle_generate_all_task(sample_task_info, mock_task_manager)


class TestProgressTracking:
    """进度跟踪测试"""
    
    @pytest.mark.asyncio
    async def test_progress_updates_during_generation(self):
        """测试生成过程中的进度更新"""
        from app.services.content_generation import ContentGenerationService
        from app.models.tender import TenderProject, TenderStatus, OutlineStructure
        
        # 创建模拟对象
        mock_db = Mock()
        mock_storage = Mock()
        mock_ai_client = Mock()
        mock_task_manager = Mock()
        
        # 设置项目模拟
        sample_project = TenderProject(
            id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.OUTLINED
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 设置大纲模拟（3个章节）
        sample_outline = OutlineStructure(
            chapters=[
                {"chapter_id": "1", "title": "项目理解"},
                {"chapter_id": "2", "title": "技术方案"},
                {"chapter_id": "3", "title": "实施计划"}
            ],
            chapter_count=3,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_outline = AsyncMock(return_value=sample_outline)
        mock_storage.load_analysis_result = AsyncMock(return_value=Mock())
        mock_storage.load_chapter_content = AsyncMock(side_effect=FileNotFoundError())
        mock_storage.save_chapter_content = AsyncMock()
        
        # 设置AI客户端模拟
        from app.services.ai_client import AIResponse
        mock_ai_client.generate = AsyncMock(return_value=AIResponse(
            success=True,
            content="生成的章节内容",
            error_message=None
        ))
        
        # 设置任务管理器模拟
        mock_task_manager.update_task_progress = AsyncMock()
        
        # 创建服务实例
        with patch('app.services.content_generation.get_task_manager', return_value=mock_task_manager):
            service = ContentGenerationService(mock_db, mock_storage, mock_ai_client)
            
            # 执行测试
            await service.generate_all_content("test-project-1")
            
            # 验证进度更新
            # 应该有初始进度更新 + 每个章节的进度更新 + 最终完成更新
            progress_calls = mock_task_manager.update_task_progress.call_args_list
            
            # 验证进度值是递增的
            progress_values = []
            for call in progress_calls:
                if len(call[0]) > 1:  # 有进度参数
                    progress_values.append(call[0][1])
            
            # 验证进度是递增的
            for i in range(1, len(progress_values)):
                assert progress_values[i] >= progress_values[i-1], "进度应该是递增的"
    
    @pytest.mark.asyncio
    async def test_progress_tracking_with_failures(self):
        """测试有失败情况下的进度跟踪"""
        from app.services.content_generation import ContentGenerationService
        from app.models.tender import TenderProject, TenderStatus, OutlineStructure
        
        # 创建模拟对象
        mock_db = Mock()
        mock_storage = Mock()
        mock_ai_client = Mock()
        
        # 设置项目模拟
        sample_project = TenderProject(
            id="test-project-1",
            tenant_id="tenant_123",
            user_id="user_456",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.OUTLINED
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 设置大纲模拟
        sample_outline = OutlineStructure(
            chapters=[
                {"chapter_id": "1", "title": "项目理解"},
                {"chapter_id": "2", "title": "技术方案"}
            ],
            chapter_count=2,
            generated_at=datetime.utcnow()
        )
        mock_storage.load_outline = AsyncMock(return_value=sample_outline)
        mock_storage.load_analysis_result = AsyncMock(return_value=Mock())
        mock_storage.load_chapter_content = AsyncMock(side_effect=FileNotFoundError())
        mock_storage.save_chapter_content = AsyncMock()
        
        # 设置AI客户端模拟（第一个成功，第二个失败）
        from app.services.ai_client import AIResponse
        mock_ai_client.generate = AsyncMock(side_effect=[
            AIResponse(success=True, content="成功生成的内容", error_message=None),
            AIResponse(success=False, content=None, error_message="AI服务错误")
        ])
        
        # 创建服务实例
        service = ContentGenerationService(mock_db, mock_storage, mock_ai_client)
        
        # 执行测试
        result = await service.generate_all_content("test-project-1")
        
        # 验证结果
        assert result["total_chapters"] == 2
        assert result["generated_count"] == 1
        assert result["failed_count"] == 1
        assert result["success_rate"] == 50.0
        
        # 验证项目状态仍然是已生成（部分成功）
        assert sample_project.status == TenderStatus.GENERATED