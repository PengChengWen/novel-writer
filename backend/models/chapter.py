"""
Chapter 模型 — 章节表
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from backend.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    volume_number = Column(Integer, default=1, comment="卷号")
    chapter_number = Column(Integer, nullable=False, comment="章节号")
    title = Column(String(200), comment="章节标题")
    content = Column(Text, comment="章节正文")
    word_count = Column(Integer, default=0, comment="字数")
    outline_text = Column(Text, comment="本章大纲")
    hooks_used = Column(JSON, comment="本章使用的爽点类型及位置")
    chapter_summary = Column(Text, comment="章节摘要（150字，供记忆系统使用）")
    cliffhanger = Column(String(500), comment="章末悬念")
    characters_in_chapter = Column(JSON, comment="本章出场人物列表")
    location = Column(String(200), comment="本章主要地点")
    emotion = Column(String(100), comment="本章情绪基调")
    quality_score = Column(Float, comment="质量评分（0-100）")
    quality_issues = Column(JSON, comment="质量检查发现的问题")
    fanqie_chapter_id = Column(String(100), comment="番茄小说章节ID")
    status = Column(
        String(20),
        default="pending",
        comment="状态: pending/writing/reviewing/completed/published",
    )
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "novel_id": self.novel_id,
            "volume_number": self.volume_number,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "outline_text": self.outline_text,
            "hooks_used": self.hooks_used,
            "quality_score": self.quality_score,
            "quality_issues": self.quality_issues,
            "chapter_summary": self.chapter_summary,
            "cliffhanger": self.cliffhanger,
            "characters_in_chapter": self.characters_in_chapter,
            "location": self.location,
            "emotion": self.emotion,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
