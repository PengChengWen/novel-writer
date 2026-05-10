"""
爽点解析器 — 扫描全文识别爽点，提取分布规律和结构模板
"""

import json
import re

from openai import OpenAI

from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)

# === 6 种爽点类型定义 ===
HOOK_TYPES = {
    "slap_face": {
        "name": "打脸",
        "description": "主角被小看/嘲笑/贬低，然后用实力证明自己，打脸对方",
        "structure": "铺垫（被贬低）→ 积蓄（展示实力的伏笔）→ 爆发（展示真正实力）→ 反转（对方震惊/后悔）→ 旁人反应（众人震惊/膜拜）",
    },
    "level_up": {
        "name": "升级",
        "description": "主角突破修为/获得新能力/解锁新技能",
        "structure": "瓶颈（遇到困难）→ 契机（获得机缘/领悟）→ 突破过程（描写突破细节）→ 蜕变（实力飞跃展示）→ 新境界探索",
    },
    "reveal": {
        "name": "揭秘",
        "description": "揭露隐藏的真相/身份/秘密",
        "structure": "悬念铺设（暗示有秘密）→ 线索累积（逐步暗示）→ 揭秘时刻（真相大白）→ 影响（真相带来的冲击）→ 后续影响",
    },
    "crisis": {
        "name": "危机",
        "description": "主角陷入绝境/面临重大威胁",
        "structure": "威胁出现（感知到危险）→ 形势恶化（逐步陷入绝境）→ 绝望时刻（最危险的瞬间）→ 转机（找到出路/获得帮助）→ 化解危机",
    },
    "romance": {
        "name": "感情",
        "description": "感情线的推进/暧昧/告白/重逢",
        "structure": "铺垫（制造相处机会）→ 暧昧（情感升温）→ 关键时刻（告白/误会/分离）→ 情感爆发（确认心意）→ 甜蜜/虐心",
    },
    "show_off": {
        "name": "装逼",
        "description": "主角低调展示碾压级实力/财力/地位",
        "structure": "低调出场（不起眼的表现）→ 别人轻视（不以为然）→ 亮底牌（展示真实实力/地位）→ 反差冲击（众人震惊）→ 后续影响（身份曝光后的连锁反应）",
    },
}

HOOK_ANALYSIS_PROMPT = """你是一位精通网络小说爽点设计的编辑。你的任务是分析一部小说中的"爽点"分布。

## 爽点类型定义

1. **打脸** — 主角被小看/嘲笑，然后用实力证明自己，打脸对方
2. **升级** — 主角突破修为/获得新能力
3. **揭秘** — 揭露隐藏的真相/身份/秘密
4. **危机** — 主角陷入绝境/面临重大威胁
5. **感情** — 感情线推进/暧昧/告白/重逢
6. **装逼** — 低调展示碾压级实力/财力/地位

## 分析要求

1. 扫描全文，识别每个爽点的位置（大约在全文的百分之几处）
2. 对每个爽点，判断其类型、强度（1-5分）、具体情节描述
3. 分析爽点之间的间隔和分布规律
4. 提炼出每种爽点的结构模板（这个作者写该类爽点的固定模式）

## 输出格式

严格输出 JSON：
```json
{
  "hooks": [
    {
      "position": 15.5,
      "type": "打脸",
      "intensity": 4,
      "description": "简要描述这个爽点的情节",
      "structure": "这个爽点的具体结构"
    }
  ],
  "distribution": {
    "total_hooks": 数字,
    "hooks_per_chapter": 平均每章爽点数,
    "avg_interval": "平均每隔X章一个爽点",
    "density_pattern": "前密后疏/均匀分布/波浪分布/集中爆发",
    "chapter_hook_positions": "爽点在章节中的常见位置（开头/中段/结尾）"
  },
  "hook_templates": {
    "打脸": "该作者写打脸爽点的结构模板和特点",
    "升级": "...",
    "揭秘": "...",
    "危机": "...",
    "感情": "...",
    "装逼": "..."
  },
  "style_notes": "关于爽点风格的整体观察（如：爽点密集度高、打脸为主、节奏快等）"
}
```

请严格按照上述 JSON 格式输出，不要添加任何额外说明文字。"""


def analyze_hooks(text: str, chapter_count: int = 0) -> dict:
    """
    分析文本中的爽点

    Args:
        text: 小说文本
        chapter_count: 章节数（用于计算每章爽点密度）

    Returns:
        爽点分析结果
    """
    # 截取前 40000 字以控制 token 消耗
    sample_text = text[:40000]

    user_content = f"请分析以下小说文本中的爽点：\n\n{sample_text}"
    if chapter_count > 0:
        user_content += f"\n\n（提示：这段文本大约包含 {chapter_count} 个章节）"

    response = client.chat.completions.create(
        model=config.MI_MODEL,
        messages=[
            {"role": "system", "content": HOOK_ANALYSIS_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
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


def get_hook_template(hook_type: str) -> dict:
    """
    获取指定爽点类型的标准结构模板

    Args:
        hook_type: 爽点类型名称（中文）

    Returns:
        爽点模板信息
    """
    # 反向查找
    for key, info in HOOK_TYPES.items():
        if info["name"] == hook_type:
            return info
    return {"error": f"未找到类型: {hook_type}"}


def get_all_hook_types() -> list[dict]:
    """获取所有爽点类型定义"""
    return [
        {"key": key, "name": info["name"], "description": info["description"], "structure": info["structure"]}
        for key, info in HOOK_TYPES.items()
    ]
