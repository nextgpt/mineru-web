"""
AI客户端服务测试
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.ai_client import (
    AIClient, 
    MockAIModel, 
    OpenAIModel,
    AIRequest, 
    AIResponse, 
    AIModelType, 
    AIServiceError,
    PromptTemplates,
    get_ai_client
)


class TestMockAIModel:
    """MockAIModel测试类"""
    
    def test_init(self):
        """测试初始化"""
        model = MockAIModel()
        assert model.available is True
        assert isinstance(model.response_templates, dict)
        assert "project_info" in model.response_templates
    
    def test_is_available(self):
        """测试可用性检查"""
        model = MockAIModel()
        assert model.is_available() is True
        
        model.available = False
        assert model.is_available() is False
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """测试成功生成响应"""
        model = MockAIModel()
        request = AIRequest(
            prompt="请提取项目基本信息",
            model_type=AIModelType.MOCK
        )
        
        response = await model.generate(request)
        
        assert isinstance(response, AIResponse)
        assert response.success is True
        assert response.model_type == AIModelType.MOCK
        assert response.content != ""
        assert response.tokens_used > 0
        assert response.response_time > 0
        assert response.metadata["mock"] is True
    
    @pytest.mark.asyncio
    async def test_generate_project_info(self):
        """测试生成项目信息"""
        model = MockAIModel()
        request = AIRequest(prompt="请提取项目基本信息")
        
        response = await model.generate(request)
        content_data = json.loads(response.content)
        
        assert "project_name" in content_data
        assert "budget" in content_data
        assert "duration" in content_data
    
    @pytest.mark.asyncio
    async def test_generate_technical_requirements(self):
        """测试生成技术要求"""
        model = MockAIModel()
        request = AIRequest(prompt="请提取技术要求")
        
        response = await model.generate(request)
        content_data = json.loads(response.content)
        
        assert "functional_requirements" in content_data
        assert "performance_requirements" in content_data
        assert isinstance(content_data["functional_requirements"], list)
    
    @pytest.mark.asyncio
    async def test_generate_evaluation_criteria(self):
        """测试生成评分标准"""
        model = MockAIModel()
        request = AIRequest(prompt="请提取评分标准")
        
        response = await model.generate(request)
        content_data = json.loads(response.content)
        
        assert "technical_score" in content_data
        assert "commercial_score" in content_data
        assert "evaluation_method" in content_data
    
    @pytest.mark.asyncio
    async def test_generate_submission_requirements(self):
        """测试生成提交要求"""
        model = MockAIModel()
        request = AIRequest(prompt="请提取提交要求")
        
        response = await model.generate(request)
        content_data = json.loads(response.content)
        
        assert "document_format" in content_data
        assert "submission_method" in content_data
        assert "required_documents" in content_data
    
    def test_generate_mock_content_unknown_type(self):
        """测试未知类型的内容生成"""
        model = MockAIModel()
        content = model._generate_mock_content("unknown prompt")
        
        # 应该返回默认的项目信息
        content_data = json.loads(content)
        assert "project_name" in content_data


class TestOpenAIModel:
    """OpenAIModel测试类"""
    
    def test_init(self):
        """测试初始化"""
        model = OpenAIModel("test-api-key", "gpt-4")
        assert model.api_key == "test-api-key"
        assert model.model_name == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_generate_not_implemented(self):
        """测试未实现的生成方法"""
        model = OpenAIModel("test-api-key")
        request = AIRequest(prompt="test")
        
        with pytest.raises(NotImplementedError):
            await model.generate(request)
    
    def test_is_available_not_implemented(self):
        """测试未实现的可用性检查"""
        model = OpenAIModel("test-api-key")
        assert model.is_available() is False


class TestAIClient:
    """AIClient测试类"""
    
    def test_init(self):
        """测试初始化"""
        client = AIClient()
        assert isinstance(client.models, dict)
        assert AIModelType.MOCK in client.models
        assert isinstance(client.fallback_chain, list)
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """测试成功生成"""
        client = AIClient()
        
        response = await client.generate("请提取项目信息")
        
        assert isinstance(response, AIResponse)
        assert response.success is True
        assert response.content != ""
    
    @pytest.mark.asyncio
    async def test_generate_with_preferred_model(self):
        """测试使用首选模型生成"""
        client = AIClient()
        
        response = await client.generate(
            "请提取项目信息", 
            preferred_model=AIModelType.MOCK
        )
        
        assert response.model_type == AIModelType.MOCK
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_generate_with_parameters(self):
        """测试带参数生成"""
        client = AIClient()
        
        response = await client.generate(
            "请提取项目信息",
            max_tokens=1000,
            temperature=0.5,
            timeout=60
        )
        
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_generate_fallback(self):
        """测试降级机制"""
        client = AIClient()
        
        # 完全移除Mock模型，模拟主要模型不可用
        del client.models[AIModelType.MOCK]
        
        # 添加一个可用的模型
        available_model = MockAIModel()
        client.add_model(AIModelType.LOCAL_LLM, available_model)
        
        response = await client.generate("test prompt")
        
        assert response.success is True
        assert response.model_type == AIModelType.LOCAL_LLM
    
    @pytest.mark.asyncio
    async def test_generate_all_models_unavailable(self):
        """测试所有模型都不可用"""
        client = AIClient()
        
        # 使所有模型不可用
        for model in client.models.values():
            model.available = False
        
        with pytest.raises(AIServiceError, match="所有AI模型都不可用"):
            await client.generate("test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_with_retry(self):
        """测试重试机制"""
        client = AIClient()
        
        # 模拟第一次调用失败，第二次成功
        mock_model = client.models[AIModelType.MOCK]
        original_generate = mock_model.generate
        
        call_count = 0
        async def mock_generate_with_failure(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return AIResponse(
                    content="",
                    model_type=AIModelType.MOCK,
                    success=False,
                    error_message="临时错误"
                )
            return await original_generate(request)
        
        mock_model.generate = mock_generate_with_failure
        
        response = await client.generate("test prompt", retry_count=2)
        
        assert response.success is True
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_timeout(self):
        """测试超时处理"""
        client = AIClient()
        
        # 模拟超时
        mock_model = client.models[AIModelType.MOCK]
        async def slow_generate(request):
            await asyncio.sleep(2)  # 超过timeout时间
            return AIResponse(content="test", model_type=AIModelType.MOCK)
        
        mock_model.generate = slow_generate
        
        with pytest.raises(AIServiceError):
            await client.generate("test prompt", timeout=1)
    
    @pytest.mark.asyncio
    async def test_generate_structured_success(self):
        """测试结构化生成成功"""
        client = AIClient()
        
        result = await client.generate_structured("请提取项目信息")
        
        assert isinstance(result, dict)
        assert "project_name" in result
    
    @pytest.mark.asyncio
    async def test_generate_structured_with_validation(self):
        """测试带验证的结构化生成"""
        client = AIClient()
        
        def validate_project_info(data):
            return isinstance(data, dict) and "project_name" in data
        
        result = await client.generate_structured(
            "请提取项目信息",
            validation_func=validate_project_info
        )
        
        assert isinstance(result, dict)
        assert "project_name" in result
    
    @pytest.mark.asyncio
    async def test_generate_structured_validation_failure(self):
        """测试验证失败"""
        client = AIClient()
        
        def strict_validation(data):
            return False  # 总是失败
        
        with pytest.raises(AIServiceError, match="数据验证失败"):
            await client.generate_structured(
                "请提取项目信息",
                validation_func=strict_validation
            )
    
    @pytest.mark.asyncio
    async def test_generate_structured_json_error(self):
        """测试JSON解析错误"""
        client = AIClient()
        
        # 模拟返回无效JSON
        mock_model = client.models[AIModelType.MOCK]
        async def invalid_json_generate(request):
            return AIResponse(
                content="invalid json content",
                model_type=AIModelType.MOCK,
                success=True
            )
        
        mock_model.generate = invalid_json_generate
        
        with pytest.raises(AIServiceError, match="AI响应格式错误"):
            await client.generate_structured("test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_structured_ai_failure(self):
        """测试AI生成失败"""
        client = AIClient()
        
        # 模拟AI生成失败
        mock_model = client.models[AIModelType.MOCK]
        async def failed_generate(request):
            return AIResponse(
                content="",
                model_type=AIModelType.MOCK,
                success=False,
                error_message="AI生成失败"
            )
        
        mock_model.generate = failed_generate
        
        with pytest.raises(AIServiceError, match="AI生成失败"):
            await client.generate_structured("test prompt")
    
    def test_add_model(self):
        """测试添加模型"""
        client = AIClient()
        new_model = MockAIModel()
        
        client.add_model(AIModelType.CLAUDE, new_model)
        
        assert AIModelType.CLAUDE in client.models
        assert client.models[AIModelType.CLAUDE] == new_model
    
    def test_remove_model(self):
        """测试移除模型"""
        client = AIClient()
        
        client.remove_model(AIModelType.MOCK)
        
        assert AIModelType.MOCK not in client.models
    
    def test_get_available_models(self):
        """测试获取可用模型列表"""
        client = AIClient()
        
        available_models = client.get_available_models()
        
        assert isinstance(available_models, list)
        assert AIModelType.MOCK in available_models
        
        # 使Mock模型不可用
        client.models[AIModelType.MOCK].available = False
        available_models = client.get_available_models()
        assert AIModelType.MOCK not in available_models


class TestPromptTemplates:
    """PromptTemplates测试类"""
    
    def test_format_project_info_prompt(self):
        """测试格式化项目信息提示词"""
        content = "这是一个测试招标文件内容"
        prompt = PromptTemplates.format_project_info_prompt(content)
        
        assert isinstance(prompt, str)
        assert "项目基本信息" in prompt
        assert "project_name" in prompt
        assert content in prompt
    
    def test_format_technical_requirements_prompt(self):
        """测试格式化技术要求提示词"""
        content = "这是技术要求内容"
        prompt = PromptTemplates.format_technical_requirements_prompt(content)
        
        assert isinstance(prompt, str)
        assert "技术要求" in prompt
        assert "functional_requirements" in prompt
        assert content in prompt
    
    def test_format_evaluation_criteria_prompt(self):
        """测试格式化评分标准提示词"""
        content = "这是评分标准内容"
        prompt = PromptTemplates.format_evaluation_criteria_prompt(content)
        
        assert isinstance(prompt, str)
        assert "评分标准" in prompt
        assert "technical_score" in prompt
        assert content in prompt
    
    def test_format_submission_requirements_prompt(self):
        """测试格式化提交要求提示词"""
        content = "这是提交要求内容"
        prompt = PromptTemplates.format_submission_requirements_prompt(content)
        
        assert isinstance(prompt, str)
        assert "提交要求" in prompt
        assert "document_format" in prompt
        assert content in prompt
    
    def test_content_truncation(self):
        """测试内容截断"""
        long_content = "x" * 5000  # 超过4000字符
        prompt = PromptTemplates.format_project_info_prompt(long_content)
        
        # 内容应该被截断到4000字符
        content_in_prompt = prompt.split("招标文件内容：\n")[1].split("\n\n请返回标准的JSON格式")[0]
        assert len(content_in_prompt) <= 4000


class TestGlobalFunctions:
    """全局函数测试"""
    
    def test_get_ai_client_singleton(self):
        """测试AI客户端单例"""
        client1 = get_ai_client()
        client2 = get_ai_client()
        
        assert client1 is client2
        assert isinstance(client1, AIClient)
    
    @patch('app.services.ai_client._ai_client', None)
    def test_get_ai_client_initialization(self):
        """测试AI客户端初始化"""
        client = get_ai_client()
        
        assert isinstance(client, AIClient)
        assert AIModelType.MOCK in client.models


class TestAIRequest:
    """AIRequest测试类"""
    
    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        request = AIRequest(prompt="test prompt")
        
        assert request.prompt == "test prompt"
        assert request.model_type == AIModelType.MOCK
        assert request.max_tokens == 2000
        assert request.temperature == 0.7
        assert request.timeout == 30
        assert request.retry_count == 3
        assert request.metadata is None
    
    def test_init_with_custom_values(self):
        """测试使用自定义值初始化"""
        metadata = {"key": "value"}
        request = AIRequest(
            prompt="custom prompt",
            model_type=AIModelType.OPENAI_GPT4,
            max_tokens=1500,
            temperature=0.5,
            timeout=60,
            retry_count=5,
            metadata=metadata
        )
        
        assert request.prompt == "custom prompt"
        assert request.model_type == AIModelType.OPENAI_GPT4
        assert request.max_tokens == 1500
        assert request.temperature == 0.5
        assert request.timeout == 60
        assert request.retry_count == 5
        assert request.metadata == metadata


class TestAIResponse:
    """AIResponse测试类"""
    
    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        response = AIResponse(
            content="test content",
            model_type=AIModelType.MOCK
        )
        
        assert response.content == "test content"
        assert response.model_type == AIModelType.MOCK
        assert response.tokens_used == 0
        assert response.response_time == 0.0
        assert response.success is True
        assert response.error_message is None
        assert response.metadata is None
    
    def test_init_with_custom_values(self):
        """测试使用自定义值初始化"""
        metadata = {"timestamp": "2024-01-01"}
        response = AIResponse(
            content="custom content",
            model_type=AIModelType.OPENAI_GPT4,
            tokens_used=150,
            response_time=2.5,
            success=False,
            error_message="Test error",
            metadata=metadata
        )
        
        assert response.content == "custom content"
        assert response.model_type == AIModelType.OPENAI_GPT4
        assert response.tokens_used == 150
        assert response.response_time == 2.5
        assert response.success is False
        assert response.error_message == "Test error"
        assert response.metadata == metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])