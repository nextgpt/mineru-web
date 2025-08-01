"""
MinerU文档解析服务客户端
提供文档上传、解析状态查询、结果获取功能
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time


class MinerUException(Exception):
    """MinerU服务异常"""
    pass


class MinerUClient:
    """MinerU文档解析服务客户端"""
    
    def __init__(self, api_url: str = "http://192.168.30.54:8088", timeout: int = 300):
        """
        初始化MinerU客户端
        
        Args:
            api_url: MinerU API服务地址
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
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
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def upload_document(
        self, 
        file_path: str, 
        file_bytes: bytes = None,
        parse_method: str = "auto",
        lang: str = "ch",
        formula_enable: bool = True,
        table_enable: bool = True
    ) -> Dict[str, Any]:
        """
        上传文档进行解析
        
        Args:
            file_path: 文件路径或文件名
            file_bytes: 文件字节内容（如果提供则使用此内容）
            parse_method: 解析方法 (auto, ocr, txt)
            lang: 语言设置 (ch, en)
            formula_enable: 是否启用公式识别
            table_enable: 是否启用表格识别
            
        Returns:
            Dict包含task_id和状态信息
            
        Raises:
            MinerUException: 上传失败时抛出
        """
        try:
            session = self._get_session()
            
            # 准备文件数据
            if file_bytes is None:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
            
            file_name = Path(file_path).name
            
            # 准备表单数据
            data = aiohttp.FormData()
            data.add_field('file', file_bytes, filename=file_name)
            data.add_field('parse_method', parse_method)
            data.add_field('lang', lang)
            data.add_field('formula_enable', str(formula_enable).lower())
            data.add_field('table_enable', str(table_enable).lower())
            
            # 发送请求
            url = f"{self.api_url}/api/v1/documents/parse"
            logger.info(f"Uploading document to MinerU: {url}")
            
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MinerUException(
                        f"Upload failed with status {response.status}: {error_text}"
                    )
                
                result = await response.json()
                logger.info(f"Document upload successful: {result}")
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during document upload: {e}")
            raise MinerUException(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during document upload: {e}")
            raise MinerUException(f"Upload error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def get_parse_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询解析状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict包含状态信息
            
        Raises:
            MinerUException: 查询失败时抛出
        """
        try:
            session = self._get_session()
            url = f"{self.api_url}/api/v1/documents/status/{task_id}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MinerUException(
                        f"Status query failed with status {response.status}: {error_text}"
                    )
                
                result = await response.json()
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during status query: {e}")
            raise MinerUException(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during status query: {e}")
            raise MinerUException(f"Status query error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def get_parse_result(self, task_id: str) -> Dict[str, Any]:
        """
        获取解析结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict包含解析结果
            
        Raises:
            MinerUException: 获取结果失败时抛出
        """
        try:
            session = self._get_session()
            url = f"{self.api_url}/api/v1/documents/result/{task_id}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MinerUException(
                        f"Result query failed with status {response.status}: {error_text}"
                    )
                
                result = await response.json()
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during result query: {e}")
            raise MinerUException(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during result query: {e}")
            raise MinerUException(f"Result query error: {e}")
    
    async def parse_document_async(
        self,
        file_path: str,
        file_bytes: bytes = None,
        parse_method: str = "auto",
        lang: str = "ch",
        formula_enable: bool = True,
        table_enable: bool = True,
        poll_interval: int = 5,
        max_wait_time: int = 600
    ) -> Dict[str, Any]:
        """
        异步解析文档（上传并等待完成）
        
        Args:
            file_path: 文件路径或文件名
            file_bytes: 文件字节内容
            parse_method: 解析方法
            lang: 语言设置
            formula_enable: 是否启用公式识别
            table_enable: 是否启用表格识别
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            Dict包含完整的解析结果
            
        Raises:
            MinerUException: 解析失败时抛出
        """
        # 上传文档
        upload_result = await self.upload_document(
            file_path, file_bytes, parse_method, lang, formula_enable, table_enable
        )
        
        task_id = upload_result.get('task_id')
        if not task_id:
            raise MinerUException("No task_id returned from upload")
        
        logger.info(f"Document uploaded, task_id: {task_id}, waiting for completion...")
        
        # 轮询状态直到完成
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status_result = await self.get_parse_status(task_id)
            status = status_result.get('status', 'unknown')
            
            logger.info(f"Parse status: {status}")
            
            if status == 'completed':
                # 获取解析结果
                result = await self.get_parse_result(task_id)
                logger.info("Document parsing completed successfully")
                return result
            elif status == 'failed':
                error_msg = status_result.get('error', 'Unknown error')
                raise MinerUException(f"Document parsing failed: {error_msg}")
            elif status in ['pending', 'processing']:
                # 继续等待
                await asyncio.sleep(poll_interval)
            else:
                logger.warning(f"Unknown status: {status}, continuing to wait...")
                await asyncio.sleep(poll_interval)
        
        raise MinerUException(f"Document parsing timeout after {max_wait_time} seconds")
    
    def parse_document_sync(
        self,
        file_path: str,
        file_bytes: bytes = None,
        parse_method: str = "auto",
        lang: str = "ch",
        formula_enable: bool = True,
        table_enable: bool = True,
        poll_interval: int = 5,
        max_wait_time: int = 600
    ) -> Dict[str, Any]:
        """
        同步解析文档（阻塞直到完成）
        
        Args:
            file_path: 文件路径或文件名
            file_bytes: 文件字节内容
            parse_method: 解析方法
            lang: 语言设置
            formula_enable: 是否启用公式识别
            table_enable: 是否启用表格识别
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            Dict包含完整的解析结果
            
        Raises:
            MinerUException: 解析失败时抛出
        """
        async def _parse():
            async with self:
                return await self.parse_document_async(
                    file_path, file_bytes, parse_method, lang,
                    formula_enable, table_enable, poll_interval, max_wait_time
                )
        
        # 运行异步函数
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_parse())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict包含服务状态信息
            
        Raises:
            MinerUException: 健康检查失败时抛出
        """
        try:
            session = self._get_session()
            url = f"{self.api_url}/health"
            
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}",
                        "service": "MinerU"
                    }
                
                result = await response.json()
                return {
                    "status": "healthy",
                    "service": "MinerU",
                    "details": result
                }
                
        except Exception as e:
            logger.error(f"MinerU health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "MinerU"
            }


# 创建全局客户端实例
mineru_client = MinerUClient()


# 便捷函数
async def parse_document(
    file_path: str,
    file_bytes: bytes = None,
    **kwargs
) -> Dict[str, Any]:
    """
    便捷的文档解析函数
    
    Args:
        file_path: 文件路径
        file_bytes: 文件字节内容
        **kwargs: 其他解析参数
        
    Returns:
        解析结果
    """
    async with MinerUClient() as client:
        return await client.parse_document_async(file_path, file_bytes, **kwargs)


def parse_document_sync(
    file_path: str,
    file_bytes: bytes = None,
    **kwargs
) -> Dict[str, Any]:
    """
    便捷的同步文档解析函数
    
    Args:
        file_path: 文件路径
        file_bytes: 文件字节内容
        **kwargs: 其他解析参数
        
    Returns:
        解析结果
    """
    client = MinerUClient()
    return client.parse_document_sync(file_path, file_bytes, **kwargs)