"""
风格指南生成器 — 根据分析结果生成详细的风格指南（后续写作时作为 system prompt）
"""

import json

from openai import OpenAI

from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)

GUIDE_GENERATION_PROMPT = """你是一位专业的写作教练。你的任务是根据小说风格分析数据，生成一份详细的「风格指南」。

这份风格指南将作为 AI 写作时的 system prompt，指导 AI 模仿原作的文笔风格进行创作。

## 指南要求

风格指南必须包含以下内容：

1. **核心风格定义** — 用 2-3 句话概括这个风格最本质的特征
2. **句式规范** — 具体的句式要求（长短句比例、偏好结构、修辞使用）
3. **词汇规范** — 用词要求（风格倾向、高频词、禁用词、推荐词汇）
4. **节奏规范** — 段落和章节的节奏控制要求
5. **描写规范** — 各类描写的详细程度和手法要求
6. **对话规范** — 对话的写法要求
7. **语气规范** — 叙述视角、基调、情绪控制
8. **爽点规范** — 爽点的写法要求和结构模板
9. **禁忌清单** — 绝对不能出现的写法（与风格不符的表达）

## 输出要求

- 直接输出可以作为 system prompt 的完整文本
- 用中文撰写
- 每条规范都要具体可执行，不要抽象空泛的描述
- 举出具体的例子来说明每条规范
- 整体控制在 2000-3000 字

请直接输出风格指南文本，不要加任何标题或前缀。"""


def generate_style_guide(style_dna: dict, hook_analysis: dict) -> str:
    """
    根据 StyleDNA 和爽点分析结果生成风格指南

    Args:
        style_dna: 风格分析结果（来自 style_parser.analyze_style）
        hook_analysis: 爽点分析结果（来自 hook_parser.analyze_hooks）

    Returns:
        风格指南文本（可直接用作 system prompt）
    """
    analysis_text = f"""
## 风格分析数据 (StyleDNA)

{json.dumps(style_dna, ensure_ascii=False, indent=2)}

## 爽点分析数据

{json.dumps(hook_analysis, ensure_ascii=False, indent=2)}
"""

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": GUIDE_GENERATION_PROMPT},
            {
                "role": "user",
                "content": f"请根据以下分析数据生成风格指南：\n\n{analysis_text}",
            },
        ],
        temperature=0.5,
        max_tokens=4000,
    )

    return response.choices[0].message.content.strip()


def generate_style_guide_from_summary(style_summary: str) -> str:
    """
    根据风格总结文本生成风格指南（简化版，用于快速启动）

    Args:
        style_summary: 风格总结文本

    Returns:
        风格指南文本
    """
    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": GUIDE_GENERATION_PROMPT},
            {
                "role": "user",
                "content": f"请根据以下风格总结生成详细的风格指南：\n\n{style_summary}",
            },
        ],
        temperature=0.5,
        max_tokens=4000,
    )

    return response.choices[0].message.content.strip()
