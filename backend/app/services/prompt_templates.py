"""
分析提示词模板管理
设计需求分析的提示词模板，实现不同分析任务的专用提示词
"""
from typing import Dict, Any, Optional
from enum import Enum
import json
import os
from datetime import datetime


class PromptType(Enum):
    """提示词类型枚举"""
    PROJECT_OVERVIEW = "project_overview"
    CLIENT_INFO = "client_info"
    BUDGET_INFO = "budget_info"
    DETAILED_REQUIREMENTS = "detailed_requirements"
    REQUIREMENTS_CLASSIFICATION = "requirements_classification"
    BID_OUTLINE = "bid_outline"
    BID_CONTENT = "bid_content"


class PromptVersion(Enum):
    """提示词版本枚举"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class PromptTemplateManager:
    """提示词模板管理器"""
    
    def __init__(self):
        """初始化提示词模板管理器"""
        self.templates = self._load_default_templates()
        self.current_version = PromptVersion.V2_0
    
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载默认提示词模板"""
        return {
            PromptType.PROJECT_OVERVIEW.value: {
                "v1.0": {
                    "template": """
请分析以下招标文件内容，提取项目概览信息。请按照以下格式输出：

**项目名称：**
**项目背景：**
**项目目标：**
**项目范围：**
**主要需求：**

招标文件内容：
{content}

请确保提取的信息准确、完整，并用简洁明了的语言表述。
""",
                    "description": "基础项目概览提取模板",
                    "created_at": "2024-01-01",
                    "parameters": ["content"]
                },
                "v2.0": {
                    "template": """
作为专业的招标文件分析专家，请仔细分析以下招标文件内容，提取项目概览信息。

请按照以下结构化格式输出，确保信息准确完整：

**项目名称：** [从文件中提取准确的项目名称]
**项目背景：** [详细描述项目产生的背景和原因]
**项目目标：** [明确列出项目要达成的具体目标]
**项目范围：** [清晰界定项目的边界和覆盖范围]
**主要需求：** [概括性描述核心需求和关键功能]
**项目特点：** [识别项目的独特性和重点关注领域]
**预期成果：** [描述项目完成后的预期交付物和效果]

分析要求：
1. 信息提取要准确，避免主观推测
2. 语言表述要专业、简洁、清晰
3. 如果某项信息在文件中未明确提及，请标注"文件中未明确说明"
4. 重点关注甲方的核心诉求和关键要求

招标文件内容：
{content}
""",
                    "description": "增强版项目概览提取模板，包含更详细的结构和分析要求",
                    "created_at": "2024-08-01",
                    "parameters": ["content"]
                }
            },
            
            PromptType.CLIENT_INFO.value: {
                "v1.0": {
                    "template": """
请分析以下招标文件内容，提取甲方相关信息。请按照以下格式输出：

**甲方单位：**
**联系方式：**
**项目负责人：**
**单位性质：**
**行业背景：**
**特殊要求：**

招标文件内容：
{content}

请确保提取的信息准确、完整。
""",
                    "description": "基础甲方信息提取模板",
                    "created_at": "2024-01-01",
                    "parameters": ["content"]
                },
                "v2.0": {
                    "template": """
作为专业的招标文件分析专家，请仔细分析以下招标文件内容，提取甲方相关信息。

请按照以下结构化格式输出：

**甲方单位：** [完整的单位名称和简称]
**单位性质：** [政府机关/事业单位/国企/民企等]
**行业背景：** [所属行业和业务领域]
**联系方式：** [联系电话、邮箱、地址等]
**项目负责人：** [负责人姓名和职务]
**组织架构：** [相关部门和决策层级]
**特殊要求：** [对供应商的特殊资质或能力要求]
**合作偏好：** [从文件中体现的合作方式和偏好]
**决策特点：** [决策流程和关注重点]

分析要求：
1. 重点关注甲方的组织特点和决策偏好
2. 识别甲方的核心关切和评判标准
3. 分析甲方的行业特点和业务需求
4. 如果信息不明确，请标注"需进一步确认"

招标文件内容：
{content}
""",
                    "description": "增强版甲方信息提取模板，更关注决策特点和合作偏好",
                    "created_at": "2024-08-01",
                    "parameters": ["content"]
                }
            },
            
            PromptType.BUDGET_INFO.value: {
                "v1.0": {
                    "template": """
请分析以下招标文件内容，提取预算相关信息。请按照以下格式输出：

**项目预算：**
**预算范围：**
**付款方式：**
**付款周期：**
**成本构成：**
**其他费用：**

招标文件内容：
{content}

请确保提取的信息准确、完整，如果某些信息未明确提及，请标注"未明确说明"。
""",
                    "description": "基础预算信息提取模板",
                    "created_at": "2024-01-01",
                    "parameters": ["content"]
                },
                "v2.0": {
                    "template": """
作为专业的招标文件分析专家，请仔细分析以下招标文件内容，提取预算和商务相关信息。

请按照以下结构化格式输出：

**项目预算：** [总预算金额和币种]
**预算范围：** [预算的上下限或区间]
**资金来源：** [政府拨款/自筹资金/专项资金等]
**付款方式：** [一次性付款/分期付款/按进度付款等]
**付款周期：** [具体的付款时间节点和条件]
**成本构成：** [硬件/软件/服务/人工等成本分解]
**价格要求：** [固定价格/可调价格/成本加成等]
**商务条件：** [质保期、维护费用、培训费用等]
**评标权重：** [价格在评标中的权重比例]
**其他费用：** [税费、运输费、安装费等额外费用]

分析要求：
1. 重点关注预算的合理性和可操作性
2. 识别隐含的成本要求和商务条件
3. 分析价格敏感度和评标倾向
4. 如果信息不明确，请标注"需进一步确认"

招标文件内容：
{content}
""",
                    "description": "增强版预算信息提取模板，包含更全面的商务分析",
                    "created_at": "2024-08-01",
                    "parameters": ["content"]
                }
            },
            
            PromptType.DETAILED_REQUIREMENTS.value: {
                "v2.0": {
                    "template": """
作为专业的需求分析专家，请仔细分析以下招标文件内容，提取所有详细的技术需求和功能需求。

请按照以下结构化格式输出：

**功能需求：**
- [系统核心功能和业务流程需求]
- [用户交互和界面需求]
- [数据处理和管理需求]
- [集成和接口需求]

**技术需求：**
- [技术架构和平台要求]
- [性能指标和容量要求]
- [安全性和可靠性要求]
- [兼容性和标准要求]

**质量需求：**
- [可用性和稳定性要求]
- [可维护性和可扩展性要求]
- [用户体验和易用性要求]
- [文档和培训要求]

**约束条件：**
- [时间进度和里程碑要求]
- [预算和成本约束]
- [技术栈和工具限制]
- [合规性和标准约束]

**交付要求：**
- [软件系统和功能模块]
- [技术文档和用户手册]
- [培训和技术支持]
- [部署和上线要求]

**验收标准：**
- [功能验收的具体标准]
- [性能测试的指标要求]
- [用户验收的评判标准]
- [项目完成的交付标准]

分析要求：
1. 需求提取要全面、准确、具体
2. 区分必需需求和可选需求
3. 识别隐含需求和潜在风险
4. 关注需求的优先级和重要性
5. 如果需求不明确，请标注"需进一步澄清"

招标文件内容：
{content}
""",
                    "description": "详细需求提取模板，包含全面的需求分析结构",
                    "created_at": "2024-08-01",
                    "parameters": ["content"]
                }
            },
            
            PromptType.REQUIREMENTS_CLASSIFICATION.value: {
                "v1.0": {
                    "template": """
请分析以下招标文件内容，根据甲方需求的关注程度将需求分为三个等级：

1. **关键需求**：必须满足的核心需求，直接影响项目成败
2. **重要需求**：对项目质量有重要影响的需求
3. **一般需求**：有助于提升项目价值但非必需的需求

请按照以下JSON格式输出：
```json
{{
    "critical_requirements": "关键需求的详细描述",
    "important_requirements": "重要需求的详细描述", 
    "general_requirements": "一般需求的详细描述"
}}
```

招标文件内容：
{content}

请确保分类准确，每个等级的需求描述要详细具体。
""",
                    "description": "基础需求分级模板",
                    "created_at": "2024-01-01",
                    "parameters": ["content"]
                },
                "v2.0": {
                    "template": """
作为专业的需求分析专家，请仔细分析以下招标文件内容，根据甲方需求的关注程度和项目成功的关键性将需求分为三个等级。

分级标准：
- **关键需求（Critical）**：必须100%满足，不满足将导致项目失败或被淘汰
- **重要需求（Important）**：应该满足，不满足会显著影响项目质量和竞争力
- **一般需求（General）**：可以满足，满足后能提升项目价值和用户满意度

请按照以下JSON格式输出，每个等级包含具体的需求条目和重要性说明：

```json
{{
    "critical_requirements": {{
        "description": "关键需求的总体描述",
        "items": [
            "具体的关键需求条目1",
            "具体的关键需求条目2"
        ],
        "impact": "不满足关键需求的影响和后果"
    }},
    "important_requirements": {{
        "description": "重要需求的总体描述",
        "items": [
            "具体的重要需求条目1",
            "具体的重要需求条目2"
        ],
        "impact": "不满足重要需求的影响"
    }},
    "general_requirements": {{
        "description": "一般需求的总体描述",
        "items": [
            "具体的一般需求条目1",
            "具体的一般需求条目2"
        ],
        "impact": "满足一般需求的价值和好处"
    }}
}}
```

分析要求：
1. 仔细识别甲方的核心关切和底线要求
2. 区分技术需求和业务需求的重要性
3. 考虑需求的实现难度和成本影响
4. 关注需求之间的依赖关系和优先级
5. 确保分类逻辑清晰、标准一致

招标文件内容：
{content}
""",
                    "description": "增强版需求分级模板，包含结构化输出和影响分析",
                    "created_at": "2024-08-01",
                    "parameters": ["content"]
                }
            },
            
            PromptType.BID_OUTLINE.value: {
                "v2.0": {
                    "template": """
作为专业的标书撰写专家，请基于以下需求分析结果，生成一份完整的技术/服务方案标书大纲。

需求分析结果：
项目概览：{project_overview}
甲方信息：{client_info}
预算信息：{budget_info}
关键需求：{critical_requirements}
重要需求：{important_requirements}
一般需求：{general_requirements}

请生成标准格式的标书大纲，使用以下层级结构：
- 一级标题：1、2、3...
- 二级标题：1.1、1.2、1.3...
- 三级标题：1.1.1、1.1.2、1.1.3...

标书大纲应包含以下核心章节（可根据项目特点调整）：

1. 项目理解与需求分析
   1.1 项目背景理解
   1.2 需求分析与解读
   1.3 项目目标与成功标准

2. 技术方案设计
   2.1 总体架构设计
   2.2 核心功能设计
   2.3 技术选型与论证

3. 实施计划与进度安排
   3.1 项目实施方法论
   3.2 详细进度计划
   3.3 里程碑与交付物

4. 团队组织与人员配置
   4.1 项目组织架构
   4.2 核心团队介绍
   4.3 人员配置与职责

5. 质量保证体系
   5.1 质量管理体系
   5.2 测试策略与方法
   5.3 质量控制措施

6. 风险控制与应对措施
   6.1 风险识别与评估
   6.2 风险应对策略
   6.3 应急预案

7. 售后服务与技术支持
   7.1 服务承诺与标准
   7.2 技术支持体系
   7.3 培训与知识转移

8. 项目预算与报价
   8.1 成本构成分析
   8.2 详细报价清单
   8.3 付款方式与条件

大纲要求：
1. 结构清晰、逻辑合理、覆盖全面
2. 针对甲方关键需求重点设计章节
3. 体现技术实力和项目管理能力
4. 符合招标文件的具体要求
5. 每个章节都要有明确的目标和内容范围

请生成详细的大纲结构，包含各级标题和简要的内容说明。
""",
                    "description": "标书大纲生成模板，基于需求分析结果生成结构化大纲",
                    "created_at": "2024-08-01",
                    "parameters": ["project_overview", "client_info", "budget_info", "critical_requirements", "important_requirements", "general_requirements"]
                }
            },
            
            PromptType.BID_CONTENT.value: {
                "v2.0": {
                    "template": """
作为专业的标书撰写专家，请基于以下上下文信息和大纲要求，生成详细的标书内容。

大纲项：{outline_item}

上下文信息：
项目概览：{project_overview}
甲方信息：{client_info}
关键需求：{critical_requirements}
重要需求：{important_requirements}

撰写要求：
1. **针对性强**：内容与大纲项高度相关，紧扣主题
2. **需求导向**：充分体现对甲方需求的深度理解
3. **方案具体**：提供具体可行的解决方案和实施方法
4. **专业表达**：使用专业术语，语言准确、逻辑清晰
5. **结构完整**：内容层次分明，要点突出
6. **价值体现**：突出方案的优势和价值

内容结构建议：
- 开篇：简要说明本章节的目标和重要性
- 主体：详细阐述具体方案、方法、措施
- 总结：强调关键要点和预期效果

请生成专业、详细、有针对性的标书内容，确保内容充实、逻辑清晰，可以直接用于标书文档。内容长度应适中，既要详细具体，又要重点突出。
""",
                    "description": "标书内容生成模板，基于大纲项和上下文生成具体内容",
                    "created_at": "2024-08-01",
                    "parameters": ["outline_item", "project_overview", "client_info", "critical_requirements", "important_requirements"]
                }
            }
        }
    
    def get_template(self, prompt_type: PromptType, version: Optional[PromptVersion] = None) -> str:
        """
        获取指定类型和版本的提示词模板
        
        Args:
            prompt_type: 提示词类型
            version: 版本号，如果不指定则使用当前版本
            
        Returns:
            提示词模板字符串
        """
        if version is None:
            version = self.current_version
        
        template_data = self.templates.get(prompt_type.value, {})
        version_data = template_data.get(version.value, {})
        
        if not version_data:
            # 如果指定版本不存在，尝试使用最新版本
            available_versions = list(template_data.keys())
            if available_versions:
                latest_version = max(available_versions)
                version_data = template_data[latest_version]
        
        return version_data.get('template', '')
    
    def get_template_info(self, prompt_type: PromptType, version: Optional[PromptVersion] = None) -> Dict[str, Any]:
        """
        获取模板的详细信息
        
        Args:
            prompt_type: 提示词类型
            version: 版本号
            
        Returns:
            包含模板信息的字典
        """
        if version is None:
            version = self.current_version
        
        template_data = self.templates.get(prompt_type.value, {})
        version_data = template_data.get(version.value, {})
        
        return {
            'type': prompt_type.value,
            'version': version.value,
            'template': version_data.get('template', ''),
            'description': version_data.get('description', ''),
            'created_at': version_data.get('created_at', ''),
            'parameters': version_data.get('parameters', [])
        }
    
    def list_available_versions(self, prompt_type: PromptType) -> list:
        """
        列出指定类型的所有可用版本
        
        Args:
            prompt_type: 提示词类型
            
        Returns:
            版本列表
        """
        template_data = self.templates.get(prompt_type.value, {})
        return list(template_data.keys())
    
    def add_template(self, prompt_type: PromptType, version: PromptVersion, 
                    template: str, description: str, parameters: list) -> bool:
        """
        添加新的模板版本
        
        Args:
            prompt_type: 提示词类型
            version: 版本号
            template: 模板内容
            description: 描述
            parameters: 参数列表
            
        Returns:
            是否添加成功
        """
        try:
            if prompt_type.value not in self.templates:
                self.templates[prompt_type.value] = {}
            
            self.templates[prompt_type.value][version.value] = {
                'template': template,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'parameters': parameters
            }
            
            return True
        except Exception:
            return False
    
    def format_template(self, prompt_type: PromptType, **kwargs) -> str:
        """
        格式化模板，填入参数
        
        Args:
            prompt_type: 提示词类型
            **kwargs: 模板参数
            
        Returns:
            格式化后的提示词
        """
        template = self.get_template(prompt_type)
        if not template:
            return ""
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"缺少必需的模板参数: {e}")
    
    def validate_template_parameters(self, prompt_type: PromptType, **kwargs) -> Dict[str, Any]:
        """
        验证模板参数是否完整
        
        Args:
            prompt_type: 提示词类型
            **kwargs: 提供的参数
            
        Returns:
            验证结果字典
        """
        template_info = self.get_template_info(prompt_type)
        required_params = template_info.get('parameters', [])
        provided_params = list(kwargs.keys())
        
        missing_params = [param for param in required_params if param not in provided_params]
        extra_params = [param for param in provided_params if param not in required_params]
        
        return {
            'is_valid': len(missing_params) == 0,
            'required_parameters': required_params,
            'provided_parameters': provided_params,
            'missing_parameters': missing_params,
            'extra_parameters': extra_params
        }
    
    def get_template_usage_stats(self) -> Dict[str, Any]:
        """
        获取模板使用统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_types': len(self.templates),
            'total_versions': sum(len(versions) for versions in self.templates.values()),
            'types_info': {}
        }
        
        for prompt_type, versions in self.templates.items():
            stats['types_info'][prompt_type] = {
                'version_count': len(versions),
                'versions': list(versions.keys()),
                'latest_version': max(versions.keys()) if versions else None
            }
        
        return stats
    
    def export_templates(self, file_path: str) -> bool:
        """
        导出模板到文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            export_data = {
                'version': self.current_version.value,
                'export_time': datetime.now().isoformat(),
                'templates': self.templates
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_templates(self, file_path: str) -> bool:
        """
        从文件导入模板
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'templates' in import_data:
                self.templates.update(import_data['templates'])
                return True
            
            return False
        except Exception:
            return False


# 创建全局模板管理器实例
prompt_template_manager = PromptTemplateManager()


# 便捷函数
def get_project_overview_template(**kwargs) -> str:
    """获取项目概览提取模板"""
    return prompt_template_manager.format_template(PromptType.PROJECT_OVERVIEW, **kwargs)


def get_client_info_template(**kwargs) -> str:
    """获取甲方信息提取模板"""
    return prompt_template_manager.format_template(PromptType.CLIENT_INFO, **kwargs)


def get_budget_info_template(**kwargs) -> str:
    """获取预算信息提取模板"""
    return prompt_template_manager.format_template(PromptType.BUDGET_INFO, **kwargs)


def get_detailed_requirements_template(**kwargs) -> str:
    """获取详细需求提取模板"""
    return prompt_template_manager.format_template(PromptType.DETAILED_REQUIREMENTS, **kwargs)


def get_requirements_classification_template(**kwargs) -> str:
    """获取需求分级模板"""
    return prompt_template_manager.format_template(PromptType.REQUIREMENTS_CLASSIFICATION, **kwargs)


def get_bid_outline_template(**kwargs) -> str:
    """获取标书大纲生成模板"""
    return prompt_template_manager.format_template(PromptType.BID_OUTLINE, **kwargs)


def get_bid_content_template(**kwargs) -> str:
    """获取标书内容生成模板"""
    return prompt_template_manager.format_template(PromptType.BID_CONTENT, **kwargs)