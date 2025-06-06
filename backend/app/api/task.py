from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.task import Task
from app.models.file import File as FileModel
from app.services.parser import ParserService
from app.utils.user_dep import get_user_id
import os
import threading
import time

router = APIRouter()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mineru.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

# 后台任务执行
TASK_THREAD_POOL = {}

def run_parse_task(task_id, user_id, file_id):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            return
        
        task.status = 'running'
        db.commit()
        
        # 获取文件信息
        file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == user_id).first()
        if not file:
            task.status = 'failed'
            task.result = '文件不存在'
            db.commit()
            return
        
        # 创建解析服务
        parser = ParserService(db)
        
        # 开始解析
        results = parser.parse_pdf(file, user_id)
        
        # 更新文件状态
        file.status = 'parsed'
        db.commit()
        
        # 更新任务状态
        task.status = 'success'
        task.progress = 1.0
        task.result = f'成功解析 {len(results)} 页内容'
        db.commit()
        
    except Exception as e:
        task.status = 'failed'
        task.result = str(e)
        db.commit()
    finally:
        db.close()

@router.post("/tasks/parse")
def submit_parse_task(file_id: int = Body(...), user_id: str = Depends(get_user_id)):
    db = SessionLocal()
    try:
        # 检查文件是否存在
        file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == user_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查是否已有正在进行的解析任务
        existing_task = db.query(Task).filter(
            Task.file_id == file_id,
            Task.user_id == user_id,
            Task.type == 'parse',
            Task.status.in_(['pending', 'running'])
        ).first()
        
        if existing_task:
            raise HTTPException(status_code=400, detail="该文件已有正在进行的解析任务")
        
        # 创建新任务
        task = Task(
            user_id=user_id,
            file_id=file_id,
            type='parse',
            status='pending',
            progress=0.0
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 启动后台线程
        t = threading.Thread(target=run_parse_task, args=(task.id, user_id, file_id))
        t.start()
        TASK_THREAD_POOL[task.id] = t
        
        return {"task_id": task.id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/tasks/{task_id}")
def get_task_status(task_id: int, user_id: str = Depends(get_user_id)):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task.to_dict()
    finally:
        db.close() 