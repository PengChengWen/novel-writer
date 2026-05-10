"""
Prompt 构建器 v2 — 集成分层记忆系统

组装 system prompt + 风格指南 + 分层记忆 + 人物设定 + 爽点模板
"""

import json
from typing import Optional

from backend.writer.memory import MemoryManager


def build_system_prompt(style_guide: str, core_rules: str = "") -> str:
    """
    构建 system prompt

    Args:
        style_guide: 风格指南文本
        core_rules: 额外的核心规则

    Returns:
        完整的 system prompt
    """
    default_rules = """## 核心写作规则

1. **严格遵守风格指南** — 每一句话都要符合风格指南中定义的句式、词汇、节奏要求
2. **保持人物一致性** — 每个角色的说话方式、行为模式必须与人设一致
3. **控制节奏** — 紧张和舒缓交替，不要一直平铺直叙
4. **章末留钩** — 每章结尾必须有悬念或引子，让读者想看下一章
5. **字数达标** — 严格按照指定字数写作，误差不超过 10%
6. **禁止说教** — 不要通过旁白或角色之口说大道理
7. **禁止出戏** — 不要出现与小说世界观不符的现代词汇或梗
8. **对话自然** — 对话要符合角色身份和性格，不要千人一面
9. **爽点到位** — 如果大纲要求有爽点，必须写出爽感，不要草草带过
10. **禁止 meta 内容** — 不要出现"作者""读者""系统"等打破第四面墙的内容
11. **连贯性** — 必须承接前文剧情，不能出现前后矛盾
12. **伏笔回收** — 如果本章大纲要求揭示伏笔，必须自然地写出来"""

    rules = core_rules if core_rules else default_rules

    return f"""{style_guide}

{rules}

## 输出要求
- 只输出小说正文，不要输出标题、章节号、作者注等任何非正文内容
- 使用中文写作
- 段落之间用空行分隔
- 对话使用中文引号「」"""


def build_user_prompt_with_memory(
    memory: MemoryManager,
    chapter_outline: dict,
    characters: list[dict],
    hook_requirement: Optional[dict] = None,
    word_target: int = 3000,
) -> str:
    """
    使用分层记忆系统构建用户 prompt

    Args:
        memory: 分层记忆管理器
        chapter_outline: 本章大纲
        characters: 出场人物设定
        hook_requirement: 爽点要求
        word_target: 目标字数

    Returns:
        完整的用户 prompt
    """
    # 从记忆系统获取上下文
    context_text = memory.build_context(
        chapter_outline=chapter_outline,
        hook_requirement=_format_hook(hook_requirement) if hook_requirement else None,
    )

    # 组装人物设定
    char_text = _build_character_text(characters)

    # 爽点要求
    hook_text = _build_hook_text(hook_requirement)

    return f"""{context_text}

## 出场人物
{char_text}
{hook_text}
## 写作要求
- 目标字数：{word_target} 字（误差不超过 10%）
- 严格按大纲推进剧情
- 按照风格指南的写法要求执行
- 章末必须留悬念
- 承接前文，保持连贯

请开始写作："""


def build_user_prompt(
    chapter_outline: dict,
    characters: list[dict],
    story_state: dict,
    previous_summary: str,
    hook_requirement: Optional[dict] = None,
    word_target: int = 3000,
) -> str:
    """
    兼容旧版的用户 prompt 构建（不使用记忆系统）

    Args:
        chapter_outline: 本章大纲
        characters: 出场人物设定
        story_state: 当前故事状态
        previous_summary: 前文摘要
        hook_requirement: 爽点要求
        word_target: 目标字数

    Returns:
        完整的用户 prompt
    """
    char_text = _build_character_text(characters)

    hook_text = _build_hook_text(hook_requirement)

    state_text = ""
    if story_state:
        state_text = f"""
## 当前故事状态
{json.dumps(story_state, ensure_ascii=False, indent=2)}
"""

    return f"""## 前情提要
{previous_summary}

{state_text}
## 本章大纲
- 标题：{chapter_outline.get('title', '未定')}
- 剧情概要：{chapter_outline.get('content', chapter_outline.get('summary', ''))}
- 关键事件：{', '.join(chapter_outline.get('key_events', []))}

## 出场人物
{char_text}
{hook_text}
## 写作要求
- 目标字数：{word_target} 字（误差不超过 10%）
- 严格按大纲推进剧情
- 按照风格指南的写法要求执行
- 章末必须留悬念

请开始写作："""


def build_continuation_prompt(
    partial_text: str,
    remaining_events: list[str],
    word_target: int,
) -> str:
    """
    构建续写 prompt（当生成内容不足时，续写至目标字数）
    """
    current_words = len(partial_text)
    remaining_words = word_target - current_words

    return f"""请继续写作，保持风格一致。

## 已写内容（最后 500 字）
...{partial_text[-500:]}

## 待写内容
{', '.join(remaining_events) if remaining_events else '按大纲继续推进'}

## 续写要求
- 还需要约 {remaining_words} 字
- 保持与前文完全一致的风格和语气
- 自然衔接，不要重复前文内容
- 继续推进剧情

请续写："""


def _build_character_text(characters: list[dict]) -> str:
    """组装人物设定文本"""
    if not characters:
        return "（无特定人物设定要求）"

    char_text = ""
    for char in characters:
        char_text += f"""
### {char['name']}（{char.get('role', '角色')}）
- 性格：{char.get('personality', '未知')}
- 说话风格：{char.get('speaking_style', '未知')}
- 战斗风格：{char.get('combat_style', '无')}
- 人设底线：{char.get('bottom_line', '无')}
"""
    return char_text


def _build_hook_text(hook_requirement: Optional[dict]) -> str:
    """组装爽点要求文本"""
    if not hook_requirement or not hook_requirement.get("has_hook"):
        return ""

    hook_type = hook_requirement.get("hook_type", "")
    hook_intensity = hook_requirement.get("hook_intensity", 3)

    return f"""
## 爽点要求
- 类型：{hook_type}
- 强度：{hook_intensity}/5
- 要求：本章必须包含一个 {hook_type} 爽点，写出爽感，让读者感到畅快。
"""


def _format_hook(hook_requirement: dict) -> str:
    """格式化爽点要求为简短文本"""
    if not hook_requirement or not hook_requirement.get("has_hook"):
        return ""
    return (
        f"类型：{hook_requirement.get('hook_type', '')}，"
        f"强度：{hook_requirement.get('hook_intensity', 3)}/5"
    )
