"""
多租户管理器
提供租户路径管理和权限验证功能
"""
import hashlib
from typing import Optional
from contextvars import ContextVar

# 租户上下文变量
tenant_context: ContextVar[Optional[str]] = ContextVar('tenant_context', default=None)


class TenantManager:
    """多租户管理器"""
    
    @staticmethod
    def get_tenant_id_from_user(user_id: str) -> str:
        """
        从用户ID生成租户ID
        这里使用简单的哈希方法，实际项目中可能需要更复杂的租户分配逻辑
        """
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        # 使用用户ID的前8位作为租户ID（简化实现）
        # 实际项目中可能需要从数据库查询用户所属租户
        tenant_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        return f"tenant_{tenant_hash}"
    
    @staticmethod
    def get_tenant_path(tenant_id: str, resource_type: str, resource_id: str = "") -> str:
        """
        生成租户专用的存储路径
        
        Args:
            tenant_id: 租户ID
            resource_type: 资源类型 (projects, files, etc.)
            resource_id: 资源ID (可选)
        
        Returns:
            租户存储路径
        """
        if not tenant_id:
            raise ValueError("租户ID不能为空")
        if not resource_type:
            raise ValueError("资源类型不能为空")
        
        base_path = f"tenants/{tenant_id}/{resource_type}"
        if resource_id:
            return f"{base_path}/{resource_id}"
        return base_path
    
    @staticmethod
    def validate_tenant_access(user_id: str, resource_path: str) -> bool:
        """
        验证用户对资源的访问权限
        
        Args:
            user_id: 用户ID
            resource_path: 资源路径
        
        Returns:
            是否有访问权限
        """
        if not user_id or not resource_path:
            return False
        
        try:
            tenant_id = TenantManager.get_tenant_id_from_user(user_id)
            expected_prefix = f"tenants/{tenant_id}/"
            return resource_path.startswith(expected_prefix)
        except Exception:
            return False
    
    @staticmethod
    def extract_tenant_from_path(resource_path: str) -> Optional[str]:
        """
        从资源路径中提取租户ID
        
        Args:
            resource_path: 资源路径
        
        Returns:
            租户ID或None
        """
        if not resource_path or not resource_path.startswith("tenants/"):
            return None
        
        parts = resource_path.split("/")
        if len(parts) >= 2:
            return parts[1]
        return None
    
    @staticmethod
    def get_current_tenant() -> Optional[str]:
        """获取当前请求的租户ID"""
        return tenant_context.get()
    
    @staticmethod
    def set_current_tenant(tenant_id: str):
        """设置当前请求的租户ID"""
        tenant_context.set(tenant_id)


def get_tenant_context():
    """获取租户上下文管理器"""
    class TenantContext:
        def __init__(self, tenant_id: str):
            self.tenant_id = tenant_id
            self.token = None
        
        def __enter__(self):
            self.token = tenant_context.set(self.tenant_id)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.token:
                tenant_context.reset(self.token)
    
    return TenantContext


def get_tenant_id(user_id: str = None) -> str:
    """
    获取租户ID的依赖函数
    
    Args:
        user_id: 用户ID（通过依赖注入获取）
    
    Returns:
        租户ID
    """
    if user_id:
        return TenantManager.get_tenant_id_from_user(user_id)
    
    # 尝试从上下文获取
    current_tenant = TenantManager.get_current_tenant()
    if current_tenant:
        return current_tenant
    
    raise ValueError("无法获取租户ID")