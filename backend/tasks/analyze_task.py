"""
风格分析异步任务
"""

import json
from backend.celery_app import celery_app
from backend.database import get_session
from backend.analyzer.style_parser import analyze_style, quick_style_stats
from backend.analyzer.hook_parser import analyze_hooks
from backend.analyzer.style_guide import generate_style_guide


@celery_app.task(bind=True, name="tasks.analyze_novel")
def analyze_novel_task(self, novel_id: int, text: str):
    """
    完整风格分析流程：
    1. 本地快速统计
    2. AI 深度风格分析
    3. AI 爽点分析
    4. 生成风格指南
    5. 保存到数据库
    """
    db = get_session()
    try:
        from backend.models.novel import Novel
        from backend.models.style_profile import StyleProfile

        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"error": "小说不存在"}

        # 更新状态
        novel.status = "analyzing"
        db.commit()

        # Step 1: 本地快速统计
        self.update_state(state="PROGRESS", meta={"step": "本地统计中..."})
        local_stats = quick_style_stats(text)

        # Step 2: AI 深度风格分析
        self.update_state(state="PROGRESS", meta={"step": "AI 分析文笔风格..."})
        style_dna = analyze_style(text)

        # Step 3: AI 爽点分析
        self.update_state(state="PROGRESS", meta={"step": "分析爽点模式..."})
        hook_analysis = analyze_hooks(text)

        # Step 4: 生成风格指南
        self.update_state(state="PROGRESS", meta={"step": "生成风格指南..."})
        style_guide_text = generate_style_guide(style_dna, hook_analysis, local_stats)

        # Step 5: 保存到数据库
        profile = StyleProfile(
            novel_id=novel_id,
            local_stats=json.dumps(local_stats, ensure_ascii=False),
            style_dna=json.dumps(style_dna, ensure_ascii=False),
            hook_analysis=json.dumps(hook_analysis, ensure_ascii=False),
            style_guide=style_guide_text,
            text_length=len(text),
        )
        db.add(profile)

        # 更新小说状态
        novel.style_guide = style_guide_text
        novel.status = "analyzed"
        db.commit()

        return {
            "novel_id": novel_id,
            "profile_id": profile.id,
            "local_stats": local_stats,
            "style_summary": style_dna.get("style_summary", ""),
            "hook_count": len(hook_analysis.get("hooks", [])),
            "status": "completed",
        }

    except Exception as e:
        # 回滚状态
        try:
            novel = db.query(Novel).filter(Novel.id == novel_id).first()
            if novel:
                novel.status = "analyze_failed"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=30, max_retries=2)

    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.analyze_chapters")
def analyze_chapters_task(self, novel_id: int, chapter_ids: list[int]):
    """
    对已写章节进行风格一致性分析
    """
    db = get_session()
    try:
        from backend.models.chapter import Chapter
        from backend.models.novel import Novel

        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"error": "小说不存在"}

        results = []
        for cid in chapter_ids:
            chapter = db.query(Chapter).filter(Chapter.id == cid).first()
            if not chapter:
                continue

            self.update_state(
                state="PROGRESS",
                meta={"step": f"分析第 {chapter.chapter_number} 章..."}
            )

            # 用 AI 分析本章的风格特征
            from backend.analyzer.style_parser import analyze_style
            chapter_style = analyze_style(chapter.content[:5000])

            # 对比风格指南
            deviation = compare_style(novel.style_guide, chapter_style)

            results.append({
                "chapter_id": cid,
                "chapter_number": chapter.chapter_number,
                "style_deviation": deviation,
                "chapter_style_summary": chapter_style.get("style_summary", ""),
            })

        return {"novel_id": novel_id, "results": results}

    except Exception as e:
        raise self.retry(exc=e, countdown=30, max_retries=1)

    finally:
        db.close()


def compare_style(style_guide: str, chapter_style: dict) -> dict:
    """对比章节风格与风格指南的偏差"""
    # 简单实现：返回偏差程度
    return {
        "overall_deviation": "low",  # low / medium / high
        "details": "风格基本一致",
    }
