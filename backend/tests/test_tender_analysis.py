"""
招标分析服务测试
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.tender import TenderProject, TenderStatus, AnalysisResult
from app.models.file import File as FileModel, FileStatus
from app.models.parsed_content import ParsedContent
from app.services.tender_analysis import TenderAnalysisService, AIServiceError
from app.services.tender_storage import TenderStorageService


# 测试数据库设置
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_storage_service():
    """模拟存储服务"""
    storage = Mock(spec=TenderStorageService)
    storage.save_analysis_result = AsyncMock()
    storage.load_analysis_result = AsyncMock()
    return storage


@pytest.fixture
def sample_tender_project(db_session):
    """创建示例招标项目"""
    project = TenderProject(
        id="test-project-123",
        tenant_id="tenant-1",
        user_id="user-1",
        project_name="测试招标项目",
        source_file_id=1,
        status=TenderStatus.ANALYZING,
        minio_path="tenants/tenant-1/projects/test-project-123"
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def sample_file(db_session):
    """创建示例文件"""
    file = FileModel(
        id=1,
        user_id="user-1",
        filename="招标文件.pdf",
        size=1024000,
        status=FileStatus.PARSED,
        minio_path="files/test.pdf",
        content_type="application/pdf"
    )
    db_session.add(file)
    db_session.commit()
    return file


@pytest.fixture
def sample_parsed_content(db_session, sample_file):
    """创建示例解析内容"""
    content = ParsedContent(
        id=1,
        user_id="user-1",
        file_id=sample_file.id,
        content="这是一个测试招标文件的内容，包含项目名称、预算、工期等关键信息。"
    )
    db_session.add(content)
    db_session.commit()
    return content


class TestTenderAnalysisService:
    """招标分析服务测试类"""
    
    def test_init(self, db_session, mock_storage_service):
        """测试服务初始化"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        assert service.db == db_session
        assert service.storage_service == mock_storage_service
    
    def test_init_with_default_storage(self, db_session):
        """测试使用默认存储服务初始化"""
        with patch('app.services.tender_analysis.TenderStorageService') as mock_storage_class:
            service = TenderAnalysisService(db_session)
            assert service.db == db_session
            mock_storage_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_tender_document_success(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project, 
        sample_file, 
        sample_parsed_content
    ):
        """测试成功分析招标文件"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 执行分析
        result = await service.analyze_tender_document(sample_tender_project.id)
        
        # 验证结果
        assert isinstance(result, AnalysisResult)
        assert result.project_info is not None
        assert result.technical_requirements is not None
        assert result.evaluation_criteria is not None
        assert result.submission_requirements is not None
        assert isinstance(result.extracted_at, datetime)
        
        # 验证项目状态更新
        db_session.refresh(sample_tender_project)
        assert sample_tender_project.status == TenderStatus.ANALYZED
        assert sample_tender_project.progress == 100
        
        # 验证存储服务调用
        mock_storage_service.save_analysis_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_tender_document_project_not_found(self, db_session, mock_storage_service):
        """测试项目不存在的情况"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        with pytest.raises(ValueError, match="项目 nonexistent 不存在"):
            await service.analyze_tender_document("nonexistent")
    
    @pytest.mark.asyncio
    async def test_analyze_tender_document_file_not_found(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project
    ):
        """测试源文件不存在的情况"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        with pytest.raises(ValueError, match="源文件 1 不存在"):
            await service.analyze_tender_document(sample_tender_project.id)
    
    @pytest.mark.asyncio
    async def test_analyze_tender_document_no_parsed_content(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project, 
        sample_file
    ):
        """测试文件未解析的情况"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        with pytest.raises(ValueError, match="招标文件尚未解析"):
            await service.analyze_tender_document(sample_tender_project.id)
    
    @pytest.mark.asyncio
    async def test_analyze_tender_document_ai_service_error(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project, 
        sample_file, 
        sample_parsed_content
    ):
        """测试AI服务异常的情况"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 模拟AI服务异常
        with patch.object(service, 'extract_project_info', side_effect=AIServiceError("AI服务不可用")):
            with pytest.raises(AIServiceError):
                await service.analyze_tender_document(sample_tender_project.id)
            
            # 验证项目状态更新为失败
            db_session.refresh(sample_tender_project)
            assert sample_tender_project.status == TenderStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_extract_project_info(self, db_session, mock_storage_service):
        """测试提取项目基本信息"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        content = "项目名称：智慧城市建设项目，预算：500万元，工期：12个月"
        result = await service.extract_project_info(content)
        
        assert isinstance(result, dict)
        assert "project_name" in result
        assert "budget" in result
        assert "duration" in result
        assert "location" in result
        assert "contact_info" in result
    
    @pytest.mark.asyncio
    async def test_extract_project_info_with_error(self, db_session, mock_storage_service):
        """测试提取项目信息时发生异常"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 模拟AI提取异常
        with patch.object(service, '_extract_project_info_with_ai', side_effect=Exception("AI异常")):
            result = await service.extract_project_info("test content")
            
            # 应该返回默认结构而不是抛出异常
            assert isinstance(result, dict)
            assert result["project_name"] == "未识别"
            assert "extraction_error" in result
    
    @pytest.mark.asyncio
    async def test_extract_technical_requirements(self, db_session, mock_storage_service):
        """测试提取技术要求"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        content = "系统应支持1000并发用户，响应时间小于3秒，采用微服务架构"
        result = await service.extract_technical_requirements(content)
        
        assert isinstance(result, dict)
        assert "functional_requirements" in result
        assert "performance_requirements" in result
        assert "technical_specifications" in result
        assert isinstance(result["functional_requirements"], list)
    
    @pytest.mark.asyncio
    async def test_extract_evaluation_criteria(self, db_session, mock_storage_service):
        """测试提取评分标准"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        content = "技术分70分，商务分30分，采用综合评分法"
        result = await service.extract_evaluation_criteria(content)
        
        assert isinstance(result, dict)
        assert "technical_score" in result
        assert "commercial_score" in result
        assert "evaluation_method" in result
        assert isinstance(result["technical_score"], dict)
    
    @pytest.mark.asyncio
    async def test_extract_submission_requirements(self, db_session, mock_storage_service):
        """测试提取提交要求"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        content = "投标文件应为PDF格式，现场提交，截止时间2024年12月31日"
        result = await service.extract_submission_requirements(content)
        
        assert isinstance(result, dict)
        assert "document_format" in result
        assert "submission_method" in result
        assert "required_documents" in result
        assert isinstance(result["required_documents"], list)
    
    @pytest.mark.asyncio
    async def test_mock_ai_extraction_project_info(self, db_session, mock_storage_service):
        """测试模拟AI提取项目信息"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        result = await service._mock_ai_extraction("test prompt", "project_info")
        
        assert isinstance(result, dict)
        assert result["project_name"] == "示例项目名称"
        assert result["budget"] == "100万元"
        assert "note" in result
    
    @pytest.mark.asyncio
    async def test_mock_ai_extraction_technical_requirements(self, db_session, mock_storage_service):
        """测试模拟AI提取技术要求"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        result = await service._mock_ai_extraction("test prompt", "technical_requirements")
        
        assert isinstance(result, dict)
        assert isinstance(result["functional_requirements"], list)
        assert isinstance(result["performance_requirements"], dict)
        assert len(result["functional_requirements"]) > 0
    
    @pytest.mark.asyncio
    async def test_mock_ai_extraction_evaluation_criteria(self, db_session, mock_storage_service):
        """测试模拟AI提取评分标准"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        result = await service._mock_ai_extraction("test prompt", "evaluation_criteria")
        
        assert isinstance(result, dict)
        assert result["technical_score"]["weight"] == 70
        assert result["commercial_score"]["weight"] == 30
        assert result["evaluation_method"] == "综合评分法"
    
    @pytest.mark.asyncio
    async def test_mock_ai_extraction_submission_requirements(self, db_session, mock_storage_service):
        """测试模拟AI提取提交要求"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        result = await service._mock_ai_extraction("test prompt", "submission_requirements")
        
        assert isinstance(result, dict)
        assert result["document_format"] == "PDF格式，A4纸张"
        assert result["submission_method"] == "现场提交 + 电子版"
        assert isinstance(result["required_documents"], list)
    
    @pytest.mark.asyncio
    async def test_mock_ai_extraction_unknown_type(self, db_session, mock_storage_service):
        """测试模拟AI提取未知类型"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        result = await service._mock_ai_extraction("test prompt", "unknown_type")
        
        assert isinstance(result, dict)
        assert "error" in result
        assert "未知的提取类型" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_success(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project
    ):
        """测试成功获取分析结果"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 模拟存储服务返回分析结果
        expected_result = AnalysisResult(
            project_info={"project_name": "测试项目"},
            technical_requirements={},
            evaluation_criteria={},
            submission_requirements={}
        )
        mock_storage_service.load_analysis_result.return_value = expected_result
        
        result = await service.get_analysis_result(sample_tender_project.id)
        
        assert result == expected_result
        mock_storage_service.load_analysis_result.assert_called_once_with(sample_tender_project)
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_project_not_found(self, db_session, mock_storage_service):
        """测试获取不存在项目的分析结果"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        result = await service.get_analysis_result("nonexistent")
        
        assert result is None
        mock_storage_service.load_analysis_result.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_analysis_result_file_not_found(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project
    ):
        """测试获取分析结果文件不存在"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 模拟文件不存在
        mock_storage_service.load_analysis_result.side_effect = FileNotFoundError()
        
        result = await service.get_analysis_result(sample_tender_project.id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_analysis_result_existing(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project
    ):
        """测试更新现有分析结果"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 模拟现有分析结果
        existing_result = AnalysisResult(
            project_info={"project_name": "原项目名称"},
            technical_requirements={"old_req": "value"},
            evaluation_criteria={},
            submission_requirements={}
        )
        mock_storage_service.load_analysis_result.return_value = existing_result
        
        # 更新数据
        update_data = {
            "project_info": {"project_name": "新项目名称", "budget": "200万"},
            "technical_requirements": {"new_req": "new_value"}
        }
        
        result = await service.update_analysis_result(sample_tender_project.id, update_data)
        
        # 验证更新结果
        assert result.project_info["project_name"] == "新项目名称"
        assert result.project_info["budget"] == "200万"
        assert result.technical_requirements["old_req"] == "value"
        assert result.technical_requirements["new_req"] == "new_value"
        
        mock_storage_service.save_analysis_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_analysis_result_new(
        self, 
        db_session, 
        mock_storage_service, 
        sample_tender_project
    ):
        """测试创建新的分析结果"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        # 模拟文件不存在
        mock_storage_service.load_analysis_result.side_effect = FileNotFoundError()
        
        # 更新数据
        update_data = {
            "project_info": {"project_name": "新项目"},
            "technical_requirements": {"req": "value"}
        }
        
        result = await service.update_analysis_result(sample_tender_project.id, update_data)
        
        # 验证新创建的结果
        assert result.project_info["project_name"] == "新项目"
        assert result.technical_requirements["req"] == "value"
        assert isinstance(result.extracted_at, datetime)
        
        mock_storage_service.save_analysis_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_analysis_result_project_not_found(self, db_session, mock_storage_service):
        """测试更新不存在项目的分析结果"""
        service = TenderAnalysisService(db_session, mock_storage_service)
        
        with pytest.raises(ValueError, match="项目 nonexistent 不存在"):
            await service.update_analysis_result("nonexistent", {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])