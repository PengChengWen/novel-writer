"""
Character 模型 — 人物表
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from backend.database import Base


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="人物姓名")
    role = Column(String(50), comment="角色：主角/配角/反派/龙套")
    personality = Column(Text, comment="性格描述")
    speaking_style = Column(Text, comment="说话风格（口头禅、语气、用词特点）")
    combat_style = Column(Text, comment="战斗风格/能力描述")
    appearance = Column(Text, comment="外貌描述")
    background = Column(Text, comment="背景故事")
    bottom_line = Column(Text, comment="人设底线（绝对不会做的事）")
    relationships = Column(JSON, comment="与其他人物的关系")
    first_appearance = Column(Integer, comment="首次出场章节号")
    status = Column(
        String(20),
        default="active",
        comment="状态: active/dead/missing/retired",
    )
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "novel_id": self.novel_id,
            "name": self.name,
            "role": self.role,
            "personality": self.personality,
            "speaking_style": self.speaking_style,
            "combat_style": self.combat_style,
            "appearance": self.appearance,
            "background": self.background,
            "bottom_line": self.bottom_line,
            "relationships": self.relationships,
            "first_appearance": self.first_appearance,
            "status": self.status,
        }
