"""
故事状态机 — 每章结束后更新世界状态
"""

import json
import re

from openai import OpenAI

from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)


def update_story_state(
    current_state: dict,
    chapter_text: str,
    chapter_summary: str,
    characters: list[dict],
) -> dict:
    """
    根据新章节内容更新故事状态

    Args:
        current_state: 当前故事状态
        chapter_text: 新章节文本
        chapter_summary: 章节概要
        characters: 相关人物列表

    Returns:
        更新后的故事状态
    """
    chars_info = ", ".join(c["name"] for c in characters)

    prompt = f"""请根据新章节的内容更新故事状态。

## 当前故事状态
{json.dumps(current_state, ensure_ascii=False, indent=2) if current_state else "暂无（第一章）"}

## 新章节概要
{chapter_summary}

## 新章节内容（前 3000 字）
{chapter_text[:3000]}

## 出场人物
{chars_info}

## 更新要求
请输出更新后的故事状态（JSON）：
```json
{{
  "current_timeline": "当前时间线描述",
  "location": "当前地点",
  "active_characters": ["当前活跃的人物"],
  "character_status": {{
    "人物名": "当前状态（位置/情绪/处境）"
  }},
  "active_plotlines": [
    {{
      "plotline": "进行中的剧情线描述",
      "progress": "进展程度"
    }}
  }},
  "pending_hooks": [
    {{
      "type": "伏笔/悬念类型",
      "description": "尚未解决的伏笔",
      "planted_chapter": "埋下的章节"
    }}
  }},
  "world_changes": ["本章发生的世界变化"],
  "power_level": "主角当前实力水平",
  "relationships_update": "人物关系变化"
}}
```

只更新有变化的部分，保持其他内容不变。严格输出 JSON。"""

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": "你是一位小说状态追踪器，负责准确记录故事的当前状态。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    result_text = response.choices[0].message.content.strip()
    try:
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        return current_state or {}


def get_story_summary(previous_chapters: list[dict], max_chars: int = 3000) -> str:
    """
    生成前文摘要（用于写作时的前情提要）

    Args:
        previous_chapters: 前面的章节列表（含 content 和 summary）
        max_chars: 摘要最大字数

    Returns:
        前文摘要文本
    """
    if not previous_chapters:
        return "这是小说的第一章，暂无前文。"

    # 如果有现成的概要，直接使用
    summaries = []
    for ch in previous_chapters:
        ch_summary = ch.get("summary") or ch.get("outline_text", "")
        if ch_summary:
            summaries.append(f"第{ch.get('chapter_number', '?')}章：{ch_summary}")
        elif ch.get("content"):
            # 如果没有概要，取前 200 字作为摘要
            summaries.append(f"第{ch.get('chapter_number', '?')}章：{ch['content'][:200]}...")

    combined = "\n".join(summaries)

    # 如果摘要太长，用 AI 压缩
    if len(combined) > max_chars:
        response = client.chat.completions.create(
            model=config.MI_MODEL,
            messages=[
                {"role": "system", "content": "请将以下章节概要压缩为简洁的前情提要，保留关键剧情和人物关系变化。"},
                {"role": "user", "content": combined},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()

    return combined


def format_context_for_writing(
    chapter_number: int,
    novel_id: int,
    db_session,
) -> dict:
    """
    准备写作所需的完整上下文

    Args:
        chapter_number: 当前章节号
        novel_id: 小说 ID
        db_session: 数据库 session

    Returns:
        上下文字典，包含 story_state、previous_summary、characters 等
    """
    from backend.models.chapter import Chapter
    from backend.models.character import Character
    from backend.models.outline import Outline

    # 获取前面的章节
    prev_chapters = (
        db_session.query(Chapter)
        .filter(
            Chapter.novel_id == novel_id,
            Chapter.chapter_number < chapter_number,
            Chapter.status == "completed",
        )
        .order_by(Chapter.chapter_number.desc())
        .limit(config.MAX_CONTEXT_CHAPTERS)
        .all()
    )
    prev_chapters_list = [ch.to_dict() for ch in reversed(prev_chapters)]

    # 获取故事状态
    from sqlalchemy import text
    result = db_session.execute(
        text("SELECT world_state FROM story_state WHERE novel_id = :novel_id ORDER BY updated_at DESC LIMIT 1"),
        {"novel_id": novel_id},
    ).fetchone()
    story_state = result[0] if result and result[0] else {}

    # 如果 world_state 是字符串，解析为 dict
    if isinstance(story_state, str):
        try:
            story_state = json.loads(story_state)
        except json.JSONDecodeError:
            story_state = {}

    # 获取人物
    characters = (
        db_session.query(Character)
        .filter(Character.novel_id == novel_id, Character.status == "active")
        .all()
    )
    chars_list = [c.to_dict() for c in characters]

    # 生成前文摘要
    previous_summary = get_story_summary(prev_chapters_list)

    return {
        "story_state": story_state,
        "previous_summary": previous_summary,
        "characters": chars_list,
        "prev_chapters_count": len(prev_chapters_list),
    }
