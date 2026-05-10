"""
核心写作引擎 v2 — 集成分层记忆系统

工作流程：
  1. 加载分层记忆（全局/卷级/近期/相关）
  2. 构建 prompt（风格指南 + 记忆上下文 + 大纲 + 人物）
  3. 调用 AI 生成正文
  4. 质量检查（字数/重复/逻辑/敏感词）
  5. 人物一致性检查
  6. 更新记忆系统
  7. 存入数据库
"""

import json
import time
import re

from openai import OpenAI

from backend.config import config
from backend.writer.prompts import (
    build_system_prompt,
    build_user_prompt_with_memory,
    build_continuation_prompt,
)
from backend.writer.memory import MemoryManager
from backend.writer.quality import check_quality
from backend.writer.characters import check_character_consistency

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)


def write_chapter(
    novel_id: int,
    chapter_number: int,
    volume_number: int = 1,
    db_session=None,
) -> dict:
    """
    写一章小说（使用分层记忆系统）

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        volume_number: 卷号
        db_session: 数据库 session

    Returns:
        写作结果
    """
    from backend.models.novel import Novel
    from backend.models.chapter import Chapter
    from backend.models.outline import Outline

    # 获取小说信息
    novel = db_session.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        return {"error": "小说不存在"}

    # 获取本章大纲
    chapter_outline = (
        db_session.query(Outline)
        .filter(
            Outline.novel_id == novel_id,
            Outline.level == "chapter",
            Outline.chapter_number == chapter_number,
            Outline.volume_number == volume_number,
        )
        .first()
    )

    if not chapter_outline:
        return {"error": f"未找到第 {volume_number} 卷第 {chapter_number} 章的大纲"}

    outline_data = chapter_outline.to_dict()
    word_target = outline_data.get("word_target", config.DEFAULT_CHAPTER_WORDS)

    # ===== 初始化分层记忆系统 =====
    memory = MemoryManager(novel_id=novel_id, db_session=db_session)
    memory.load_from_db()

    # 获取人物设定
    characters = get_characters_for_chapter(novel_id, outline_data, db_session)

    # 构建 prompt（使用记忆系统）
    system_prompt = build_system_prompt(novel.style_guide or "")
    user_prompt = build_user_prompt_with_memory(
        memory=memory,
        chapter_outline=outline_data,
        characters=characters,
        hook_requirement=outline_data.get("hook_plan"),
        word_target=word_target,
    )

    # 调用 AI 生成
    start_time = time.time()
    chapter_text = generate_text(system_prompt, user_prompt, max_tokens=8000)
    generation_time = time.time() - start_time

    if not chapter_text:
        return {"error": "AI 生成失败，返回空内容"}

    # 如果字数不足，尝试续写一次
    current_words = len(chapter_text)
    if current_words < word_target * 0.85:
        remaining_events = outline_data.get("key_events", [])
        continuation = build_continuation_prompt(chapter_text, remaining_events, word_target)
        extra_text = generate_text("", continuation, max_tokens=4000)
        if extra_text:
            chapter_text += "\n" + extra_text

    # 质量检查
    quality_result = check_quality(
        chapter_text=chapter_text,
        word_target=word_target,
        outline_text=outline_data.get("content", ""),
        style_guide=novel.style_guide or "",
        characters=characters,
    )

    # 人物一致性检查
    consistency_result = {}
    if characters:
        consistency_result = check_character_consistency(chapter_text, characters)

    # 自动生成章节摘要（用于记忆系统）
    chapter_summary = generate_chapter_summary(chapter_text)

    # ===== 更新记忆系统 =====
    memory.update_after_chapter(
        chapter_number=chapter_number,
        chapter_text=chapter_text,
        chapter_summary=chapter_summary,
    )

    # 保存故事状态到数据库
    save_story_state(novel_id, memory.story_state, chapter_number, db_session)

    # 保存到数据库
    chapter = Chapter(
        novel_id=novel_id,
        volume_number=volume_number,
        chapter_number=chapter_number,
        title=outline_data.get("title", f"第{chapter_number}章"),
        content=chapter_text,
        word_count=len(chapter_text),
        outline_text=outline_data.get("content", ""),
        chapter_summary=chapter_summary,
        hooks_used=outline_data.get("hook_plan"),
        quality_score=quality_result.get("score", 0),
        quality_issues=quality_result.get("issues", []),
        characters_in_chapter=[c["name"] for c in characters] if characters else [],
        status="completed",
    )
    db_session.add(chapter)

    # 更新小说字数
    from sqlalchemy import func
    total_words = db_session.query(func.sum(Chapter.word_count)).filter(
        Chapter.novel_id == novel_id
    ).scalar() or 0
    novel.current_words = total_words + len(chapter_text)

    db_session.commit()

    return {
        "chapter_id": chapter.id,
        "chapter_number": chapter_number,
        "volume_number": volume_number,
        "title": chapter.title,
        "word_count": chapter.word_count,
        "quality": quality_result,
        "consistency": consistency_result,
        "generation_time": round(generation_time, 1),
        "story_state_updated": True,
        "memory_stats": memory.get_memory_stats(),
    }


