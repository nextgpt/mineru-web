"""
数据库连接和会话管理
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mineru.db')

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()