"""
写作异步任务
"""

import json
from backend.celery_app import celery_app
from backend.database import get_session
from backend.writer.engine import write_chapter, batch_write_chapters


@celery_app.task(bind=True, name="tasks.write_chapter")
def write_chapter_task(self, novel_id: int, chapter_number: int, volume_number: int = 1):
    """
    写一章小说（异步）
    """
    db = get_session()
    try:
        from backend.models.novel import Novel

        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"error": "小说不存在"}

        self.update_state(
            state="PROGRESS",
            meta={"step": f"正在写第 {volume_number} 卷第 {chapter_number} 章..."}
        )

        result = write_chapter(
            novel_id=novel_id,
            chapter_number=chapter_number,
            volume_number=volume_number,
            db_session=db,
        )

        # 更新小说字数统计
        if "error" not in result:
            from backend.models.chapter import Chapter
            from sqlalchemy import func
            total_words = db.query(func.sum(Chapter.word_count)).filter(
                Chapter.novel_id == novel_id
            ).scalar() or 0
            novel.current_words = total_words
            db.commit()

        return result

    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=2)

    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.write_novel")
def write_novel_task(self, novel_id: int, start_chapter: int = 1, end_chapter: int = None, volume_number: int = 1):
    """
    批量写小说（从 start_chapter 到 end_chapter）
    """
    db = get_session()
    try:
        from backend.models.novel import Novel
        from backend.models.outline import Outline

        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"error": "小说不存在"}

        # 如果没指定结束章节，取大纲中最大章节号
        if end_chapter is None:
            max_ch = db.query(Outline.chapter_number).filter(
                Outline.novel_id == novel_id,
                Outline.level == "chapter",
            ).order_by(Outline.chapter_number.desc()).first()
            end_chapter = max_ch[0] if max_ch else 1

        # 更新小说状态
        novel.status = "writing"
        db.commit()

        total = end_chapter - start_chapter + 1
        results = []
        errors = []

        for i, ch_num in enumerate(range(start_chapter, end_chapter + 1)):
            self.update_state(
                state="PROGRESS",
                meta={
                    "step": f"写作进度: {i+1}/{total}",
                    "current_chapter": ch_num,
                    "total_chapters": total,
                    "progress": round((i / total) * 100, 1),
                }
            )

            try:
                result = write_chapter(
                    novel_id=novel_id,
                    chapter_number=ch_num,
                    volume_number=volume_number,
                    db_session=db,
                )
                if "error" in result:
                    errors.append({"chapter": ch_num, "error": result["error"]})
                else:
                    results.append(result)

                    # 更新字数
                    from backend.models.chapter import Chapter
                    from sqlalchemy import func
                    total_words = db.query(func.sum(Chapter.word_count)).filter(
                        Chapter.novel_id == novel_id
                    ).scalar() or 0
                    novel.current_words = total_words
                    db.commit()

            except Exception as e:
                errors.append({"chapter": ch_num, "error": str(e)})

        # 更新小说状态
        novel.status = "completed" if not errors else "partially_completed"
        db.commit()

        return {
            "novel_id": novel_id,
            "total": total,
            "success": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    except Exception as e:
        # 回滚状态
        try:
            novel = db.query(Novel).filter(Novel.id == novel_id).first()
            if novel:
                novel.status = "write_failed"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=120, max_retries=1)

    finally:
        db.close()
