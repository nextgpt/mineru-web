from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.file import File

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> dict:
        """获取统计数据"""
        # 计算总文件数
        total_files = self.db.query(File).count()

        # 计算今日上传数
        today = date.today()
        today_uploads = self.db.query(File).filter(
            File.upload_time >= datetime.combine(today, datetime.min.time())
        ).count()

        # 计算已用空间（MB）
        used_space = self.db.query(File).with_entities(
            func.sum(File.size)
        ).scalar() or 0
        used_space = round(used_space / (1024 * 1024), 2)  # 转换为MB

        return {
            'totalFiles': total_files,
            'todayUploads': today_uploads,
            'usedSpace': used_space
        } 