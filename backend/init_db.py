#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def init_database():
    """初始化数据库"""
    try:
        # 设置环境变量
        os.environ['DATABASE_URL'] = 'postgresql://postgres:password@192.168.30.220:15432/bidgen'
        
        # 导入数据库模块
        from app.database import create_tables, engine
        from app.models import base, project, requirement_analysis, bid_outline, bid_document, file
        
        print("🗄️ 正在创建数据库表...")
        
        # 创建所有表
        create_tables()
        
        print("✅ 数据库表创建成功")
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ 数据库连接测试成功")
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def main():
    print("🚀 初始化标书生成系统数据库...")
    
    if init_database():
        print("🎉 数据库初始化完成")
    else:
        print("❌ 数据库初始化失败")
        sys.exit(1)

if __name__ == "__main__":
    main()