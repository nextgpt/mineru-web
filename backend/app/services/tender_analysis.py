"""
招标文件分析服务
提供AI驱动的关键信息提取功能
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.tender import (
    TenderProject, 
    TenderStatus, 
    AnalysisResult
)
from app.models.file import File as FileModel
from app.models.parsed_content import ParsedContent
from app.services.tender_storage import TenderStorageService
from app.services.ai_client import get_ai_client, AIServiceError, PromptTemplates

logger = logging.getLogger(__name__)


class TenderAnalysisService:
    """招标文件分析服务"""
    
    def __init__(self, db: Session, storage_service: TenderStorageService = None, ai_client=None):
        self.db = db
        self.storage_service = storage_service or TenderStorageService()
        self.ai_client = ai_client or get_ai_client()
    
    async def analyze_tender_document(self, project_id: str) -> AnalysisResult:
        """
        分析招标文件，提取关键信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            AnalysisResult: 分析结果
            
        Raises:
            ValueError: 项目不存在或文件未解析
            AIServiceError: AI服务调用失败
        """
        # 获取项目信息
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        logger.info(f"开始分析招标文件，项目ID: {project_id}")
        
        try:
            # 更新项目状态为分析中
            project.status = TenderStatus.ANALYZING
            project.progress = 10
            self.db.commit()
            
            # 获取原始文件内容
            source_file = self.db.query(FileModel).filter(
                FileModel.id == project.source_file_id
            ).first()
            
            if not source_file:
                raise ValueError(f"源文件 {project.source_file_id} 不存在")
            
            # 获取解析后的内容
            parsed_content = self.db.query(ParsedContent).filter(
                ParsedContent.file_id == source_file.id
            ).first()
            
            if not parsed_content:
                raise ValueError("招标文件尚未解析，请先解析文件")
            
            logger.info(f"获取到解析内容，长度: {len(parsed_content.content)}")
            
            # 更新进度
            project.progress = 30
            self.db.commit()
            
            # 提取各类关键信息
            project_info = await self.extract_project_info(parsed_content.content)
            project.progress = 50
            self.db.commit()
            
            technical_requirements = await self.extract_technical_requirements(parsed_content.content)
            project.progress = 70
            self.db.commit()
            
            evaluation_criteria = await self.extract_evaluation_criteria(parsed_content.content)
            project.progress = 85
            self.db.commit()
            
            submission_requirements = await self.extract_submission_requirements(parsed_content.content)
            project.progress = 95
            self.db.commit()
            
            # 创建分析结果
            analysis = AnalysisResult(
                project_info=project_info,
                technical_requirements=technical_requirements,
                evaluation_criteria=evaluation_criteria,
                submission_requirements=submission_requirements,
                extracted_at=datetime.utcnow()
            )
            
            # 保存分析结果到MinIO
            await self.storage_service.save_analysis_result(project, analysis)
            
            # 更新项目状态为已分析
            project.status = TenderStatus.ANALYZED
            project.progress = 100
            self.db.commit()
            
            logger.info(f"招标文件分析完成，项目ID: {project_id}")
            return analysis
            
        except Exception as e:
            # 更新项目状态为失败
            project.status = TenderStatus.FAILED
            self.db.commit()
            logger.error(f"招标文件分析失败，项目ID: {project_id}, 错误: {str(e)}")
            raise
    
    async def extract_project_info(self, content: str) -> Dict[str, Any]:
        """
        提取项目基本信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            Dict: 项目基本信息
        """
        logger.info("开始提取项目基本信息")
        
        try:
            # TODO: 集成真实的AI模型进行信息提取
            # 这里先使用规则匹配和关键词提取作为占位符
            project_info = await self._extract_project_info_with_ai(content)
            
            logger.info(f"项目基本信息提取完成: {len(project_info)} 个字段")
            return project_info
            
        except Exception as e:
            logger.error(f"提取项目基本信息失败: {str(e)}")
            # 返回默认结构，避免完全失败
            return {
                "project_name": "未识别",
                "budget": "未识别", 
                "duration": "未识别",
                "location": "未识别",
                "contact_info": "未识别",
                "deadline": "未识别",
                "extraction_error": str(e)
            }
    
    async def extract_technical_requirements(self, content: str) -> Dict[str, Any]:
        """
        提取技术要求
        
        Args:
            content: 招标文件内容
            
        Returns:
            Dict: 技术要求信息
        """
        logger.info("开始提取技术要求")
        
        try:
            # TODO: 集成真实的AI模型进行信息提取
            technical_requirements = await self._extract_technical_requirements_with_ai(content)
            
            logger.info(f"技术要求提取完成: {len(technical_requirements)} 个字段")
            return technical_requirements
            
        except Exception as e:
            logger.error(f"提取技术要求失败: {str(e)}")
            return {
                "functional_requirements": [],
                "performance_requirements": {},
                "technical_specifications": {},
                "compliance_standards": [],
                "extraction_error": str(e)
            }
    
    async def extract_evaluation_criteria(self, content: str) -> Dict[str, Any]:
        """
        提取评分标准
        
        Args:
            content: 招标文件内容
            
        Returns:
            Dict: 评分标准信息
        """
        logger.info("开始提取评分标准")
        
        try:
            # TODO: 集成真实的AI模型进行信息提取
            evaluation_criteria = await self._extract_evaluation_criteria_with_ai(content)
            
            logger.info(f"评分标准提取完成: {len(evaluation_criteria)} 个字段")
            return evaluation_criteria
            
        except Exception as e:
            logger.error(f"提取评分标准失败: {str(e)}")
            return {
                "technical_score": {"weight": 0, "criteria": []},
                "commercial_score": {"weight": 0, "criteria": []},
                "qualification_requirements": [],
                "evaluation_method": "未识别",
                "extraction_error": str(e)
            }
    
    async def extract_submission_requirements(self, content: str) -> Dict[str, Any]:
        """
        提取提交要求
        
        Args:
            content: 招标文件内容
            
        Returns:
            Dict: 提交要求信息
        """
        logger.info("开始提取提交要求")
        
        try:
            # TODO: 集成真实的AI模型进行信息提取
            submission_requirements = await self._extract_submission_requirements_with_ai(content)
            
            logger.info(f"提交要求提取完成: {len(submission_requirements)} 个字段")
            return submission_requirements
            
        except Exception as e:
            logger.error(f"提取提交要求失败: {str(e)}")
            return {
                "document_format": "未识别",
                "submission_method": "未识别",
                "required_documents": [],
                "document_structure": {},
                "extraction_error": str(e)
            }
    
    async def _extract_project_info_with_ai(self, content: str) -> Dict[str, Any]:
        """
        使用AI提取项目基本信息
        
        Args:
            content: 文档内容
            
        Returns:
            Dict: 提取的项目信息
        """
        try:
            # 使用提示词模板
            prompt = PromptTemplates.format_project_info_prompt(content)
            
            # 调用AI服务进行结构化提取
            result = await self.ai_client.generate_structured(
                prompt=prompt,
                expected_format="json",
                validation_func=self._validate_project_info,
                max_tokens=1500,
                temperature=0.3
            )
            
            return result
            
        except AIServiceError as e:
            logger.error(f"AI提取项目信息失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"提取项目信息时发生未知错误: {str(e)}")
            raise AIServiceError(f"项目信息提取失败: {str(e)}")
    
    async def _extract_technical_requirements_with_ai(self, content: str) -> Dict[str, Any]:
        """
        使用AI提取技术要求
        
        Args:
            content: 文档内容
            
        Returns:
            Dict: 提取的技术要求
        """
        try:
            # 使用提示词模板
            prompt = PromptTemplates.format_technical_requirements_prompt(content)
            
            # 调用AI服务进行结构化提取
            result = await self.ai_client.generate_structured(
                prompt=prompt,
                expected_format="json",
                validation_func=self._validate_technical_requirements,
                max_tokens=2000,
                temperature=0.3
            )
            
            return result
            
        except AIServiceError as e:
            logger.error(f"AI提取技术要求失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"提取技术要求时发生未知错误: {str(e)}")
            raise AIServiceError(f"技术要求提取失败: {str(e)}")
    
    async def _extract_evaluation_criteria_with_ai(self, content: str) -> Dict[str, Any]:
        """
        使用AI提取评分标准
        
        Args:
            content: 文档内容
            
        Returns:
            Dict: 提取的评分标准
        """
        try:
            # 使用提示词模板
            prompt = PromptTemplates.format_evaluation_criteria_prompt(content)
            
            # 调用AI服务进行结构化提取
            result = await self.ai_client.generate_structured(
                prompt=prompt,
                expected_format="json",
                validation_func=self._validate_evaluation_criteria,
                max_tokens=1800,
                temperature=0.3
            )
            
            return result
            
        except AIServiceError as e:
            logger.error(f"AI提取评分标准失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"提取评分标准时发生未知错误: {str(e)}")
            raise AIServiceError(f"评分标准提取失败: {str(e)}")
    
    async def _extract_submission_requirements_with_ai(self, content: str) -> Dict[str, Any]:
        """
        使用AI提取提交要求
        
        Args:
            content: 文档内容
            
        Returns:
            Dict: 提取的提交要求
        """
        try:
            # 使用提示词模板
            prompt = PromptTemplates.format_submission_requirements_prompt(content)
            
            # 调用AI服务进行结构化提取
            result = await self.ai_client.generate_structured(
                prompt=prompt,
                expected_format="json",
                validation_func=self._validate_submission_requirements,
                max_tokens=1600,
                temperature=0.3
            )
            
            return result
            
        except AIServiceError as e:
            logger.error(f"AI提取提交要求失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"提取提交要求时发生未知错误: {str(e)}")
            raise AIServiceError(f"提交要求提取失败: {str(e)}")
    
    async def _mock_ai_extraction(self, prompt: str, extraction_type: str) -> Dict[str, Any]:
        """
        模拟AI提取功能（占位符实现）
        
        Args:
            prompt: AI提示词
            extraction_type: 提取类型
            
        Returns:
            Dict: 模拟的提取结果
        """
        logger.info(f"模拟AI提取: {extraction_type}")
        
        # 根据不同类型返回不同的模拟数据
        if extraction_type == "project_info":
            return {
                "project_name": "示例项目名称",
                "budget": "100万元",
                "duration": "6个月",
                "location": "示例城市",
                "contact_info": "联系人：张三，电话：138****1234",
                "deadline": "2024-12-31",
                "procurement_method": "公开招标",
                "project_overview": "这是一个示例项目的概述信息",
                "note": "这是模拟数据，实际使用时需要集成真实的AI服务"
            }
        elif extraction_type == "technical_requirements":
            return {
                "functional_requirements": [
                    "支持用户管理功能",
                    "支持数据导入导出",
                    "支持报表生成"
                ],
                "performance_requirements": {
                    "response_time": "< 3秒",
                    "concurrent_users": "> 1000",
                    "availability": "99.9%"
                },
                "technical_specifications": {
                    "database": "MySQL 8.0+",
                    "framework": "Spring Boot",
                    "deployment": "Docker容器化部署"
                },
                "compliance_standards": [
                    "GB/T 25000.51-2016",
                    "等保三级"
                ],
                "security_requirements": [
                    "数据加密传输",
                    "用户身份认证",
                    "操作日志记录"
                ],
                "interface_requirements": [
                    "RESTful API接口",
                    "支持JSON数据格式"
                ],
                "note": "这是模拟数据，实际使用时需要集成真实的AI服务"
            }
        elif extraction_type == "evaluation_criteria":
            return {
                "technical_score": {
                    "weight": 70,
                    "criteria": [
                        "技术方案完整性",
                        "技术先进性",
                        "系统架构合理性"
                    ]
                },
                "commercial_score": {
                    "weight": 30,
                    "criteria": [
                        "投标报价",
                        "商务条款"
                    ]
                },
                "qualification_requirements": [
                    "软件企业认证",
                    "ISO9001质量管理体系认证",
                    "3年以上相关项目经验"
                ],
                "evaluation_method": "综合评分法",
                "scoring_details": {
                    "technical_max": 70,
                    "commercial_max": 30,
                    "total_max": 100
                },
                "note": "这是模拟数据，实际使用时需要集成真实的AI服务"
            }
        elif extraction_type == "submission_requirements":
            return {
                "document_format": "PDF格式，A4纸张",
                "submission_method": "现场提交 + 电子版",
                "required_documents": [
                    "投标函",
                    "技术方案书",
                    "商务报价书",
                    "企业资质证明",
                    "项目经验证明"
                ],
                "document_structure": {
                    "volume_1": "商务文件",
                    "volume_2": "技术文件",
                    "volume_3": "资质文件"
                },
                "submission_deadline": "2024-12-31 14:00",
                "submission_location": "招标代理机构会议室",
                "note": "这是模拟数据，实际使用时需要集成真实的AI服务"
            }
        else:
            return {"error": f"未知的提取类型: {extraction_type}"}
    
    async def get_analysis_result(self, project_id: str) -> Optional[AnalysisResult]:
        """
        获取项目的分析结果
        
        Args:
            project_id: 项目ID
            
        Returns:
            AnalysisResult: 分析结果，如果不存在返回None
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            return None
        
        try:
            return await self.storage_service.load_analysis_result(project)
        except FileNotFoundError:
            return None
    
    async def update_analysis_result(self, project_id: str, analysis_data: Dict[str, Any]) -> AnalysisResult:
        """
        更新项目的分析结果
        
        Args:
            project_id: 项目ID
            analysis_data: 更新的分析数据
            
        Returns:
            AnalysisResult: 更新后的分析结果
        """
        project = self.db.query(TenderProject).filter(
            TenderProject.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 加载现有分析结果或创建新的
        try:
            current_analysis = await self.storage_service.load_analysis_result(project)
            # 更新字段
            if "project_info" in analysis_data:
                current_analysis.project_info.update(analysis_data["project_info"])
            if "technical_requirements" in analysis_data:
                current_analysis.technical_requirements.update(analysis_data["technical_requirements"])
            if "evaluation_criteria" in analysis_data:
                current_analysis.evaluation_criteria.update(analysis_data["evaluation_criteria"])
            if "submission_requirements" in analysis_data:
                current_analysis.submission_requirements.update(analysis_data["submission_requirements"])
        except FileNotFoundError:
            # 创建新的分析结果
            current_analysis = AnalysisResult(
                project_info=analysis_data.get("project_info", {}),
                technical_requirements=analysis_data.get("technical_requirements", {}),
                evaluation_criteria=analysis_data.get("evaluation_criteria", {}),
                submission_requirements=analysis_data.get("submission_requirements", {}),
                extracted_at=datetime.utcnow()
            )
        
        # 保存更新后的结果
        await self.storage_service.save_analysis_result(project, current_analysis)
        
        logger.info(f"更新分析结果完成，项目ID: {project_id}")
        return current_analysis
    
    def _validate_project_info(self, data: Dict[str, Any]) -> bool:
        """
        验证项目基本信息数据结构
        
        Args:
            data: 待验证的数据
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = [
            "project_name", "budget", "duration", "location", 
            "contact_info", "deadline", "procurement_method", "project_overview"
        ]
        
        if not isinstance(data, dict):
            return False
        
        # 检查必需字段是否存在
        for field in required_fields:
            if field not in data:
                logger.warning(f"项目信息缺少必需字段: {field}")
                return False
        
        return True
    
    def _validate_technical_requirements(self, data: Dict[str, Any]) -> bool:
        """
        验证技术要求数据结构
        
        Args:
            data: 待验证的数据
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = [
            "functional_requirements", "performance_requirements", 
            "technical_specifications", "compliance_standards",
            "security_requirements", "interface_requirements"
        ]
        
        if not isinstance(data, dict):
            return False
        
        # 检查必需字段是否存在
        for field in required_fields:
            if field not in data:
                logger.warning(f"技术要求缺少必需字段: {field}")
                return False
        
        # 检查列表类型字段
        list_fields = ["functional_requirements", "compliance_standards", 
                      "security_requirements", "interface_requirements"]
        for field in list_fields:
            if not isinstance(data[field], list):
                logger.warning(f"技术要求字段 {field} 应为列表类型")
                return False
        
        # 检查字典类型字段
        dict_fields = ["performance_requirements", "technical_specifications"]
        for field in dict_fields:
            if not isinstance(data[field], dict):
                logger.warning(f"技术要求字段 {field} 应为字典类型")
                return False
        
        return True
    
    def _validate_evaluation_criteria(self, data: Dict[str, Any]) -> bool:
        """
        验证评分标准数据结构
        
        Args:
            data: 待验证的数据
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = [
            "technical_score", "commercial_score", 
            "qualification_requirements", "evaluation_method"
        ]
        
        if not isinstance(data, dict):
            return False
        
        # 检查必需字段是否存在
        for field in required_fields:
            if field not in data:
                logger.warning(f"评分标准缺少必需字段: {field}")
                return False
        
        # 检查评分结构
        score_fields = ["technical_score", "commercial_score"]
        for field in score_fields:
            if not isinstance(data[field], dict):
                logger.warning(f"评分标准字段 {field} 应为字典类型")
                return False
            
            if "weight" not in data[field]:
                logger.warning(f"评分标准字段 {field} 缺少权重信息")
                return False
            
            if not isinstance(data[field]["weight"], (int, float)):
                logger.warning(f"评分标准字段 {field} 权重应为数字类型")
                return False
        
        # 检查资质要求
        if not isinstance(data["qualification_requirements"], list):
            logger.warning("资质要求应为列表类型")
            return False
        
        return True
    
    def _validate_submission_requirements(self, data: Dict[str, Any]) -> bool:
        """
        验证提交要求数据结构
        
        Args:
            data: 待验证的数据
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = [
            "document_format", "submission_method", "required_documents",
            "document_structure", "submission_deadline", "submission_location"
        ]
        
        if not isinstance(data, dict):
            return False
        
        # 检查必需字段是否存在
        for field in required_fields:
            if field not in data:
                logger.warning(f"提交要求缺少必需字段: {field}")
                return False
        
        # 检查必需文档列表
        if not isinstance(data["required_documents"], list):
            logger.warning("必需文档应为列表类型")
            return False
        
        # 检查文档结构
        if not isinstance(data["document_structure"], dict):
            logger.warning("文档结构应为字典类型")
            return False
        
        return True