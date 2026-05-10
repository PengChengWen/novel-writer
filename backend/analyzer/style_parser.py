"""
风格解析器 — 分析参考小说的文笔特征，输出 StyleDNA
"""

import json
import re
from typing import Optional

from openai import OpenAI

from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)

# === 风格分析 System Prompt ===
STYLE_ANALYSIS_PROMPT = """你是一位资深的文学评论家和小说分析师。你的任务是深入分析一部小说的写作风格，输出结构化的风格特征数据。

## 分析维度

请从以下 6 个维度全面分析：

### 1. 句式分析 (sentence_analysis)
- 平均句长（字数）
- 短句占比、中句占比、长句占比
- 偏好句式结构（主谓宾/倒装/省略主语等）
- 是否频繁使用排比、对偶等修辞
- 感叹句、反问句的使用频率

### 2. 词汇分析 (vocabulary_analysis)
- 高频词 TOP20（排除常见停用词）
- 用词风格倾向（古风/现代白话/口语化/书面化/网络化）
- 是否使用方言或特殊用语
- 专业领域词汇（如修仙、都市、科幻等术语）
- 四字词语使用频率

### 3. 节奏分析 (rhythm_analysis)
- 段落平均长度
- 场景切换频率（每章平均切换几次）
- 紧张段落与舒缓段落的比例
- 是否有固定的节奏模式（如：铺垫→爆发→喘息）
- 章节结尾风格（悬念/总结/开放式）

### 4. 描写手法 (description_analysis)
- 环境描写的详细程度（极简/适中/详细）
- 人物外貌描写风格（白描/工笔/侧面烘托）
- 动作描写的风格（简洁利落/细节丰富/夸张）
- 心理描写的方式（直接叙述/内心独白/行为暗示）
- 是否常用比喻、拟人等修辞

### 5. 对话风格 (dialogue_analysis)
- 对话在全文中的占比（百分比）
- 对话标记风格（"说"字系/动作穿插/纯对话）
- 角色对话是否有明显的个性化区分
- 是否使用语气词、方言
- 对话的平均长度

### 6. 语气基调 (tone_analysis)
- 整体基调（热血/沉稳/幽默/阴暗/轻松/严肃）
- 叙述视角（第一人称/第三人称有限/第三人称全知）
- 是否有"旁白吐槽"或打破第四面墙的倾向
- 情绪起伏模式（持续高潮型/波浪型/渐进型）

## 输出格式

严格输出 JSON，结构如下：
```json
{
  "sentence_analysis": {
    "avg_sentence_length": 数字,
    "short_sentence_ratio": 百分比,
    "medium_sentence_ratio": 百分比,
    "long_sentence_ratio": 百分比,
    "preferred_structures": ["结构1", "结构2"],
    "rhetoric_frequency": "高/中/低",
    "question_exclamation_ratio": 百分比
  },
  "vocabulary_analysis": {
    "top_words": ["词1", "词2", ...],
    "style_tendency": "古风/现代/口语/书面/网络",
    "four_char_phrases_ratio": 百分比,
    "domain_terms": ["术语1", "术语2", ...],
    "dialect_usage": "描述"
  },
  "rhythm_analysis": {
    "avg_paragraph_length": 数字,
    "scene_switch_frequency": "高/中/低",
    "tension_ratio": 百分比,
    "rhythm_pattern": "描述",
    "chapter_ending_style": "悬念/总结/开放式"
  },
  "description_analysis": {
    "environment_detail_level": "极简/适中/详细",
    "appearance_style": "白描/工笔/侧面烘托",
    "action_style": "简洁利落/细节丰富/夸张",
    "psychology_style": "直接叙述/内心独白/行为暗示",
    "metaphor_frequency": "高/中/低"
  },
  "dialogue_analysis": {
    "dialogue_ratio": 百分比,
    "dialogue_markers": "描述",
    "character_differentiation": true/false,
    "avg_dialogue_length": 数字,
    "tone_words": ["语气词1", "语气词2"]
  },
  "tone_analysis": {
    "overall_tone": "描述",
    "narrative_perspective": "第一人称/第三人称有限/第三人称全知",
    "fourth_wall_breaks": true/false,
    "emotion_pattern": "持续高潮型/波浪型/渐进型"
  },
  "style_summary": "200字以内的风格总结，概括这部小说最核心的文笔特征"
}
```

请严格按照上述 JSON 格式输出，不要添加任何额外说明文字。"""


def analyze_style(text: str) -> dict:
    """
    分析给定文本的文笔风格特征

    Args:
        text: 参考小说文本（最多取前 30000 字进行分析）

    Returns:
        StyleDNA 字典
    """
    # 截取前 30000 字以控制 token 消耗
    sample_text = text[:30000]

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": STYLE_ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": f"请分析以下小说文本的写作风格：\n\n{sample_text}",
            },
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    result_text = response.choices[0].message.content.strip()

    # 尝试提取 JSON
    try:
        # 处理可能被 markdown 包裹的情况
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {"error": "JSON 解析失败", "raw": result_text}


def quick_style_stats(text: str) -> dict:
    """
    快速统计基础文本特征（不调用 AI，纯本地计算）

    Args:
        text: 小说文本

    Returns:
        基础统计信息
    """
    # 去除空白
    clean_text = text.strip()
    total_chars = len(clean_text)

    # 按句号、感叹号、问号分句
    sentences = re.split(r"[。！？!?]+", clean_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    # 平均句长
    avg_sentence_len = total_chars / sentence_count if sentence_count > 0 else 0

    # 短句(<10字)、中句(10-30字)、长句(>30字) 占比
    short = sum(1 for s in sentences if len(s) < 10)
    medium = sum(1 for s in sentences if 10 <= len(s) <= 30)
    long = sum(1 for s in sentences if len(s) > 30)

    # 按段落分割
    paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip()]
    para_count = len(paragraphs)
    avg_para_len = total_chars / para_count if para_count > 0 else 0

    # 对话比例（引号内内容）
    dialogue_chars = sum(len(m) for m in re.findall(r"[""](.*?)[""]", clean_text))
    dialogue_chars += sum(len(m) for m in re.findall(r"「(.*?)」", clean_text))
    dialogue_ratio = dialogue_chars / total_chars if total_chars > 0 else 0

    return {
        "total_chars": total_chars,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "short_sentence_ratio": round(short / sentence_count * 100, 1) if sentence_count else 0,
        "medium_sentence_ratio": round(medium / sentence_count * 100, 1) if sentence_count else 0,
        "long_sentence_ratio": round(long / sentence_count * 100, 1) if sentence_count else 0,
        "paragraph_count": para_count,
        "avg_paragraph_length": round(avg_para_len, 1),
        "dialogue_ratio": round(dialogue_ratio * 100, 1),
    }
