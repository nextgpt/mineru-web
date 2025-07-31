"""
大纲生成服务
基于分析结果智能生成标书大纲
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.tender import (
    TenderProject, 
    TenderStatus, 
    AnalysisResult,
    OutlineStructure,
    ChapterInfo
)
from app.services.tender_storage import TenderStorageService
from app.services.ai_client import get_ai_client, AIServiceError, PromptTemplates

logger = logging.getLogger(__name__)


class OutlineTemplateEngine:
    """大纲模板引擎"""
    
    @staticmethod
    def get_default_template() -> List[Dict[str, Any]]:
        """获取默认标书大纲模板"""
        return [
            {
                "chapter_id": "1",
                "title": "项目理解",
                "description": "对招标项目的深入理解和分析",
                "subsections": [
                    {"id": "1.1", "title": "项目背景分析"},
                    {"id": "1.2", "title": "需求理解"},
                    {"id": "1.3", "title": "项目目标"}
                ]
            },
            {
                "chapter_id": "2", 
                "title": "技术方案",
                "description": "详细的技术实施方案",
                "subsections": [
                    {"id": "2.1", "title": "总体架构设计"},
                    {"id": "2.2", "title": "技术选型"},
                    {"id": "2.3", "title": "功能设计"},
                    {"id": "2.4", "title": "性能设计"}
                ]
            },
            {
                "chapter_id": "3",
                "title": "实施计划",
                "description": "项目实施的详细计划安排",
                "subsections": [
                    {"id": "3.1", "title": "项目组织架构"},
                    {"id": "3.2", "title": "实施进度安排"},
                    {"id": "3.3", "title": "里程碑计划"},
                    {"id": "3.4", "title": "资源配置"}
                ]
            },
            {
                "chapter_id": "4",
                "title": "质量保证",
                "description": "项目质量保证措施和方案",
                "subsections": [
                    {"id": "4.1", "title": "质量管理体系"},
                    {"id": "4.2", "title": "测试方案"},
                    {"id": "4.3", "title": "验收标准"},
                    {"id": "4.4", "title": "风险控制"}
                ]
            },
            {
                "chapter_id": "5",
                "title": "服务保障",
                "description": "项目服务保障和售后支持",
                "subsections": [
                    {"id": "5.1", "title": "培训方案"},
                    {"id": "5.2", "title": "运维支持"},
                    {"id": "5.3", "title": "技术支持"},
                    {"id": "5.4", "title": "升级维护"}
                ]
            },
            {
                "chapter_id": "6",
                "title": "商务条款",
                "description": "商务相关条款和承诺",
                "subsections": [
                    {"id": "6.1", "title": "报价说明"},
                    {"id": "6.2", "title": "付款方式"},
                    {"id": "6.3", "title": "交付承诺"},
                    {"id": "6.4", "title": "售后服务"}
                ]
            }
        ]
    
    @staticmethod
    def get_template_by_type(project_type: str) -> List[Dict[str, Any]]:
        """根据项目类型获取专用模板"""
        templates = {
            "software_development": [
                {
                    "chapter_id": "1",
                    "title": "项目理解",
                    "description": "软件开发项目理解",
                    "subsections": [
                        {"id": "1.1", "title": "业务需求分析"},
                        {"id": "1.2", "title": "功能需求理解"},
                        {"id": "1.3", "title": "非功能需求分析"}
                    ]
                },
                {
                    "chapter_id": "2",
                    "title": "系统设计",
                    "description": "软件系统架构设计",
                    "subsections": [
                        {"id": "2.1", "title": "系统架构设计"},
                        {"id": "2.2", "title": "数据库设计"},
                        {"id": "2.3", "title": "接口设计"},
                        {"id": "2.4", "title": "安全设计"}
                    ]
                },
                {
                    "chapter_id": "3",
                    "title": "开发方案",
                    "description": "软件开发实施方案",
                    "subsections": [
                        {"id": "3.1", "title": "开发方法论"},
                        {"id": "3.2", "title": "技术栈选择"},
                        {"id": "3.3", "title": "开发环境"},
                        {"id": "3.4", "title": "版本控制"}
                    ]
                },
                {
                    "chapter_id": "4",
                    "title": "测试方案",
                    "description": "软件测试策略和方案",
                    "subsections": [
                        {"id": "4.1", "title": "测试策略"},
                        {"id": "4.2", "title": "单元测试"},
                        {"id": "4.3", "title": "集成测试"},
                        {"id": "4.4", "title": "系统测试"}
                    ]
                },
                {
                    "chapter_id": "5",
                    "title": "部署运维",
                    "description": "系统部署和运维方案",
                    "subsections": [
                        {"id": "5.1", "title": "部署架构"},
                        {"id": "5.2", "title": "监控方案"},
                        {"id": "5.3", "title": "备份策略"},
                        {"id": "5.4", "title": "应急预案"}
                    ]
                }
            ],
            "infrastructure": [
                {
                    "chapter_id": "1",
                    "title": "项目概述",
                    "description": "基础设施项目概述",
                    "subsections": [
                        {"id": "1.1", "title": "项目背景"},
                        {"id": "1.2", "title": "建设目标"},
                        {"id": "1.3", "title": "建设内容"}
                    ]
                },
                {
                    "chapter_id": "2",
                    "title": "技术方案",
                    "description": "基础设施技术方案",
                    "subsections": [
                        {"id": "2.1", "title": "网络架构"},
                        {"id": "2.2", "title": "硬件配置"},
                        {"id": "2.3", "title": "软件配置"},
                        {"id": "2.4", "title": "安全方案"}
                    ]
                },
                {
                    "chapter_id": "3",
                    "title": "实施方案",
                    "description": "基础设施实施方案",
                    "subsections": [
                        {"id": "3.1", "title": "施工组织"},
                        {"id": "3.2", "title": "进度安排"},
                        {"id": "3.3", "title": "质量控制"},
                        {"id": "3.4", "title": "安全措施"}
                    ]
                }
            ],
            "consulting": [
                {
                    "chapter_id": "1",
                    "title": "咨询理解",
                    "description": "咨询项目理解和分析",
                    "subsections": [
                        {"id": "1.1", "title": "项目背景理解"},
                        {"id": "1.2", "title": "咨询目标"},
                        {"id": "1.3", "title": "预期成果"}
                    ]
                },
                {
                    "chapter_id": "2",
                    "title": "咨询方法",
                    "description": "咨询方法论和工具",
                    "subsections": [
                        {"id": "2.1", "title": "咨询方法论"},
                        {"id": "2.2", "title": "分析工具"},
                        {"id": "2.3", "title": "调研方案"},
                        {"id": "2.4", "title": "评估框架"}
                    ]
                },
                {
                    "chapter_id": "3",
                    "title": "工作计划",
                    "description": "咨询工作计划和安排",
                    "subsections": [
                        {"id": "3.1", "title": "工作阶段"},
                        {"id": "3.2", "title": "时间安排"},
                        {"id": "3.3", "title": "人员配置"},
                        {"id": "3.4", "title": "交付物"}
                    ]
                }
            ]
        }
        
        return templates.get(project_type, OutlineTemplateEngine.get_default_template())
    
    @staticmethod
    def detect_project_type(analysis: AnalysisResult) -> str:
        """根据分析结果检测项目类型"""
        project_info = analysis.project_info
        technical_requirements = analysis.technical_requirements
        
        # 检查项目名称和描述中的关键词
        project_name = project_info.get("project_name", "").lower()
        project_overview = project_info.get("project_overview", "").lower()
        
        # 软件开发项目关键词
        software_keywords = ["软件", "系统开发", "应用开发", "平台开发", "信息系统", "管理系统"]
        if any(keyword in project_name or keyword in project_overview for keyword in software_keywords):
            return "software_development"
        
        # 基础设施项目关键词
        infrastructure_keywords = ["网络建设", "机房建设", "基础设施", "硬件采购", "设备采购"]
        if any(keyword in project_name or keyword in project_overview for keyword in infrastructure_keywords):
            return "infrastructure"
        
        # 咨询项目关键词
        consulting_keywords = ["咨询", "规划", "设计", "评估", "调研", "方案设计"]
        if any(keyword in project_name or keyword in project_overview for keyword in consulting_keywords):
            return "consulting"
        
        # 默认返回通用类型
        return "general"


class OutlineGenerationService:
    """大纲生成服务"""
    
    def __init__(self, db: Session, storage_service: TenderStorageService = None, ai_client=None):
        self.db = db
        self.storage_service = storage_service or TenderStorageService()
        self.ai_client = ai_client or get_ai_client()
        self.template_engine = OutlineTemplateEngine()
    
    async def generate_outline(self, project_id: str, use_ai: bool = True) -> OutlineStructure:
        """
        基于分析结果生成方案大纲
        
        Args:
            project_id: 项目ID
            use_ai: 是否使用AI生成，False时使用模板
            
        Returns:
            OutlineStructure: 生成的大纲结构
            
        Raises:
            ValueError: 项目不存在或分析结果不存在
            AIServiceError: AI服务调用失败
        """
        # 获取项目信息
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        logger.info(f"开始生成大纲，项目ID: {project_id}, 使用AI: {use_ai}")
        
        try:
            # 更新项目状态为大纲生成中
            project.status = TenderStatus.OUTLINING
            project.progress = 10
            self.db.commit()
            
            # 加载分析结果
            analysis = await self.storage_service.load_analysis_result(project)
            project.progress = 30
            self.db.commit()
            
            if use_ai:
                # 使用AI生成大纲
                outline = await self._generate_outline_with_ai(analysis)
            else:
                # 使用模板生成大纲
                outline = await self._generate_outline_with_template(analysis)
            
            project.progress = 80
            self.db.commit()
            
            # 保存大纲到MinIO
            await self.storage_service.save_outline(project, outline)
            
            # 更新项目状态为大纲已生成
            project.status = TenderStatus.OUTLINED
            project.progress = 100
            self.db.commit()
            
            logger.info(f"大纲生成完成，项目ID: {project_id}, 章节数: {outline.chapter_count}")
            return outline
            
        except Exception as e:
            # 更新项目状态为失败
            project.status = TenderStatus.FAILED
            self.db.commit()
            logger.error(f"大纲生成失败，项目ID: {project_id}, 错误: {str(e)}")
            raise
    
    async def _generate_outline_with_ai(self, analysis: AnalysisResult) -> OutlineStructure:
        """
        使用AI生成大纲
        
        Args:
            analysis: 分析结果
            
        Returns:
            OutlineStructure: 生成的大纲结构
        """
        logger.info("使用AI生成大纲")
        
        try:
            # 构建AI提示词
            prompt = self._build_outline_generation_prompt(analysis)
            
            # 调用AI服务生成大纲
            result = await self.ai_client.generate_structured(
                prompt=prompt,
                expected_format="json",
                validation_func=self._validate_outline_structure,
                max_tokens=3000,
                temperature=0.7
            )
            
            # 转换为OutlineStructure对象
            chapters = [ChapterInfo(**chapter) for chapter in result["chapters"]]
            
            outline = OutlineStructure(
                chapters=chapters,
                chapter_count=len(chapters),
                generated_at=datetime.utcnow()
            )
            
            logger.info(f"AI大纲生成完成，章节数: {len(chapters)}")
            return outline
            
        except AIServiceError as e:
            logger.error(f"AI生成大纲失败: {str(e)}")
            # 降级到模板生成
            logger.info("降级使用模板生成大纲")
            return await self._generate_outline_with_template(analysis)
        except Exception as e:
            logger.error(f"大纲生成时发生未知错误: {str(e)}")
            raise AIServiceError(f"大纲生成失败: {str(e)}")
    
    async def _generate_outline_with_template(self, analysis: AnalysisResult) -> OutlineStructure:
        """
        使用模板生成大纲
        
        Args:
            analysis: 分析结果
            
        Returns:
            OutlineStructure: 生成的大纲结构
        """
        logger.info("使用模板生成大纲")
        
        # 检测项目类型
        project_type = self.template_engine.detect_project_type(analysis)
        logger.info(f"检测到项目类型: {project_type}")
        
        # 获取对应模板
        template_chapters = self.template_engine.get_template_by_type(project_type)
        
        # 根据分析结果调整模板
        adjusted_chapters = self._adjust_template_by_analysis(template_chapters, analysis)
        
        # 转换为ChapterInfo对象
        chapters = [ChapterInfo(**chapter) for chapter in adjusted_chapters]
        
        outline = OutlineStructure(
            chapters=chapters,
            chapter_count=len(chapters),
            generated_at=datetime.utcnow()
        )
        
        logger.info(f"模板大纲生成完成，章节数: {len(chapters)}")
        return outline
    
    def _build_outline_generation_prompt(self, analysis: AnalysisResult) -> str:
        """
        构建大纲生成AI提示词
        
        Args:
            analysis: 分析结果
            
        Returns:
            str: AI提示词
        """
        # 检测项目类型，使用对应的提示词模板
        project_type = self.template_engine.detect_project_type(analysis)
        
        if project_type in ["software_development", "infrastructure", "consulting"]:
            # 使用专门的项目类型提示词
            return PromptTemplates.format_project_type_outline_prompt(
                project_type=project_type,
                project_info=analysis.project_info,
                technical_requirements=analysis.technical_requirements,
                evaluation_criteria=analysis.evaluation_criteria
            )
        else:
            # 使用通用提示词
            return PromptTemplates.format_outline_generation_prompt(
                project_info=analysis.project_info,
                technical_requirements=analysis.technical_requirements,
                evaluation_criteria=analysis.evaluation_criteria,
                submission_requirements=analysis.submission_requirements
            )
    
    def _adjust_template_by_analysis(self, template_chapters: List[Dict[str, Any]], analysis: AnalysisResult) -> List[Dict[str, Any]]:
        """
        根据分析结果调整模板
        
        Args:
            template_chapters: 模板章节
            analysis: 分析结果
            
        Returns:
            List[Dict]: 调整后的章节
        """
        adjusted_chapters = template_chapters.copy()
        
        # 根据技术要求调整技术方案章节
        tech_requirements = analysis.technical_requirements
        if tech_requirements:
            for chapter in adjusted_chapters:
                if "技术方案" in chapter["title"] or "系统设计" in chapter["title"]:
                    # 根据技术要求添加特定子章节
                    if tech_requirements.get("security_requirements"):
                        chapter["subsections"].append({"id": f"{chapter['chapter_id']}.{len(chapter['subsections'])+1}", "title": "安全方案"})
                    
                    if tech_requirements.get("performance_requirements"):
                        chapter["subsections"].append({"id": f"{chapter['chapter_id']}.{len(chapter['subsections'])+1}", "title": "性能优化"})
                    
                    if tech_requirements.get("interface_requirements"):
                        chapter["subsections"].append({"id": f"{chapter['chapter_id']}.{len(chapter['subsections'])+1}", "title": "接口设计"})
        
        # 根据评分标准调整章节权重
        eval_criteria = analysis.evaluation_criteria
        if eval_criteria:
            technical_weight = eval_criteria.get("technical_score", {}).get("weight", 0)
            commercial_weight = eval_criteria.get("commercial_score", {}).get("weight", 0)
            
            # 如果技术分权重高，增加技术相关章节的子章节
            if technical_weight > commercial_weight:
                for chapter in adjusted_chapters:
                    if any(keyword in chapter["title"] for keyword in ["技术", "方案", "设计"]):
                        if len(chapter["subsections"]) < 6:
                            chapter["subsections"].append({
                                "id": f"{chapter['chapter_id']}.{len(chapter['subsections'])+1}", 
                                "title": "技术创新点"
                            })
        
        return adjusted_chapters
    
    def _validate_outline_structure(self, data: Dict[str, Any]) -> bool:
        """
        验证大纲结构数据
        
        Args:
            data: 待验证的数据
            
        Returns:
            bool: 验证是否通过
        """
        if not isinstance(data, dict):
            logger.warning("大纲数据必须是字典类型")
            return False
        
        if "chapters" not in data:
            logger.warning("大纲数据缺少chapters字段")
            return False
        
        chapters = data["chapters"]
        if not isinstance(chapters, list):
            logger.warning("chapters字段必须是列表类型")
            return False
        
        if len(chapters) == 0:
            logger.warning("大纲至少需要包含一个章节")
            return False
        
        # 验证每个章节的结构
        for i, chapter in enumerate(chapters):
            if not isinstance(chapter, dict):
                logger.warning(f"第{i+1}个章节必须是字典类型")
                return False
            
            required_fields = ["chapter_id", "title", "description", "subsections"]
            for field in required_fields:
                if field not in chapter:
                    logger.warning(f"第{i+1}个章节缺少必需字段: {field}")
                    return False
            
            # 验证子章节
            subsections = chapter["subsections"]
            if not isinstance(subsections, list):
                logger.warning(f"第{i+1}个章节的subsections必须是列表类型")
                return False
            
            for j, subsection in enumerate(subsections):
                if not isinstance(subsection, dict):
                    logger.warning(f"第{i+1}个章节的第{j+1}个子章节必须是字典类型")
                    return False
                
                if "id" not in subsection or "title" not in subsection:
                    logger.warning(f"第{i+1}个章节的第{j+1}个子章节缺少必需字段")
                    return False
        
        return True
    
    async def customize_outline(self, project_id: str, user_input: Dict[str, Any]) -> OutlineStructure:
        """
        根据用户输入定制大纲
        
        Args:
            project_id: 项目ID
            user_input: 用户输入的大纲修改
            
        Returns:
            OutlineStructure: 定制后的大纲结构
            
        Raises:
            ValueError: 项目不存在或输入无效
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        logger.info(f"开始定制大纲，项目ID: {project_id}")
        
        try:
            # 加载现有大纲
            try:
                current_outline = await self.storage_service.load_outline(project)
            except FileNotFoundError:
                # 如果没有现有大纲，先生成一个
                logger.info("未找到现有大纲，先生成默认大纲")
                current_outline = await self.generate_outline(project_id, use_ai=False)
            
            # 应用用户修改
            updated_chapters = self._apply_user_modifications(current_outline.chapters, user_input)
            
            # 创建新的大纲结构
            outline = OutlineStructure(
                chapters=updated_chapters,
                chapter_count=len(updated_chapters),
                generated_at=datetime.utcnow()
            )
            
            # 保存更新后的大纲
            await self.storage_service.save_outline(project, outline)
            
            logger.info(f"大纲定制完成，项目ID: {project_id}, 章节数: {outline.chapter_count}")
            return outline
            
        except Exception as e:
            logger.error(f"大纲定制失败，项目ID: {project_id}, 错误: {str(e)}")
            raise
    
    def _apply_user_modifications(self, current_chapters: List[ChapterInfo], user_input: Dict[str, Any]) -> List[ChapterInfo]:
        """
        应用用户修改到现有大纲
        
        Args:
            current_chapters: 当前章节列表
            user_input: 用户输入的修改
            
        Returns:
            List[ChapterInfo]: 修改后的章节列表
        """
        # 如果用户提供了完整的章节列表，直接使用
        if "chapters" in user_input:
            chapters_data = user_input["chapters"]
            return [ChapterInfo(**chapter) for chapter in chapters_data]
        
        # 否则应用增量修改
        updated_chapters = []
        
        for chapter in current_chapters:
            chapter_dict = chapter.model_dump()
            chapter_id = chapter.chapter_id
            
            # 检查是否有针对此章节的修改
            if f"chapter_{chapter_id}" in user_input:
                chapter_modifications = user_input[f"chapter_{chapter_id}"]
                
                # 应用标题修改
                if "title" in chapter_modifications:
                    chapter_dict["title"] = chapter_modifications["title"]
                
                # 应用描述修改
                if "description" in chapter_modifications:
                    chapter_dict["description"] = chapter_modifications["description"]
                
                # 应用子章节修改
                if "subsections" in chapter_modifications:
                    chapter_dict["subsections"] = chapter_modifications["subsections"]
            
            updated_chapters.append(ChapterInfo(**chapter_dict))
        
        # 检查是否有新增章节
        if "new_chapters" in user_input:
            for new_chapter_data in user_input["new_chapters"]:
                updated_chapters.append(ChapterInfo(**new_chapter_data))
        
        return updated_chapters
    
    async def get_outline(self, project_id: str) -> Optional[OutlineStructure]:
        """
        获取项目的大纲结构
        
        Args:
            project_id: 项目ID
            
        Returns:
            OutlineStructure: 大纲结构，如果不存在返回None
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return None
        
        try:
            return await self.storage_service.load_outline(project)
        except FileNotFoundError:
            return None
    
    async def validate_outline_quality(self, outline: OutlineStructure, analysis: AnalysisResult) -> Dict[str, Any]:
        """
        评估大纲质量
        
        Args:
            outline: 大纲结构
            analysis: 分析结果
            
        Returns:
            Dict: 质量评估结果
        """
        logger.info("开始评估大纲质量")
        
        quality_score = 0
        max_score = 100
        issues = []
        suggestions = []
        
        # 1. 检查章节数量 (20分)
        chapter_count = outline.chapter_count
        if 5 <= chapter_count <= 8:
            quality_score += 20
        elif 3 <= chapter_count <= 10:
            quality_score += 15
            suggestions.append("建议章节数量控制在5-8个之间")
        else:
            quality_score += 10
            issues.append(f"章节数量({chapter_count})不够合理，建议5-8个章节")
        
        # 2. 检查章节完整性 (30分)
        essential_chapters = ["项目理解", "技术方案", "实施计划", "质量保证"]
        found_essential = 0
        
        for chapter in outline.chapters:
            for essential in essential_chapters:
                if essential in chapter.title or any(essential in subsec["title"] for subsec in chapter.subsections):
                    found_essential += 1
                    break
        
        completeness_score = (found_essential / len(essential_chapters)) * 30
        quality_score += completeness_score
        
        if found_essential < len(essential_chapters):
            missing = len(essential_chapters) - found_essential
            issues.append(f"缺少{missing}个核心章节，建议包含：{', '.join(essential_chapters)}")
        
        # 3. 检查子章节详细程度 (25分)
        total_subsections = sum(len(chapter.subsections) for chapter in outline.chapters)
        avg_subsections = total_subsections / chapter_count if chapter_count > 0 else 0
        
        if 3 <= avg_subsections <= 6:
            quality_score += 25
        elif 2 <= avg_subsections <= 7:
            quality_score += 20
            suggestions.append("建议每个章节包含3-6个子章节")
        else:
            quality_score += 15
            issues.append(f"子章节数量不够合理，平均每章{avg_subsections:.1f}个")
        
        # 4. 检查与招标要求的匹配度 (25分)
        matching_score = self._calculate_requirement_matching(outline, analysis)
        quality_score += matching_score
        
        if matching_score < 20:
            issues.append("大纲与招标要求匹配度较低，建议增加针对性内容")
        elif matching_score < 25:
            suggestions.append("可以进一步提高与招标要求的匹配度")
        
        # 生成质量等级
        if quality_score >= 90:
            quality_level = "优秀"
        elif quality_score >= 80:
            quality_level = "良好"
        elif quality_score >= 70:
            quality_level = "中等"
        elif quality_score >= 60:
            quality_level = "及格"
        else:
            quality_level = "需要改进"
        
        result = {
            "quality_score": quality_score,
            "max_score": max_score,
            "quality_level": quality_level,
            "chapter_count": chapter_count,
            "total_subsections": total_subsections,
            "avg_subsections_per_chapter": avg_subsections,
            "issues": issues,
            "suggestions": suggestions,
            "evaluation_time": datetime.utcnow().isoformat()
        }
        
        logger.info(f"大纲质量评估完成，得分: {quality_score}/{max_score}, 等级: {quality_level}")
        return result
    
    def _calculate_requirement_matching(self, outline: OutlineStructure, analysis: AnalysisResult) -> float:
        """
        计算大纲与招标要求的匹配度
        
        Args:
            outline: 大纲结构
            analysis: 分析结果
            
        Returns:
            float: 匹配度分数 (0-25)
        """
        matching_score = 0
        
        # 提取招标要求中的关键词
        tech_keywords = []
        if analysis.technical_requirements:
            for key, value in analysis.technical_requirements.items():
                if isinstance(value, list):
                    tech_keywords.extend([str(item) for item in value])
                elif isinstance(value, dict):
                    tech_keywords.extend([str(v) for v in value.values()])
                else:
                    tech_keywords.append(str(value))
        
        eval_keywords = []
        if analysis.evaluation_criteria:
            for key, value in analysis.evaluation_criteria.items():
                if isinstance(value, dict) and "criteria" in value:
                    eval_keywords.extend(value["criteria"])
        
        # 检查大纲中是否包含相关内容
        outline_text = ""
        for chapter in outline.chapters:
            outline_text += chapter.title + " " + chapter.description + " "
            for subsection in chapter.subsections:
                outline_text += subsection["title"] + " "
        
        outline_text = outline_text.lower()
        
        # 计算技术要求匹配度 (15分)
        tech_matches = 0
        for keyword in tech_keywords[:10]:  # 限制检查数量
            if keyword.lower() in outline_text:
                tech_matches += 1
        
        if tech_keywords:
            tech_score = (tech_matches / min(len(tech_keywords), 10)) * 15
            matching_score += tech_score
        
        # 计算评分标准匹配度 (10分)
        eval_matches = 0
        for keyword in eval_keywords[:5]:  # 限制检查数量
            if keyword.lower() in outline_text:
                eval_matches += 1
        
        if eval_keywords:
            eval_score = (eval_matches / min(len(eval_keywords), 5)) * 10
            matching_score += eval_score
        
        return min(matching_score, 25)  # 确保不超过最大分数  
  
    async def optimize_outline(self, project_id: str, current_outline: OutlineStructure, analysis: AnalysisResult) -> Dict[str, Any]:
        """
        使用AI优化大纲结构
        
        Args:
            project_id: 项目ID
            current_outline: 当前大纲结构
            analysis: 分析结果
            
        Returns:
            Dict: 优化结果，包含评估和改进建议
        """
        logger.info(f"开始优化大纲，项目ID: {project_id}")
        
        try:
            # 构建优化提示词
            requirements_summary = {
                "project_info": analysis.project_info,
                "technical_requirements": analysis.technical_requirements
            }
            
            prompt = PromptTemplates.format_outline_optimization_prompt(
                current_outline=current_outline.model_dump(),
                requirements_summary=requirements_summary,
                evaluation_criteria=analysis.evaluation_criteria
            )
            
            # 调用AI服务进行优化
            result = await self.ai_client.generate_structured(
                prompt=prompt,
                expected_format="json",
                max_tokens=4000,
                temperature=0.5
            )
            
            # 验证优化结果
            if "optimized_outline" in result and "chapters" in result["optimized_outline"]:
                # 创建优化后的大纲结构
                optimized_chapters = [ChapterInfo(**chapter) for chapter in result["optimized_outline"]["chapters"]]
                optimized_outline = OutlineStructure(
                    chapters=optimized_chapters,
                    chapter_count=len(optimized_chapters),
                    generated_at=datetime.utcnow()
                )
                result["optimized_outline_object"] = optimized_outline
            
            logger.info(f"大纲优化完成，项目ID: {project_id}")
            return result
            
        except AIServiceError as e:
            logger.error(f"AI优化大纲失败: {str(e)}")
            # 降级到质量评估
            quality_result = await self.validate_outline_quality(current_outline, analysis)
            return {
                "quality_score": quality_result["quality_score"],
                "strengths": ["现有大纲结构合理"],
                "weaknesses": quality_result["issues"],
                "suggestions": quality_result["suggestions"],
                "optimized_outline": current_outline.model_dump(),
                "optimized_outline_object": current_outline,
                "note": "AI优化服务不可用，返回质量评估结果"
            }
        except Exception as e:
            logger.error(f"大纲优化时发生未知错误: {str(e)}")
            raise AIServiceError(f"大纲优化失败: {str(e)}")
    
    async def generate_outline_variations(self, project_id: str, analysis: AnalysisResult, count: int = 3) -> List[OutlineStructure]:
        """
        生成多个大纲变体供用户选择
        
        Args:
            project_id: 项目ID
            analysis: 分析结果
            count: 生成变体数量
            
        Returns:
            List[OutlineStructure]: 大纲变体列表
        """
        logger.info(f"开始生成大纲变体，项目ID: {project_id}, 数量: {count}")
        
        variations = []
        
        try:
            # 生成不同风格的大纲
            for i in range(count):
                if i == 0:
                    # 第一个使用AI生成
                    try:
                        outline = await self._generate_outline_with_ai(analysis)
                        variations.append(outline)
                    except:
                        # AI失败时使用默认模板
                        outline = await self._generate_outline_with_template(analysis)
                        variations.append(outline)
                elif i == 1:
                    # 第二个使用项目类型特定模板
                    project_type = self.template_engine.detect_project_type(analysis)
                    template_chapters = self.template_engine.get_template_by_type(project_type)
                    adjusted_chapters = self._adjust_template_by_analysis(template_chapters, analysis)
                    chapters = [ChapterInfo(**chapter) for chapter in adjusted_chapters]
                    outline = OutlineStructure(
                        chapters=chapters,
                        chapter_count=len(chapters),
                        generated_at=datetime.utcnow()
                    )
                    variations.append(outline)
                else:
                    # 第三个使用默认模板
                    template_chapters = self.template_engine.get_default_template()
                    adjusted_chapters = self._adjust_template_by_analysis(template_chapters, analysis)
                    chapters = [ChapterInfo(**chapter) for chapter in adjusted_chapters]
                    outline = OutlineStructure(
                        chapters=chapters,
                        chapter_count=len(chapters),
                        generated_at=datetime.utcnow()
                    )
                    variations.append(outline)
            
            logger.info(f"大纲变体生成完成，项目ID: {project_id}, 实际生成数量: {len(variations)}")
            return variations
            
        except Exception as e:
            logger.error(f"生成大纲变体失败，项目ID: {project_id}, 错误: {str(e)}")
            # 至少返回一个基础大纲
            if not variations:
                template_chapters = self.template_engine.get_default_template()
                chapters = [ChapterInfo(**chapter) for chapter in template_chapters]
                outline = OutlineStructure(
                    chapters=chapters,
                    chapter_count=len(chapters),
                    generated_at=datetime.utcnow()
                )
                variations.append(outline)
            
            return variations