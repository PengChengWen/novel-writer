"""
StyleProfile 模型 — 风格分析结果存储
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from backend.database import Base


class StyleProfile(Base):
    __tablename__ = "style_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, unique=True)

    # === StyleDNA：文笔特征 ===
    sentence_analysis = Column(JSON, comment="句式分析：平均长度、结构偏好、长短句比例")
    vocabulary_analysis = Column(JSON, comment="词汇分析：高频词、用词风格、专业领域词汇")
    rhythm_analysis = Column(JSON, comment="节奏分析：段落节奏、场景切换频率、紧张舒缓节奏")
    description_analysis = Column(JSON, comment="描写手法：环境描写、人物描写、动作描写风格")
    dialogue_analysis = Column(JSON, comment="对话风格：对话比例、对话标记、语气词使用")
    tone_analysis = Column(JSON, comment="语气基调：整体基调、情绪变化模式")

    # === 爽点分析 ===
    hook_analysis = Column(JSON, comment="爽点扫描结果：类型、位置、结构模板")
    hook_distribution = Column(JSON, comment="爽点分布规律：章节分布、间隔、密度")
    hook_templates = Column(JSON, comment="6 种爽点的结构模板")

    # === 综合 ===
    style_summary = Column(Text, comment="风格总结文本")
    raw_analysis = Column(JSON, comment="AI 原始分析结果")

    status = Column(String(20), default="pending", comment="状态: pending/analyzing/completed/failed")
    error_message = Column(Text, comment="错误信息（失败时）")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "novel_id": self.novel_id,
            "sentence_analysis": self.sentence_analysis,
            "vocabulary_analysis": self.vocabulary_analysis,
            "rhythm_analysis": self.rhythm_analysis,
            "description_analysis": self.description_analysis,
            "dialogue_analysis": self.dialogue_analysis,
            "tone_analysis": self.tone_analysis,
            "hook_analysis": self.hook_analysis,
            "hook_distribution": self.hook_distribution,
            "hook_templates": self.hook_templates,
            "style_summary": self.style_summary,
            "status": self.status,
        }
