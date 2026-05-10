"""
发布异步任务
"""

import asyncio
from backend.celery_app import celery_app
from backend.database import get_session


@celery_app.task(bind=True, name="tasks.publish_novel")
def publish_novel_task(self, novel_id: int):
    """
    发布整本小说到番茄小说
    """
    db = get_session()
    try:
        from backend.models.novel import Novel
        from backend.models.chapter import Chapter

        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"error": "小说不存在"}

        # 获取所有已完成但未发布的章节
        chapters = (
            db.query(Chapter)
            .filter(
                Chapter.novel_id == novel_id,
                Chapter.status == "completed",
            )
            .order_by(Chapter.chapter_number)
            .all()
        )

        if not chapters:
            return {"error": "没有待发布的章节"}

        novel.status = "publishing"
        db.commit()

        # 初始化发布器
        from backend.publisher.fanqie import FanqiePublisher
        publisher = FanqiePublisher()

        # 运行异步发布
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(publisher.init())

            # 检查登录状态
            self.update_state(state="PROGRESS", meta={"step": "检查番茄小说登录状态..."})
            login_ok = loop.run_until_complete(publisher.check_login())

            if not login_ok:
                # 需要用户手动登录
                novel.status = "publish_need_login"
                db.commit()
                return {
                    "error": "需要手动登录番茄小说",
                    "action": "login_required",
                    "message": "请在服务器上运行登录脚本完成番茄小说登录",
                }

            # 逐章发布
            total = len(chapters)
            published = 0
            failed = []

            for i, chapter in enumerate(chapters):
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "step": f"发布进度: {i+1}/{total}",
                        "current_chapter": chapter.chapter_number,
                        "progress": round((i / total) * 100, 1),
                    }
                )

                try:
                    # 如果是第一章，先确保小说已创建
                    if i == 0 and not novel.fanqie_id:
                        self.update_state(state="PROGRESS", meta={"step": "创建番茄小说..."})
                        fanqie_id = loop.run_until_complete(
                            publisher.create_novel(
                                title=novel.title,
                                synopsis=novel.synopsis or "",
                                genre=novel.genre or "其他",
                            )
                        )
                        novel.fanqie_id = fanqie_id
                        db.commit()

                    # 发布章节
                    result = loop.run_until_complete(
                        publisher.publish_chapter(
                            novel_id=novel.fanqie_id,
                            chapter_title=chapter.title or f"第{chapter.chapter_number}章",
                            chapter_content=chapter.content,
                        )
                    )

                    if result.get("success"):
                        chapter.status = "published"
                        chapter.fanqie_chapter_id = result.get("chapter_id", "")
                        published += 1
                    else:
                        chapter.status = "publish_failed"
                        failed.append({
                            "chapter": chapter.chapter_number,
                            "error": result.get("error", "未知错误"),
                        })

                    db.commit()

                    # 发布间隔，避免风控
                    import time
                    time.sleep(3)

                except Exception as e:
                    chapter.status = "publish_failed"
                    failed.append({"chapter": chapter.chapter_number, "error": str(e)})
                    db.commit()

        finally:
            loop.run_until_complete(publisher.close())
            loop.close()

        # 更新小说状态
        novel.status = "published" if not failed else "partially_published"
        db.commit()

        return {
            "novel_id": novel_id,
            "total_chapters": total,
            "published": published,
            "failed": len(failed),
            "failures": failed,
        }

    except Exception as e:
        try:
            novel = db.query(Novel).filter(Novel.id == novel_id).first()
            if novel:
                novel.status = "publish_failed"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=120, max_retries=2)

    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.publish_chapters")
def publish_chapters_task(self, novel_id: int, chapter_ids: list[int]):
    """
    发布指定章节到番茄小说
    """
    db = get_session()
    try:
        from backend.models.novel import Novel
        from backend.models.chapter import Chapter
        from backend.publisher.fanqie import FanqiePublisher
        import asyncio

        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"error": "小说不存在"}

        chapters = (
            db.query(Chapter)
            .filter(Chapter.id.in_(chapter_ids))
            .order_by(Chapter.chapter_number)
            .all()
        )

        publisher = FanqiePublisher()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        results = []
        try:
            loop.run_until_complete(publisher.init())

            for chapter in chapters:
                self.update_state(
                    state="PROGRESS",
                    meta={"step": f"发布第 {chapter.chapter_number} 章..."}
                )

                try:
                    result = loop.run_until_complete(
                        publisher.publish_chapter(
                            novel_id=novel.fanqie_id,
                            chapter_title=chapter.title or f"第{chapter.chapter_number}章",
                            chapter_content=chapter.content,
                        )
                    )
                    results.append({
                        "chapter_id": chapter.id,
                        "chapter_number": chapter.chapter_number,
                        "success": result.get("success", False),
                        "error": result.get("error"),
                    })
                    import time
                    time.sleep(3)
                except Exception as e:
                    results.append({
                        "chapter_id": chapter.id,
                        "chapter_number": chapter.chapter_number,
                        "success": False,
                        "error": str(e),
                    })
        finally:
            loop.run_until_complete(publisher.close())
            loop.close()

        return {"novel_id": novel_id, "results": results}

    finally:
        db.close()
