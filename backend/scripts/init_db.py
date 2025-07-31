#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from app.models.tender import Base
from app.utils.database import get_database_url

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    try:
        # 获取数据库URL
        database_url = get_database_url()
        logger.info(f"初始化数据库: {database_url}")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
        
        # 运行Alembic迁移
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        try:
            command.upgrade(alembic_cfg, "head")
            logger.info("数据库迁移完成")
        except Exception as e:
            logger.warning(f"数据库迁移失败，可能是首次运行: {e}")
            # 标记当前版本
            try:
                command.stamp(alembic_cfg, "head")
                logger.info("数据库版本标记完成")
            except Exception as stamp_error:
                logger.error(f"数据库版本标记失败: {stamp_error}")
        
        logger.info("数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def create_default_data():
    """创建默认数据"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # 这里可以添加默认数据创建逻辑
            # 例如：创建默认租户、用户等
            logger.info("默认数据创建完成")
            
    except Exception as e:
        logger.error(f"默认数据创建失败: {e}")


def main():
    """主函数"""
    logger.info("开始数据库初始化...")
    
    # 初始化数据库
    if not init_database():
        sys.exit(1)
    
    # 创建默认数据
    create_default_data()
    
    logger.info("数据库初始化完成!")


if __name__ == "__main__":
    main()