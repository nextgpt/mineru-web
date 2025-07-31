"""
招标项目数据模型单元测试
"""
import pytest
from datetime import datetime
from app.models.tender import (
    TenderProject, 
    TenderStatus,
    ProjectMetadata,
    AnalysisResult,
    OutlineStructure,
    ChapterContent,
    ChapterInfo,
    CreateProjectRequest,
    ProjectResponse
)


class TestTenderStatus:
    """TenderStatus枚举测试"""
    
    def test_tender_status_values(self):
        """测试状态枚举值"""
        assert TenderStatus.ANALYZING.value == 'analyzing'
        assert TenderStatus.ANALYZED.value == 'analyzed'
        assert TenderStatus.OUTLINING.value == 'outlining'
        assert TenderStatus.OUTLINED.value == 'outlined'
        assert TenderStatus.GENERATING.value == 'generating'
        assert TenderStatus.GENERATED.value == 'generated'
        assert TenderStatus.EXPORTING.value == 'exporting'
        assert TenderStatus.COMPLETED.value == 'completed'
        assert TenderStatus.FAILED.value == 'failed'


class TestTenderProject:
    """TenderProject模型测试"""
    
    def test_get_storage_path(self):
        """测试存储路径生成"""
        project = TenderProject(
            id="test-project-123",
            tenant_id="tenant_12345678",
            user_id="user123",
            project_name="测试项目",
            source_file_id=1,
            minio_path="test/path"
        )
        
        expected_path = "tenants/tenant_12345678/projects/test-project-123"
        assert project.get_storage_path() == expected_path
    
    def test_to_dict(self):
        """测试转换为字典"""
        now = datetime.utcnow()
        project = TenderProject(
            id="test-project-123",
            tenant_id="tenant_12345678",
            user_id="user123",
            project_name="测试项目",
            source_file_id=1,
            status=TenderStatus.ANALYZING,
            minio_path="test/path",
            progress=50,
            created_at=now,
            updated_at=now
        )
        
        result = project.to_dict()
        
        assert result['id'] == "test-project-123"
        assert result['tenant_id'] == "tenant_12345678"
        assert result['user_id'] == "user123"
        assert result['project_name'] == "测试项目"
        assert result['source_file_id'] == 1
        assert result['status'] == 'analyzing'
        assert result['minio_path'] == "test/path"
        assert result['progress'] == 50
        assert result['created_at'] == now.isoformat()
        assert result['updated_at'] == now.isoformat()


class TestProjectMetadata:
    """ProjectMetadata模型测试"""
    
    def test_project_metadata_creation(self):
        """测试项目元数据创建"""
        now = datetime.utcnow()
        metadata = ProjectMetadata(
            project_id="test-project-123",
            project_name="测试项目",
            tenant_id="tenant_12345678",
            user_id="user123",
            source_file_id=1,
            status=TenderStatus.ANALYZING,
            created_at=now,
            updated_at=now,
            progress=25
        )
        
        assert metadata.project_id == "test-project-123"
        assert metadata.project_name == "测试项目"
        assert metadata.tenant_id == "tenant_12345678"
        assert metadata.user_id == "user123"
        assert metadata.source_file_id == 1
        # With use_enum_values=True, the status will be converted to string
        assert metadata.status == 'analyzing'
        assert metadata.progress == 25
    
    def test_project_metadata_json_serialization(self):
        """测试JSON序列化"""
        now = datetime.utcnow()
        metadata = ProjectMetadata(
            project_id="test-project-123",
            project_name="测试项目",
            tenant_id="tenant_12345678",
            user_id="user123",
            source_file_id=1,
            status=TenderStatus.ANALYZING,
            created_at=now,
            updated_at=now
        )
        
        # 测试可以序列化为JSON
        json_data = metadata.dict()
        assert json_data['status'] == 'analyzing'  # 枚举值应该被序列化


