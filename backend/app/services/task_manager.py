"""
异步任务管理服务
处理长时间运行的任务，如内容生成、文档导出等
"""
import json
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class TaskType(Enum):
    """任务类型枚举"""
    CONTENT_GENERATION = "content_generation"
    DOCUMENT_EXPORT = "document_export"
    ANALYSIS = "analysis"
    OUTLINE_GENERATION = "outline_generation"


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    project_id: str
    tenant_id: str
    user_id: str
    title: str
    description: str = ""
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理枚举类型
        data['task_type'] = self.task_type.value
        data['status'] = self.status.value
        # 处理日期时间
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskInfo':
        """从字典创建任务信息"""
        # 处理枚举类型
        data['task_type'] = TaskType(data['task_type'])
        data['status'] = TaskStatus(data['status'])
        # 处理日期时间
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


class TaskManager:
    """异步任务管理器"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis_client
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[TaskType, Callable] = {}
        
        # Redis键前缀
        self.task_key_prefix = "task:"
        self.user_tasks_key_prefix = "user_tasks:"
        self.project_tasks_key_prefix = "project_tasks:"
    
    def register_handler(self, task_type: TaskType, handler: Callable):
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理器函数
        """
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type.value}")
    
    async def create_task(
        self,
        task_type: TaskType,
        project_id: str,
        tenant_id: str,
        user_id: str,
        title: str,
        description: str = "",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        创建新任务
        
        Args:
            task_type: 任务类型
            project_id: 项目ID
            tenant_id: 租户ID
            user_id: 用户ID
            title: 任务标题
            description: 任务描述
            metadata: 任务元数据
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        
        # 保存任务信息到Redis
        await self._save_task_info(task_info)
        
        # 添加到用户任务列表
        await self._add_to_user_tasks(user_id, task_id)
        
        # 添加到项目任务列表
        await self._add_to_project_tasks(project_id, task_id)
        
        logger.info(f"创建任务: {task_id}, 类型: {task_type.value}, 项目: {project_id}")
        return task_id
    
    async def start_task(self, task_id: str) -> bool:
        """
        启动任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功启动
        """
        task_info = await self.get_task_info(task_id)
        if not task_info:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        if task_info.status != TaskStatus.PENDING:
            logger.warning(f"任务状态不正确，无法启动: {task_id}, 状态: {task_info.status}")
            return False
        
        # 检查是否有对应的处理器
        if task_info.task_type not in self.task_handlers:
            logger.error(f"未找到任务处理器: {task_info.task_type}")
            await self._update_task_status(task_id, TaskStatus.FAILED, error_message="未找到任务处理器")
            return False
        
        # 更新任务状态为运行中
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.utcnow()
        await self._save_task_info(task_info)
        
        # 创建异步任务
        handler = self.task_handlers[task_info.task_type]
        async_task = asyncio.create_task(self._execute_task(task_id, handler))
        self.running_tasks[task_id] = async_task
        
        logger.info(f"启动任务: {task_id}")
        return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        task_info = await self.get_task_info(task_id)
        if not task_info:
            return False
        
        # 如果任务正在运行，取消异步任务
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # 更新任务状态
        await self._update_task_status(task_id, TaskStatus.CANCELLED)
        
        logger.info(f"取消任务: {task_id}")
        return True
    
    async def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskInfo: 任务信息，不存在时返回None
        """
        try:
            key = f"{self.task_key_prefix}{task_id}"
            data = await self.redis_client.get(key)
            if data:
                return TaskInfo.from_dict(json.loads(data))
            return None
        except Exception as e:
            logger.error(f"获取任务信息失败: {task_id}, 错误: {str(e)}")
            return None
    
    async def update_task_progress(self, task_id: str, progress: int, message: str = None):
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        task_info = await self.get_task_info(task_id)
        if task_info:
            task_info.progress = max(0, min(100, progress))
            if message:
                task_info.description = message
            await self._save_task_info(task_info)
            
            # 发布进度更新事件
            await self._publish_progress_update(task_id, progress, message)
    
    async def complete_task(self, task_id: str, result: Dict[str, Any] = None):
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
        """
        task_info = await self.get_task_info(task_id)
        if task_info:
            task_info.status = TaskStatus.COMPLETED
            task_info.progress = 100
            task_info.completed_at = datetime.utcnow()
            task_info.result = result or {}
            await self._save_task_info(task_info)
            
            # 清理运行中的任务
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            logger.info(f"任务完成: {task_id}")
    
    async def fail_task(self, task_id: str, error_message: str):
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
        """
        await self._update_task_status(task_id, TaskStatus.FAILED, error_message=error_message)
        
        # 清理运行中的任务
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        logger.error(f"任务失败: {task_id}, 错误: {error_message}")
    
    async def get_user_tasks(self, user_id: str, limit: int = 50) -> List[TaskInfo]:
        """
        获取用户的任务列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            List[TaskInfo]: 任务列表
        """
        try:
            key = f"{self.user_tasks_key_prefix}{user_id}"
            task_ids = await self.redis_client.lrange(key, 0, limit - 1)
            
            tasks = []
            for task_id in task_ids:
                task_info = await self.get_task_info(task_id.decode())
                if task_info:
                    tasks.append(task_info)
            
            return tasks
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {user_id}, 错误: {str(e)}")
            return []
    
    async def get_project_tasks(self, project_id: str, limit: int = 50) -> List[TaskInfo]:
        """
        获取项目的任务列表
        
        Args:
            project_id: 项目ID
            limit: 返回数量限制
            
        Returns:
            List[TaskInfo]: 任务列表
        """
        try:
            key = f"{self.project_tasks_key_prefix}{project_id}"
            task_ids = await self.redis_client.lrange(key, 0, limit - 1)
            
            tasks = []
            for task_id in task_ids:
                task_info = await self.get_task_info(task_id.decode())
                if task_info:
                    tasks.append(task_info)
            
            return tasks
        except Exception as e:
            logger.error(f"获取项目任务列表失败: {project_id}, 错误: {str(e)}")
            return []
    
    async def cleanup_old_tasks(self, days: int = 7):
        """
        清理旧任务
        
        Args:
            days: 保留天数
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 这里需要实现清理逻辑
        # 由于Redis没有直接的方式来查询所有任务，
        # 实际实现中可能需要维护一个任务索引
        logger.info(f"清理 {days} 天前的旧任务")
    
    async def _execute_task(self, task_id: str, handler: Callable):
        """
        执行任务
        
        Args:
            task_id: 任务ID
            handler: 任务处理器
        """
        try:
            task_info = await self.get_task_info(task_id)
            if not task_info:
                return
            
            # 执行任务处理器
            result = await handler(task_info, self)
            
            # 完成任务
            await self.complete_task(task_id, result)
            
        except asyncio.CancelledError:
            logger.info(f"任务被取消: {task_id}")
            await self._update_task_status(task_id, TaskStatus.CANCELLED)
        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {str(e)}")
            await self.fail_task(task_id, str(e))
    
    async def _save_task_info(self, task_info: TaskInfo):
        """保存任务信息到Redis"""
        try:
            key = f"{self.task_key_prefix}{task_info.task_id}"
            data = json.dumps(task_info.to_dict(), ensure_ascii=False)
            await self.redis_client.set(key, data, ex=7 * 24 * 3600)  # 7天过期
        except Exception as e:
            logger.error(f"保存任务信息失败: {task_info.task_id}, 错误: {str(e)}")
    
    async def _update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus, 
        error_message: str = None
    ):
        """更新任务状态"""
        task_info = await self.get_task_info(task_id)
        if task_info:
            task_info.status = status
            if error_message:
                task_info.error_message = error_message
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task_info.completed_at = datetime.utcnow()
            await self._save_task_info(task_info)
    
    async def _add_to_user_tasks(self, user_id: str, task_id: str):
        """添加任务到用户任务列表"""
        try:
            key = f"{self.user_tasks_key_prefix}{user_id}"
            await self.redis_client.lpush(key, task_id)
            await self.redis_client.ltrim(key, 0, 99)  # 保留最近100个任务
            await self.redis_client.expire(key, 30 * 24 * 3600)  # 30天过期
        except Exception as e:
            logger.error(f"添加用户任务失败: {user_id}, {task_id}, 错误: {str(e)}")
    
    async def _add_to_project_tasks(self, project_id: str, task_id: str):
        """添加任务到项目任务列表"""
        try:
            key = f"{self.project_tasks_key_prefix}{project_id}"
            await self.redis_client.lpush(key, task_id)
            await self.redis_client.ltrim(key, 0, 49)  # 保留最近50个任务
            await self.redis_client.expire(key, 30 * 24 * 3600)  # 30天过期
        except Exception as e:
            logger.error(f"添加项目任务失败: {project_id}, {task_id}, 错误: {str(e)}")
    
    async def _publish_progress_update(self, task_id: str, progress: int, message: str = None):
        """发布进度更新事件"""
        try:
            channel = f"task_progress:{task_id}"
            data = {
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.redis_client.publish(channel, json.dumps(data))
        except Exception as e:
            logger.error(f"发布进度更新失败: {task_id}, 错误: {str(e)}")


# 全局任务管理器实例
_task_manager = None


def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager