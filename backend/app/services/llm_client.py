"""
大模型API客户端
提供聊天完成、文档分析、内容生成接口
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import os


class LLMException(Exception):
    """大模型服务异常"""
    pass


class LLMClient:
    """大模型API客户端"""
    
    def __init__(
        self, 
        api_url: str = "http://192.168.30.54:3000/v1",
        api_key: str = "token-abc123",
        model_name: str = "Qwen3-30B-A3B-FP8",
        timeout: int = 300
    ):
        """
        初始化大模型客户端
        
        Args:
            api_url: 大模型API服务地址
            api_key: API密钥
            model_name: 模型名称
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if not self.session:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        聊天完成接口
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            stream: 是否流式输出
            
        Returns:
            生成的回复内容
            
        Raises:
            LLMException: 请求失败时抛出
        """
        try:
            session = self._get_session()
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            url = f"{self.api_url}/chat/completions"
            logger.info(f"Sending chat completion request to: {url}")
            logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMException(
                        f"Chat completion failed with status {response.status}: {error_text}"
                    )
                
                result = await response.json()
                
                # 提取回复内容
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    logger.info("Chat completion successful")
                    return content
                else:
                    raise LLMException("No valid response in chat completion result")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during chat completion: {e}")
            raise LLMException(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during chat completion: {e}")
            raise LLMException(f"Chat completion error: {e}")
    
    async def analyze_document(
        self, 
        content: str, 
        prompt_template: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        文档分析接口
        
        Args:
            content: 文档内容
            prompt_template: 分析提示词模板
            temperature: 温度参数
            max_tokens: 最大生成token数
            
        Returns:
            分析结果
            
        Raises:
            LLMException: 分析失败时抛出
        """
        try:
            # 构建分析消息
            analysis_prompt = prompt_template.format(content=content)
            messages = [
                {"role": "system", "content": "你是一个专业的招标文件分析专家，能够准确提取和分析招标文件中的关键信息。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            logger.info("Starting document analysis")
            result = await self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            logger.info("Document analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise LLMException(f"Document analysis error: {e}")
    
    async def generate_content(
        self, 
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        内容生成接口
        
        Args:
            prompt: 生成提示词
            temperature: 温度参数
            max_tokens: 最大生成token数
            
        Returns:
            生成的内容
            
        Raises:
            LLMException: 生成失败时抛出
        """
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            logger.info("Starting content generation")
            result = await self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            logger.info("Content generation completed")
            return result
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise LLMException(f"Content generation error: {e}")
    
    async def extract_project_overview(self, content: str) -> str:
        """
        提取项目概览信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            项目概览信息
        """
        prompt_template = """
请分析以下招标文件内容，提取项目概览信息。请按照以下格式输出：

**项目名称：**
**项目背景：**
**项目目标：**
**项目范围：**
**主要需求：**

招标文件内容：
{content}

请确保提取的信息准确、完整，并用简洁明了的语言表述。
"""
        
        return await self.analyze_document(content, prompt_template)
    
    async def extract_client_info(self, content: str) -> str:
        """
        提取甲方信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            甲方信息
        """
        prompt_template = """
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
"""
        
        return await self.analyze_document(content, prompt_template)
    
    async def extract_budget_info(self, content: str) -> str:
        """
        提取预算信息
        
        Args:
            content: 招标文件内容
            
        Returns:
            预算信息
        """
        prompt_template = """
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
"""
        
        return await self.analyze_document(content, prompt_template)
    
    async def classify_requirements(self, content: str) -> Dict[str, str]:
        """
        需求分级分类
        
        Args:
            content: 招标文件内容
            
        Returns:
            分级后的需求字典，包含critical_requirements, important_requirements, general_requirements
        """
        prompt_template = """
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
"""
        
        result = await self.analyze_document(content, prompt_template, temperature=0.3)
        
        try:
            # 尝试解析JSON结果
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
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
    
    async def generate_bid_outline(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成标书大纲
        
        Args:
            analysis_result: 需求分析结果
            
        Returns:
            标书大纲内容
        """
        prompt = f"""
基于以下需求分析结果，生成一份完整的技术/服务方案标书大纲。

项目概览：
{analysis_result.get('project_overview', '')}

甲方信息：
{analysis_result.get('client_info', '')}

预算信息：
{analysis_result.get('budget_info', '')}

关键需求：
{analysis_result.get('critical_requirements', '')}

重要需求：
{analysis_result.get('important_requirements', '')}

一般需求：
{analysis_result.get('general_requirements', '')}

请生成标准格式的标书大纲，使用以下层级结构：
- 一级标题：1、2、3...
- 二级标题：1.1、1.2、1.3...
- 三级标题：1.1.1、1.1.2、1.1.3...

大纲应包含但不限于：
1. 项目理解与需求分析
2. 技术方案设计
3. 实施计划与进度安排
4. 团队组织与人员配置
5. 质量保证体系
6. 风险控制与应对措施
7. 售后服务与技术支持
8. 项目预算与报价

请确保大纲结构清晰、逻辑合理、覆盖全面。
"""
        
        return await self.generate_content(prompt, temperature=0.5)
    
    async def generate_bid_content(self, outline_item: str, context: Dict[str, Any]) -> str:
        """
        基于大纲项生成标书内容
        
        Args:
            outline_item: 大纲项标题和描述
            context: 上下文信息（需求分析结果等）
            
        Returns:
            生成的标书内容
        """
        prompt = f"""
基于以下上下文信息和大纲要求，生成详细的标书内容。

大纲项：{outline_item}

上下文信息：
项目概览：{context.get('project_overview', '')}
甲方信息：{context.get('client_info', '')}
关键需求：{context.get('critical_requirements', '')}
重要需求：{context.get('important_requirements', '')}

请生成专业、详细、有针对性的标书内容，确保：
1. 内容与大纲项高度相关
2. 充分体现对甲方需求的理解
3. 提供具体可行的解决方案
4. 语言专业、逻辑清晰
5. 篇幅适中，内容充实

生成的内容应该是完整的段落，可以直接用于标书文档。
"""
        
        return await self.generate_content(prompt, temperature=0.6)
    
    def chat_completion_sync(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """
        同步聊天完成接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            生成的回复内容
        """
        async def _chat():
            async with self:
                return await self.chat_completion(messages, **kwargs)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_chat())
    
    def analyze_document_sync(self, content: str, prompt_template: str, **kwargs) -> str:
        """
        同步文档分析接口
        
        Args:
            content: 文档内容
            prompt_template: 提示词模板
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        async def _analyze():
            async with self:
                return await self.analyze_document(content, prompt_template, **kwargs)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_analyze())
    
    def generate_content_sync(self, prompt: str, **kwargs) -> str:
        """
        同步内容生成接口
        
        Args:
            prompt: 生成提示词
            **kwargs: 其他参数
            
        Returns:
            生成的内容
        """
        async def _generate():
            async with self:
                return await self.generate_content(prompt, **kwargs)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_generate())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict包含服务状态信息
        """
        try:
            # 发送简单的测试请求
            test_messages = [{"role": "user", "content": "Hello"}]
            await self.chat_completion(test_messages, max_tokens=10)
            
            return {
                "status": "healthy",
                "service": "LLM",
                "model": self.model_name,
                "api_url": self.api_url
            }
            
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "LLM",
                "model": self.model_name,
                "api_url": self.api_url
            }


# 从环境变量获取配置
LLM_API_URL = os.getenv("LLM_API_URL", "http://192.168.30.54:3000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "token-abc123")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Qwen3-30B-A3B-FP8")

# 创建全局客户端实例
llm_client = LLMClient(
    api_url=LLM_API_URL,
    api_key=LLM_API_KEY,
    model_name=LLM_MODEL_NAME
)


# 便捷函数
async def chat_completion(messages: List[Dict[str, str]], **kwargs) -> str:
    """便捷的聊天完成函数"""
    async with LLMClient() as client:
        return await client.chat_completion(messages, **kwargs)


async def analyze_document(content: str, prompt_template: str, **kwargs) -> str:
    """便捷的文档分析函数"""
    async with LLMClient() as client:
        return await client.analyze_document(content, prompt_template, **kwargs)


async def generate_content(prompt: str, **kwargs) -> str:
    """便捷的内容生成函数"""
    async with LLMClient() as client:
        return await client.generate_content(prompt, **kwargs)