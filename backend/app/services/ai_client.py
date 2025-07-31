"""
AI客户端服务
提供统一的AI模型调用接口，支持重试和降级机制
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AIModelType(Enum):
    """AI模型类型"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    CLAUDE = "claude"
    LOCAL_LLM = "local_llm"
    MOCK = "mock"  # 用于测试


@dataclass
class AIRequest:
    """AI请求数据结构"""
    prompt: str
    model_type: AIModelType = AIModelType.MOCK
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    retry_count: int = 3
    metadata: Dict[str, Any] = None


@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    model_type: AIModelType
    tokens_used: int = 0
    response_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class AIServiceError(Exception):
    """AI服务异常"""
    pass


class AIModelInterface(ABC):
    """AI模型接口"""
    
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """生成AI响应"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查模型是否可用"""
        pass


class MockAIModel(AIModelInterface):
    """模拟AI模型（用于测试和开发）"""
    
    def __init__(self):
        self.available = True
        self.response_templates = {
            "project_info": {
                "project_name": "智慧城市综合管理平台建设项目",
                "budget": "800万元人民币",
                "duration": "18个月",
                "location": "某某市政府大楼",
                "contact_info": "联系人：李经理，电话：138****5678，邮箱：li.manager@example.com",
                "deadline": "2024-12-31 14:00:00",
                "procurement_method": "公开招标",
                "project_overview": "本项目旨在建设一套综合性的智慧城市管理平台，整合城市各类数据资源，提供统一的管理和服务界面。"
            },
            "technical_requirements": {
                "functional_requirements": [
                    "用户权限管理系统",
                    "数据采集与处理模块",
                    "实时监控与预警功能",
                    "报表生成与统计分析",
                    "移动端应用支持",
                    "第三方系统集成接口"
                ],
                "performance_requirements": {
                    "response_time": "页面响应时间 < 3秒",
                    "concurrent_users": "支持1000+并发用户",
                    "availability": "系统可用性 ≥ 99.5%",
                    "data_processing": "支持TB级数据处理能力"
                },
                "technical_specifications": {
                    "architecture": "微服务架构",
                    "database": "MySQL 8.0+ / PostgreSQL 12+",
                    "framework": "Spring Boot 2.7+",
                    "frontend": "Vue.js 3.0+ / React 18+",
                    "deployment": "Docker容器化部署",
                    "cloud_platform": "支持阿里云/腾讯云部署"
                },
                "compliance_standards": [
                    "GB/T 25000.51-2016 软件产品质量要求与测试细则",
                    "GB/T 20273-2006 信息安全技术数据库管理系统安全技术要求",
                    "等保三级认证要求",
                    "ISO 27001信息安全管理体系"
                ],
                "security_requirements": [
                    "数据传输加密（HTTPS/TLS 1.3）",
                    "用户身份认证与授权",
                    "操作日志记录与审计",
                    "数据备份与恢复机制",
                    "防SQL注入和XSS攻击"
                ],
                "interface_requirements": [
                    "RESTful API接口设计",
                    "支持JSON/XML数据格式",
                    "WebSocket实时通信支持",
                    "标准化接口文档（OpenAPI 3.0）"
                ]
            },
            "evaluation_criteria": {
                "technical_score": {
                    "weight": 70,
                    "criteria": [
                        "技术方案完整性与可行性（20分）",
                        "系统架构设计合理性（15分）",
                        "技术先进性与创新性（15分）",
                        "系统安全性设计（10分）",
                        "项目实施方案（10分）"
                    ]
                },
                "commercial_score": {
                    "weight": 30,
                    "criteria": [
                        "投标报价合理性（15分）",
                        "商务条款响应度（8分）",
                        "售后服务方案（7分）"
                    ]
                },
                "qualification_requirements": [
                    "软件企业认证证书",
                    "ISO9001质量管理体系认证",
                    "CMMI3级及以上认证",
                    "近3年内类似项目经验不少于2个",
                    "项目团队核心成员具备相关技术认证"
                ],
                "evaluation_method": "综合评分法",
                "scoring_details": {
                    "technical_max": 70,
                    "commercial_max": 30,
                    "total_max": 100,
                    "pass_threshold": 60
                }
            },
            "submission_requirements": {
                "document_format": "PDF格式，A4纸张，单面打印",
                "submission_method": "现场密封提交 + 电子版U盘",
                "required_documents": [
                    "投标函及投标函附录",
                    "法定代表人身份证明书",
                    "授权委托书",
                    "技术方案书",
                    "商务报价书",
                    "企业资质证明材料",
                    "项目经验证明材料",
                    "项目团队简历",
                    "售后服务承诺书"
                ],
                "document_structure": {
                    "volume_1": "商务文件（投标函、资质证明等）",
                    "volume_2": "技术文件（技术方案、实施计划等）",
                    "volume_3": "报价文件（商务报价、成本分析等）"
                },
                "submission_deadline": "2024-12-31 14:00:00",
                "submission_location": "某某市政府采购中心三楼会议室",
                "special_requirements": [
                    "投标文件需加盖公章",
                    "电子版与纸质版内容必须一致",
                    "逾期提交的投标文件不予受理"
                ]
            },
            "outline_generation": {
                "chapters": [
                    {
                        "chapter_id": "1",
                        "title": "项目理解",
                        "description": "对招标项目的深入理解和分析，展示对项目背景、目标和需求的准确把握",
                        "subsections": [
                            {"id": "1.1", "title": "项目背景分析"},
                            {"id": "1.2", "title": "需求理解与分析"},
                            {"id": "1.3", "title": "项目目标与价值"},
                            {"id": "1.4", "title": "建设意义与必要性"}
                        ]
                    },
                    {
                        "chapter_id": "2",
                        "title": "技术方案",
                        "description": "详细的技术实施方案，包括系统架构、技术选型和实现方案",
                        "subsections": [
                            {"id": "2.1", "title": "总体架构设计"},
                            {"id": "2.2", "title": "技术选型与论证"},
                            {"id": "2.3", "title": "功能模块设计"},
                            {"id": "2.4", "title": "性能与安全设计"},
                            {"id": "2.5", "title": "接口设计方案"}
                        ]
                    },
                    {
                        "chapter_id": "3",
                        "title": "实施方案",
                        "description": "项目实施的详细计划和组织安排，确保项目顺利交付",
                        "subsections": [
                            {"id": "3.1", "title": "项目组织架构"},
                            {"id": "3.2", "title": "实施进度计划"},
                            {"id": "3.3", "title": "里程碑与交付物"},
                            {"id": "3.4", "title": "资源配置方案"},
                            {"id": "3.5", "title": "风险管控措施"}
                        ]
                    },
                    {
                        "chapter_id": "4",
                        "title": "质量保证",
                        "description": "全面的质量保证体系和措施，确保项目质量达到预期标准",
                        "subsections": [
                            {"id": "4.1", "title": "质量管理体系"},
                            {"id": "4.2", "title": "测试方案与策略"},
                            {"id": "4.3", "title": "验收标准与流程"},
                            {"id": "4.4", "title": "质量控制措施"}
                        ]
                    },
                    {
                        "chapter_id": "5",
                        "title": "团队实力",
                        "description": "项目团队的专业能力和项目经验展示",
                        "subsections": [
                            {"id": "5.1", "title": "团队组织结构"},
                            {"id": "5.2", "title": "核心人员简介"},
                            {"id": "5.3", "title": "类似项目经验"},
                            {"id": "5.4", "title": "技术认证与资质"}
                        ]
                    },
                    {
                        "chapter_id": "6",
                        "title": "服务保障",
                        "description": "完善的服务保障体系，包括培训、运维和技术支持",
                        "subsections": [
                            {"id": "6.1", "title": "培训服务方案"},
                            {"id": "6.2", "title": "运维支持体系"},
                            {"id": "6.3", "title": "技术支持服务"},
                            {"id": "6.4", "title": "系统升级维护"}
                        ]
                    }
                ]
            },
            "software_outline": {
                "chapters": [
                    {
                        "chapter_id": "1",
                        "title": "需求分析",
                        "description": "深入分析软件系统的功能需求和非功能需求",
                        "subsections": [
                            {"id": "1.1", "title": "业务需求分析"},
                            {"id": "1.2", "title": "功能需求规格"},
                            {"id": "1.3", "title": "非功能需求分析"},
                            {"id": "1.4", "title": "用户场景分析"}
                        ]
                    },
                    {
                        "chapter_id": "2",
                        "title": "系统设计",
                        "description": "软件系统的架构设计和详细设计方案",
                        "subsections": [
                            {"id": "2.1", "title": "系统架构设计"},
                            {"id": "2.2", "title": "数据库设计"},
                            {"id": "2.3", "title": "接口设计"},
                            {"id": "2.4", "title": "安全设计方案"},
                            {"id": "2.5", "title": "用户界面设计"}
                        ]
                    },
                    {
                        "chapter_id": "3",
                        "title": "开发方案",
                        "description": "软件开发的技术方案和实施策略",
                        "subsections": [
                            {"id": "3.1", "title": "开发方法论"},
                            {"id": "3.2", "title": "技术栈选择"},
                            {"id": "3.3", "title": "开发环境搭建"},
                            {"id": "3.4", "title": "代码规范与管理"}
                        ]
                    },
                    {
                        "chapter_id": "4",
                        "title": "测试方案",
                        "description": "全面的软件测试策略和实施方案",
                        "subsections": [
                            {"id": "4.1", "title": "测试策略与计划"},
                            {"id": "4.2", "title": "单元测试方案"},
                            {"id": "4.3", "title": "集成测试方案"},
                            {"id": "4.4", "title": "系统测试与验收"}
                        ]
                    },
                    {
                        "chapter_id": "5",
                        "title": "部署运维",
                        "description": "系统部署和运维保障方案",
                        "subsections": [
                            {"id": "5.1", "title": "部署架构方案"},
                            {"id": "5.2", "title": "监控告警体系"},
                            {"id": "5.3", "title": "备份恢复策略"},
                            {"id": "5.4", "title": "运维应急预案"}
                        ]
                    }
                ]
            },
            "infrastructure_outline": {
                "chapters": [
                    {
                        "chapter_id": "1",
                        "title": "项目概述",
                        "description": "基础设施项目的整体规划和建设目标",
                        "subsections": [
                            {"id": "1.1", "title": "项目背景与意义"},
                            {"id": "1.2", "title": "建设目标与范围"},
                            {"id": "1.3", "title": "技术路线选择"}
                        ]
                    },
                    {
                        "chapter_id": "2",
                        "title": "技术方案",
                        "description": "基础设施的技术设计和实施方案",
                        "subsections": [
                            {"id": "2.1", "title": "网络架构设计"},
                            {"id": "2.2", "title": "硬件配置方案"},
                            {"id": "2.3", "title": "软件平台选择"},
                            {"id": "2.4", "title": "安全防护体系"}
                        ]
                    },
                    {
                        "chapter_id": "3",
                        "title": "实施方案",
                        "description": "基础设施建设的具体实施计划",
                        "subsections": [
                            {"id": "3.1", "title": "施工组织设计"},
                            {"id": "3.2", "title": "进度计划安排"},
                            {"id": "3.3", "title": "质量控制措施"},
                            {"id": "3.4", "title": "安全施工保障"}
                        ]
                    }
                ]
            },
            "consulting_outline": {
                "chapters": [
                    {
                        "chapter_id": "1",
                        "title": "咨询理解",
                        "description": "对咨询项目需求和目标的深入理解",
                        "subsections": [
                            {"id": "1.1", "title": "项目背景理解"},
                            {"id": "1.2", "title": "咨询目标分析"},
                            {"id": "1.3", "title": "预期成果定义"}
                        ]
                    },
                    {
                        "chapter_id": "2",
                        "title": "咨询方法",
                        "description": "专业的咨询方法论和分析工具",
                        "subsections": [
                            {"id": "2.1", "title": "咨询方法论"},
                            {"id": "2.2", "title": "分析工具与模型"},
                            {"id": "2.3", "title": "调研实施方案"}
                        ]
                    },
                    {
                        "chapter_id": "3",
                        "title": "工作计划",
                        "description": "咨询项目的详细工作计划和安排",
                        "subsections": [
                            {"id": "3.1", "title": "工作阶段划分"},
                            {"id": "3.2", "title": "时间进度安排"},
                            {"id": "3.3", "title": "人员配置方案"},
                            {"id": "3.4", "title": "交付物清单"}
                        ]
                    }
                ]
            }
        }
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """生成模拟AI响应"""
        start_time = datetime.now()
        
        try:
            # 模拟网络延迟
            await asyncio.sleep(0.1)
            
            # 根据提示词内容判断返回类型
            content = self._generate_mock_content(request.prompt)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return AIResponse(
                content=content,
                model_type=request.model_type,
                tokens_used=len(content) // 4,  # 粗略估算token数
                response_time=response_time,
                success=True,
                metadata={"mock": True, "timestamp": end_time.isoformat()}
            )
            
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return AIResponse(
                content="",
                model_type=request.model_type,
                response_time=response_time,
                success=False,
                error_message=str(e),
                metadata={"mock": True, "error": True}
            )
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.available
    
    def _generate_mock_content(self, prompt: str) -> str:
        """根据提示词生成模拟内容"""
        prompt_lower = prompt.lower()
        
        if "项目基本信息" in prompt or "project_info" in prompt_lower:
            return json.dumps(self.response_templates["project_info"], ensure_ascii=False, indent=2)
        elif "技术要求" in prompt or "technical_requirements" in prompt_lower:
            return json.dumps(self.response_templates["technical_requirements"], ensure_ascii=False, indent=2)
        elif "评分标准" in prompt or "evaluation_criteria" in prompt_lower:
            return json.dumps(self.response_templates["evaluation_criteria"], ensure_ascii=False, indent=2)
        elif "提交要求" in prompt or "submission_requirements" in prompt_lower:
            return json.dumps(self.response_templates["submission_requirements"], ensure_ascii=False, indent=2)
        elif "大纲" in prompt or "outline" in prompt_lower:
            # 根据项目类型返回不同的大纲模板
            if "软件开发" in prompt or "software" in prompt_lower:
                return json.dumps(self.response_templates["software_outline"], ensure_ascii=False, indent=2)
            elif "基础设施" in prompt or "infrastructure" in prompt_lower:
                return json.dumps(self.response_templates["infrastructure_outline"], ensure_ascii=False, indent=2)
            elif "咨询" in prompt or "consulting" in prompt_lower:
                return json.dumps(self.response_templates["consulting_outline"], ensure_ascii=False, indent=2)
            else:
                return json.dumps(self.response_templates["outline_generation"], ensure_ascii=False, indent=2)
        else:
            # 默认返回项目信息
            return json.dumps(self.response_templates["project_info"], ensure_ascii=False, indent=2)


