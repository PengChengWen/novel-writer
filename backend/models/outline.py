"""
Outline 模型 — 大纲表（三层结构：总纲→分卷→章节）
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from backend.database import Base


class Outline(Base):
    __tablename__ = "outlines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    level = Column(
        String(20),
        nullable=False,
        comment="层级: master（总纲）/ volume（分卷）/ chapter（章节）",
    )
    volume_number = Column(Integer, comment="卷号（volume/chapter 层级时有值）")
    chapter_number = Column(Integer, comment="章节号（chapter 层级时有值）")
    title = Column(String(200), comment="标题")
    content = Column(Text, comment="大纲内容")
    key_events = Column(JSON, comment="关键事件列表")
    hook_plan = Column(JSON, comment="爽点安排")
    word_target = Column(Integer, comment="目标字数")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "novel_id": self.novel_id,
            "level": self.level,
            "volume_number": self.volume_number,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "content": self.content,
            "key_events": self.key_events,
            "hook_plan": self.hook_plan,
            "word_target": self.word_target,
            "sort_order": self.sort_order,
        }
