"""
质量检查 — 字数、重复、逻辑矛盾、敏感词、风格一致性
"""

import re
from typing import Optional

from openai import OpenAI

from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)

# === 敏感词列表（示例，实际应从配置文件加载）===
SENSITIVE_WORDS = [
    # 政治敏感词（示例）
    # 实际使用时应从外部文件加载完整列表
]


def check_quality(
    chapter_text: str,
    word_target: int = 3000,
    outline_text: str = "",
    style_guide: str = "",
    characters: list[dict] = None,
) -> dict:
    """
    综合质量检查

    Args:
        chapter_text: 章节文本
        word_target: 目标字数
        outline_text: 本章大纲
        style_guide: 风格指南
        characters: 人物设定

    Returns:
        质量检查结果
    """
    issues = []
    score = 100.0

    # 1. 字数检查
    word_count = len(chapter_text)
    word_ratio = word_count / word_target if word_target > 0 else 1
    if word_ratio < 0.85:
        issues.append({
            "type": "字数不足",
            "severity": "high",
            "detail": f"当前 {word_count} 字，目标 {word_target} 字，差距 {word_target - word_count} 字",
        })
        score -= 20
    elif word_ratio > 1.15:
        issues.append({
            "type": "字数过多",
            "severity": "medium",
            "detail": f"当前 {word_count} 字，超出目标 {word_count - word_target} 字",
        })
        score -= 5

    # 2. 重复检查
    repeat_issues = check_repetition(chapter_text)
    if repeat_issues:
        issues.extend(repeat_issues)
        score -= len(repeat_issues) * 5

    # 3. 敏感词检查
    sensitive_issues = check_sensitive_words(chapter_text)
    if sensitive_issues:
        issues.extend(sensitive_issues)
        score -= len(sensitive_issues) * 10

    # 4. 段落结构检查
    structure_issues = check_structure(chapter_text)
    if structure_issues:
        issues.extend(structure_issues)
        score -= len(structure_issues) * 3

    # 5. AI 深度检查（风格一致性 + 逻辑矛盾）
    if style_guide and len(chapter_text) > 500:
        ai_issues = ai_deep_check(chapter_text, outline_text, style_guide, characters or [])
        if ai_issues:
            issues.extend(ai_issues)
            score -= len(ai_issues) * 8

    score = max(0, min(100, score))

    return {
        "score": round(score, 1),
        "word_count": word_count,
        "word_target": word_target,
        "issues": issues,
        "pass": score >= 60,
    }


def check_repetition(text: str) -> list[dict]:
    """
    检查文本中的重复内容

    Args:
        text: 章节文本

    Returns:
        重复问题列表
    """
    issues = []

    # 检查连续重复句子
    sentences = re.split(r"[。！？]", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    for i in range(len(sentences) - 1):
        if sentences[i] and sentences[i] == sentences[i + 1]:
            issues.append({
                "type": "连续重复",
                "severity": "high",
                "detail": f"连续重复句子：「{sentences[i][:50]}...」",
            })

    # 检查高频词组（出现超过 5 次的 4 字以上词组）
    phrases = {}
    for i in range(len(text) - 3):
        for length in [4, 6, 8]:
            if i + length <= len(text):
                phrase = text[i:i + length]
                if not re.search(r"[，。！？\s]", phrase):  # 排除含标点的
                    phrases[phrase] = phrases.get(phrase, 0) + 1

    # 找出高频重复
    for phrase, count in sorted(phrases.items(), key=lambda x: -x[1]):
        if count >= 5 and len(phrase) >= 4:
            issues.append({
                "type": "高频重复",
                "severity": "medium",
                "detail": f"「{phrase}」出现 {count} 次",
            })
            if len(issues) >= 10:  # 最多报 10 个
                break

    return issues[:5]  # 最多返回 5 个


def check_sensitive_words(text: str) -> list[dict]:
    """
    检查敏感词

    Args:
        text: 章节文本

    Returns:
        敏感词问题列表
    """
    issues = []
    for word in SENSITIVE_WORDS:
        count = text.count(word)
        if count > 0:
            issues.append({
                "type": "敏感词",
                "severity": "high",
                "detail": f"包含敏感词「{word}」，出现 {count} 次",
            })
    return issues


def check_structure(text: str) -> list[dict]:
    """
    检查段落结构

    Args:
        text: 章节文本

    Returns:
        结构问题列表
    """
    issues = []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    if not paragraphs:
        issues.append({
            "type": "结构问题",
            "severity": "high",
            "detail": "章节为空或没有有效段落",
        })
        return issues

    # 检查是否有过长段落（超过 500 字没有换行）
    for i, para in enumerate(paragraphs):
        if len(para) > 500:
            issues.append({
                "type": "段落过长",
                "severity": "low",
                "detail": f"第 {i + 1} 段超过 500 字（{len(para)} 字），建议适当分段",
            })

    # 检查是否有过短段落（连续多个 10 字以下段落）
    short_count = sum(1 for p in paragraphs if len(p) < 10)
    if short_count > len(paragraphs) * 0.3 and short_count > 5:
        issues.append({
            "type": "碎片化",
            "severity": "medium",
            "detail": f"过多过短段落（{short_count} 个），文本碎片化严重",
        })

    return issues


def ai_deep_check(
    chapter_text: str,
    outline_text: str,
    style_guide: str,
    characters: list[dict],
) -> list[dict]:
    """
    AI 深度检查：风格一致性 + 逻辑矛盾

    Args:
        chapter_text: 章节文本
        outline_text: 本章大纲
        style_guide: 风格指南
        characters: 人物设定

    Returns:
        问题列表
    """
    chars_info = "\n".join(
        f"- {c['name']}：{c.get('personality', '')}，说话风格：{c.get('speaking_style', '')}"
        for c in characters[:5]  # 最多检查 5 个角色
    )

    prompt = f"""请检查以下小说章节的质量问题。

## 风格指南（摘要）
{style_guide[:1500]}

## 本章大纲
{outline_text}

## 人物设定
{chars_info}

## 章节文本
{chapter_text[:6000]}

## 检查维度
1. **风格一致性** — 是否偏离了风格指南的要求？
2. **逻辑矛盾** — 是否有与前文或大纲矛盾的地方？
3. **人设崩塌** — 角色言行是否与设定一致？
4. **剧情推进** — 是否按大纲推进？是否有偏题？

## 输出格式（JSON）
```json
{{
  "issues": [
    {{
      "type": "风格偏离/逻辑矛盾/人设崩塌/剧情偏题",
      "severity": "high/medium/low",
      "detail": "具体问题描述",
      "text_excerpt": "相关原文（如有）"
    }}
  ]
}}
```

如果没有问题，返回空数组。严格输出 JSON。"""

    try:
        response = client.chat.completions.create(
            model=config.MI_MODEL,
            messages=[
                {"role": "system", "content": "你是一位严格的小说质量审核编辑。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content.strip()
        import json
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("issues", [])
    except Exception:
        pass

    return []
