"""
人物管理 — 人设定义、一致性检查
"""

import json
import re

from openai import OpenAI

from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)


def create_character(
    name: str,
    role: str,
    personality: str,
    speaking_style: str,
    combat_style: str = "",
    appearance: str = "",
    background: str = "",
    bottom_line: str = "",
    relationships: dict = None,
) -> dict:
    """
    创建人物设定

    Args:
        name: 姓名
        role: 角色（主角/配角/反派/龙套）
        personality: 性格描述
        speaking_style: 说话风格
        combat_style: 战斗风格
        appearance: 外貌
        background: 背景故事
        bottom_line: 人设底线
        relationships: 人物关系

    Returns:
        人物设定字典
    """
    return {
        "name": name,
        "role": role,
        "personality": personality,
        "speaking_style": speaking_style,
        "combat_style": combat_style,
        "appearance": appearance,
        "background": background,
        "bottom_line": bottom_line,
        "relationships": relationships or {},
    }


def check_character_consistency(
    chapter_text: str,
    characters: list[dict],
) -> dict:
    """
    检查章节中人物的一致性

    Args:
        chapter_text: 章节文本
        characters: 人物设定列表

    Returns:
        检查结果
    """
    chars_info = "\n".join(
        f"- {c['name']}（{c.get('role', '角色')}）：性格={c.get('personality', '未知')}，"
        f"说话风格={c.get('speaking_style', '未知')}，"
        f"人设底线={c.get('bottom_line', '无')}"
        for c in characters
    )

    prompt = f"""请检查以下小说章节中的人物是否与设定一致。

## 人物设定
{chars_info}

## 章节文本
{chapter_text[:8000]}

## 检查要求
1. 每个出场角色的言行是否符合其性格设定？
2. 说话方式是否与说话风格一致？
3. 是否有人设崩塌（做了底线内绝对不会做的事）？
4. 人物关系是否正确？

## 输出格式（JSON）
```json
{{
  "consistency_score": 0-100,
  "issues": [
    {{
      "character": "角色名",
      "issue_type": "性格崩塌/说话风格不符/人设底线违反/关系错误",
      "description": "具体问题描述",
      "text_excerpt": "相关原文摘录",
      "severity": "high/medium/low"
    }}
  ],
  "summary": "整体一致性评价"
}}
```

严格输出 JSON。"""

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": "你是一位严格的小说编辑，专门检查人物一致性。"},
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
        return {"error": "JSON 解析失败", "raw": result_text, "consistency_score": 0}


def extract_characters_from_text(text: str) -> list[dict]:
    """
    从小说文本中自动提取人物信息

    Args:
        text: 小说文本

    Returns:
        人物列表
    """
    sample = text[:20000]

    prompt = f"""请从小说文本中提取主要人物信息。

## 文本
{sample}

## 输出格式（JSON）
```json
{{
  "characters": [
    {{
      "name": "人物名",
      "role": "主角/配角/反派/龙套",
      "personality": "性格描述",
      "speaking_style": "说话风格描述",
      "combat_style": "战斗风格/能力（如适用）",
      "first_appearance": "首次出场的大致描述"
    }}
  ]
}}
```

只提取出场次数较多的重要角色（最多 10 个）。严格输出 JSON。"""

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": "你是一位小说分析专家，擅长从文本中提取人物信息。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=3000,
    )

    result_text = response.choices[0].message.content.strip()
    try:
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("characters", [])
        return json.loads(result_text).get("characters", [])
    except json.JSONDecodeError:
        return []
