"""
大文本分治处理器 — 解决超长文本（百万字级）的风格分析问题

核心思路：
1. 分块：按章节/段落切分为可处理的小块
2. 并行分析：每块独立提取风格特征
3. 聚合：合并所有块的分析结果为统一风格画像
4. 采样优化：对超大文本智能采样，不牺牲分析质量
"""

import json
import re
import math
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from openai import OpenAI
from backend.config import config

client = OpenAI(api_key=config.MI_API_KEY, base_url=config.MI_BASE_URL)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ChunkInfo:
    """文本块元信息"""
    index: int              # 块序号
    title: str              # 章节标题（如有）
    text: str               # 原文
    char_count: int         # 字数
    start_pos: int          # 在原文中的起始位置
    chapter_num: int = 0    # 章节号


@dataclass
class ChunkAnalysis:
    """单块分析结果"""
    chunk_index: int
    sentence_stats: dict = field(default_factory=dict)
    vocabulary_stats: dict = field(default_factory=dict)
    rhythm_stats: dict = field(default_factory=dict)
    dialogue_stats: dict = field(default_factory=dict)
    hook_candidates: list = field(default_factory=list)
    tone: str = ""
    keywords: list = field(default_factory=list)


@dataclass
class AggregatedResult:
    """聚合后的全局风格画像"""
    total_chars: int = 0
    total_chunks: int = 0
    sampled_chunks: int = 0
    sentence_analysis: dict = field(default_factory=dict)
    vocabulary_analysis: dict = field(default_factory=dict)
    rhythm_analysis: dict = field(default_factory=dict)
    description_analysis: dict = field(default_factory=dict)
    dialogue_analysis: dict = field(default_factory=dict)
    tone_analysis: dict = field(default_factory=dict)
    hook_analysis: dict = field(default_factory=dict)
    style_summary: str = ""
    confidence: float = 0.0  # 分析置信度 0-1


# ============================================================
# 第一步：智能分块
# ============================================================

def split_into_chunks(
    text: str,
    max_chunk_chars: int = 6000,    # 每块最大字数（约2000 tokens）
    min_chunk_chars: int = 500,     # 每块最小字数
    max_chunks: int = 50,           # 最多处理多少块
) -> list[ChunkInfo]:
    """
    智能分块策略：
    1. 优先按章节标题切分
    2. 章节过长则按段落二次切分
    3. 超出 max_chunks 时进行采样
    """
    chunks = []
    
    # 策略1：按章节标题切分
    chapter_pattern = re.compile(
        r'^[　 \t]*'
        r'(?:第[一二三四五六七八九十百千万零\d]+[章节回卷]'
        r'|Chapter\s*\d+'
        r'|CHAPTER\s*\d+)'
        r'[^\n]*',
        re.MULTILINE
    )
    
    chapter_starts = [m.start() for m in chapter_pattern.finditer(text)]
    
    if len(chapter_starts) >= 3:
        # 有明确章节结构
        for i, start in enumerate(chapter_starts):
            end = chapter_starts[i + 1] if i + 1 < len(chapter_starts) else len(text)
            chapter_text = text[start:end].strip()
            
            if len(chapter_text) < min_chunk_chars:
                continue
            
            # 提取章节标题
            title_match = chapter_pattern.match(chapter_text)
            title = title_match.group().strip() if title_match else f"段落{i+1}"
            
            # 章节过长时二次切分
            if len(chapter_text) > max_chunk_chars * 2:
                sub_chunks = _split_by_paragraphs(chapter_text, max_chunk_chars, min_chunk_chars)
                for j, (sub_text, sub_start) in enumerate(sub_chunks):
                    chunks.append(ChunkInfo(
                        index=len(chunks),
                        title=f"{title}（第{j+1}段）",
                        text=sub_text,
                        char_count=len(sub_text),
                        start_pos=start + sub_start,
                        chapter_num=i + 1,
                    ))
            else:
                chunks.append(ChunkInfo(
                    index=len(chunks),
                    title=title,
                    text=chapter_text,
                    char_count=len(chapter_text),
                    start_pos=start,
                    chapter_num=i + 1,
                ))
    else:
        # 无明确章节，按段落切分
        sub_chunks = _split_by_paragraphs(text, max_chunk_chars, min_chunk_chars)
        for j, (sub_text, sub_start) in enumerate(sub_chunks):
            chunks.append(ChunkInfo(
                index=len(chunks),
                title=f"段落{j+1}",
                text=sub_text,
                char_count=len(sub_text),
                start_pos=sub_start,
            ))
    
    # 超出 max_chunks 时智能采样
    if len(chunks) > max_chunks:
        chunks = _sample_chunks(chunks, max_chunks)
    
    return chunks


