"""
分层记忆系统 — 解决长篇小说 AI 写作的上下文限制问题

核心思路：不塞全文，而是维护结构化的"记忆"，写作时按需注入相关记忆。

记忆层级：
  Layer 1: 全局记忆 — 世界观、主角、主线冲突（始终注入）
  Layer 2: 卷级记忆 — 当前卷的事件摘要和人物
  Layer 3: 近期记忆 — 前 2-3 章的详细摘要
  Layer 4: 相关记忆 — 从向量数据库检索与本章相关的历史信息
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GlobalMemory:
    """Layer 1: 全局记忆 — 始终注入，约 500 tokens"""

    world_setting: str = ""       # 世界观核心设定（2-3 句话）
    protagonist: str = ""         # 主角人设卡
    main_conflict: str = ""       # 当前主线冲突
    genre_rules: str = ""         # 题材规则（如修仙体系、都市设定）
    tone: str = ""                # 整体基调

    def to_prompt(self) -> str:
        """转为 prompt 片段，控制在 500 tokens 以内"""
        parts = []
        if self.world_setting:
            parts.append(f"【世界观】{self.world_setting}")
        if self.protagonist:
            parts.append(f"【主角】{self.protagonist}")
        if self.main_conflict:
            parts.append(f"【主线冲突】{self.main_conflict}")
        if self.genre_rules:
            parts.append(f"【题材规则】{self.genre_rules}")
        if self.tone:
            parts.append(f"【基调】{self.tone}")
        return "\n".join(parts)


@dataclass
class VolumeMemory:
    """Layer 2: 卷级记忆 — 当前卷，约 300 tokens"""

    volume_number: int = 1
    volume_summary: str = ""      # 本卷主要事件摘要（200 字以内）
    new_characters: list = field(default_factory=list)  # 本卷新出场人物
    unresolved_hooks: list = field(default_factory=list) # 未解决的悬念
    key_events: list = field(default_factory=list)       # 关键事件列表

    def to_prompt(self) -> str:
        parts = [f"【第{self.volume_number}卷概况】{self.volume_summary}"]
        if self.new_characters:
            parts.append(f"本卷新人物：{', '.join(self.new_characters)}")
        if self.unresolved_hooks:
            parts.append(f"未解悬念：{'; '.join(self.unresolved_hooks)}")
        if self.key_events:
            # 只保留最近 5 个关键事件
            recent = self.key_events[-5:]
            parts.append(f"近期事件：{' → '.join(recent)}")
        return "\n".join(parts)


@dataclass
class ChapterSummary:
    """单章摘要"""

    chapter_number: int
    title: str = ""
    summary: str = ""             # 150 字以内详细摘要
    key_dialogue: str = ""        # 关键对话（保留原汁原味）
    cliffhanger: str = ""         # 章末悬念
    characters_present: list = field(default_factory=list)
    location: str = ""
    emotion: str = ""             # 本章情绪基调


@dataclass
class RecentMemory:
    """Layer 3: 近期记忆 — 前 2-3 章，约 800 tokens"""

    chapters: list = field(default_factory=list)  # list[ChapterSummary]

    def to_prompt(self) -> str:
        if not self.chapters:
            return "【前情】这是故事的开始。"

        parts = ["【前情提要】"]
        for ch in self.chapters:
            line = f"第{ch.chapter_number}章"
            if ch.title:
                line += f"《{ch.title}》"
            line += f"：{ch.summary}"
            if ch.cliffhanger:
                line += f"（悬念：{ch.cliffhanger}）"
            parts.append(line)

        # 上一章的结尾场景（如果有）
        last = self.chapters[-1]
        if last.key_dialogue:
            parts.append(f"\n上一章关键对话：{last.key_dialogue}")

        return "\n".join(parts)


@dataclass
class RelevantMemory:
    """Layer 4: 相关记忆 — 按需检索，约 500 tokens"""

    related_foreshadowing: list = field(default_factory=list)  # 相关伏笔
    related_characters: list = field(default_factory=list)     # 相关人物历史
    related_events: list = field(default_factory=list)         # 相关事件
    world_rules: list = field(default_factory=list)            # 相关世界观设定

    def to_prompt(self) -> str:
        parts = []
        if self.related_foreshadowing:
            parts.append(f"【相关伏笔】{'; '.join(self.related_foreshadowing)}")
        if self.related_characters:
            parts.append(f"【相关人物】{'; '.join(self.related_characters)}")
        if self.related_events:
            parts.append(f"【相关事件】{'; '.join(self.related_events)}")
        if self.world_rules:
            parts.append(f"【相关设定】{'; '.join(self.world_rules)}")
        return "\n".join(parts)


@dataclass
class StoryState:
    """故事当前状态快照"""

    timeline: str = ""            # 当前时间线（如"第三天傍晚"）
    location: str = ""            # 当前地点
    characters_present: list = field(default_factory=list)  # 当前在场人物
    active_conflicts: list = field(default_factory=list)    # 进行中的冲突
    revealed_secrets: list = field(default_factory=list)    # 已揭示的秘密
    pending_foreshadowing: list = field(default_factory=list)  # 未揭开的伏笔
    power_level: str = ""         # 主角当前实力
    relationships: dict = field(default_factory=dict)       # 人物关系变化
    inventory: list = field(default_factory=list)           # 主角持有物品/能力

    def to_prompt(self) -> str:
        parts = [f"【当前状态】"]
        if self.timeline:
            parts.append(f"时间：{self.timeline}")
        if self.location:
            parts.append(f"地点：{self.location}")
        if self.characters_present:
            parts.append(f"在场人物：{', '.join(self.characters_present)}")
        if self.active_conflicts:
            parts.append(f"进行中冲突：{'; '.join(self.active_conflicts)}")
        if self.pending_foreshadowing:
            parts.append(f"待揭伏笔：{'; '.join(self.pending_foreshadowing)}")
        if self.power_level:
            parts.append(f"主角实力：{self.power_level}")
        return "\n".join(parts)


class MemoryManager:
    """
    分层记忆管理器

    核心职责：
    1. 维护各层记忆数据
    2. 写作时组装完整的上下文
    3. 每章写完后更新记忆
    4. 管理 token 预算
    """

    # 各层 token 预算（近似值）
    # 20k 上下文模型，留 6k 给正文生成，14k 给上下文
    TOKEN_BUDGET = {
        "global": 800,          # 世界观+主角+主线
        "volume": 500,          # 当前卷摘要
        "recent": 3000,         # 前 3 章详细摘要（每章约 1000 tokens）
        "relevant": 1500,       # 相关伏笔/人物/事件
        "story_state": 800,     # 故事状态快照
        "chapter_outline": 600, # 本章大纲
        "hook_requirement": 300,# 爽点要求
        "characters": 1500,     # 人物设定
        "total_context": 9000,  # 上下文总预算
    }

    def __init__(self, novel_id: int, db_session=None):
        self.novel_id = novel_id
        self.db = db_session
        self.global_memory = GlobalMemory()
        self.volume_memory = VolumeMemory()
        self.recent_memory = RecentMemory()
        self.relevant_memory = RelevantMemory()
        self.story_state = StoryState()
        self._chapter_summaries: dict[int, ChapterSummary] = {}

    def load_from_db(self):
        """从数据库加载所有记忆"""
        self._load_global_memory()
        self._load_volume_memory()
        self._load_recent_memory()
        self._load_story_state()

    def _load_global_memory(self):
        """从数据库加载全局记忆"""
        from backend.models.novel import Novel
        novel = self.db.query(Novel).filter(Novel.id == self.novel_id).first()
        if not novel:
            return

        config = novel.config or {}
        self.global_memory = GlobalMemory(
            world_setting=config.get("world_setting", ""),
            protagonist=config.get("protagonist", ""),
            main_conflict=config.get("main_conflict", ""),
            genre_rules=config.get("genre_rules", ""),
            tone=config.get("tone", ""),
        )

    def _load_volume_memory(self):
        """加载当前卷的记忆"""
        from backend.models.outline import Outline
        # 获取当前卷的大纲
        # 具体实现依赖数据库结构
        pass

    def _load_recent_memory(self, current_chapter: int = 0):
        """加载前 2-3 章的摘要"""
        from backend.models.chapter import Chapter

        recent_chapters = (
            self.db.query(Chapter)
            .filter(
                Chapter.novel_id == self.novel_id,
                Chapter.chapter_number < current_chapter,
                Chapter.chapter_number >= current_chapter - 3,
            )
            .order_by(Chapter.chapter_number)
            .all()
        )

        self.recent_memory = RecentMemory(
            chapters=[
                ChapterSummary(
                    chapter_number=ch.chapter_number,
                    title=ch.title or "",
                    summary=ch.chapter_summary or self._auto_summary(ch.content),
                    cliffhanger=ch.cliffhanger or "",
                    characters_present=ch.characters_in_chapter or [],
                    location=ch.location or "",
                    emotion=ch.emotion or "",
                )
                for ch in recent_chapters
            ]
        )

    def _load_story_state(self):
        """加载故事状态快照"""
        from sqlalchemy import text as sql_text
        result = self.db.execute(
            sql_text("SELECT world_state FROM story_state WHERE novel_id = :nid"),
            {"nid": self.novel_id},
        ).fetchone()

        if result and result[0]:
            state_data = json.loads(result[0]) if isinstance(result[0], str) else result[0]
            self.story_state = StoryState(
                timeline=state_data.get("timeline", ""),
                location=state_data.get("location", ""),
                characters_present=state_data.get("characters_present", []),
                active_conflicts=state_data.get("active_conflicts", []),
                revealed_secrets=state_data.get("revealed_secrets", []),
                pending_foreshadowing=state_data.get("pending_foreshadowing", []),
                power_level=state_data.get("power_level", ""),
                relationships=state_data.get("relationships", {}),
                inventory=state_data.get("inventory", []),
            )

    def update_after_chapter(self, chapter_number: int, chapter_text: str, chapter_summary: str):
        """每章写完后更新记忆"""
        # 更新近期记忆
        summary = ChapterSummary(
            chapter_number=chapter_number,
            summary=chapter_summary,
        )
        self._chapter_summaries[chapter_number] = summary

        # 保持最近 3 章
        self.recent_memory.chapters = sorted(
            self._chapter_summaries.values(),
            key=lambda x: x.chapter_number,
        )[-3:]

        # 更新故事状态（调用 AI 分析）
        self._update_story_state(chapter_text, chapter_number)

    def _update_story_state(self, chapter_text: str, chapter_number: int):
        """调用 AI 更新故事状态"""
        from openai import OpenAI
        from backend.config import config

        client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)

        prompt = f"""
