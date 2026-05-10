"""
大纲生成器 — 根据风格指南 + 用户输入生成三层大纲（总纲→分卷→章节）
"""

import json
import re

from openai import OpenAI

from backend.config import config
from backend.planner.templates import get_genre_template

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)


def generate_master_outline(
    genre: str,
    title: str,
    description: str,
    target_words: int,
    sell_points: list[str],
    style_summary: str = "",
) -> dict:
    """
    生成总纲（第一层大纲）

    Args:
        genre: 题材
        title: 标题
        description: 简介/卖点描述
        target_words: 目标总字数
        sell_points: 卖点列表
        style_summary: 风格总结（可选）

    Returns:
        总纲字典
    """
    template = get_genre_template(genre)
    volume_count = max(3, target_words // 100000)  # 约 10 万字一卷

    prompt = f"""你是一位顶级网络小说策划编辑，请为以下小说生成总纲。

## 基本信息
- 标题：{title}
- 题材：{genre}（{template['name']}）
- 目标字数：{target_words} 字
- 计划卷数：{volume_count} 卷

## 简介/核心设定
{description}

## 卖点
{', '.join(sell_points)}

## 题材参考
- 力量体系：{template['power_system']}
- 世界结构：{template['world_structure']}
- 典型冲突：{', '.join(template['typical_conflicts'])}
- 典型结构：{template['chapter_structure']}

{f"## 风格要求{chr(10)}{style_summary}" if style_summary else ""}

## 输出要求

请生成总纲，包含以下内容（JSON 格式）：

```json
{{
  "core_concept": "一句话概括核心卖点",
  "world_setting": "世界观设定（200字以内）",
  "power_system": "力量体系详细设定",
  "main_character": {{
    "name": "主角名",
    "background": "背景",
    "ability": "能力",
    "personality": "性格",
    "goal": "目标"
  }},
  "main_conflict": "核心矛盾/最终目标",
  "volumes": [
    {{
      "volume_number": 1,
      "title": "卷标题",
      "description": "本卷主线和关键事件（100字以内）",
      "word_target": 目标字数,
      "key_arc": "核心剧情弧"
    }}
  ],
  "ending_type": "结局类型（大圆满/开放式/悲剧等）",
  "selling_points_execution": "卖点如何在剧情中体现"
}}
```

严格输出 JSON，不要添加额外文字。"""

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": "你是顶级网络小说策划编辑，擅长设计引人入胜的剧情大纲。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
    )

    result_text = response.choices[0].message.content.strip()
    try:
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {"error": "JSON 解析失败", "raw": result_text}


def generate_volume_outline(
    master_outline: dict,
    volume_number: int,
    style_guide: str = "",
) -> dict:
    """
    生成分卷大纲（第二层）

    Args:
        master_outline: 总纲
        volume_number: 卷号
        style_guide: 风格指南（可选）

    Returns:
        分卷大纲字典
    """
    volume_info = None
    for v in master_outline.get("volumes", []):
        if v.get("volume_number") == volume_number:
            volume_info = v
            break

    if not volume_info:
        return {"error": f"未找到第 {volume_number} 卷的信息"}

    chapter_count = max(10, volume_info.get("word_target", 100000) // 3000)

    prompt = f"""请为小说的第 {volume_number} 卷生成详细的章节大纲。

## 总纲参考
{json.dumps(master_outline, ensure_ascii=False, indent=2)}

## 本卷信息
- 卷标题：{volume_info.get('title', f'第{volume_number}卷')}
- 本卷描述：{volume_info.get('description', '')}
- 目标字数：{volume_info.get('word_target', 100000)} 字
- 计划章节数：约 {chapter_count} 章

## 输出要求

请生成每章的大纲（JSON 格式）：

```json
{{
  "volume_number": {volume_number},
  "volume_title": "卷标题",
  "chapter_outlines": [
    {{
      "chapter_number": 1,
      "title": "章节标题",
      "summary": "本章剧情概要（50-100字）",
      "key_events": ["事件1", "事件2"],
      "hook_plan": {{
        "has_hook": true/false,
        "hook_type": "打脸/升级/揭秘/危机/感情/装逼",
        "hook_intensity": 1-5
      }},
      "characters": ["出场人物1", "人物2"],
      "word_target": 3000
    }}
  ]
}}
```

## 重要规则
1. 每章必须有明确的剧情推进
2. 爽点分布要合理，不要扎堆也不要太久没有
3. 每 2-3 章至少安排一个爽点
4. 章节结尾要有钩子（让读者想看下一章）
5. 人物出场要自然，不要突然冒出新角色

严格输出 JSON。"""

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": "你是顶级网络小说编辑，擅长设计紧凑有趣的章节大纲。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=6000,
    )

    result_text = response.choices[0].message.content.strip()
    try:
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {"error": "JSON 解析失败", "raw": result_text}
