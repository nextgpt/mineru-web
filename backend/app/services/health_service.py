"""
外部服务健康检查服务
提供服务可用性检测和连接状态监控
"""
import asyncio
import aiohttp
import aioredis
import psycopg2
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime
import os

from app.services.mineru_client import MinerUClient
from app.services.llm_client import LLMClient
from app.utils.minio_client import minio_client


class HealthService:
    """健康检查服务"""
    
    def __init__(self):
        self.services = {
            "mineru": self._check_mineru_health,
            "llm": self._check_llm_health,
            "redis": self._check_redis_health,
            "postgres": self._check_postgres_health,
            "minio": self._check_minio_health
        }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """
        检查所有外部服务的健康状态
        
        Returns:
            Dict包含所有服务的健康状态
        """
        results = {}
        overall_status = "healthy"
        
        # 并发检查所有服务
        tasks = []
        for service_name, check_func in self.services.items():
            task = asyncio.create_task(self._safe_check(service_name, check_func))
            tasks.append(task)
        
        # 等待所有检查完成
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, (service_name, _) in enumerate(self.services.items()):
            result = check_results[i]
            if isinstance(result, Exception):
                results[service_name] = {
                    "status": "unhealthy",
                    "error": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_status = "unhealthy"
            else:
                results[service_name] = result
                if result.get("status") != "healthy":
                    overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "services": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_service(self, service_name: str) -> Dict[str, Any]:
        """
        检查单个服务的健康状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict包含服务健康状态
        """
        if service_name not in self.services:
            return {
                "status": "unknown",
                "error": f"Unknown service: {service_name}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        check_func = self.services[service_name]
        return await self._safe_check(service_name, check_func)
    
    async def _safe_check(self, service_name: str, check_func) -> Dict[str, Any]:
        """
        安全地执行健康检查
        
        Args:
            service_name: 服务名称
            check_func: 检查函数
            
        Returns:
            检查结果
        """
        try:
            result = await check_func()
            result["timestamp"] = datetime.utcnow().isoformat()
            return result
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": service_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_mineru_health(self) -> Dict[str, Any]:
        """检查MinerU服务健康状态"""
        try:
            mineru_api_url = os.getenv("MINERU_API_URL", "http://192.168.30.54:8088")
            client = MinerUClient(api_url=mineru_api_url)
            
            async with client:
                result = await client.health_check()
                return result
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "MinerU"
            }
    
    async def _check_llm_health(self) -> Dict[str, Any]:
        """检查大模型服务健康状态"""
        try:
            llm_api_url = os.getenv("LLM_API_URL", "http://192.168.30.54:3000/v1")
            llm_api_key = os.getenv("LLM_API_KEY", "token-abc123")
            llm_model_name = os.getenv("LLM_MODEL_NAME", "Qwen3-30B-A3B-FP8")
            
            client = LLMClient(
                api_url=llm_api_url,
                api_key=llm_api_key,
                model_name=llm_model_name
            )
            
            async with client:
                result = await client.health_check()
                return result
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "LLM"
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """检查Redis服务健康状态"""
        try:
            redis_host = os.getenv("REDIS_HOST", "redis")
            redis_port = int(os.getenv("REDIS_PORT", "16379"))
            
            # 创建Redis连接
            redis = aioredis.from_url(
                f"redis://{redis_host}:{redis_port}",
                decode_responses=True
            )
            
            # 执行ping命令
            pong = await redis.ping()
            await redis.close()
            
            if pong:
                return {
                    "status": "healthy",
                    "service": "Redis",
                    "host": redis_host,
                    "port": redis_port
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Ping failed",
                    "service": "Redis"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "Redis"
            }
    
    async def _check_postgres_health(self) -> Dict[str, Any]:
        """检查PostgreSQL服务健康状态"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return {
                    "status": "unhealthy",
                    "error": "DATABASE_URL not configured",
                    "service": "PostgreSQL"
                }
            
            # 解析数据库URL
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            
            # 创建连接（同步方式，因为psycopg2不支持异步）
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # 去掉开头的 /
                user=parsed.username,
                password=parsed.password
            )
            
            # 执行简单查询
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result and result[0] == 1:
                return {
                    "status": "healthy",
                    "service": "PostgreSQL",
                    "host": parsed.hostname,
                    "port": parsed.port or 5432,
                    "database": parsed.path[1:]
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Query failed",
                    "service": "PostgreSQL"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "PostgreSQL"
            }
    
    async def _check_minio_health(self) -> Dict[str, Any]:
        """检查MinIO服务健康状态"""
        try:
            # 尝试列出存储桶
            buckets = minio_client.list_buckets()
            
            return {
                "status": "healthy",
                "service": "MinIO",
                "buckets_count": len(buckets),
                "endpoint": minio_client._base_url
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "MinIO"
            }
    
    def get_service_status_summary(self, health_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取服务状态摘要
        
        Args:
            health_result: 健康检查结果
            
        Returns:
            状态摘要
        """
        services = health_result.get("services", {})
        
        healthy_count = sum(1 for service in services.values() if service.get("status") == "healthy")
        total_count = len(services)
        unhealthy_services = [
            name for name, service in services.items() 
            if service.get("status") != "healthy"
        ]
        
        return {
            "overall_status": health_result.get("overall_status"),
            "healthy_services": healthy_count,
            "total_services": total_count,
            "unhealthy_services": unhealthy_services,
            "timestamp": health_result.get("timestamp")
        }


# 创建全局健康检查服务实例
health_service = HealthService()


# 便捷函数
async def check_all_services() -> Dict[str, Any]:
    """检查所有服务健康状态的便捷函数"""
    return await health_service.check_all_services()


async def check_service(service_name: str) -> Dict[str, Any]:
    """检查单个服务健康状态的便捷函数"""
    return await health_service.check_service(service_name)