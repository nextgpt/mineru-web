"""大纲质量评估器测试"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from app.services.outline_quality_assessor import OutlineQualityAssessor, QualityMetric, QualityAssessment
from app.models.tender import OutlineStructure, ChapterInfo, SubsectionInfo, AnalysisResult


class TestOutlineQualityAssessor:
    """大纲质量评估器测试"""
    
    @pytest.fixture
    def assessor(self):
        """创建质量评估器实例"""
        return OutlineQualityAssessor()
    
    @pytest.fixture
    def sample_outline(self):
        """示例大纲结构"""
        chapters = [
            ChapterInfo(
                chapter_id="1",
                title="项目理解",
                description="对项目需求的深入理解",
                subsections=[
                    SubsectionInfo(id="1.1", title="项目背景分析"),
                    SubsectionInfo(id="1.2", title="需求理解"),
                    SubsectionInfo(id="1.3", title="目标分析")
                ]
            ),
            ChapterInfo(
                chapter_id="2",
                title="技术方案",
                description="详细的技术实施方案",
                subsections=[
                    SubsectionInfo(id="2.1", title="架构设计"),
                    SubsectionInfo(id="2.2", title="技术选型"),
                    SubsectionInfo(id="2.3", title="系统设计"),
                    SubsectionInfo(id="2.4", title="开发方案")
                ]
            ),
            ChapterInfo(
                chapter_id="3",
                title="实施计划",
                description="项目实施的详细计划",
                subsections=[
                    SubsectionInfo(id="3.1", title="项目管理"),
                    SubsectionInfo(id="3.2", title="进度安排"),
                    SubsectionInfo(id="3.3", title="资源配置")
                ]
            ),
            ChapterInfo(
                chapter_id="4",
                title="质量保证",
                description="质量保证措施",
                subsections=[
                    SubsectionInfo(id="4.1", title="测试方案"),
                    SubsectionInfo(id="4.2", title="质量控制"),
                    SubsectionInfo(id="4.3", title="验收标准")
                ]
            ),
            ChapterInfo(
                chapter_id="5",
                title="服务保障",
                description="服务保障措施",
                subsections=[
                    SubsectionInfo(id="5.1", title="技术支持"),
                    SubsectionInfo(id="5.2", title="运维服务"),
                    SubsectionInfo(id="5.3", title="培训服务")
                ]
            )
        ]
        
        return OutlineStructure(
            chapters=chapters,
            chapter_count=len(chapters),
            generated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_analysis(self):
        """示例分析结果"""
        analysis = Mock(spec=AnalysisResult)
        analysis.project_type = "软件开发"
        analysis.technical_requirements = [
            {"requirement": "系统架构设计要求"},
            {"requirement": "数据库设计规范"},
            {"requirement": "接口开发标准"},
            {"requirement": "安全性要求"},
            {"requirement": "性能指标要求"}
        ]
        return analysis