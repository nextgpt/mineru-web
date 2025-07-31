"""
租户隔离中间件
提供请求级别的租户隔离功能
"""
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.tenant_manager import TenantManager, get_tenant_context
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """租户隔离中间件"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        # 不需要租户验证的路径
        self.exclude_paths = exclude_paths or [
            "/ping",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/file_parse"  # 保持现有API兼容性
        ]
    
    async def dispatch(self, request: Request, call_next):
        """处理请求的租户隔离逻辑"""
        
        # 检查是否为排除路径
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        try:
            # 从请求头中提取用户ID
            user_id = self._extract_user_id(request)
            if not user_id:
                raise HTTPException(
                    status_code=400, 
                    detail="Missing X-User-Id header"
                )
            
            # 生成租户ID
            tenant_id = TenantManager.get_tenant_id_from_user(user_id)
            
            # 设置租户上下文
            request.state.tenant_id = tenant_id
            request.state.user_id = user_id
            
            # 在租户上下文中处理请求
            tenant_context_manager = get_tenant_context()
            with tenant_context_manager(tenant_id):
                response = await call_next(request)
            
            # 添加租户信息到响应头（用于调试）
            response.headers["X-Tenant-Id"] = tenant_id
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"租户中间件处理错误: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error in tenant processing"
            )
    
    def _should_exclude_path(self, path: str) -> bool:
        """检查路径是否应该排除租户验证"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    def _extract_user_id(self, request: Request) -> str:
        """从请求中提取用户ID"""
        # 优先从请求头获取
        user_id = request.headers.get("X-User-Id")
        if user_id:
            return user_id
        
        # 如果没有请求头，可以从其他地方获取（如JWT token等）
        # 这里保持与现有系统的兼容性
        return None
    
    def _validate_tenant_access(self, user_id: str, resource_path: str) -> bool:
        """验证租户访问权限"""
        return TenantManager.validate_tenant_access(user_id, resource_path)


def get_current_tenant_id(request: Request) -> str:
    """从请求中获取当前租户ID"""
    return getattr(request.state, 'tenant_id', None)


def get_current_user_id(request: Request) -> str:
    """从请求中获取当前用户ID"""
    return getattr(request.state, 'user_id', None)