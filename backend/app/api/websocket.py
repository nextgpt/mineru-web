"""
WebSocket API for real-time updates
支持任务进度推送、状态更新等实时通信
"""
import json
import logging
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from app.services.task_manager import get_task_manager
from app.utils.user_dep import get_user_id_from_websocket
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 存储用户订阅的任务: {user_id: {task_id}}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # 存储任务订阅者: {task_id: {user_id}}
        self.task_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """建立WebSocket连接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][connection_id] = websocket
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        logger.info(f"WebSocket连接建立: 用户={user_id}, 连接ID={connection_id}")
    
    def disconnect(self, user_id: str, connection_id: str):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
            
            # 如果用户没有其他连接，清理订阅
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # 清理任务订阅
                if user_id in self.user_subscriptions:
                    for task_id in self.user_subscriptions[user_id]:
                        if task_id in self.task_subscribers:
                            self.task_subscribers[task_id].discard(user_id)
                            if not self.task_subscribers[task_id]:
                                del self.task_subscribers[task_id]
                    del self.user_subscriptions[user_id]
        
        logger.info(f"WebSocket连接断开: 用户={user_id}, 连接ID={connection_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """发送个人消息"""
        if user_id in self.active_connections:
            message_str = json.dumps(message, ensure_ascii=False)
            
            # 向用户的所有连接发送消息
            disconnected_connections = []
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(message_str)
                    else:
                        disconnected_connections.append(connection_id)
                except Exception as e:
                    logger.error(f"发送消息失败: 用户={user_id}, 连接ID={connection_id}, 错误={str(e)}")
                    disconnected_connections.append(connection_id)
            
            # 清理断开的连接
            for connection_id in disconnected_connections:
                self.disconnect(user_id, connection_id)
    
    async def send_task_update(self, task_id: str, message: dict):
        """发送任务更新消息给所有订阅者"""
        if task_id in self.task_subscribers:
            for user_id in self.task_subscribers[task_id].copy():
                await self.send_personal_message(message, user_id)
    
    def subscribe_task(self, user_id: str, task_id: str):
        """订阅任务更新"""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(task_id)
        
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        
        self.task_subscribers[task_id].add(user_id)
        
        logger.info(f"用户订阅任务: 用户={user_id}, 任务={task_id}")
    
    def unsubscribe_task(self, user_id: str, task_id: str):
        """取消订阅任务更新"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(task_id)
        
        if task_id in self.task_subscribers:
            self.task_subscribers[task_id].discard(user_id)
            if not self.task_subscribers[task_id]:
                del self.task_subscribers[task_id]
        
        logger.info(f"用户取消订阅任务: 用户={user_id}, 任务={task_id}")
    
    def get_connection_count(self) -> int:
        """获取活跃连接数"""
        total = 0
        for user_connections in self.active_connections.values():
            total += len(user_connections)
        return total


# 全局连接管理器
manager = ConnectionManager()


class ProgressListener:
    """进度监听器"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self.redis_client = redis_client
        self.listening = False
        self.listener_task = None
    
    async def start_listening(self):
        """开始监听Redis进度更新"""
        if self.listening:
            return
        
        self.listening = True
        self.listener_task = asyncio.create_task(self._listen_progress_updates())
        logger.info("开始监听任务进度更新")
    
    async def stop_listening(self):
        """停止监听"""
        self.listening = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("停止监听任务进度更新")
    
    async def _listen_progress_updates(self):
        """监听Redis进度更新频道"""
        try:
            if not self.redis_client.client:
                logger.warning("Redis客户端未连接，无法监听进度更新")
                return
            
            # 订阅进度更新频道
            pubsub = self.redis_client.client.pubsub()
            await pubsub.psubscribe("task_progress:*")
            
            while self.listening:
                try:
                    message = await pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'pmessage':
                        await self._handle_progress_message(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"处理进度消息时发生错误: {str(e)}")
                    await asyncio.sleep(1)
            
            await pubsub.punsubscribe("task_progress:*")
            await pubsub.close()
            
        except Exception as e:
            logger.error(f"监听进度更新时发生错误: {str(e)}")
    
    async def _handle_progress_message(self, message):
        """处理进度更新消息"""
        try:
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'].decode('utf-8'))
            
            # 提取任务ID
            task_id = channel.split(':', 1)[1]
            
            # 构建WebSocket消息
            ws_message = {
                "type": "task_progress",
                "task_id": task_id,
                "progress": data.get("progress", 0),
                "message": data.get("message", ""),
                "timestamp": data.get("timestamp", "")
            }
            
            # 发送给订阅者
            await self.manager.send_task_update(task_id, ws_message)
            
        except Exception as e:
            logger.error(f"处理进度消息失败: {str(e)}")


# 全局进度监听器
progress_listener = ProgressListener(manager)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket连接端点"""
    connection_id = f"{user_id}_{id(websocket)}"
    
    try:
        await manager.connect(websocket, user_id, connection_id)
        
        # 启动进度监听器（如果还没启动）
        if not progress_listener.listening:
            await progress_listener.start_listening()
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "user_id": user_id,
            "connection_id": connection_id,
            "message": "WebSocket连接建立成功"
        }, ensure_ascii=False))
        
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_websocket_message(websocket, user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id, connection_id)
        logger.info(f"WebSocket连接断开: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {user_id}, 错误: {str(e)}")
        manager.disconnect(user_id, connection_id)


