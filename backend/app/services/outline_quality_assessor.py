"""大纲质量评估器
提供全面的大纲质量评估和改进建议
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from app.models.tender import OutlineStructure, AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class QualityMetric:
    """质量指标"""
    name: str
    score: float
    max_score: float
    weight: float
    description: str
    issues: List[str]
    suggestions: List[str]


@dataclass
class QualityAssessment:
    """质量评估结果"""
    overall_score: float
    max_score: float
    quality_level: str
    metrics: List[QualityMetric]
    summary: Dict[str, Any]
    recommendations: List[str]
    assessed_at: datetime


class OutlineQualityAssessor:
    """大纲质量评估器"""
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 90,
            "good": 80,
            "fair": 70,
            "poor": 60,
            "very_poor": 0
        }
        
        self.essential_chapters = [
            "项目理解", "需求分析", "项目概述", "咨询理解",
            "技术方案", "系统设计", "开发方案", "咨询方法",
            "实施计划", "实施方案", "工作计划",
            "质量保证", "测试方案"
        ]
        
        self.technical_keywords = [
            "架构", "设计", "技术", "开发", "实现", "方案"
        ]    
def assess_outline_quality(self, outline: OutlineStructure, analysis: AnalysisResult) -> QualityAssessment:
        """评估大纲质量
        
        Args:
            outline: 大纲结构
            analysis: 分析结果
            
        Returns:
            QualityAssessment: 质量评估结果
        """
        logger.info("开始评估大纲质量")
        
        metrics = []
        
        # 1. 结构完整性评估
        structure_metric = self._assess_structure_completeness(outline)
        metrics.append(structure_metric)
        
        # 2. 内容覆盖度评估
        coverage_metric = self._assess_content_coverage(outline, analysis)
        metrics.append(coverage_metric)
        
        # 3. 逻辑性评估
        logic_metric = self._assess_logical_structure(outline)
        metrics.append(logic_metric)
        
        # 4. 专业性评估
        professionalism_metric = self._assess_professionalism(outline, analysis)
        metrics.append(professionalism_metric)
        
        # 计算总分
        total_weighted_score = sum(m.score * m.weight for m in metrics)
        total_weight = sum(m.weight for m in metrics)
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # 确定质量等级
        quality_level = self._determine_quality_level(overall_score)
        
        # 生成改进建议
        recommendations = self._generate_recommendations(metrics, outline, analysis)
        
        # 创建摘要
        summary = self._create_summary(outline, metrics, overall_score)
        
        assessment = QualityAssessment(
            overall_score=overall_score,
            max_score=100.0,
            quality_level=quality_level,
            metrics=metrics,
            summary=summary,
            recommendations=recommendations,
            assessed_at=datetime.utcnow()
        )
        
        logger.info(f"大纲质量评估完成，总分: {overall_score:.1f}, 等级: {quality_level}")
        return assessment    
  
  def _assess_structure_completeness(self, outline: OutlineStructure) -> QualityMetric:
        """评估结构完整性"""
        issues = []
        suggestions = []
        score = 0
        max_score = 25
        
        chapter_count = outline.chapter_count
        
        # 章节数量评估
        if 5 <= chapter_count <= 8:
            score += 10
        elif 3 <= chapter_count <= 10:
            score += 8
            suggestions.append("建议章节数量控制在5-8个之间以保持最佳结构")
        else:
            score += 5
            issues.append(f"章节数量({chapter_count})不够合理，建议5-8个章节")
        
        # 子章节分布评估
        total_subsections = sum(len(chapter.subsections) for chapter in outline.chapters)
        avg_subsections = total_subsections / chapter_count if chapter_count > 0 else 0
        
        if 3 <= avg_subsections <= 6:
            score += 10
        elif 2 <= avg_subsections <= 7:
            score += 8
            suggestions.append("建议每个章节包含3-6个子章节")
        else:
            score += 5
            issues.append(f"子章节数量不够合理，平均每章{avg_subsections:.1f}个")
        
        # 章节标题质量评估
        title_quality_score = 0
        for chapter in outline.chapters:
            if len(chapter.title) >= 4 and len(chapter.title) <= 20:
                title_quality_score += 1
            if chapter.description and len(chapter.description) >= 10:
                title_quality_score += 1
        
        title_score = (title_quality_score / (chapter_count * 2)) * 5 if chapter_count > 0 else 0
        score += title_score
        
        if title_score < 3:
            suggestions.append("建议完善章节标题和描述，使其更加清晰明确")
        
        return QualityMetric(
            name="结构完整性",
            score=score,
            max_score=max_score,
            weight=0.25,
            description="评估大纲的整体结构是否完整、合理",
            issues=issues,
            suggestions=suggestions
        )  
  
    def _assess_content_coverage(self, outline: OutlineStructure, analysis: AnalysisResult) -> QualityMetric:
        """评估内容覆盖度"""
        issues = []
        suggestions = []
        score = 0
        max_score = 25
        
        # 检查必要章节覆盖
        found_essential = 0
        outline_text = self._get_outline_text(outline)
        
        for essential in self.essential_chapters:
            if essential in outline_text:
                found_essential += 1
        
        essential_score = (found_essential / len(self.essential_chapters)) * 15
        score += essential_score
        
        if essential_score < 10:
            missing_count = len(self.essential_chapters) - found_essential
            issues.append(f"缺少{missing_count}个核心章节类型")
            suggestions.append("建议增加项目理解、技术方案、实施计划、质量保证等核心章节")
        
        # 检查技术要求覆盖
        tech_coverage = self._calculate_technical_coverage(outline, analysis)
        score += tech_coverage * 10
        
        if tech_coverage < 0.7:
            issues.append("技术要求覆盖不足")
            suggestions.append("建议增加更多技术相关内容以满足招标要求")
        
        return QualityMetric(
            name="内容覆盖度",
            score=score,
            max_score=max_score,
            weight=0.3,
            description="评估大纲内容是否全面覆盖招标要求",
            issues=issues,
            suggestions=suggestions
        )
    
    def _assess_logical_structure(self, outline: OutlineStructure) -> QualityMetric:
        """评估逻辑结构"""
        issues = []
        suggestions = []
        score = 0
        max_score = 20
        
        chapters = outline.chapters
        if not chapters:
            return QualityMetric(
                name="逻辑结构",
                score=0,
                max_score=max_score,
                weight=0.2,
                description="评估大纲的逻辑结构是否合理",
                issues=["大纲没有章节"],
                suggestions=["请添加章节内容"]
            )
        
        # 检查章节顺序逻辑
        logical_patterns = ["理解", "方案", "实施", "质量", "服务"]
        pattern_matches = 0
        
        for i, pattern in enumerate(logical_patterns):
            for j, chapter in enumerate(chapters):
                if pattern in chapter.title and j >= i * (len(chapters) // len(logical_patterns)):
                    pattern_matches += 1
                    break
        
        logic_score = (pattern_matches / len(logical_patterns)) * 20
        score += logic_score
        
        if logic_score < 15:
            issues.append("章节逻辑顺序不够合理")
            suggestions.append("建议按照理解→方案→实施→质量→服务的逻辑顺序组织章节")
        
        return QualityMetric(
            name="逻辑结构",
            score=score,
            max_score=max_score,
            weight=0.2,
            description="评估大纲的逻辑结构是否合理",
            issues=issues,
            suggestions=suggestions
        ) 
   
    def _assess_professionalism(self, outline: OutlineStructure, analysis: AnalysisResult) -> QualityMetric:
        """评估专业性"""
        issues = []
        suggestions = []
        score = 0
        max_score = 30
        
        outline_text = self._get_outline_text(outline)
        
        # 技术术语使用评估
        tech_term_count = sum(1 for keyword in self.technical_keywords if keyword in outline_text)
        tech_score = min(tech_term_count / 5, 1.0) * 15
        score += tech_score
        
        if tech_score < 10:
            issues.append("技术术语使用不足")
            suggestions.append("建议增加更多专业技术术语以提升专业性")
        
        # 行业标准符合度评估
        if analysis and hasattr(analysis, 'project_type'):
            industry_score = self._assess_industry_standards(outline, analysis.project_type)
            score += industry_score
        else:
            score += 7.5  # 默认中等分数
        
        return QualityMetric(
            name="专业性",
            score=score,
            max_score=max_score,
            weight=0.25,
            description="评估大纲的专业性和行业标准符合度",
            issues=issues,
            suggestions=suggestions
        )
    
    def _get_outline_text(self, outline: OutlineStructure) -> str:
        """获取大纲的文本内容"""
        text_parts = []
        for chapter in outline.chapters:
            text_parts.append(chapter.title)
            if chapter.description:
                text_parts.append(chapter.description)
            for subsection in chapter.subsections:
                text_parts.append(subsection.title)
                if hasattr(subsection, 'description') and subsection.description:
                    text_parts.append(subsection.description)
        return " ".join(text_parts)
    
    def _calculate_technical_coverage(self, outline: OutlineStructure, analysis: AnalysisResult) -> float:
        """计算技术要求覆盖度"""
        if not analysis or not hasattr(analysis, 'technical_requirements'):
            return 0.5  # 默认中等覆盖度
        
        outline_text = self._get_outline_text(outline).lower()
        tech_requirements = analysis.technical_requirements or []
        
        if not tech_requirements:
            return 0.5
        
        covered_count = 0
        for req in tech_requirements:
            if isinstance(req, dict) and 'requirement' in req:
                req_text = req['requirement'].lower()
                # 简单的关键词匹配
                key_words = req_text.split()[:3]  # 取前3个关键词
                if any(word in outline_text for word in key_words):
                    covered_count += 1
        
        return covered_count / len(tech_requirements) if tech_requirements else 0.5
    
    def _assess_industry_standards(self, outline: OutlineStructure, project_type: str) -> float:
        """评估行业标准符合度"""
        # 根据项目类型评估标准符合度
        standard_keywords = {
            "软件开发": ["需求分析", "系统设计", "测试", "部署", "运维"],
            "基础设施": ["网络", "安全", "监控", "备份", "容灾"],
            "咨询服务": ["调研", "分析", "建议", "实施", "评估"]
        }
        
        outline_text = self._get_outline_text(outline)
        keywords = standard_keywords.get(project_type, standard_keywords["软件开发"])
        
        found_keywords = sum(1 for keyword in keywords if keyword in outline_text)
        return (found_keywords / len(keywords)) * 15   
 
    def _determine_quality_level(self, score: float) -> str:
        """确定质量等级"""
        for level, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return level
        return "very_poor"
    
    def _generate_recommendations(self, metrics: List[QualityMetric], outline: OutlineStructure, analysis: AnalysisResult) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 收集所有建议
        for metric in metrics:
            recommendations.extend(metric.suggestions)
        
        # 添加基于整体分析的建议
        if outline.chapter_count < 5:
            recommendations.append("建议增加章节数量，确保内容的全面性")
        elif outline.chapter_count > 10:
            recommendations.append("建议合并相关章节，避免结构过于复杂")
        
        # 去重并排序
        recommendations = list(set(recommendations))
        return recommendations[:10]  # 限制建议数量
    
    def _create_summary(self, outline: OutlineStructure, metrics: List[QualityMetric], overall_score: float) -> Dict[str, Any]:
        """创建评估摘要"""
        return {
            "chapter_count": outline.chapter_count,
            "total_subsections": sum(len(chapter.subsections) for chapter in outline.chapters),
            "avg_subsections_per_chapter": sum(len(chapter.subsections) for chapter in outline.chapters) / outline.chapter_count if outline.chapter_count > 0 else 0,
            "metric_scores": {metric.name: metric.score for metric in metrics},
            "overall_score": overall_score,
            "strengths": [metric.name for metric in metrics if metric.score / metric.max_score > 0.8],
            "weaknesses": [metric.name for metric in metrics if metric.score / metric.max_score < 0.6],
            "total_issues": sum(len(metric.issues) for metric in metrics),
            "total_suggestions": sum(len(metric.suggestions) for metric in metrics)
        }


# 全局质量评估器实例
_quality_assessor = None

def get_quality_assessor() -> OutlineQualityAssessor:
    """获取质量评估器实例"""
    global _quality_assessor
    if _quality_assessor is None:
        _quality_assessor = OutlineQualityAssessor()
    return _quality_assessor