分析以下章节内容，更新故事状态。输出 JSON。

当前状态：
{json.dumps(self.story_state.__dict__, ensure_ascii=False)}

第{chapter_number}章内容（前 2000 字）：
{chapter_text[:2000]}

更新规则：
1. 只更新发生变化的部分
2. 新出场的人物加入 characters_present
3. 已解决的冲突从 active_conflicts 移除
4. 新揭示的秘密加入 revealed_secrets
5. 新的伏笔加入 pending_foreshadowing
6. 更新 timeline、location、power_level

输出更新后的完整状态 JSON：
"""

        try:
            response = client.chat.completions.create(
                model=config.MI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000,
            )
            result_text = response.choices[0].message.content.strip()
            # 提取 JSON
            import re
            json_match = re.search(r"\{[\s\S]*\}", result_text)
            if json_match:
                new_state = json.loads(json_match.group())
                for key, value in new_state.items():
                    if hasattr(self.story_state, key) and value:
                        setattr(self.story_state, key, value)
        except Exception as e:
            print(f"[Memory] 更新故事状态失败: {e}")

    def build_context(self, chapter_outline: dict, hook_requirement: str = None) -> str:
        """
        组装写作上下文 — 核心方法

        将四层记忆 + 章节大纲组装成一个完整的 prompt 片段，
        控制在 token 预算内。

        Args:
            chapter_outline: 本章大纲信息
            hook_requirement: 爽点要求（如有）

        Returns:
            组装好的上下文文本
        """
        parts = []

        # Layer 1: 全局记忆（必须注入）
        global_text = self.global_memory.to_prompt()
        if global_text:
            parts.append(global_text)

        # Layer 2: 卷级记忆
        volume_text = self.volume_memory.to_prompt()
        if volume_text:
            parts.append(volume_text)

        # Layer 3: 近期记忆
        recent_text = self.recent_memory.to_prompt()
        if recent_text:
            parts.append(recent_text)

        # Layer 4: 故事当前状态
        state_text = self.story_state.to_prompt()
        if state_text:
            parts.append(state_text)

        # 本章大纲
        outline_text = self._format_outline(chapter_outline)
        if outline_text:
            parts.append(outline_text)

        # 爽点要求
        if hook_requirement:
            parts.append(f"【本章爽点】{hook_requirement}")

        return "\n\n".join(parts)

    def _format_outline(self, outline: dict) -> str:
        """格式化章节大纲"""
        parts = []
        if outline.get("title"):
            parts.append(f"【本章标题】{outline['title']}")
        if outline.get("content"):
            parts.append(f"【本章大纲】{outline['content']}")
        if outline.get("key_events"):
            parts.append(f"关键事件：{'; '.join(outline['key_events'])}")
        if outline.get("characters"):
            parts.append(f"出场人物：{', '.join(outline['characters'])}")
        if outline.get("emotion"):
            parts.append(f"情绪基调：{outline['emotion']}")
        return "\n".join(parts)

    def _auto_summary(self, content: str) -> str:
        """自动摘要（如果章节没有存摘要）"""
        if not content:
            return ""
        # 简单截取前 150 字作为摘要
        return content[:150] + "..."

    def get_memory_stats(self) -> dict:
        """获取记忆统计信息"""
        return {
            "global_memory": bool(self.global_memory.world_setting),
            "volume_memory": bool(self.volume_memory.volume_summary),
            "recent_chapters": len(self.recent_memory.chapters),
            "story_state": bool(self.story_state.timeline),
            "pending_foreshadowing": len(self.story_state.pending_foreshadowing),
            "active_conflicts": len(self.story_state.active_conflicts),
        }