def _split_by_paragraphs(
    text: str,
    max_chars: int,
    min_chars: int,
) -> list[tuple[str, int]]:
    """按段落切分，合并过短段落"""
    paragraphs = re.split(r'\n{2,}', text)
    result = []
    current = ""
    current_start = 0
    pos = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            pos += len(para) + 2
            continue
        
        if len(current) + len(para) > max_chars and len(current) >= min_chars:
            result.append((current, current_start))
            current = para
            current_start = pos
        else:
            if not current:
                current_start = pos
            current += "\n" + para if current else para
        
        pos += len(para) + 2
    
    if current and len(current) >= min_chars:
        result.append((current, current_start))
    
    return result


def _sample_chunks(chunks: list[ChunkInfo], target_count: int) -> list[ChunkInfo]:
    """
    智能采样：确保覆盖开头、中间、结尾，且均匀分布
    """
    n = len(chunks)
    if n <= target_count:
        return chunks
    
    # 始终包含前3章和最后1章
    must_include = [0, 1, 2, n - 1]
    remaining = [i for i in range(n) if i not in must_include]
    
    # 从剩余中均匀采样
    step = len(remaining) / (target_count - len(must_include))
    sampled_indices = must_include + [remaining[int(i * step)] for i in range(target_count - len(must_include))]
    sampled_indices = sorted(set(sampled_indices))[:target_count]
    
    sampled = [chunks[i] for i in sampled_indices]
    # 重新编号
    for i, chunk in enumerate(sampled):
        chunk.index = i
    
    return sampled


# ============================================================
# 第二步：单块分析（本地统计 + AI 分析）
# ============================================================

def analyze_chunk_local(chunk: ChunkInfo) -> ChunkAnalysis:
    """
    本地快速统计（不调用 AI，秒级完成）
    用于提取可量化的基础特征
    """
    text = chunk.text
    result = ChunkAnalysis(chunk_index=chunk.index)
    
    # 句子统计
    sentences = re.split(r'[。！？…]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]
    
    if sentences:
        lengths = [len(s) for s in sentences]
        result.sentence_stats = {
            "count": len(sentences),
            "avg_length": round(sum(lengths) / len(lengths), 1),
            "short_ratio": round(sum(1 for l in lengths if l <= 15) / len(lengths) * 100, 1),
            "medium_ratio": round(sum(1 for l in lengths if 15 < l <= 40) / len(lengths) * 100, 1),
            "long_ratio": round(sum(1 for l in lengths if l > 40) / len(lengths) * 100, 1),
        }
    
    # 对话统计
    dialogue_matches = re.findall(r'[""「」『』【】][^""「」『』【】]*[""「」『』【】]', text)
    dialogue_chars = sum(len(m) for m in dialogue_matches)
    result.dialogue_stats = {
        "count": len(dialogue_matches),
        "char_ratio": round(dialogue_chars / max(len(text), 1) * 100, 1),
        "avg_length": round(dialogue_chars / max(len(dialogue_matches), 1), 1),
    }
    
    # 段落统计
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    para_lengths = [len(p) for p in paragraphs]
    result.rhythm_stats = {
        "paragraph_count": len(paragraphs),
        "avg_paragraph_length": round(sum(para_lengths) / max(len(para_lengths), 1), 1),
    }
    
    # 关键词提取（高频词）
    # 简单实现：2-4字词频统计
    words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
    word_freq = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:30]
    # 过滤常见停用词
    stopwords = {'一个', '我们', '他们', '这个', '那个', '没有', '不是', '可以', '已经', '什么', '自己', '知道', '时候', '出来', '起来'}
    result.keywords = [(w, c) for w, c in top_words if w not in stopwords][:20]
    
    return result