async def handle_websocket_message(websocket: WebSocket, user_id: str, message: dict):
    """处理WebSocket消息"""
    try:
        message_type = message.get("type")
        
        if message_type == "subscribe_task":
            # 订阅任务更新
            task_id = message.get("task_id")
            if task_id:
                manager.subscribe_task(user_id, task_id)
                
                # 发送订阅确认
                await websocket.send_text(json.dumps({
                    "type": "subscription",
                    "status": "subscribed",
                    "task_id": task_id,
                    "message": f"已订阅任务 {task_id} 的更新"
                }, ensure_ascii=False))
                
                # 发送当前任务状态
                task_manager = get_task_manager()
                task_info = await task_manager.get_task_info(task_id)
                if task_info:
                    await websocket.send_text(json.dumps({
                        "type": "task_status",
                        "task_id": task_id,
                        "status": task_info.status.value,
                        "progress": task_info.progress,
                        "message": task_info.description,
                        "created_at": task_info.created_at.isoformat() if task_info.created_at else None,
                        "started_at": task_info.started_at.isoformat() if task_info.started_at else None,
                        "completed_at": task_info.completed_at.isoformat() if task_info.completed_at else None
                    }, ensure_ascii=False))
        
        elif message_type == "unsubscribe_task":
            # 取消订阅任务更新
            task_id = message.get("task_id")
            if task_id:
                manager.unsubscribe_task(user_id, task_id)
                
                await websocket.send_text(json.dumps({
                    "type": "subscription",
                    "status": "unsubscribed",
                    "task_id": task_id,
                    "message": f"已取消订阅任务 {task_id} 的更新"
                }, ensure_ascii=False))
        
        elif message_type == "cancel_task":
            # 取消任务
            task_id = message.get("task_id")
            if task_id:
                task_manager = get_task_manager()
                success = await task_manager.cancel_task(task_id)
                
                await websocket.send_text(json.dumps({
                    "type": "task_action",
                    "action": "cancel",
                    "task_id": task_id,
                    "success": success,
                    "message": "任务取消成功" if success else "任务取消失败"
                }, ensure_ascii=False))
        
        elif message_type == "ping":
            # 心跳检测
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": message.get("timestamp")
            }, ensure_ascii=False))
        
        else:
            # 未知消息类型
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"未知的消息类型: {message_type}"
            }, ensure_ascii=False))
    
    except Exception as e:
        logger.error(f"处理WebSocket消息失败: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"处理消息时发生错误: {str(e)}"
        }, ensure_ascii=False))


@router.get("/ws/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计"""
    return {
        "active_connections": manager.get_connection_count(),
        "active_users": len(manager.active_connections),
        "total_subscriptions": sum(len(subs) for subs in manager.user_subscriptions.values()),
        "listening": progress_listener.listening
    }


# 应用启动时启动进度监听器
async def startup_websocket_listener():
    """启动WebSocket监听器"""
    await progress_listener.start_listening()


# 应用关闭时停止进度监听器
async def shutdown_websocket_listener():
    """关闭WebSocket监听器"""
    await progress_listener.stop_listening()