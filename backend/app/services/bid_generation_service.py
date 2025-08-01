from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.bid_outline import BidOutline
from app.models.bid_document import BidDocument, DocumentStatus
from app.models.requirement_analysis import RequirementAnalysis
from app.models.project import Project, ProjectStatus
from app.services.llm_client import LLMClient
from app.services.prompt_templates import get_bid_outline_template, get_bid_content_template
import logging
import json
import re

logger = logging.getLogger(__name__)


class BidGenerationService:
    """标书生成服务"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()
    
    def generate_outline(self, db: Session, project_id: int, user_id: str, analysis: RequirementAnalysis) -> List[BidOutline]:
        """基于需求分析生成标书大纲"""
        try:
            logger.info(f"开始为项目 {project_id} 生成大纲")
            
            # 构建提示词
            prompt = self._build_outline_prompt(analysis)
            
            # 调用大模型生成大纲
            response = self.llm_client.generate_content(prompt, max_tokens=2000)
            
            # 解析大纲结构
            outline_data = self._parse_outline_response(response)
            
            # 验证大纲结构
            validated_outline = self._validate_outline_structure(outline_data)
            
            # 保存大纲到数据库
            outlines = self._save_outline_to_db(db, project_id, user_id, validated_outline)
            
            logger.info(f"项目 {project_id} 大纲生成完成，共 {len(outlines)} 个节点")
            return outlines
            
        except Exception as e:
            logger.error(f"项目 {project_id} 大纲生成失败: {str(e)}")
            raise
    
    def _build_outline_prompt(self, analysis: RequirementAnalysis) -> str:
        """构建大纲生成提示词"""
        prompt_data = {
            "project_overview": analysis.project_overview or "无项目概述",
            "client_info": analysis.client_info or "无甲方信息",
            "budget_info": analysis.budget_info or "无预算信息",
            "critical_requirements": analysis.critical_requirements or "无关键需求",
            "important_requirements": analysis.important_requirements or "无重要需求",
            "general_requirements": analysis.general_requirements or "无一般需求"
        }
        
        return get_bid_outline_template(**prompt_data)
    
    def _parse_outline_response(self, response: str) -> List[Dict]:
        """解析大模型返回的大纲结构"""
        try:
            # 尝试解析JSON格式
            if response.strip().startswith('[') or response.strip().startswith('{'):
                return json.loads(response)
            
            # 如果不是JSON，尝试解析文本格式
            return self._parse_text_outline(response)
            
        except json.JSONDecodeError:
            # JSON解析失败，尝试文本解析
            return self._parse_text_outline(response)
    
    def _parse_text_outline(self, text: str) -> List[Dict]:
        """解析文本格式的大纲"""
        outlines = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 匹配不同层级的标题格式
            # 一级标题：1. 标题 或 1 标题
            level1_match = re.match(r'^(\d+)\.?\s+(.+)', line)
            # 二级标题：1.1 标题 或 1.1. 标题
            level2_match = re.match(r'^(\d+\.\d+)\.?\s+(.+)', line)
            # 三级标题：1.1.1 标题 或 1.1.1. 标题
            level3_match = re.match(r'^(\d+\.\d+\.\d+)\.?\s+(.+)', line)
            
            if level3_match:
                sequence, title = level3_match.groups()
                outlines.append({
                    "title": title.strip(),
                    "level": 3,
                    "sequence": sequence,
                    "content": f"三级标题：{title.strip()}"
                })
            elif level2_match:
                sequence, title = level2_match.groups()
                outlines.append({
                    "title": title.strip(),
                    "level": 2,
                    "sequence": sequence,
                    "content": f"二级标题：{title.strip()}"
                })
            elif level1_match:
                sequence, title = level1_match.groups()
                outlines.append({
                    "title": title.strip(),
                    "level": 1,
                    "sequence": sequence,
                    "content": f"一级标题：{title.strip()}"
                })
        
        return outlines
    
    def _validate_outline_structure(self, outline_data: List[Dict]) -> List[Dict]:
        """验证和优化大纲结构"""
        if not outline_data:
            # 如果没有生成大纲，使用默认结构
            return self._get_default_outline_structure()
        
        validated = []
        level1_count = 0
        level2_counts = {}
        level3_counts = {}
        
        for item in outline_data:
            if not isinstance(item, dict) or 'title' not in item:
                continue
            
            level = item.get('level', 1)
            title = item['title'].strip()
            
            if not title:
                continue
            
            if level == 1:
                level1_count += 1
                sequence = str(level1_count)
                level2_counts[level1_count] = 0
            elif level == 2:
                if level1_count == 0:
                    # 如果没有一级标题，先创建一个
                    level1_count = 1
                    level2_counts[level1_count] = 0
                
                level2_counts[level1_count] += 1
                sequence = f"{level1_count}.{level2_counts[level1_count]}"
                level3_counts[sequence] = 0
            elif level == 3:
                if level1_count == 0:
                    level1_count = 1
                    level2_counts[level1_count] = 1
                    parent_sequence = f"{level1_count}.1"
                else:
                    # 找到最近的二级标题
                    parent_sequence = None
                    for seq in level2_counts:
                        if level2_counts[seq] > 0:
                            parent_sequence = f"{seq}.{level2_counts[seq]}"
                    
                    if not parent_sequence:
                        level2_counts[level1_count] = 1
                        parent_sequence = f"{level1_count}.1"
                
                if parent_sequence not in level3_counts:
                    level3_counts[parent_sequence] = 0
                
                level3_counts[parent_sequence] += 1
                sequence = f"{parent_sequence}.{level3_counts[parent_sequence]}"
            else:
                continue
            
            validated.append({
                "title": title,
                "level": level,
                "sequence": sequence,
                "content": item.get('content', f"{title}的详细内容")
            })
        
        return validated if validated else self._get_default_outline_structure()
    
    def _get_default_outline_structure(self) -> List[Dict]:
        """获取默认大纲结构"""
        return [
            {
                "title": "项目概述",
                "level": 1,
                "sequence": "1",
                "content": "项目基本情况、背景和目标介绍"
            },
            {
                "title": "项目理解",
                "level": 2,
                "sequence": "1.1",
                "content": "对招标需求的理解和分析"
            },
            {
                "title": "项目目标",
                "level": 2,
                "sequence": "1.2",
                "content": "项目实施目标和预期成果"
            },
            {
                "title": "技术方案",
                "level": 1,
                "sequence": "2",
                "content": "详细的技术实施方案"
            },
            {
                "title": "技术架构",
                "level": 2,
                "sequence": "2.1",
                "content": "系统技术架构设计"
            },
            {
                "title": "实施方案",
                "level": 2,
                "sequence": "2.2",
                "content": "具体的实施步骤和方法"
            },
            {
                "title": "项目管理",
                "level": 1,
                "sequence": "3",
                "content": "项目管理和实施计划"
            },
            {
                "title": "项目计划",
                "level": 2,
                "sequence": "3.1",
                "content": "详细的项目实施计划"
            },
            {
                "title": "团队组织",
                "level": 2,
                "sequence": "3.2",
                "content": "项目团队组织架构"
            },
            {
                "title": "质量保证",
                "level": 1,
                "sequence": "4",
                "content": "质量保证措施和标准"
            },
            {
                "title": "质量管理体系",
                "level": 2,
                "sequence": "4.1",
                "content": "质量管理体系和流程"
            },
            {
                "title": "测试方案",
                "level": 2,
                "sequence": "4.2",
                "content": "系统测试方案和标准"
            },
            {
                "title": "售后服务",
                "level": 1,
                "sequence": "5",
                "content": "售后服务承诺和保障"
            },
            {
                "title": "服务承诺",
                "level": 2,
                "sequence": "5.1",
                "content": "具体的服务承诺内容"
            },
            {
                "title": "技术支持",
                "level": 2,
                "sequence": "5.2",
                "content": "技术支持和维护方案"
            }
        ]
    
    def _save_outline_to_db(self, db: Session, project_id: int, user_id: str, outline_data: List[Dict]) -> List[BidOutline]:
        """保存大纲到数据库"""
        outlines = []
        parent_map = {}  # 用于存储父子关系映射
        
        try:
            for i, item in enumerate(outline_data):
                # 确定父节点ID
                parent_id = None
                if item['level'] > 1:
                    parent_sequence = self._get_parent_sequence(item['sequence'])
                    parent_id = parent_map.get(parent_sequence)
                
                # 创建大纲节点
                outline = BidOutline(
                    project_id=project_id,
                    user_id=user_id,
                    title=item['title'],
                    level=item['level'],
                    sequence=item['sequence'],
                    parent_id=parent_id,
                    order_index=i + 1,
                    content=item['content']
                )
                
                db.add(outline)
                db.flush()  # 获取ID但不提交
                
                # 记录序号到ID的映射
                parent_map[item['sequence']] = outline.id
                outlines.append(outline)
            
            db.commit()
            return outlines
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存大纲到数据库失败: {str(e)}")
            raise
    
    def _get_parent_sequence(self, sequence: str) -> str:
        """获取父序号"""
        parts = sequence.split('.')
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return ""
    
    def optimize_outline_structure(self, db: Session, project_id: int, user_id: str) -> bool:
        """优化大纲结构"""
        try:
            outlines = db.query(BidOutline).filter(
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).order_by(BidOutline.sequence).all()
            
            if not outlines:
                return False
            
            # 重新生成序号和排序
            level1_count = 0
            level2_counts = {}
            level3_counts = {}
            
            for outline in outlines:
                if outline.level == 1:
                    level1_count += 1
                    outline.sequence = str(level1_count)
                    outline.order_index = level1_count
                    level2_counts[level1_count] = 0
                elif outline.level == 2:
                    if level1_count == 0:
                        level1_count = 1
                        level2_counts[level1_count] = 0
                    
                    level2_counts[level1_count] += 1
                    outline.sequence = f"{level1_count}.{level2_counts[level1_count]}"
                    level3_counts[outline.sequence] = 0
                elif outline.level == 3:
                    # 找到对应的二级标题
                    parent_sequence = self._find_parent_sequence_for_level3(outlines, outline)
                    if parent_sequence not in level3_counts:
                        level3_counts[parent_sequence] = 0
                    
                    level3_counts[parent_sequence] += 1
                    outline.sequence = f"{parent_sequence}.{level3_counts[parent_sequence]}"
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"优化大纲结构失败: {str(e)}")
            return False
    
    def _find_parent_sequence_for_level3(self, outlines: List[BidOutline], current_outline: BidOutline) -> str:
        """为三级标题找到对应的二级标题序号"""
        # 找到当前节点之前最近的二级标题
        for outline in reversed(outlines):
            if outline.id == current_outline.id:
                break
            if outline.level == 2:
                return outline.sequence
        
        # 如果没找到，返回默认值
        return "1.1"
    
    def generate_document_content(self, db: Session, project_id: int, user_id: str, 
                                outline_id: int, regenerate: bool = False) -> Optional[BidDocument]:
        """基于大纲节点生成文档内容"""
        try:
            logger.info(f"开始为项目 {project_id} 大纲节点 {outline_id} 生成文档内容")
            
            # 获取大纲节点
            outline = db.query(BidOutline).filter(
                BidOutline.id == outline_id,
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).first()
            
            if not outline:
                logger.error(f"大纲节点 {outline_id} 不存在")
                return None
            
            # 检查是否已有文档
            existing_doc = db.query(BidDocument).filter(
                BidDocument.project_id == project_id,
                BidDocument.user_id == user_id,
                BidDocument.outline_id == outline_id
            ).first()
            
            if existing_doc and not regenerate:
                logger.info(f"大纲节点 {outline_id} 已有对应文档，跳过生成")
                return existing_doc
            
            # 获取项目需求分析
            analysis = db.query(RequirementAnalysis).filter(
                RequirementAnalysis.project_id == project_id,
                RequirementAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                logger.error(f"项目 {project_id} 需求分析不存在")
                return None
            
            # 构建文档生成提示词
            prompt = self._build_document_prompt(outline, analysis, db, project_id, user_id)
            
            # 调用大模型生成内容
            content = self.llm_client.generate_content(prompt, max_tokens=3000)
            
            # 清理和优化内容
            cleaned_content = self._clean_document_content(content)
            
            # 质量检查
            quality_score = self._check_content_quality(cleaned_content, outline)
            
            if existing_doc:
                # 更新现有文档
                existing_doc.content = cleaned_content
                existing_doc.status = DocumentStatus.GENERATED
                existing_doc.version += 1
                db.commit()
                db.refresh(existing_doc)
                
                logger.info(f"大纲节点 {outline_id} 文档内容更新完成，质量评分: {quality_score}")
                return existing_doc
            else:
                # 创建新文档
                document = BidDocument(
                    project_id=project_id,
                    user_id=user_id,
                    title=f"{outline.sequence} {outline.title}",
                    content=cleaned_content,
                    outline_id=outline_id,
                    status=DocumentStatus.GENERATED,
                    version=1
                )
                
                db.add(document)
                db.commit()
                db.refresh(document)
                
                logger.info(f"大纲节点 {outline_id} 文档内容生成完成，质量评分: {quality_score}")
                return document
                
        except Exception as e:
            logger.error(f"生成文档内容失败: {str(e)}")
            db.rollback()
            return None
    
    def generate_all_documents(self, db: Session, project_id: int, user_id: str, 
                             regenerate: bool = False) -> List[BidDocument]:
        """生成所有大纲节点的文档内容"""
        try:
            logger.info(f"开始为项目 {project_id} 生成所有文档内容")
            
            # 获取所有大纲节点
            outlines = db.query(BidOutline).filter(
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).order_by(BidOutline.level, BidOutline.order_index).all()
            
            if not outlines:
                logger.error(f"项目 {project_id} 没有大纲节点")
                return []
            
            documents = []
            for outline in outlines:
                document = self.generate_document_content(
                    db, project_id, user_id, outline.id, regenerate
                )
                if document:
                    documents.append(document)
            
            logger.info(f"项目 {project_id} 所有文档生成完成，共生成 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"生成所有文档失败: {str(e)}")
            return []
    
    def _build_document_prompt(self, outline: BidOutline, analysis: RequirementAnalysis, 
                             db: Session, project_id: int, user_id: str) -> str:
        """构建文档内容生成提示词"""
        # 获取相关上下文信息
        context_info = self._get_context_info(outline, db, project_id, user_id)
        
        # 构建大纲项信息
        outline_item = f"{outline.sequence} {outline.title}"
        if outline.content:
            outline_item += f"\n内容说明：{outline.content}"
        if context_info:
            outline_item += f"\n上下文信息：{context_info}"
        
        prompt_data = {
            "outline_item": outline_item,
            "project_overview": analysis.project_overview or "无项目概述信息",
            "client_info": analysis.client_info or "无甲方信息",
            "critical_requirements": analysis.critical_requirements or "无关键需求信息",
            "important_requirements": analysis.important_requirements or "无重要需求信息"
        }
        
        return get_bid_content_template(**prompt_data)
    
    def _get_context_info(self, outline: BidOutline, db: Session, project_id: int, user_id: str) -> str:
        """获取大纲节点的上下文信息"""
        context_parts = []
        
        # 获取父节点信息
        if outline.parent_id:
            parent = db.query(BidOutline).filter(
                BidOutline.id == outline.parent_id,
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).first()
            if parent:
                context_parts.append(f"父章节: {parent.sequence} {parent.title}")
                if parent.content:
                    context_parts.append(f"父章节描述: {parent.content}")
        
        # 获取同级节点信息
        siblings = db.query(BidOutline).filter(
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id,
            BidOutline.parent_id == outline.parent_id,
            BidOutline.level == outline.level,
            BidOutline.id != outline.id
        ).order_by(BidOutline.order_index).all()
        
        if siblings:
            sibling_titles = [f"{s.sequence} {s.title}" for s in siblings]
            context_parts.append(f"同级章节: {', '.join(sibling_titles)}")
        
        # 获取子节点信息
        children = db.query(BidOutline).filter(
            BidOutline.parent_id == outline.id,
            BidOutline.project_id == project_id,
            BidOutline.user_id == user_id
        ).order_by(BidOutline.order_index).all()
        
        if children:
            child_titles = [f"{c.sequence} {c.title}" for c in children]
            context_parts.append(f"子章节: {', '.join(child_titles)}")
        
        return "\n".join(context_parts) if context_parts else "无相关上下文信息"
    
    def _clean_document_content(self, content: str) -> str:
        """清理和优化文档内容"""
        if not content:
            return ""
        
        # 移除多余的空行
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:
                    cleaned_lines.append('')
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        # 移除开头和结尾的空行
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def _check_content_quality(self, content: str, outline: BidOutline) -> float:
        """检查内容质量并返回评分（0-100）"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # 长度检查（20分）
        content_length = len(content.strip())
        if content_length >= 500:
            score += 20
        elif content_length >= 200:
            score += 15
        elif content_length >= 100:
            score += 10
        elif content_length >= 50:
            score += 5
        
        # 结构检查（20分）
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) >= 5:
            score += 20
        elif len(non_empty_lines) >= 3:
            score += 15
        elif len(non_empty_lines) >= 2:
            score += 10
        
        # 关键词相关性检查（30分）
        title_words = outline.title.lower().split()
        content_lower = content.lower()
        
        relevant_words = 0
        for word in title_words:
            if len(word) > 1 and word in content_lower:
                relevant_words += 1
        
        if title_words:
            relevance_ratio = relevant_words / len(title_words)
            score += relevance_ratio * 30
        
        # 专业术语检查（15分）
        professional_terms = [
            '技术', '方案', '实施', '管理', '质量', '服务', '系统', '架构',
            '设计', '开发', '测试', '部署', '维护', '支持', '培训', '文档'
        ]
        
        term_count = 0
        for term in professional_terms:
            if term in content:
                term_count += 1
        
        score += min(term_count * 2, 15)
        
        # 格式检查（15分）
        if '。' in content or '.' in content:
            score += 5
        if '：' in content or ':' in content:
            score += 5
        if any(char in content for char in ['、', '，', ',']):
            score += 5
        
        return min(score, 100.0)
    
    def optimize_document_content(self, db: Session, document_id: int, user_id: str) -> bool:
        """优化文档内容"""
        try:
            document = db.query(BidDocument).filter(
                BidDocument.id == document_id,
                BidDocument.user_id == user_id
            ).first()
            
            if not document:
                return False
            
            # 获取相关大纲和分析信息
            outline = db.query(BidOutline).filter(
                BidOutline.id == document.outline_id
            ).first()
            
            if not outline:
                return False
            
            analysis = db.query(RequirementAnalysis).filter(
                RequirementAnalysis.project_id == document.project_id,
                RequirementAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                return False
            
            # 构建优化提示词
            optimize_prompt = f"""
请优化以下标书章节内容，使其更加专业、完整和符合招标要求：

章节标题：{outline.sequence} {outline.title}
当前内容：
{document.content}

优化要求：
1. 保持内容的专业性和准确性
2. 确保内容与章节标题高度相关
3. 增加必要的技术细节和实施方案
4. 使用规范的商务文档语言
5. 确保内容结构清晰、逻辑合理

请返回优化后的内容：
"""
            
            # 调用大模型优化内容
            optimized_content = self.llm_client.generate_content(optimize_prompt, max_tokens=3000)
            
            if optimized_content and len(optimized_content.strip()) > len(document.content.strip()) * 0.5:
                # 更新文档内容
                document.content = self._clean_document_content(optimized_content)
                document.version += 1
                document.status = DocumentStatus.EDITED
                
                db.commit()
                logger.info(f"文档 {document_id} 内容优化完成")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"优化文档内容失败: {str(e)}")
            db.rollback()
            return False
    
    def generate_full_document(self, db: Session, project_id: int, user_id: str) -> str:
        """生成完整的标书文档"""
        try:
            # 获取项目信息
            project = db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == user_id
            ).first()
            
            if not project:
                return ""
            
            # 获取所有大纲节点（按序号排序）
            outlines = db.query(BidOutline).filter(
                BidOutline.project_id == project_id,
                BidOutline.user_id == user_id
            ).order_by(BidOutline.level, BidOutline.order_index).all()
            
            if not outlines:
                return ""
            
            # 获取所有文档内容
            documents = db.query(BidDocument).filter(
                BidDocument.project_id == project_id,
                BidDocument.user_id == user_id
            ).all()
            
            # 创建大纲ID到文档内容的映射
            doc_map = {doc.outline_id: doc for doc in documents if doc.outline_id}
            
            # 构建完整文档
            full_content = []
            
            # 添加文档标题
            full_content.append(f"# {project.name}")
            full_content.append("")
            full_content.append("---")
            full_content.append("")
            
            # 添加目录
            full_content.append("## 目录")
            full_content.append("")
            for outline in outlines:
                indent = "  " * (outline.level - 1)
                full_content.append(f"{indent}- {outline.sequence} {outline.title}")
            full_content.append("")
            full_content.append("---")
            full_content.append("")
            
            # 添加各章节内容
            for outline in outlines:
                # 添加章节标题
                level_prefix = "#" * (outline.level + 1)
                full_content.append(f"{level_prefix} {outline.sequence} {outline.title}")
                full_content.append("")
                
                # 添加对应的文档内容
                if outline.id in doc_map:
                    document = doc_map[outline.id]
                    full_content.append(document.content)
                else:
                    full_content.append("*此章节内容尚未生成*")
                
                full_content.append("")
                full_content.append("---")
                full_content.append("")
            
            return "\n".join(full_content)
            
        except Exception as e:
            logger.error(f"生成完整文档失败: {str(e)}")
            return ""