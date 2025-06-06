import os
import redis
import json
from loguru import logger
from typing import Dict, Any, List, Tuple

class RedisClient:
    def __init__(self):
        REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_DB = int(os.getenv("REDIS_DB", 0))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

        self.client = None
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=False  # 保持原始字节格式
            )
            # 测试连接
            self.client.ping()
            logger.info("Redis connection successful!")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            self.client = None

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

redis_client = RedisClient() 