"""
大纲生成服务测试
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.outline_generation import OutlineGenerationService, OutlineTemplateEngine
from app.models.tender import (
    TenderProject, 
    TenderStatus, 
    AnalysisResult,
    OutlineStructure,
    ChapterInfo
)
from app.services.tender_storage import TenderStorageService
from app.services.ai_client import AIServiceError


class TestOutlineTemplateEngine:
    """大纲模板引擎测试"""
    
    def test_get_default_template(self):
        """测试获取默认模板"""
        template = OutlineTemplateEngine.get_default_template()
        
        assert isinstance(template, list)
        assert len(template) > 0
        
        # 检查模板结构
        for chapter in template:
            assert "chapter_id" in chapter
            assert "title" in chapter
            assert "description" in chapter
            assert "subsections" in chapter
            assert isinstance(chapter["subsections"], list)
    
    def test_get_template_by_type_software(self):
        """测试获取软件开发模板"""
        template = OutlineTemplateEngine.get_template_by_type("software_development")
        
        assert isinstance(template, list)
        assert len(template) > 0
        
        # 检查是否包含软件开发相关章节
        titles = [chapter["title"] for chapter in template]
        assert any("系统设计" in title or "开发方案" in title for title in titles)
    
    def test_get_template_by_type_infrastructure(self):
        """测试获取基础设施模板"""
        template = OutlineTemplateEngine.get_template_by_type("infrastructure")
        
        assert isinstance(template, list)
        assert len(template) > 0
        
        # 检查是否包含基础设施相关章节
        titles = [chapter["title"] for chapter in template]
        assert any("网络架构" in str(chapter) or "硬件配置" in str(chapter) for chapter in template)
    
    def test_get_template_by_type_unknown(self):
        """测试获取未知类型模板，应返回默认模板"""
        template = OutlineTemplateEngine.get_template_by_type("unknown_type")
        default_template = OutlineTemplateEngine.get_default_template()
        
        assert template == default_template
    
    def test_detect_project_type_software(self):
        """测试检测软件项目类型"""
        analysis = AnalysisResult(
            project_info={
                "project_name": "某某管理系统开发项目",
                "project_overview": "开发一套完整的信息管理系统"
            },
            technical_requirements={},
            evaluation_criteria={},
            submission_requirements={}
        )
        
        project_type = OutlineTemplateEngine.detect_project_type(analysis)
        assert project_type == "software_development"
    
    def test_detect_project_type_infrastructure(self):
        """测试检测基础设施项目类型"""
        analysis = AnalysisResult(
            project_info={
                "project_name": "数据中心网络建设项目",
                "project_overview": "建设企业级网络基础设施"
            },
            technical_requirements={},
            evaluation_criteria={},
            submission_requirements={}
        )
        
        project_type = OutlineTemplateEngine.detect_project_type(analysis)
        assert project_type == "infrastructure"
    
    def test_detect_project_type_consulting(self):
        """测试检测咨询项目类型"""
        analysis = AnalysisResult(
            project_info={
                "project_name": "IT规划咨询项目",
                "project_overview": "为企业提供信息化规划咨询服务"
            },
            technical_requirements={},
            evaluation_criteria={},
            submission_requirements={}
        )
        
        project_type = OutlineTemplateEngine.detect_project_type(analysis)
        assert project_type == "consulting"
    
    def test_detect_project_type_general(self):
        """测试检测通用项目类型"""
        analysis = AnalysisResult(
            project_info={
                "project_name": "某某项目",
                "project_overview": "一般性项目描述"
            },
            technical_requirements={},
            evaluation_criteria={},
            submission_requirements={}
        )
        
        project_type = OutlineTemplateEngine.detect_project_type(analysis)
        assert project_type == "general"


class TestOutlineGenerationService:
    """大纲生成服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_storage(self):
        """模拟存储服务"""
        storage = Mock(spec=TenderStorageService)
        storage.load_analysis_result = AsyncMock()
        storage.save_outline = AsyncMock()
        storage.load_outline = AsyncMock()
        return storage
    
    @pytest.fixture
    def mock_ai_client(self):
        """模拟AI客户端"""
        ai_client = Mock()
        ai_client.generate_structured = AsyncMock()
        return ai_client
    
    @pytest.fixture
    def service(self, mock_db, mock_storage, mock_ai_client):
        """创建服务实例"""
        return OutlineGenerationService(
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
            status=TenderStatus.ANALYZED,
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
    
    @pytest.mark.asyncio
    async def test_generate_outline_with_ai_success(self, service, mock_db, mock_storage, mock_ai_client, sample_project, sample_analysis):
        """测试使用AI成功生成大纲"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_analysis_result.return_value = sample_analysis
        
        # 模拟AI返回结果
        ai_result = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "项目理解",
                    "description": "对项目的深入理解",
                    "subsections": [
                        {"id": "1.1", "title": "项目背景"},
                        {"id": "1.2", "title": "需求分析"}
                    ]
                },
                {
                    "chapter_id": "2",
                    "title": "技术方案",
                    "description": "详细的技术实施方案",
                    "subsections": [
                        {"id": "2.1", "title": "架构设计"},
                        {"id": "2.2", "title": "技术选型"}
                    ]
                }
            ]
        }
        mock_ai_client.generate_structured.return_value = ai_result
        
        # 执行测试
        result = await service.generate_outline("test-project-id", use_ai=True)
        
        # 验证结果
        assert isinstance(result, OutlineStructure)
        assert result.chapter_count == 2
        assert len(result.chapters) == 2
        assert result.chapters[0].title == "项目理解"
        assert result.chapters[1].title == "技术方案"
        
        # 验证调用
        mock_storage.load_analysis_result.assert_called_once()
        mock_storage.save_outline.assert_called_once()
        mock_ai_client.generate_structured.assert_called_once()
        
        # 验证项目状态更新
        assert sample_project.status == TenderStatus.OUTLINED
        assert sample_project.progress == 100
    
    @pytest.mark.asyncio
    async def test_generate_outline_with_template(self, service, mock_db, mock_storage, sample_project, sample_analysis):
        """测试使用模板生成大纲"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_analysis_result.return_value = sample_analysis
        
        # 执行测试
        result = await service.generate_outline("test-project-id", use_ai=False)
        
        # 验证结果
        assert isinstance(result, OutlineStructure)
        assert result.chapter_count > 0
        assert len(result.chapters) > 0
        
        # 验证调用
        mock_storage.load_analysis_result.assert_called_once()
        mock_storage.save_outline.assert_called_once()
        
        # 验证项目状态更新
        assert sample_project.status == TenderStatus.OUTLINED
    
    @pytest.mark.asyncio
    async def test_generate_outline_ai_fallback_to_template(self, service, mock_db, mock_storage, mock_ai_client, sample_project, sample_analysis):
        """测试AI失败时降级到模板"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_analysis_result.return_value = sample_analysis
        mock_ai_client.generate_structured.side_effect = AIServiceError("AI服务不可用")
        
        # 执行测试
        result = await service.generate_outline("test-project-id", use_ai=True)
        
        # 验证结果 - 应该使用模板生成
        assert isinstance(result, OutlineStructure)
        assert result.chapter_count > 0
        
        # 验证AI被调用但失败
        mock_ai_client.generate_structured.assert_called_once()
        
        # 验证最终状态
        assert sample_project.status == TenderStatus.OUTLINED
    
    @pytest.mark.asyncio
    async def test_generate_outline_project_not_found(self, service, mock_db):
        """测试项目不存在的情况"""
        # 设置模拟 - 项目不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="项目 .* 不存在"):
            await service.generate_outline("non-existent-project")
    
    @pytest.mark.asyncio
    async def test_customize_outline_success(self, service, mock_db, mock_storage, sample_project):
        """测试成功定制大纲"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        # 现有大纲
        existing_outline = OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="原始标题",
                    description="原始描述",
                    subsections=[{"id": "1.1", "title": "原始子章节"}]
                )
            ],
            chapter_count=1
        )
        mock_storage.load_outline.return_value = existing_outline
        
        # 用户修改
        user_input = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "修改后的标题",
                    "description": "修改后的描述",
                    "subsections": [
                        {"id": "1.1", "title": "修改后的子章节"},
                        {"id": "1.2", "title": "新增子章节"}
                    ]
                }
            ]
        }
        
        # 执行测试
        result = await service.customize_outline("test-project-id", user_input)
        
        # 验证结果
        assert isinstance(result, OutlineStructure)
        assert result.chapter_count == 1
        assert result.chapters[0].title == "修改后的标题"
        assert result.chapters[0].description == "修改后的描述"
        assert len(result.chapters[0].subsections) == 2
        
        # 验证保存
        mock_storage.save_outline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customize_outline_no_existing_outline(self, service, mock_db, mock_storage, sample_project, sample_analysis):
        """测试没有现有大纲时的定制"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_outline.side_effect = FileNotFoundError("大纲不存在")
        mock_storage.load_analysis_result.return_value = sample_analysis
        
        # 用户修改
        user_input = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "新标题",
                    "description": "新描述",
                    "subsections": [{"id": "1.1", "title": "新子章节"}]
                }
            ]
        }
        
        # 执行测试
        result = await service.customize_outline("test-project-id", user_input)
        
        # 验证结果
        assert isinstance(result, OutlineStructure)
        assert result.chapters[0].title == "新标题"
        
        # 验证先生成了默认大纲，然后应用了修改
        assert mock_storage.save_outline.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_get_outline_success(self, service, mock_db, mock_storage, sample_project):
        """测试成功获取大纲"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        expected_outline = OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="测试章节",
                    description="测试描述",
                    subsections=[]
                )
            ],
            chapter_count=1
        )
        mock_storage.load_outline.return_value = expected_outline
        
        # 执行测试
        result = await service.get_outline("test-project-id")
        
        # 验证结果
        assert result == expected_outline
        mock_storage.load_outline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_outline_not_found(self, service, mock_db, mock_storage, sample_project):
        """测试大纲不存在的情况"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_storage.load_outline.side_effect = FileNotFoundError("大纲不存在")
        
        # 执行测试
        result = await service.get_outline("test-project-id")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_outline_project_not_found(self, service, mock_db):
        """测试项目不存在时获取大纲"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行测试
        result = await service.get_outline("non-existent-project")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_outline_quality(self, service, sample_analysis):
        """测试大纲质量评估"""
        # 创建测试大纲
        outline = OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="项目理解",
                    description="对项目的深入理解",
                    subsections=[
                        {"id": "1.1", "title": "项目背景"},
                        {"id": "1.2", "title": "需求分析"},
                        {"id": "1.3", "title": "目标确定"}
                    ]
                ),
                ChapterInfo(
                    chapter_id="2",
                    title="技术方案",
                    description="详细的技术方案",
                    subsections=[
                        {"id": "2.1", "title": "架构设计"},
                        {"id": "2.2", "title": "技术选型"},
                        {"id": "2.3", "title": "安全设计"}
                    ]
                ),
                ChapterInfo(
                    chapter_id="3",
                    title="实施计划",
                    description="项目实施计划",
                    subsections=[
                        {"id": "3.1", "title": "进度安排"},
                        {"id": "3.2", "title": "资源配置"}
                    ]
                ),
                ChapterInfo(
                    chapter_id="4",
                    title="质量保证",
                    description="质量保证措施",
                    subsections=[
                        {"id": "4.1", "title": "测试方案"},
                        {"id": "4.2", "title": "验收标准"}
                    ]
                )
            ],
            chapter_count=4
        )
        
        # 执行测试
        result = await service.validate_outline_quality(outline, sample_analysis)
        
        # 验证结果
        assert isinstance(result, dict)
        assert "quality_score" in result
        assert "quality_level" in result
        assert "chapter_count" in result
        assert "issues" in result
        assert "suggestions" in result
        
        assert result["chapter_count"] == 4
        assert 0 <= result["quality_score"] <= 100
        assert result["quality_level"] in ["优秀", "良好", "中等", "及格", "需要改进"]
    
    def test_validate_outline_structure_valid(self, service):
        """测试有效的大纲结构验证"""
        valid_data = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "测试章节",
                    "description": "测试描述",
                    "subsections": [
                        {"id": "1.1", "title": "子章节1"},
                        {"id": "1.2", "title": "子章节2"}
                    ]
                }
            ]
        }
        
        result = service._validate_outline_structure(valid_data)
        assert result is True
    
    def test_validate_outline_structure_invalid(self, service):
        """测试无效的大纲结构验证"""
        # 缺少必需字段
        invalid_data = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "测试章节"
                    # 缺少 description 和 subsections
                }
            ]
        }
        
        result = service._validate_outline_structure(invalid_data)
        assert result is False
        
        # 空章节列表
        empty_data = {"chapters": []}
        result = service._validate_outline_structure(empty_data)
        assert result is False
        
        # 不是字典类型
        result = service._validate_outline_structure("not a dict")
        assert result is False
    
    def test_apply_user_modifications_complete_replacement(self, service):
        """测试完整替换用户修改"""
        current_chapters = [
            ChapterInfo(
                chapter_id="1",
                title="原始标题",
                description="原始描述",
                subsections=[]
            )
        ]
        
        user_input = {
            "chapters": [
                {
                    "chapter_id": "1",
                    "title": "新标题",
                    "description": "新描述",
                    "subsections": [{"id": "1.1", "title": "新子章节"}]
                }
            ]
        }
        
        result = service._apply_user_modifications(current_chapters, user_input)
        
        assert len(result) == 1
        assert result[0].title == "新标题"
        assert result[0].description == "新描述"
        assert len(result[0].subsections) == 1
    
    def test_apply_user_modifications_incremental(self, service):
        """测试增量修改"""
        current_chapters = [
            ChapterInfo(
                chapter_id="1",
                title="原始标题",
                description="原始描述",
                subsections=[{"id": "1.1", "title": "原始子章节"}]
            )
        ]
        
        user_input = {
            "chapter_1": {
                "title": "修改后的标题",
                "subsections": [
                    {"id": "1.1", "title": "修改后的子章节"},
                    {"id": "1.2", "title": "新增子章节"}
                ]
            }
        }
        
        result = service._apply_user_modifications(current_chapters, user_input)
        
        assert len(result) == 1
        assert result[0].title == "修改后的标题"
        assert result[0].description == "原始描述"  # 未修改的保持原样
        assert len(result[0].subsections) == 2
    
    def test_calculate_requirement_matching(self, service, sample_analysis):
        """测试需求匹配度计算"""
        outline = OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="用户管理方案",
                    description="包含用户认证和数据加密功能",
                    subsections=[
                        {"id": "1.1", "title": "用户管理"},
                        {"id": "1.2", "title": "数据管理"}
                    ]
                )
            ],
            chapter_count=1
        )
        
        score = service._calculate_requirement_matching(outline, sample_analysis)
        
        # 应该有一定的匹配度，因为大纲包含了分析结果中的关键词
        assert 0 <= score <= 25
        assert score > 0  # 应该有一些匹配
    
    def test_adjust_template_by_analysis(self, service, sample_analysis):
        """测试根据分析结果调整模板"""
        template_chapters = [
            {
                "chapter_id": "1",
                "title": "技术方案",
                "description": "技术实施方案",
                "subsections": [
                    {"id": "1.1", "title": "基础架构"}
                ]
            }
        ]
        
        result = service._adjust_template_by_analysis(template_chapters, sample_analysis)
        
        # 验证调整结果
        assert len(result) == 1
        tech_chapter = result[0]
        assert tech_chapter["title"] == "技术方案"
        
        # 应该根据安全要求添加了安全方案子章节
        subsection_titles = [sub["title"] for sub in tech_chapter["subsections"]]
        assert "安全方案" in subsection_titles


    @pytest.mark.asyncio
    async def test_optimize_outline_success(self, service, mock_ai_client, sample_analysis):
        """测试大纲优化成功"""
        # 创建测试大纲
        outline = OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="项目理解",
                    description="项目理解描述",
                    subsections=[{"id": "1.1", "title": "背景分析"}]
                )
            ],
            chapter_count=1
        )
        
        # 模拟AI优化结果
        optimization_result = {
            "quality_score": 85,
            "strengths": ["结构清晰", "逻辑合理"],
            "weaknesses": ["内容不够详细"],
            "suggestions": ["增加技术细节", "补充实施方案"],
            "optimized_outline": {
                "chapters": [
                    {
                        "chapter_id": "1",
                        "title": "项目理解与分析",
                        "description": "深入的项目理解和需求分析",
                        "subsections": [
                            {"id": "1.1", "title": "项目背景分析"},
                            {"id": "1.2", "title": "需求深度解析"}
                        ]
                    }
                ]
            }
        }
        mock_ai_client.generate_structured.return_value = optimization_result
        
        # 执行测试
        result = await service.optimize_outline("test-project", outline, sample_analysis)
        
        # 验证结果
        assert isinstance(result, dict)
        assert "quality_score" in result
        assert "optimized_outline_object" in result
        assert isinstance(result["optimized_outline_object"], OutlineStructure)
        
        # 验证AI调用
        mock_ai_client.generate_structured.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_optimize_outline_ai_failure(self, service, mock_ai_client, sample_analysis):
        """测试AI优化失败时的降级处理"""
        outline = OutlineStructure(
            chapters=[
                ChapterInfo(
                    chapter_id="1",
                    title="项目理解",
                    description="项目理解描述",
                    subsections=[{"id": "1.1", "title": "背景分析"}]
                )
            ],
            chapter_count=1
        )
        
        # 模拟AI失败
        mock_ai_client.generate_structured.side_effect = AIServiceError("AI服务不可用")
        
        # 执行测试
        result = await service.optimize_outline("test-project", outline, sample_analysis)
        
        # 验证降级结果
        assert isinstance(result, dict)
        assert "quality_score" in result
        assert "note" in result
        assert "AI优化服务不可用" in result["note"]
    
    @pytest.mark.asyncio
    async def test_generate_outline_variations(self, service, sample_analysis):
        """测试生成大纲变体"""
        # 执行测试
        variations = await service.generate_outline_variations("test-project", sample_analysis, count=3)
        
        # 验证结果
        assert isinstance(variations, list)
        assert len(variations) >= 1  # 至少有一个变体
        assert len(variations) <= 3  # 不超过请求数量
        
        for variation in variations:
            assert isinstance(variation, OutlineStructure)
            # 由于AI可能失败，至少要有一个基于模板的变体
            if variation.chapter_count == 0:
                # 如果某个变体为空，跳过检查，但至少要有一个非空变体
                continue
            assert variation.chapter_count > 0
            assert len(variation.chapters) > 0
        
        # 确保至少有一个非空变体
        non_empty_variations = [v for v in variations if v.chapter_count > 0]
        assert len(non_empty_variations) >= 1, "至少应该有一个非空的大纲变体"
    
    @pytest.mark.asyncio
    async def test_generate_outline_variations_with_ai_failure(self, service, mock_ai_client, sample_analysis):
        """测试AI失败时仍能生成变体"""
        # 模拟AI失败
        mock_ai_client.generate_structured.side_effect = AIServiceError("AI服务不可用")
        
        # 执行测试
        variations = await service.generate_outline_variations("test-project", sample_analysis, count=2)
        
        # 验证结果 - 即使AI失败也应该有基于模板的变体
        assert isinstance(variations, list)
        assert len(variations) >= 1
        
        for variation in variations:
            assert isinstance(variation, OutlineStructure)
            assert variation.chapter_count > 0
    
    def test_build_outline_generation_prompt_with_project_type(self, service, sample_analysis):
        """测试根据项目类型构建提示词"""
        # 修改分析结果为软件项目
        sample_analysis.project_info["project_name"] = "某某管理系统开发项目"
        
        # 执行测试
        prompt = service._build_outline_generation_prompt(sample_analysis)
        
        # 验证结果
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "软件" in prompt or "系统设计" in prompt or "开发方案" in prompt
    
    def test_build_outline_generation_prompt_general(self, service, sample_analysis):
        """测试通用项目类型的提示词构建"""
        # 修改分析结果为通用项目
        sample_analysis.project_info["project_name"] = "通用项目"
        sample_analysis.project_info["project_overview"] = "一般性项目"
        
        # 执行测试
        prompt = service._build_outline_generation_prompt(sample_analysis)
        
        # 验证结果
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "大纲" in prompt


if __name__ == "__main__":
    pytest.main([__file__])