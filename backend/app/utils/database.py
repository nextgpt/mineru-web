"""
数据库工具模块
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    """获取数据库URL"""
    return os.getenv("DATABASE_URL", "sqlite:///./mineru.db")


def create_database_engine():
    """创建数据库引擎"""
    database_url = get_database_url()
    
    # SQLite特殊配置
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    else:
        engine = create_engine(database_url, echo=False)
    
    return engine


def get_session_local():
    """获取数据库会话工厂"""
    engine = create_database_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)