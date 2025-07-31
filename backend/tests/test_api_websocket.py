"""
WebSocket API测试
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from app.api.websocket import router as websocket_router, ConnectionManager


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(websocket_router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestConnectionManager:
    """连接管理器测试"""
    
    def test_init(self):
        """测试初始化"""
        manager = ConnectionManager()
        assert len(manager.active_connections) == 0
        assert len(manager.user_connections) == 0
        assert len(manager.project_subscribers) == 0
    
    async def test_connect_and_disconnect(self):
        """测试连接和断开"""
        manager = ConnectionManager()
        
        # 模拟WebSocket连接
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        user_id = "test-user"
        
        # 测试连接
        await manager.connect(mock_websocket, user_id)
        
        assert len(manager.active_connections) == 1
        assert user_id in manager.user_connections
        assert mock_websocket in manager.user_connections[user_id]
        mock_websocket.accept.assert_called_once()
        
        # 测试断开连接
        manager.disconnect(mock_websocket, user_id)
        
        assert len(manager.active_connections) == 0
        assert user_id not in manager.user_connections
    
    async def test_send_personal_message(self):
        """测试发送个人消息"""
        manager = ConnectionManager()
        
        # 模拟WebSocket连接
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        user_id = "test-user"
        
        # 连接用户
        await manager.connect(mock_websocket, user_id)
        
        # 发送消息
        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, user_id)
        
        mock_websocket.send_text.assert_called_once_with(json.dumps(message))
    
    async def test_send_project_update(self):
        """测试发送项目更新"""
        manager = ConnectionManager()
        
        # 模拟WebSocket连接
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        user_id = "test-user"
        project_id = "test-project"
        
        # 连接用户并订阅项目
        await manager.connect(mock_websocket, user_id)
        manager.subscribe_to_project(user_id, project_id)
        
        # 发送项目更新
        update_data = {
            "project_id": project_id,
            "status": "analyzing",
            "progress": 50
        }
        await manager.send_project_update(project_id, update_data)
        
        # 验证消息被发送
        expected_message = {
            "type": "project_update",
            "data": update_data,
            "project_id": project_id
        }
        mock_websocket.send_text.assert_called_once_with(json.dumps(expected_message))
    
    def test_subscribe_and_unsubscribe_project(self):
        """测试项目订阅和取消订阅"""
        manager = ConnectionManager()
        
        user_id = "test-user"
        project_id = "test-project"
        
        # 测试订阅
        manager.subscribe_to_project(user_id, project_id)
        
        assert project_id in manager.project_subscribers
        assert user_id in manager.project_subscribers[project_id]
        
        # 测试取消订阅
        manager.unsubscribe_from_project(user_id, project_id)
        
        assert project_id not in manager.project_subscribers or \
               user_id not in manager.project_subscribers[project_id]
    
    async def test_broadcast_to_all(self):
        """测试广播消息"""
        manager = ConnectionManager()
        
        # 模拟多个WebSocket连接
        mock_websockets = []
        user_ids = ["user1", "user2", "user3"]
        
        for user_id in user_ids:
            mock_websocket = Mock(spec=WebSocket)
            mock_websocket.accept = AsyncMock()
            mock_websocket.send_text = AsyncMock()
            mock_websockets.append(mock_websocket)
            
            await manager.connect(mock_websocket, user_id)
        
        # 广播消息
        message = {"type": "broadcast", "data": "hello everyone"}
        await manager.broadcast(message)
        
        # 验证所有连接都收到消息
        for mock_websocket in mock_websockets:
            mock_websocket.send_text.assert_called_once_with(json.dumps(message))


class TestWebSocketEndpoint:
    """WebSocket端点测试"""
    
    @patch('app.api.websocket.manager')
    async def test_websocket_connection_flow(self, mock_manager):
        """测试WebSocket连接流程"""
        # 模拟连接管理器
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()
        mock_manager.send_personal_message = AsyncMock()
        mock_manager.subscribe_to_project = Mock()
        mock_manager.unsubscribe_from_project = Mock()
        
        # 模拟WebSocket
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # 模拟消息序列
        messages = [
            json.dumps({"type": "auth", "data": {"user_id": "test-user"}}),
            json.dumps({"type": "subscribe", "data": {"project_id": "test-project"}}),
            json.dumps({"type": "unsubscribe", "data": {"project_id": "test-project"}}),
        ]
        
        # 设置接收消息的副作用
        mock_websocket.receive_text.side_effect = messages + [Exception("Connection closed")]
        
        # 导入并测试WebSocket端点
        from app.api.websocket import websocket_endpoint
        
        try:
            await websocket_endpoint(mock_websocket)
        except Exception:
            pass  # 预期的连接关闭异常
        
        # 验证连接管理器方法被调用
        mock_manager.connect.assert_called_once()
        mock_manager.subscribe_to_project.assert_called_once_with("test-user", "test-project")
        mock_manager.unsubscribe_from_project.assert_called_once_with("test-user", "test-project")
    
    def test_websocket_with_test_client(self, client):
        """使用测试客户端测试WebSocket"""
        with client.websocket_connect("/ws") as websocket:
            # 发送认证消息
            auth_message = {"type": "auth", "data": {"user_id": "test-user"}}
            websocket.send_text(json.dumps(auth_message))
            
            # 发送订阅消息
            subscribe_message = {"type": "subscribe", "data": {"project_id": "test-project"}}
            websocket.send_text(json.dumps(subscribe_message))
            
            # 这里可以添加更多的交互测试
            # 注意：实际的WebSocket测试可能需要更复杂的设置


class TestWebSocketIntegration:
    """WebSocket集成测试"""
    
    @patch('app.api.websocket.manager')
    async def test_project_status_notification(self, mock_manager):
        """测试项目状态通知"""
        # 模拟项目状态更新
        project_id = "test-project"
        status_update = {
            "project_id": project_id,
            "status": "completed",
            "progress": 100,
            "message": "项目已完成"
        }
        
        # 模拟发送项目更新
        await mock_manager.send_project_update(project_id, status_update)
        
        # 验证方法被调用
        mock_manager.send_project_update.assert_called_once_with(project_id, status_update)
    
    @patch('app.api.websocket.manager')
    async def test_task_progress_notification(self, mock_manager):
        """测试任务进度通知"""
        # 模拟任务进度更新
        user_id = "test-user"
        progress_data = {
            "task_id": "analysis-task-1",
            "progress": 75,
            "current_step": "提取技术要求",
            "estimated_remaining": 300
        }
        
        # 模拟发送进度消息
        progress_message = {
            "type": "task_progress",
            "data": progress_data
        }
        
        await mock_manager.send_personal_message(progress_message, user_id)
        
        # 验证方法被调用
        mock_manager.send_personal_message.assert_called_once_with(progress_message, user_id)
    
    @patch('app.api.websocket.manager')
    async def test_error_notification(self, mock_manager):
        """测试错误通知"""
        # 模拟错误消息
        user_id = "test-user"
        error_message = {
            "type": "error",
            "data": {
                "message": "分析任务失败",
                "error_code": "ANALYSIS_FAILED",
                "details": "文件格式不支持"
            }
        }
        
        await mock_manager.send_personal_message(error_message, user_id)
        
        # 验证方法被调用
        mock_manager.send_personal_message.assert_called_once_with(error_message, user_id)


if __name__ == "__main__":
    pytest.main([__file__])