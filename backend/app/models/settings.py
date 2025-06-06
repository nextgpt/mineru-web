from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.models.base import Base
from datetime import datetime

class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    ocr_lang = Column(String(32), default='auto')
    force_ocr = Column(Boolean, default=False)
    table_recognition = Column(Boolean, default=False)
    formula_recognition = Column(Boolean, default=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'ocr_lang': self.ocr_lang,
            'force_ocr': self.force_ocr,
            'table_recognition': self.table_recognition,
            'formula_recognition': self.formula_recognition
        } 