from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.bid_outline import BidOutline
from app.models.requirement_analysis import RequirementAnalysis
from app.models.project import Project, ProjectStatus
from app.services.llm_client import LLMClient
from app.services.prompt_templates import get_bid_outline_template
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