class OpenAIModel(AIModelInterface):
    """OpenAI模型实现（占位符）"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4"):
        self.api_key = api_key
        self.model_name = model_name
        # TODO: 初始化OpenAI客户端
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """调用OpenAI API"""
        # TODO: 实现OpenAI API调用
        raise NotImplementedError("OpenAI集成待实现")
    
    def is_available(self) -> bool:
        """检查OpenAI服务是否可用"""
        # TODO: 实现可用性检查
        return False


class AIClient:
    """AI客户端，提供统一的AI服务接口"""
    
    def __init__(self):
        self.models: Dict[AIModelType, AIModelInterface] = {}
        self.fallback_chain: List[AIModelType] = [
            AIModelType.OPENAI_GPT4,
            AIModelType.OPENAI_GPT35,
            AIModelType.CLAUDE,
            AIModelType.LOCAL_LLM,
            AIModelType.MOCK  # 最后的降级选项
        ]
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化AI模型"""
        # 目前只初始化Mock模型，其他模型待实现
        self.models[AIModelType.MOCK] = MockAIModel()
        
        # TODO: 根据配置初始化其他模型
        # self.models[AIModelType.OPENAI_GPT4] = OpenAIModel(api_key="...", model_name="gpt-4")
    
    async def generate(self, prompt: str, preferred_model: AIModelType = None, **kwargs) -> AIResponse:
        """
        生成AI响应，支持自动降级
        
        Args:
            prompt: 提示词
            preferred_model: 首选模型类型
            **kwargs: 其他参数
            
        Returns:
            AIResponse: AI响应结果
        """
        request = AIRequest(
            prompt=prompt,
            model_type=preferred_model or AIModelType.MOCK,
            **kwargs
        )
        
        # 确定尝试顺序
        if preferred_model and preferred_model in self.models:
            try_order = [preferred_model] + [m for m in self.fallback_chain if m != preferred_model]
        else:
            try_order = self.fallback_chain
        
        last_error = None
        
        for model_type in try_order:
            if model_type not in self.models:
                continue
                
            model = self.models[model_type]
            if not model.is_available():
                logger.warning(f"模型 {model_type.value} 不可用，尝试下一个")
                continue
            
            try:
                logger.info(f"尝试使用模型 {model_type.value}")
                request.model_type = model_type
                
                # 执行重试逻辑
                for attempt in range(request.retry_count):
                    try:
                        response = await asyncio.wait_for(
                            model.generate(request),
                            timeout=request.timeout
                        )
                        
                        if response.success:
                            logger.info(f"模型 {model_type.value} 调用成功")
                            return response
                        else:
                            logger.warning(f"模型 {model_type.value} 返回错误: {response.error_message}")
                            last_error = response.error_message
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"模型 {model_type.value} 调用超时，尝试 {attempt + 1}/{request.retry_count}")
                        last_error = "调用超时"
                        if attempt < request.retry_count - 1:
                            await asyncio.sleep(2 ** attempt)  # 指数退避
                            
                    except Exception as e:
                        logger.warning(f"模型 {model_type.value} 调用异常: {str(e)}")
                        last_error = str(e)
                        if attempt < request.retry_count - 1:
                            await asyncio.sleep(2 ** attempt)
                        
            except Exception as e:
                logger.error(f"模型 {model_type.value} 初始化失败: {str(e)}")
                last_error = str(e)
                continue
        
        # 所有模型都失败了
        raise AIServiceError(f"所有AI模型都不可用，最后错误: {last_error}")
    
    async def generate_structured(
        self, 
        prompt: str, 
        expected_format: str = "json",
        validation_func: callable = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化响应
        
        Args:
            prompt: 提示词
            expected_format: 期望的格式（json, yaml等）
            validation_func: 验证函数
            **kwargs: 其他参数
            
        Returns:
            Dict: 解析后的结构化数据
        """
        response = await self.generate(prompt, **kwargs)
        
        if not response.success:
            raise AIServiceError(f"AI生成失败: {response.error_message}")
        
        try:
            if expected_format.lower() == "json":
                data = json.loads(response.content)
            else:
                raise ValueError(f"不支持的格式: {expected_format}")
            
            # 执行验证
            if validation_func and not validation_func(data):
                raise ValueError("数据验证失败")
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 内容: {response.content[:200]}...")
            raise AIServiceError(f"AI响应格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"结构化数据处理失败: {str(e)}")
            raise AIServiceError(f"数据处理失败: {str(e)}")
    
    def add_model(self, model_type: AIModelType, model: AIModelInterface):
        """添加AI模型"""
        self.models[model_type] = model
        logger.info(f"添加AI模型: {model_type.value}")
    
    def remove_model(self, model_type: AIModelType):
        """移除AI模型"""
        if model_type in self.models:
            del self.models[model_type]
            logger.info(f"移除AI模型: {model_type.value}")
    
    def get_available_models(self) -> List[AIModelType]:
        """获取可用的模型列表"""
        return [
            model_type for model_type, model in self.models.items()
            if model.is_available()
        ]


# 全局AI客户端实例
_ai_client = None


def get_ai_client() -> AIClient:
    """获取AI客户端实例"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


# 提示词模板
class PromptTemplates:
    """AI提示词模板"""
    
    PROJECT_INFO_TEMPLATE = """
请从以下招标文件中提取项目基本信息，以JSON格式返回：

需要提取的信息包括：
- project_name: 项目名称
- budget: 项目预算（包含数字和单位）
- duration: 项目工期（包含时间长度）
- location: 项目地点
- contact_info: 联系方式（包含联系人、电话、邮箱等）
- deadline: 投标截止时间
- procurement_method: 采购方式
- project_overview: 项目概述

招标文件内容：
{content}

请返回标准的JSON格式，如果某个字段无法识别，请设置为"未识别"。
确保返回的是有效的JSON格式，不要包含任何其他文本。
"""

    TECHNICAL_REQUIREMENTS_TEMPLATE = """
请从以下招标文件中提取技术要求，以JSON格式返回：

需要提取的信息包括：
- functional_requirements: 功能性要求列表
- performance_requirements: 性能要求（如响应时间、并发数等）
- technical_specifications: 技术规格（如硬件配置、软件版本等）
- compliance_standards: 合规标准（如国标、行标等）
- security_requirements: 安全要求
- interface_requirements: 接口要求

招标文件内容：
{content}

请返回标准的JSON格式，列表类型的字段如果为空请返回空数组[]。
确保返回的是有效的JSON格式，不要包含任何其他文本。
"""

    EVALUATION_CRITERIA_TEMPLATE = """
请从以下招标文件中提取评分标准，以JSON格式返回：

需要提取的信息包括：
- technical_score: 技术分权重和评分标准
- commercial_score: 商务分权重和评分标准  
- qualification_requirements: 资质要求
- evaluation_method: 评标方法（如综合评分法、最低价法等）
- scoring_details: 具体评分细则

招标文件内容：
{content}

请返回标准的JSON格式，权重请用数字表示（如70表示70%）。
确保返回的是有效的JSON格式，不要包含任何其他文本。
"""

    SUBMISSION_REQUIREMENTS_TEMPLATE = """
请从以下招标文件中提取投标文件提交要求，以JSON格式返回：

需要提取的信息包括：
- document_format: 文档格式要求（如PDF、Word等）
- submission_method: 提交方式（如现场提交、邮寄、电子投标等）
- required_documents: 必需文档清单
- document_structure: 文档结构要求
- submission_deadline: 提交截止时间
- submission_location: 提交地点
- special_requirements: 特殊要求

招标文件内容：
{content}

请返回标准的JSON格式。
确保返回的是有效的JSON格式，不要包含任何其他文本。
"""

    @classmethod
    def format_project_info_prompt(cls, content: str) -> str:
        """格式化项目信息提取提示词"""
        return cls.PROJECT_INFO_TEMPLATE.format(content=content[:4000])
    
    @classmethod
    def format_technical_requirements_prompt(cls, content: str) -> str:
        """格式化技术要求提取提示词"""
        return cls.TECHNICAL_REQUIREMENTS_TEMPLATE.format(content=content[:4000])
    
    @classmethod
    def format_evaluation_criteria_prompt(cls, content: str) -> str:
        """格式化评分标准提取提示词"""
        return cls.EVALUATION_CRITERIA_TEMPLATE.format(content=content[:4000])
    
    @classmethod
    def format_submission_requirements_prompt(cls, content: str) -> str:
        """格式化提交要求提取提示词"""
        return cls.SUBMISSION_REQUIREMENTS_TEMPLATE.format(content=content[:4000])

    # 大纲生成相关提示词模板
    OUTLINE_GENERATION_TEMPLATE = """
基于以下招标分析结果，生成专业的标书大纲结构。请以JSON格式返回，包含详细的章节和子章节信息。

项目基本信息：
{project_info}

技术要求：
{technical_requirements}

评分标准：
{evaluation_criteria}

提交要求：
{submission_requirements}

请生成包含以下结构的大纲：
{{
    "chapters": [
        {{
            "chapter_id": "1",
            "title": "章节标题",
            "description": "章节描述，说明本章节的主要内容和目的",
            "subsections": [
                {{"id": "1.1", "title": "子章节标题"}},
                {{"id": "1.2", "title": "子章节标题"}}
            ]
        }}
    ]
}}

要求：
1. 大纲应该全面覆盖招标要求的所有方面
2. 章节安排要逻辑清晰，层次分明
3. 每个章节都要有明确的描述说明
4. 子章节要具体且有针对性
5. 大纲应该突出技术实力和竞争优势
6. 符合标书撰写的专业规范
7. 章节数量控制在5-8个主要章节
8. 每个主要章节包含3-6个子章节

请确保生成的大纲专业、完整、有针对性。
确保返回的是有效的JSON格式，不要包含任何其他文本。
"""

    SOFTWARE_OUTLINE_TEMPLATE = """
基于以下软件开发项目的招标分析结果，生成专业的软件项目标书大纲。

项目信息：{project_info}
技术要求：{technical_requirements}
评分标准：{evaluation_criteria}

请生成适合软件开发项目的标书大纲，重点突出：
1. 需求分析和系统设计能力
2. 技术架构和开发方案
3. 项目管理和质量保证
4. 团队实力和项目经验

返回JSON格式的大纲结构，包含章节ID、标题、描述和子章节。
确保大纲符合软件项目特点，体现技术专业性。
"""

    INFRASTRUCTURE_OUTLINE_TEMPLATE = """
基于以下基础设施项目的招标分析结果，生成专业的基础设施项目标书大纲。

项目信息：{project_info}
技术要求：{technical_requirements}
评分标准：{evaluation_criteria}

请生成适合基础设施项目的标书大纲，重点突出：
1. 工程设计和施工方案
2. 设备选型和技术规格
3. 项目实施和进度控制
4. 质量管理和安全保障

返回JSON格式的大纲结构，包含章节ID、标题、描述和子章节。
确保大纲符合基础设施项目特点，体现工程专业性。
"""

    CONSULTING_OUTLINE_TEMPLATE = """
基于以下咨询项目的招标分析结果，生成专业的咨询项目标书大纲。

项目信息：{project_info}
技术要求：{technical_requirements}
评分标准：{evaluation_criteria}

请生成适合咨询项目的标书大纲，重点突出：
1. 咨询方法论和分析框架
2. 调研方案和实施计划
3. 专业团队和项目经验
4. 成果交付和价值体现

返回JSON格式的大纲结构，包含章节ID、标题、描述和子章节。
确保大纲符合咨询项目特点，体现专业咨询能力。
"""

    OUTLINE_OPTIMIZATION_TEMPLATE = """
请对以下标书大纲进行质量评估和优化建议：

当前大纲：
{current_outline}

招标要求：
{requirements_summary}

评分标准：
{evaluation_criteria}

请从以下方面进行评估：
1. 大纲完整性 - 是否覆盖所有招标要求
2. 逻辑结构 - 章节安排是否合理
3. 针对性 - 是否突出竞争优势
4. 专业性 - 是否符合行业规范

返回JSON格式的评估结果：
{{
    "quality_score": 85,
    "strengths": ["优势点1", "优势点2"],
    "weaknesses": ["不足点1", "不足点2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "optimized_outline": {{
        "chapters": [...]
    }}
}}
"""

    @classmethod
    def format_outline_generation_prompt(
        cls, 
        project_info: dict, 
        technical_requirements: dict,
        evaluation_criteria: dict,
        submission_requirements: dict
    ) -> str:
        """格式化大纲生成提示词"""
        import json
        return cls.OUTLINE_GENERATION_TEMPLATE.format(
            project_info=json.dumps(project_info, ensure_ascii=False, indent=2),
            technical_requirements=json.dumps(technical_requirements, ensure_ascii=False, indent=2),
            evaluation_criteria=json.dumps(evaluation_criteria, ensure_ascii=False, indent=2),
            submission_requirements=json.dumps(submission_requirements, ensure_ascii=False, indent=2)
        )
    
    @classmethod
    def format_project_type_outline_prompt(
        cls,
        project_type: str,
        project_info: dict,
        technical_requirements: dict,
        evaluation_criteria: dict
    ) -> str:
        """根据项目类型格式化大纲生成提示词"""
        import json
        
        template_map = {
            "software_development": cls.SOFTWARE_OUTLINE_TEMPLATE,
            "infrastructure": cls.INFRASTRUCTURE_OUTLINE_TEMPLATE,
            "consulting": cls.CONSULTING_OUTLINE_TEMPLATE
        }
        
        template = template_map.get(project_type, cls.OUTLINE_GENERATION_TEMPLATE)
        
        return template.format(
            project_info=json.dumps(project_info, ensure_ascii=False, indent=2),
            technical_requirements=json.dumps(technical_requirements, ensure_ascii=False, indent=2),
            evaluation_criteria=json.dumps(evaluation_criteria, ensure_ascii=False, indent=2)
        )
    
    @classmethod
    def format_outline_optimization_prompt(
        cls,
        current_outline: dict,
        requirements_summary: dict,
        evaluation_criteria: dict
    ) -> str:
        """格式化大纲优化提示词"""
        import json
        from datetime import datetime
        
        def json_serializer(obj):
            """JSON序列化器，处理特殊类型"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return cls.OUTLINE_OPTIMIZATION_TEMPLATE.format(
            current_outline=json.dumps(current_outline, ensure_ascii=False, indent=2, default=json_serializer),
            requirements_summary=json.dumps(requirements_summary, ensure_ascii=False, indent=2, default=json_serializer),
            evaluation_criteria=json.dumps(evaluation_criteria, ensure_ascii=False, indent=2, default=json_serializer)
        )

    # 内容生成相关提示词模板
    CONTENT_GENERATION_TEMPLATE = """
请为标书的"{chapter_title}"章节生成专业、详细的内容。

项目背景信息：
{project_context}

章节要求：
- 章节标题：{chapter_title}
- 章节描述：{chapter_description}
{subsections_info}

技术要求参考：
{technical_requirements}

评分标准：{evaluation_criteria}

内容生成要求：
1. 内容要专业、详细，符合标书撰写规范
2. 突出我方的技术实力和竞争优势
3. 针对招标要求进行有针对性的回应
4. 内容结构清晰，逻辑性强
5. 字数控制在800-2000字之间
6. 使用专业术语，体现技术深度
7. 避免空洞的表述，要有具体的方案和措施

请生成该章节的完整内容：
"""

    PROJECT_UNDERSTANDING_TEMPLATE = """
请为标书的"项目理解"章节生成专业内容。

项目信息：
{project_info}

技术要求：
{technical_requirements}

评分标准：
{evaluation_criteria}

请从以下几个方面生成项目理解内容：
1. 项目背景分析 - 深入分析项目的背景和意义
2. 需求理解 - 准确理解和分析项目需求
3. 目标把握 - 明确项目目标和预期成果
4. 价值体现 - 阐述项目的价值和重要性

内容要求：
- 体现对项目的深度理解
- 突出我方的专业能力
- 针对性强，避免泛泛而谈
- 逻辑清晰，结构合理
- 字数1000-1500字

请生成专业的项目理解内容：
"""

    TECHNICAL_SOLUTION_TEMPLATE = """
请为标书的"技术方案"章节生成专业内容。

项目信息：
{project_info}

技术要求：
{technical_requirements}

评分标准：
{evaluation_criteria}

请从以下几个方面生成技术方案内容：
1. 总体架构设计 - 系统整体架构和设计思路
2. 技术选型 - 关键技术的选择和论证
3. 功能设计 - 核心功能的设计方案
4. 性能设计 - 性能优化和保障措施
5. 安全设计 - 安全防护和风险控制

内容要求：
- 技术方案具体可行
- 体现技术先进性和创新性
- 针对招标要求进行设计
- 包含具体的技术细节
- 字数1500-2500字

请生成专业的技术方案内容：
"""

    IMPLEMENTATION_PLAN_TEMPLATE = """
请为标书的"实施计划"章节生成专业内容。

项目信息：
{project_info}

技术要求：
{technical_requirements}

评分标准：
{evaluation_criteria}

请从以下几个方面生成实施计划内容：
1. 项目组织架构 - 项目团队组织和人员配置
2. 实施进度安排 - 详细的时间计划和里程碑
3. 资源配置 - 人力、物力资源的配置方案
4. 风险管控 - 风险识别和应对措施

内容要求：
- 计划详细可执行
- 时间安排合理
- 资源配置充分
- 风险考虑全面
- 字数1200-1800字

请生成专业的实施计划内容：
"""

    QUALITY_ASSURANCE_TEMPLATE = """
请为标书的"质量保证"章节生成专业内容。

项目信息：
{project_info}

技术要求：
{technical_requirements}

评分标准：
{evaluation_criteria}

请从以下几个方面生成质量保证内容：
1. 质量管理体系 - 质量管理的组织和制度
2. 测试方案 - 全面的测试策略和方法
3. 验收标准 - 明确的验收标准和流程
4. 质量控制 - 质量控制的具体措施

内容要求：
- 质量体系完整
- 测试方案全面
- 验收标准明确
- 控制措施具体
- 字数1000-1500字

请生成专业的质量保证内容：
"""

    SERVICE_SUPPORT_TEMPLATE = """
请为标书的"服务保障"章节生成专业内容。

项目信息：
{project_info}

技术要求：
{technical_requirements}

评分标准：
{evaluation_criteria}

请从以下几个方面生成服务保障内容：
1. 培训服务 - 用户培训和技术培训方案
2. 运维支持 - 系统运维和技术支持服务
3. 技术支持 - 技术咨询和问题解决
4. 升级维护 - 系统升级和维护服务

内容要求：
- 服务内容全面
- 服务标准明确
- 响应时间具体
- 保障措施到位
- 字数800-1200字

请生成专业的服务保障内容：
"""

    @classmethod
    def format_content_generation_prompt(
        cls,
        chapter_title: str,
        chapter_description: str,
        project_context: dict,
        subsections_info: str,
        technical_requirements: str,
        evaluation_criteria: str
    ) -> str:
        """格式化内容生成提示词"""
        import json
        
        project_context_str = "\n".join([
            f"- {key}: {value}" for key, value in project_context.items()
        ])
        
        return cls.CONTENT_GENERATION_TEMPLATE.format(
            chapter_title=chapter_title,
            project_context=project_context_str,
            chapter_description=chapter_description,
            subsections_info=subsections_info,
            technical_requirements=technical_requirements,
            evaluation_criteria=evaluation_criteria
        )
    
    @classmethod
    def format_chapter_specific_prompt(
        cls,
        chapter_type: str,
        project_info: dict,
        technical_requirements: dict,
        evaluation_criteria: dict
    ) -> str:
        """根据章节类型格式化特定提示词"""
        import json
        
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        template_map = {
            "project_understanding": cls.PROJECT_UNDERSTANDING_TEMPLATE,
            "technical_solution": cls.TECHNICAL_SOLUTION_TEMPLATE,
            "implementation_plan": cls.IMPLEMENTATION_PLAN_TEMPLATE,
            "quality_assurance": cls.QUALITY_ASSURANCE_TEMPLATE,
            "service_support": cls.SERVICE_SUPPORT_TEMPLATE
        }
        
        template = template_map.get(chapter_type, cls.CONTENT_GENERATION_TEMPLATE)
        
        return template.format(
            project_info=json.dumps(project_info, ensure_ascii=False, indent=2, default=json_serializer),
            technical_requirements=json.dumps(technical_requirements, ensure_ascii=False, indent=2, default=json_serializer),
            evaluation_criteria=json.dumps(evaluation_criteria, ensure_ascii=False, indent=2, default=json_serializer)
        )