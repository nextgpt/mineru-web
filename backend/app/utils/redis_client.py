import os
import redis
import redis.asyncio as aioredis
import json
from loguru import logger
from typing import Dict, Any, List, Tuple, Optional

class RedisClient:
    def __init__(self):
        REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_DB = int(os.getenv("REDIS_DB", 0))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

        # 同步客户端
        self.client = None
        # 异步客户端
        self.async_client = None
        
        try:
            # 初始化同步客户端
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=False  # 保持原始字节格式
            )
            # 测试连接
            self.client.ping()
            logger.info("Redis sync connection successful!")
            
            # 初始化异步客户端
            self.async_client = aioredis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True  # 异步客户端使用字符串响应
            )
            logger.info("Redis async connection initialized!")
            
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            self.client = None
            self.async_client = None

    def create_consumer_group(self, stream: str, group: str):
        """创建消费者组"""
        try:
            self.client.xgroup_create(stream, group, mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # 消费者组已存在，忽略错误
                pass
            else:
                raise

    def read_stream(self, stream: str, group: str, consumer: str, count: int = 1, block: int = 1000) -> List[Tuple[str, Dict]]:
        """从 Stream 中读取消息"""
        try:
            # 使用 XREADGROUP 命令读取消息
            response = self.client.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={stream: '>'},  # 只读取新消息
                count=count,
                block=block
            )
            
            if not response:
                return []
                
            # 解析响应
            messages = []
            for stream_name, stream_messages in response:
                for message_id, message_data in stream_messages:
                    messages.append((message_id, message_data))
            
            return messages
        except redis.exceptions.ResponseError as e:
            if "NOGROUP" in str(e):
                # 消费者组不存在，创建它
                self.create_consumer_group(stream, group)
                return self.read_stream(stream, group, consumer, count, block)
            raise

    def ack_message(self, stream: str, group: str, message_id: str):
        """确认消息已处理"""
        self.client.xack(stream, group, message_id)

    def publish_task(self, stream: str, task_data: dict):
        """发布任务到 Stream"""
        self.client.xadd(stream, {
            'data': json.dumps(task_data)
        })

    def subscribe_channel(self, channel: str):
        """
        订阅 Redis 频道
        Args:
            channel (str): Redis 频道名称
        Returns:
            redis.client.PubSub: PubSub 对象
        """
        if self.client:
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel '{channel}'")
            return pubsub
        else:
            logger.error("Redis client is not connected, cannot subscribe to channel.")
            return None
    
    # 异步方法
    async def get(self, key: str) -> Optional[str]:
        """异步获取键值"""
        if self.async_client:
            return await self.async_client.get(key)
        return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """异步设置键值"""
        if self.async_client:
            return await self.async_client.set(key, value, ex=ex)
        return False
    
    async def lpush(self, key: str, *values) -> int:
        """异步左推入列表"""
        if self.async_client:
            return await self.async_client.lpush(key, *values)
        return 0
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """异步获取列表范围"""
        if self.async_client:
            return await self.async_client.lrange(key, start, end)
        return []
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """异步修剪列表"""
        if self.async_client:
            return await self.async_client.ltrim(key, start, end)
        return False
    
    async def expire(self, key: str, time: int) -> bool:
        """异步设置过期时间"""
        if self.async_client:
            return await self.async_client.expire(key, time)
        return False
    
    async def publish(self, channel: str, message: str) -> int:
        """异步发布消息"""
        if self.async_client:
            return await self.async_client.publish(channel, message)
        return 0

redis_client = RedisClient() 