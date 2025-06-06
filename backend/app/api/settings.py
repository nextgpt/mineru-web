from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from app.models.settings import Settings
from app.utils.user_dep import get_user_id
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

router = APIRouter()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./mineru.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

@router.get("/settings")
def get_settings(user_id: str = Depends(get_user_id)):
    db = SessionLocal()
    settings = db.query(Settings).filter(Settings.user_id == user_id).first()
    db.close()
    if not settings:
        # 返回默认设置
        return {
            "user_id": user_id,
            "ocr_enabled": True,
            "ocr_lang": "auto",
            "force_ocr": False,
            "table_recognition": False,
            "formula_recognition": False
        }
    return settings.to_dict()

@router.put("/settings")
def update_settings(
    settings: dict = Body(...),
    user_id: str = Depends(get_user_id)
):
    db = SessionLocal()
    db_settings = db.query(Settings).filter(Settings.user_id == user_id).first()
    if not db_settings:
        db_settings = Settings(user_id=user_id)
        db.add(db_settings)
    
    # 更新设置
    for key, value in settings.items():
        if hasattr(db_settings, key):
            setattr(db_settings, key, value)
    
    db.commit()
    db.refresh(db_settings)
    db.close()
    return db_settings.to_dict() 