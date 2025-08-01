import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base

# 数据库连接配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mineru.db')

# 根据数据库类型设置连接参数
if DATABASE_URL.startswith('sqlite'):
    # SQLite 配置
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
elif DATABASE_URL.startswith('postgresql'):
    # PostgreSQL 配置
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600
    )
else:
    # 默认配置
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)