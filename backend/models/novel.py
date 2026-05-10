"""
Novel 模型 — 小说主表
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from backend.database import Base


class Novel(Base):
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="小说标题")
    genre = Column(String(50), nullable=False, comment="题材类型")
    description = Column(Text, comment="小说简介")
    target_words = Column(Integer, default=300000, comment="目标总字数")
    sell_points = Column(JSON, comment="卖点列表")
    reference_text = Column(Text, comment="参考小说原文（上传后存储）")
    style_guide = Column(Text, comment="生成的风格指南（system prompt）")
    status = Column(
        String(20),
        default="draft",
        comment="状态: draft/analyzing/planning/writing/paused/completed/published",
    )
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "description": self.description,
            "target_words": self.target_words,
            "sell_points": self.sell_points,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