class TestAnalysisResult:
    """AnalysisResult模型测试"""
    
    def test_analysis_result_creation(self):
        """测试分析结果创建"""
        analysis = AnalysisResult(
            project_info={"name": "测试项目", "budget": "100万"},
            technical_requirements={"tech": "Python", "framework": "FastAPI"},
            evaluation_criteria={"technical": 70, "commercial": 30},
            submission_requirements={"format": "PDF", "deadline": "2024-01-01"}
        )
        
        assert analysis.project_info["name"] == "测试项目"
        assert analysis.technical_requirements["tech"] == "Python"
        assert analysis.evaluation_criteria["technical"] == 70
        assert analysis.submission_requirements["format"] == "PDF"
        assert isinstance(analysis.extracted_at, datetime)
    
    def test_analysis_result_defaults(self):
        """测试默认值"""
        analysis = AnalysisResult()
        
        assert analysis.project_info == {}
        assert analysis.technical_requirements == {}
        assert analysis.evaluation_criteria == {}
        assert analysis.submission_requirements == {}
        assert isinstance(analysis.extracted_at, datetime)


class TestOutlineStructure:
    """OutlineStructure模型测试"""
    
    def test_outline_structure_creation(self):
        """测试大纲结构创建"""
        chapter1 = ChapterInfo(
            chapter_id="1",
            title="项目理解",
            description="项目背景和需求分析",
            subsections=[
                {"id": "1.1", "title": "项目背景"},
                {"id": "1.2", "title": "需求分析"}
            ]
        )
        
        chapter2 = ChapterInfo(
            chapter_id="2",
            title="技术方案",
            description="技术实现方案"
        )
        
        outline = OutlineStructure(
            chapters=[chapter1, chapter2],
            chapter_count=2
        )
        
        assert len(outline.chapters) == 2
        assert outline.chapter_count == 2
        assert outline.chapters[0].title == "项目理解"
        assert outline.chapters[1].title == "技术方案"
        assert isinstance(outline.generated_at, datetime)
    
    def test_outline_structure_defaults(self):
        """测试默认值"""
        outline = OutlineStructure()
        
        assert outline.chapters == []
        assert outline.chapter_count == 0
        assert isinstance(outline.generated_at, datetime)


class TestChapterContent:
    """ChapterContent模型测试"""
    
    def test_chapter_content_creation(self):
        """测试章节内容创建"""
        content = ChapterContent(
            chapter_id="1.1",
            chapter_title="项目背景",
            content="这是项目背景的详细内容...",
            word_count=500
        )
        
        assert content.chapter_id == "1.1"
        assert content.chapter_title == "项目背景"
        assert content.content == "这是项目背景的详细内容..."
        assert content.word_count == 500
        assert isinstance(content.generated_at, datetime)
    
    def test_chapter_content_defaults(self):
        """测试默认值"""
        content = ChapterContent(
            chapter_id="1",
            chapter_title="测试章节",
            content="测试内容"
        )
        
        assert content.word_count == 0
        assert isinstance(content.generated_at, datetime)


class TestAPIModels:
    """API请求/响应模型测试"""
    
    def test_create_project_request(self):
        """测试创建项目请求"""
        request = CreateProjectRequest(
            project_name="测试项目",
            source_file_id=123
        )
        
        assert request.project_name == "测试项目"
        assert request.source_file_id == 123
    
    def test_create_project_request_validation(self):
        """测试创建项目请求验证"""
        # 测试空项目名称
        with pytest.raises(ValueError):
            CreateProjectRequest(
                project_name="",
                source_file_id=123
            )
        
        # 测试无效的文件ID
        with pytest.raises(ValueError):
            CreateProjectRequest(
                project_name="测试项目",
                source_file_id=0
            )
    
    def test_project_response(self):
        """测试项目响应"""
        now = datetime.utcnow()
        response = ProjectResponse(
            id="test-project-123",
            project_name="测试项目",
            tenant_id="tenant_12345678",
            user_id="user123",
            source_file_id=123,
            status=TenderStatus.ANALYZING,
            progress=25,
            created_at=now,
            updated_at=now
        )
        
        assert response.id == "test-project-123"
        assert response.project_name == "测试项目"
        # With use_enum_values=True, the status will be converted to string
        assert response.status == 'analyzing'
        assert response.progress == 25