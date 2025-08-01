"""
AI需求分析服务
实现项目概览、甲方信息、预算信息提取和需求分级算法
"""
import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger
from app.services.llm_client import LLMClient, LLMException
from app.services.prompt_templates import (
    prompt_template_manager, 
    PromptType,
    get_project_overview_template,
    get_client_info_template,
    get_budget_info_template,
    get_detailed_requirements_template,
    get_requirements_classification_template
)
import os


class AIAnalysisException(Exception):
    """AI分析异常"""
    pass


class AIAnalysisService:
    """AI需求分析服务"""
    
    def __init__(self):
        """初始化AI分析服务"""
        self.llm_client = LLMClient(
            api_url=os.getenv("LLM_API_URL", "http://192.168.30.54:3000/v1"),
            api_key=os.getenv("LLM_API_KEY", "token-abc123"),
            model_name=os.getenv("LLM_MODEL_NAME", "Qwen3-30B-A3B-FP8")
        )
    
    def analyze_tender_document(self, project_id: int, parsed_content: str) -> Dict[str, Any]:
        """
        分析招标文件，提取需求理解概况和需求分级
        
        Args:
            project_id: 项目ID
            parsed_content: 解析后的文档内容
            
        Returns:
            包含分析结果的字典
            
        Raises:
            AIAnalysisException: 分析失败时抛出
        """
        try:
            logger.info(f"开始分析项目 {project_id} 的招标文件")
            
            # 使用同步方法执行分析
            analysis_result = self._perform_analysis_sync(parsed_content)
            
            logger.info(f"项目 {project_id} 分析完成")
            return analysis_result
            
        except Exception as e:
            logger.error(f"项目 {project_id} 分析失败: {str(e)}")
            raise AIAnalysisException(f"分析失败: {str(e)}")
    
    def _perform_analysis_sync(self, content: str) -> Dict[str, Any]:
        """
        同步执行分析任务
        
        Args:
            content: 文档内容
            
        Returns:
            分析结果字典
        """
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self._perform_analysis_async(content))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"同步分析执行失败: {str(e)}")
            raise AIAnalysisException(f"分析执行失败: {str(e)}")
    
    async def _perform_analysis_async(self, content: str) -> Dict[str, Any]:
        """
        异步执行完整分析流程
        
        Args:
            content: 文档内容
            
        Returns:
            分析结果字典
        """
        async with self.llm_client:
            # 并行执行基础信息提取
            project_overview_task = self.llm_client.extract_project_overview(content)
            client_info_task = self.llm_client.extract_client_info(content)
            budget_info_task = self.llm_client.extract_budget_info(content)
            
            # 等待基础信息提取完成
            project_overview, client_info, budget_info = await asyncio.gather(
                project_overview_task,
                client_info_task,
                budget_info_task,
                return_exceptions=True
            )
            
            # 处理异常结果
            if isinstance(project_overview, Exception):
                logger.warning(f"项目概览提取失败: {project_overview}")
                project_overview = "项目概览提取失败"
            
            if isinstance(client_info, Exception):
                logger.warning(f"甲方信息提取失败: {client_info}")
                client_info = "甲方信息提取失败"
            
            if isinstance(budget_info, Exception):
                logger.warning(f"预算信息提取失败: {budget_info}")
                budget_info = "预算信息提取失败"
            
            # 提取详细需求
            detailed_requirements = await self.extract_detailed_requirements(content)
            
            # 需求分级
            requirements_classification = await self.llm_client.classify_requirements(content)
            
            return {
                'project_overview': project_overview,
                'client_info': client_info,
                'budget_info': budget_info,
                'detailed_requirements': detailed_requirements,
                'critical_requirements': requirements_classification.get('critical_requirements', ''),
                'important_requirements': requirements_classification.get('important_requirements', ''),
                'general_requirements': requirements_classification.get('general_requirements', '')
            }
    
    async def extract_project_overview(self, content: str) -> str:
        """
        提取项目概览信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            项目概览信息
        """
        try:
            template = get_project_overview_template(content=content)
            return await self.llm_client.analyze_document(content, template)
        except LLMException as e:
            logger.error(f"项目概览提取失败: {e}")
            raise AIAnalysisException(f"项目概览提取失败: {e}")
    
    async def extract_client_info(self, content: str) -> str:
        """
        提取甲方信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            甲方信息
        """
        try:
            template = get_client_info_template(content=content)
            return await self.llm_client.analyze_document(content, template)
        except LLMException as e:
            logger.error(f"甲方信息提取失败: {e}")
            raise AIAnalysisException(f"甲方信息提取失败: {e}")
    
    async def extract_budget_info(self, content: str) -> str:
        """
        提取预算信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            预算信息
        """
        try:
            template = get_budget_info_template(content=content)
            return await self.llm_client.analyze_document(content, template)
        except LLMException as e:
            logger.error(f"预算信息提取失败: {e}")
            raise AIAnalysisException(f"预算信息提取失败: {e}")
    
    async def extract_detailed_requirements(self, content: str) -> str:
        """
        提取详细需求信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            详细需求信息
        """
        try:
            template = get_detailed_requirements_template(content=content)
            return await self.llm_client.analyze_document(content, template)
        except LLMException as e:
            logger.error(f"详细需求提取失败: {e}")
            raise AIAnalysisException(f"详细需求提取失败: {e}")
    
    async def classify_requirements(self, content: str) -> Dict[str, str]:
        """
        需求分级分类
        
        Args:
            content: 招标文件内容
            
        Returns:
            分级后的需求字典
        """
        try:
            template = get_requirements_classification_template(content=content)
            result = await self.llm_client.analyze_document(content, template, temperature=0.3)
            
            # 尝试解析JSON结果
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_result = json.loads(json_str)
                
                # 处理新的结构化格式
                if isinstance(parsed_result.get('critical_requirements'), dict):
                    return {
                        'critical_requirements': self._format_requirement_section(parsed_result.get('critical_requirements', {})),
                        'important_requirements': self._format_requirement_section(parsed_result.get('important_requirements', {})),
                        'general_requirements': self._format_requirement_section(parsed_result.get('general_requirements', {}))
                    }
                else:
                    # 兼容旧格式
                    return {
                        'critical_requirements': parsed_result.get('critical_requirements', ''),
                        'important_requirements': parsed_result.get('important_requirements', ''),
                        'general_requirements': parsed_result.get('general_requirements', '')
                    }
            else:
                # 如果没有找到JSON格式，尝试直接解析
                return json.loads(result)
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse requirements classification as JSON, returning raw text")
            # 如果解析失败，返回原始文本的结构化版本
            return {
                "critical_requirements": result,
                "important_requirements": "",
                "general_requirements": ""
            }
        except LLMException as e:
            logger.error(f"需求分级失败: {e}")
            raise AIAnalysisException(f"需求分级失败: {e}")
    
    def _format_requirement_section(self, section_data: Dict[str, Any]) -> str:
        """
        格式化需求分级结果的单个部分
        
        Args:
            section_data: 需求分级数据
            
        Returns:
            格式化后的字符串
        """
        if not isinstance(section_data, dict):
            return str(section_data)
        
        formatted_parts = []
        
        if section_data.get('description'):
            formatted_parts.append(f"**总体描述：**\n{section_data['description']}")
        
        if section_data.get('items'):
            items_text = "\n".join([f"- {item}" for item in section_data['items']])
            formatted_parts.append(f"**具体需求：**\n{items_text}")
        
        if section_data.get('impact'):
            formatted_parts.append(f"**影响说明：**\n{section_data['impact']}")
        
        return "\n\n".join(formatted_parts)
    
    def generate_requirement_summary(self, analysis: Dict[str, Any]) -> str:
        """
        生成需求概况总结
        
        Args:
            analysis: 分析结果
            
        Returns:
            需求概况总结
        """
        try:
            summary_parts = []
            
            if analysis.get('project_overview'):
                summary_parts.append(f"## 项目概览\n{analysis['project_overview']}")
            
            if analysis.get('client_info'):
                summary_parts.append(f"## 甲方信息\n{analysis['client_info']}")
            
            if analysis.get('budget_info'):
                summary_parts.append(f"## 预算信息\n{analysis['budget_info']}")
            
            if analysis.get('detailed_requirements'):
                summary_parts.append(f"## 详细需求\n{analysis['detailed_requirements']}")
            
            # 需求分级总结
            requirements_summary = []
            if analysis.get('critical_requirements'):
                requirements_summary.append(f"### 关键需求\n{analysis['critical_requirements']}")
            
            if analysis.get('important_requirements'):
                requirements_summary.append(f"### 重要需求\n{analysis['important_requirements']}")
            
            if analysis.get('general_requirements'):
                requirements_summary.append(f"### 一般需求\n{analysis['general_requirements']}")
            
            if requirements_summary:
                summary_parts.append("## 需求分级\n" + "\n\n".join(requirements_summary))
            
            return "\n\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"生成需求概况总结失败: {e}")
            return "需求概况总结生成失败"
    
    async def validate_analysis_quality(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证分析结果质量
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            包含质量评估的字典
        """
        quality_score = 0
        quality_issues = []
        
        # 检查必要字段是否存在且有内容
        required_fields = [
            'project_overview', 'client_info', 'budget_info', 
            'detailed_requirements', 'critical_requirements'
        ]
        
        for field in required_fields:
            if field in analysis_result and analysis_result[field] and len(analysis_result[field].strip()) > 10:
                quality_score += 20
            else:
                quality_issues.append(f"缺少或内容不足: {field}")
        
        # 检查需求分级是否合理
        if (analysis_result.get('critical_requirements') and 
            analysis_result.get('important_requirements') and 
            analysis_result.get('general_requirements')):
            quality_score += 10
        else:
            quality_issues.append("需求分级不完整")
        
        # 检查内容长度是否合理
        total_length = sum(len(str(v)) for v in analysis_result.values() if v)
        if total_length > 500:
            quality_score += 10
        else:
            quality_issues.append("分析内容过于简短")
        
        return {
            'quality_score': min(quality_score, 100),
            'quality_issues': quality_issues,
            'is_acceptable': quality_score >= 60
        }
    
    async def enhance_analysis_result(self, analysis_result: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        """
        增强分析结果，补充缺失信息
        
        Args:
            analysis_result: 原始分析结果
            original_content: 原始文档内容
            
        Returns:
            增强后的分析结果
        """
        enhanced_result = analysis_result.copy()
        
        # 检查并补充缺失的信息
        if not enhanced_result.get('project_overview') or len(enhanced_result['project_overview'].strip()) < 50:
            logger.info("补充项目概览信息")
            try:
                enhanced_result['project_overview'] = await self.extract_project_overview(original_content)
            except Exception as e:
                logger.warning(f"补充项目概览失败: {e}")
        
        if not enhanced_result.get('detailed_requirements') or len(enhanced_result['detailed_requirements'].strip()) < 100:
            logger.info("补充详细需求信息")
            try:
                enhanced_result['detailed_requirements'] = await self.extract_detailed_requirements(original_content)
            except Exception as e:
                logger.warning(f"补充详细需求失败: {e}")
        
        return enhanced_result
    
    def get_analysis_statistics(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取分析结果统计信息
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            统计信息字典
        """
        stats = {
            'total_fields': len(analysis_result),
            'filled_fields': sum(1 for v in analysis_result.values() if v and str(v).strip()),
            'total_characters': sum(len(str(v)) for v in analysis_result.values() if v),
            'field_lengths': {}
        }
        
        for field, value in analysis_result.items():
            if value:
                stats['field_lengths'][field] = len(str(value))
            else:
                stats['field_lengths'][field] = 0
        
        stats['completion_rate'] = (stats['filled_fields'] / stats['total_fields']) * 100 if stats['total_fields'] > 0 else 0
        
        return stats


# 创建全局服务实例
ai_analysis_service = AIAnalysisService()


# 便捷函数
def analyze_tender_document_sync(project_id: int, content: str) -> Dict[str, Any]:
    """同步分析招标文件的便捷函数"""
    return ai_analysis_service.analyze_tender_document(project_id, content)


async def analyze_tender_document_async(project_id: int, content: str) -> Dict[str, Any]:
    """异步分析招标文件的便捷函数"""
    service = AIAnalysisService()
    return await service._perform_analysis_async(content)