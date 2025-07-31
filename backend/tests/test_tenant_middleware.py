"""
租户中间件单元测试
"""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.tenant_middleware import TenantMiddleware, get_current_tenant_id, get_current_user_id


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    
    # 添加租户中间件
    app.add_middleware(TenantMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {
            "tenant_id": get_current_tenant_id(request),
            "user_id": get_current_user_id(request)
        }
    
    @app.get("/ping")
    async def ping():
        return {"msg": "pong"}
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestTenantMiddleware:
    """租户中间件测试类"""
    
    def test_middleware_with_user_id(self, client):
        """测试带用户ID的请求"""
        response = client.get("/test", headers={"X-User-Id": "user123"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tenant_id" in data
        assert data["tenant_id"].startswith("tenant_")
        assert data["user_id"] == "user123"
        
        # 检查响应头中的租户信息
        assert "X-Tenant-Id" in response.headers
        assert response.headers["X-Tenant-Id"] == data["tenant_id"]
    
    def test_middleware_without_user_id(self, client):
        """测试没有用户ID的请求"""
        with pytest.raises(Exception):  # HTTPException will be raised
            response = client.get("/test")
    
    def test_middleware_exclude_paths(self, client):
        """测试排除路径不需要租户验证"""
        # ping路径应该被排除
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"msg": "pong"}
        
        # 不应该有租户相关的响应头
        assert "X-Tenant-Id" not in response.headers
    
    def test_consistent_tenant_id(self, client):
        """测试相同用户ID生成一致的租户ID"""
        user_id = "user123"
        
        # 第一次请求
        response1 = client.get("/test", headers={"X-User-Id": user_id})
        tenant_id1 = response1.json()["tenant_id"]
        
        # 第二次请求
        response2 = client.get("/test", headers={"X-User-Id": user_id})
        tenant_id2 = response2.json()["tenant_id"]
        
        # 应该生成相同的租户ID
        assert tenant_id1 == tenant_id2
    
    def test_different_users_different_tenants(self, client):
        """测试不同用户生成不同的租户ID"""
        # 用户1
        response1 = client.get("/test", headers={"X-User-Id": "user123"})
        tenant_id1 = response1.json()["tenant_id"]
        
        # 用户2
        response2 = client.get("/test", headers={"X-User-Id": "user456"})
        tenant_id2 = response2.json()["tenant_id"]
        
        # 应该生成不同的租户ID
        assert tenant_id1 != tenant_id2


class TestTenantMiddlewareCustomExcludes:
    """测试自定义排除路径的租户中间件"""
    
    def test_custom_exclude_paths(self):
        """测试自定义排除路径"""
        app = FastAPI()
        
        # 添加带自定义排除路径的中间件
        app.add_middleware(TenantMiddleware, exclude_paths=["/ping", "/health", "/custom"])
        
        @app.get("/custom")
        async def custom_endpoint():
            return {"msg": "custom"}
        
        @app.get("/protected")
        async def protected_endpoint(request: Request):
            return {"tenant_id": get_current_tenant_id(request)}
        
        client = TestClient(app)
        
        # 自定义排除路径应该可以访问
        response = client.get("/custom")
        assert response.status_code == 200
        assert response.json() == {"msg": "custom"}
        
        # 受保护的路径需要用户ID
        with pytest.raises(Exception):  # HTTPException will be raised
            response = client.get("/protected")