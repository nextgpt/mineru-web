"""
多租户管理器单元测试
"""
import pytest
from app.utils.tenant_manager import TenantManager, get_tenant_context, tenant_context


class TestTenantManager:
    """TenantManager测试类"""
    
    def test_get_tenant_id_from_user(self):
        """测试从用户ID生成租户ID"""
        user_id = "user123"
        tenant_id = TenantManager.get_tenant_id_from_user(user_id)
        
        assert tenant_id.startswith("tenant_")
        assert len(tenant_id) == 15  # "tenant_" + 8位哈希
        
        # 相同用户ID应该生成相同的租户ID
        tenant_id2 = TenantManager.get_tenant_id_from_user(user_id)
        assert tenant_id == tenant_id2
        
        # 不同用户ID应该生成不同的租户ID
        different_tenant_id = TenantManager.get_tenant_id_from_user("user456")
        assert tenant_id != different_tenant_id
    
    def test_get_tenant_id_from_user_empty(self):
        """测试空用户ID的处理"""
        with pytest.raises(ValueError, match="用户ID不能为空"):
            TenantManager.get_tenant_id_from_user("")
        
        with pytest.raises(ValueError, match="用户ID不能为空"):
            TenantManager.get_tenant_id_from_user(None)
    
    def test_get_tenant_path(self):
        """测试租户路径生成"""
        tenant_id = "tenant_12345678"
        
        # 测试基础路径
        path = TenantManager.get_tenant_path(tenant_id, "projects")
        assert path == "tenants/tenant_12345678/projects"
        
        # 测试带资源ID的路径
        path_with_id = TenantManager.get_tenant_path(tenant_id, "projects", "proj123")
        assert path_with_id == "tenants/tenant_12345678/projects/proj123"
    
    def test_get_tenant_path_validation(self):
        """测试租户路径生成的参数验证"""
        with pytest.raises(ValueError, match="租户ID不能为空"):
            TenantManager.get_tenant_path("", "projects")
        
        with pytest.raises(ValueError, match="资源类型不能为空"):
            TenantManager.get_tenant_path("tenant_123", "")
    
    def test_validate_tenant_access(self):
        """测试租户访问权限验证"""
        user_id = "user123"
        tenant_id = TenantManager.get_tenant_id_from_user(user_id)
        
        # 有效的访问
        valid_path = f"tenants/{tenant_id}/projects/proj123"
        assert TenantManager.validate_tenant_access(user_id, valid_path) is True
        
        # 无效的访问（不同租户）
        invalid_path = "tenants/other_tenant/projects/proj123"
        assert TenantManager.validate_tenant_access(user_id, invalid_path) is False
        
        # 无效的路径格式
        invalid_format = "invalid/path/format"
        assert TenantManager.validate_tenant_access(user_id, invalid_format) is False
        
        # 空参数
        assert TenantManager.validate_tenant_access("", valid_path) is False
        assert TenantManager.validate_tenant_access(user_id, "") is False
    
    def test_extract_tenant_from_path(self):
        """测试从路径中提取租户ID"""
        # 有效路径
        path = "tenants/tenant_12345678/projects/proj123"
        tenant_id = TenantManager.extract_tenant_from_path(path)
        assert tenant_id == "tenant_12345678"
        
        # 无效路径
        invalid_path = "invalid/path/format"
        assert TenantManager.extract_tenant_from_path(invalid_path) is None
        
        # 空路径
        assert TenantManager.extract_tenant_from_path("") is None
        assert TenantManager.extract_tenant_from_path(None) is None
    
    def test_tenant_context(self):
        """测试租户上下文管理"""
        tenant_id = "tenant_12345678"
        
        # 初始状态应该为None
        assert TenantManager.get_current_tenant() is None
        
        # 使用上下文管理器
        tenant_context_manager = get_tenant_context()
        with tenant_context_manager(tenant_id):
            assert TenantManager.get_current_tenant() == tenant_id
        
        # 退出上下文后应该恢复
        assert TenantManager.get_current_tenant() is None
    
    def test_set_current_tenant(self):
        """测试设置当前租户"""
        tenant_id = "tenant_12345678"
        
        # 设置租户
        TenantManager.set_current_tenant(tenant_id)
        assert TenantManager.get_current_tenant() == tenant_id
        
        # 清理
        tenant_context.set(None)