def generate_text(system_prompt: str, user_prompt: str, max_tokens: int = 8000) -> str:
    """调用 AI 生成文本"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = client.chat.completions.create(
            model=config.MI_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=max_tokens,
            top_p=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Writer] AI 调用失败: {e}")
        return ""


def generate_chapter_summary(chapter_text: str) -> str:
    """自动生成章节摘要（150 字以内）"""
    try:
        response = client.chat.completions.create(
            model=config.MI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个小说摘要助手。请用 150 字以内概括以下章节的核心剧情。只输出摘要，不要其他内容。",
                },
                {"role": "user", "content": chapter_text[:3000]},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # 降级：截取前 150 字
        return chapter_text[:150] + "..."


def get_characters_for_chapter(
    novel_id: int,
    outline_data: dict,
    db_session,
) -> list[dict]:
    """获取本章出场人物的设定"""
    from backend.models.character import Character

    character_names = outline_data.get("characters", [])
    if not character_names:
        # 如果大纲没有指定人物，获取所有主要人物
        characters = db_session.query(Character).filter(
            Character.novel_id == novel_id,
        ).all()
    else:
        characters = db_session.query(Character).filter(
            Character.novel_id == novel_id,
            Character.name.in_(character_names),
        ).all()

    return [
        {
            "name": c.name,
            "role": c.role or "角色",
            "personality": c.personality or "未知",
            "speaking_style": c.speaking_style or "未知",
            "combat_style": c.combat_style or "无",
            "bottom_line": c.bottom_line or "无",
        }
        for c in characters
    ]


def save_story_state(novel_id: int, story_state, current_chapter: int, db_session):
    """保存故事状态到数据库"""
    from sqlalchemy import text as sql_text

    state_data = json.dumps(story_state.__dict__, ensure_ascii=False)

    existing = db_session.execute(
        sql_text("SELECT id FROM story_state WHERE novel_id = :novel_id"),
        {"novel_id": novel_id},
    ).fetchone()

    if existing:
        db_session.execute(
            sql_text(
                "UPDATE story_state SET world_state = :state, current_chapter = :ch, "
                "updated_at = NOW() WHERE novel_id = :novel_id"
            ),
            {"state": state_data, "ch": current_chapter, "novel_id": novel_id},
        )
    else:
        db_session.execute(
            sql_text(
                "INSERT INTO story_state (novel_id, current_chapter, world_state) "
                "VALUES (:novel_id, :ch, :state)"
            ),
            {"novel_id": novel_id, "ch": current_chapter, "state": state_data},
        )


def batch_write_chapters(
    novel_id: int,
    start_chapter: int,
    end_chapter: int,
    volume_number: int = 1,
    db_session=None,
) -> dict:
    """批量写作多章"""
    results = []
    errors = []

    for ch_num in range(start_chapter, end_chapter + 1):
        try:
            result = write_chapter(
                novel_id=novel_id,
                chapter_number=ch_num,
                volume_number=volume_number,
                db_session=db_session,
            )
            if "error" in result:
                errors.append({"chapter": ch_num, "error": result["error"]})
            else:
                results.append(result)
        except Exception as e:
            errors.append({"chapter": ch_num, "error": str(e)})

    return {
        "total": end_chapter - start_chapter + 1,
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
