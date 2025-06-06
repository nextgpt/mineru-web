from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from app.models.base import Base  # 统一 Base 导入
from datetime import datetime

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False, index=True)
    type = Column(String(32), default='parse')  # 任务类型
    status = Column(String(32), default='pending')  # pending, running, success, failed
    progress = Column(Float, default=0.0)  # 0~1
    result = Column(Text, nullable=True)  # 可存放错误信息或结果摘要
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_id': self.file_id,
            'type': self.type,
            'status': self.status,
            'progress': self.progress,
            'result': self.result,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 