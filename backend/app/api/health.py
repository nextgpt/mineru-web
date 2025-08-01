"""
健康检查API端点
提供系统和外部服务的健康状态查询接口
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from loguru import logger

from app.services.health_service import health_service


router = APIRouter()


@router.get("/health", summary="系统健康检查", description="检查所有外部服务的健康状态")
async def get_system_health() -> Dict[str, Any]:
    """
    获取系统整体健康状态
    
    Returns:
        包含所有服务健康状态的详细信息
    """
    try:
        result = await health_service.check_all_services()
        logger.info(f"System health check completed: {result['overall_status']}")
        return result
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/health/summary", summary="健康状态摘要", description="获取系统健康状态的简要摘要")
async def get_health_summary() -> Dict[str, Any]:
    """
    获取健康状态摘要
    
    Returns:
        健康状态的简要摘要信息
    """
    try:
        health_result = await health_service.check_all_services()
        summary = health_service.get_service_status_summary(health_result)
        logger.info(f"Health summary: {summary['healthy_services']}/{summary['total_services']} services healthy")
        return summary
    except Exception as e:
        logger.error(f"Health summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health summary failed: {str(e)}")


@router.get("/health/{service_name}", summary="单个服务健康检查", description="检查指定服务的健康状态")
async def get_service_health(service_name: str) -> Dict[str, Any]:
    """
    获取单个服务的健康状态
    
    Args:
        service_name: 服务名称 (mineru, llm, redis, postgres, minio)
        
    Returns:
        指定服务的健康状态信息
    """
    try:
        result = await health_service.check_service(service_name)
        logger.info(f"Service {service_name} health check: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Service {service_name} health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service health check failed: {str(e)}")


@router.get("/health/services/list", summary="获取服务列表", description="获取所有可监控的服务列表")
async def get_services_list() -> Dict[str, Any]:
    """
    获取所有可监控的服务列表
    
    Returns:
        服务列表和描述信息
    """
    services_info = {
        "mineru": {
            "name": "MinerU文档解析服务",
            "description": "负责PDF文档解析和内容提取",
            "endpoint": "/health/mineru"
        },
        "llm": {
            "name": "大模型API服务",
            "description": "负责AI分析和内容生成",
            "endpoint": "/health/llm"
        },
        "redis": {
            "name": "Redis缓存服务",
            "description": "负责缓存和会话管理",
            "endpoint": "/health/redis"
        },
        "postgres": {
            "name": "PostgreSQL数据库",
            "description": "负责数据持久化存储",
            "endpoint": "/health/postgres"
        },
        "minio": {
            "name": "MinIO对象存储",
            "description": "负责文件存储管理",
            "endpoint": "/health/minio"
        }
    }
    
    return {
        "services": services_info,
        "total_services": len(services_info)
    }


@router.post("/health/check", summary="手动触发健康检查", description="手动触发所有服务的健康检查")
async def trigger_health_check(
    services: Optional[str] = Query(None, description="指定要检查的服务，多个服务用逗号分隔，不指定则检查所有服务")
) -> Dict[str, Any]:
    """
    手动触发健康检查
    
    Args:
        services: 可选，指定要检查的服务列表
        
    Returns:
        健康检查结果
    """
    try:
        if services:
            # 检查指定的服务
            service_list = [s.strip() for s in services.split(",")]
            results = {}
            
            for service_name in service_list:
                result = await health_service.check_service(service_name)
                results[service_name] = result
            
            # 计算整体状态
            overall_status = "healthy"
            for result in results.values():
                if result.get("status") != "healthy":
                    overall_status = "unhealthy"
                    break
            
            return {
                "overall_status": overall_status,
                "services": results,
                "requested_services": service_list
            }
        else:
            # 检查所有服务
            result = await health_service.check_all_services()
            return result
            
    except Exception as e:
        logger.error(f"Manual health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Manual health check failed: {str(e)}")


# 兼容性端点 - 简单的ping检查
@router.get("/ping", summary="简单ping检查", description="简单的服务可用性检查")
async def ping() -> Dict[str, str]:
    """
    简单的ping检查
    
    Returns:
        简单的pong响应
    """
    return {"status": "ok", "message": "pong"}


# 就绪检查端点
@router.get("/ready", summary="就绪检查", description="检查服务是否准备好接收请求")
async def readiness_check() -> Dict[str, Any]:
    """
    就绪检查 - 检查关键服务是否可用
    
    Returns:
        就绪状态信息
    """
    try:
        # 检查关键服务：数据库和Redis
        critical_services = ["postgres", "redis"]
        results = {}
        
        for service_name in critical_services:
            result = await health_service.check_service(service_name)
            results[service_name] = result
        
        # 判断是否就绪
        ready = all(result.get("status") == "healthy" for result in results.values())
        
        return {
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "critical_services": results
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "status": "not_ready",
            "error": str(e)
        }


# 存活检查端点
@router.get("/live", summary="存活检查", description="检查服务是否存活")
async def liveness_check() -> Dict[str, str]:
    """
    存活检查 - 简单检查服务是否运行
    
    Returns:
        存活状态信息
    """
    return {
        "status": "alive",
        "message": "Service is running"
    }