def analyze_chunk_ai(chunk: ChunkInfo, analysis_type: str = "style") -> ChunkAnalysis:
    """
    AI 深度分析单块文本
    analysis_type: "style" | "hooks"
    """
    result = ChunkAnalysis(chunk_index=chunk.index)
    
    if analysis_type == "style":
        prompt = """分析以下文本的写作风格特征，返回 JSON：
{
  "tone": "整体语气基调（如：轻松幽默/严肃深沉/热血激昂）",
  "narrative_pov": "叙事视角（第一人称/第三人称有限/第三人称全知）",
  "vocabulary_style": "用词风格（口语化/书面化/古风/网络化）",
  "rhetoric": ["使用的主要修辞手法"],
  "sentence_pattern": "句式特点",
  "emotion_flow": "情绪走向（如：平淡→高潮→舒缓）"
}

文本：
"""
    elif analysis_type == "hooks":
        prompt = """分析以下文本中的"爽点"设计，返回 JSON：
{
  "hooks": [
    {
      "type": "爽点类型（打脸/逆袭/升级/揭秘/意外收获/实力碾压）",
      "position": "在文本中的位置百分比",
      "description": "简述这个爽点",
      "intensity": "强度 1-10"
    }
  ],
  "tension_curve": "紧张度曲线描述"
}

文本：
"""
    
    try:
        resp = client.chat.completions.create(
            model=config.MI_MODEL,
            messages=[
                {"role": "system", "content": "你是文学分析专家，只返回 JSON，不要其他内容。"},
                {"role": "user", "content": prompt + chunk.text[:5000]},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        
        content = resp.choices[0].message.content.strip()
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            if analysis_type == "style":
                result.tone = data.get("tone", "")
                result.vocabulary_stats = data
            elif analysis_type == "hooks":
                result.hook_candidates = data.get("hooks", [])
    except Exception as e:
        print(f"[Chunk {chunk.index}] AI分析失败: {e}")
    
    return result


# ============================================================
# 第三步：并行处理
# ============================================================

def process_chunks_parallel(
    chunks: list[ChunkInfo],
    analysis_type: str = "style",
    max_workers: int = 4,
    use_ai: bool = True,
) -> list[ChunkAnalysis]:
    """
    并行处理所有文本块
    
    策略：
    - 本地统计：全部并行，秒级完成
    - AI 分析：并行但限速，避免 API 限流
    """
    results = []
    
    # 第一轮：本地统计（全部并行）
    local_results = []
    for chunk in chunks:
        local_results.append(analyze_chunk_local(chunk))
    
    if not use_ai:
        return local_results
    
    # 第二轮：AI 分析（并行 + 限速）
    ai_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, chunk in enumerate(chunks):
            future = executor.submit(analyze_chunk_ai, chunk, analysis_type)
            futures[future] = i
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                ai_result = future.result()
                ai_results.append((idx, ai_result))
            except Exception as e:
                print(f"[Chunk {idx}] AI分析异常: {e}")
    
    # 合并本地统计和 AI 分析
    ai_map = {idx: r for idx, r in ai_results}
    for i, local in enumerate(local_results):
        ai = ai_map.get(i, ChunkAnalysis(chunk_index=i))
        merged = ChunkAnalysis(
            chunk_index=i,
            sentence_stats=local.sentence_stats,
            vocabulary_stats={**local.vocabulary_stats, **ai.vocabulary_stats},
            rhythm_stats=local.rhythm_stats,
            dialogue_stats=local.dialogue_stats,
            hook_candidates=ai.hook_candidates,
            tone=ai.tone,
            keywords=local.keywords,
        )
        results.append(merged)
    
    return results


# ============================================================
# 第四步：聚合分析结果
# ============================================================

def aggregate_analyses(
    chunks: list[ChunkInfo],
    analyses: list[ChunkAnalysis],
    novel_title: str = "",
) -> AggregatedResult:
    """
    将多个块的分析结果聚合为统一的风格画像
    """
    result = AggregatedResult(
        total_chars=sum(c.char_count for c in chunks),
        total_chunks=len(chunks),
        sampled_chunks=len(chunks),
    )
    
    if not analyses:
        return result
    
    # ---- 句式聚合 ----
    all_sentence_stats = [a.sentence_stats for a in analyses if a.sentence_stats]
    if all_sentence_stats:
        result.sentence_analysis = {
            "avg_sentence_length": round(
                sum(s.get("avg_length", 0) for s in all_sentence_stats) / len(all_sentence_stats), 1
            ),
            "short_sentence_ratio": f"{round(sum(s.get('short_ratio', 0) for s in all_sentence_stats) / len(all_sentence_stats), 1)}%",
            "medium_sentence_ratio": f"{round(sum(s.get('medium_ratio', 0) for s in all_sentence_stats) / len(all_sentence_stats), 1)}%",
            "long_sentence_ratio": f"{round(sum(s.get('long_ratio', 0) for s in all_sentence_stats) / len(all_sentence_stats), 1)}%",
        }
    
    # ---- 对话聚合 ----
    all_dialogue = [a.dialogue_stats for a in analyses if a.dialogue_stats]
    if all_dialogue:
        result.dialogue_analysis = {
            "avg_dialogue_count_per_chunk": round(sum(d.get("count", 0) for d in all_dialogue) / len(all_dialogue), 1),
            "dialogue_char_ratio": f"{round(sum(d.get('char_ratio', 0) for d in all_dialogue) / len(all_dialogue), 1)}%",
            "avg_dialogue_length": round(sum(d.get("avg_length", 0) for d in all_dialogue) / len(all_dialogue), 1),
        }
    
    # ---- 节奏聚合 ----
    all_rhythm = [a.rhythm_stats for a in analyses if a.rhythm_stats]
    if all_rhythm:
        result.rhythm_analysis = {
            "avg_paragraph_length": round(sum(r.get("avg_paragraph_length", 0) for r in all_rhythm) / len(all_rhythm), 1),
            "paragraph_density": "高" if sum(r.get("paragraph_count", 0) for r in all_rhythm) / len(all_rhythm) > 30 else "中",
        }
    
    # ---- 语气聚合 ----
    tones = [a.tone for a in analyses if a.tone]
    if tones:
        tone_freq = {}
        for t in tones:
            tone_freq[t] = tone_freq.get(t, 0) + 1
        dominant_tone = max(tone_freq, key=tone_freq.get)
        result.tone_analysis = {
            "dominant_tone": dominant_tone,
            "tone_variety": len(tone_freq),
            "tone_distribution": tone_freq,
        }
    
    # ---- 关键词聚合 ----
    all_keywords = {}
    for a in analyses:
        for word, count in a.keywords:
            all_keywords[word] = all_keywords.get(word, 0) + count
    top_global = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:30]
    result.vocabulary_analysis = {
        "top_keywords": top_global[:20],
        "vocabulary_richness": len(all_keywords),
    }
    
    # ---- 爽点聚合 ----
    all_hooks = []
    for a in analyses:
        all_hooks.extend(a.hook_candidates)
    if all_hooks:
        hook_types = {}
        for h in all_hooks:
            htype = h.get("type", "未知")
            hook_types[htype] = hook_types.get(htype, 0) + 1
        result.hook_analysis = {
            "total_hooks": len(all_hooks),
            "hook_types": hook_types,
            "avg_intensity": round(
                sum(h.get("intensity", 5) for h in all_hooks) / len(all_hooks), 1
            ),
            "hooks": all_hooks[:10],  # 保留前10个示例
        }
    
    # ---- 置信度计算 ----
    # 基于采样覆盖率和分析一致性
    coverage = min(1.0, len(chunks) / max(result.total_chars / 5000, 1))
    consistency = 1.0  # 可以通过块间差异计算
    result.confidence = round(coverage * consistency * 100, 1)
    
    return result


# ============================================================
# 第五步：生成风格指南（System Prompt）
# ============================================================

def generate_style_guide_from_aggregated(
    agg: AggregatedResult,
    novel_title: str,
    genre: str,
) -> str:
    """
    基于聚合分析结果，生成可直接用作 System Prompt 的风格指南
    """
    prompt = f"""你是一位小说风格模仿专家。请严格模仿以下风格特征来写作。

## 原著风格画像

### 基础信息
- 作品：{novel_title}
- 题材：{genre}
- 总字数：{agg.total_chars:,} 字
- 分析置信度：{agg.confidence}%

### 句式特征
- 平均句长：{agg.sentence_analysis.get('avg_sentence_length', '未知')} 字
- 短句占比：{agg.sentence_analysis.get('short_sentence_ratio', '未知')}
- 中句占比：{agg.sentence_analysis.get('medium_sentence_ratio', '未知')}
- 长句占比：{agg.sentence_analysis.get('long_sentence_ratio', '未知')}

### 对话风格
- 对话占比：{agg.dialogue_analysis.get('dialogue_char_ratio', '未知')}
- 平均对话长度：{agg.dialogue_analysis.get('avg_dialogue_length', '未知')} 字

### 语气基调
- 主要基调：{agg.tone_analysis.get('dominant_tone', '未知')}
- 基调变化：{json.dumps(agg.tone_analysis.get('tone_distribution', {}), ensure_ascii=False)}

### 高频词汇
{', '.join(w for w, _ in agg.vocabulary_analysis.get('top_keywords', [])[:15])}

### 爽点设计
- 爽点类型：{json.dumps(agg.hook_analysis.get('hook_types', {}), ensure_ascii=False)}
- 平均强度：{agg.hook_analysis.get('avg_intensity', '未知')}/10

## 写作要求
1. 严格保持上述句式比例和对话风格
2. 使用相似的高频词汇和用语习惯
3. 保持一致的语气基调
4. 每章至少包含 1-2 个爽点设计
5. 段落长度和节奏感要与原著一致
"""
    
    return prompt


# ============================================================
# 主入口：一键分析
# ============================================================

def analyze_large_text(
    text: str,
    novel_title: str = "",
    genre: str = "",
    max_chunks: int = 30,
    max_workers: int = 3,
    use_ai: bool = True,
) -> dict:
    """
    大文本完整分析流程
    
    Args:
        text: 原文
        novel_title: 书名
        genre: 题材
        max_chunks: 最多分析多少块
        max_workers: AI 并行数
        use_ai: 是否调用 AI（False 则仅本地统计）
    
    Returns:
        完整分析结果字典
    """
    print(f"[大文本分析] 总字数: {len(text):,}, 书名: {novel_title}")
    
    # Step 1: 分块
    chunks = split_into_chunks(text, max_chunks=max_chunks)
    print(f"[分块完成] 共 {len(chunks)} 块, 采样率: {len(chunks)}/{max_chunks}")
    
    # Step 2+3: 并行分析
    analyses = process_chunks_parallel(chunks, max_workers=max_workers, use_ai=use_ai)
    print(f"[分析完成] {len(analyses)} 块已分析")
    
    # Step 4: 聚合
    agg = aggregate_analyses(chunks, analyses, novel_title)
    print(f"[聚合完成] 置信度: {agg.confidence}%")
    
    # Step 5: 生成风格指南
    style_guide = generate_style_guide_from_aggregated(agg, novel_title, genre)
    
    return {
        "total_chars": agg.total_chars,
        "total_chunks": agg.total_chunks,
        "sampled_chunks": agg.sampled_chunks,
        "confidence": agg.confidence,
        "sentence_analysis": agg.sentence_analysis,
        "vocabulary_analysis": agg.vocabulary_analysis,
        "rhythm_analysis": agg.rhythm_analysis,
        "dialogue_analysis": agg.dialogue_analysis,
        "tone_analysis": agg.tone_analysis,
        "hook_analysis": agg.hook_analysis,
        "style_summary": f"本书共{agg.total_chars:,}字，{agg.total_chunks}个分析单元。"
            f"文风{agg.tone_analysis.get('dominant_tone', '中性')}，"
            f"对话占比{agg.dialogue_analysis.get('dialogue_char_ratio', '未知')}，"
            f"爽点密度{agg.hook_analysis.get('total_hooks', 0)}个/{agg.total_chunks}段。",
        "style_guide": style_guide,
    }
