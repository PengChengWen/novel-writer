"""
发布引擎 API 路由
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.novel import Novel
from backend.models.chapter import Chapter

router = APIRouter()


class PublishChapterRequest(BaseModel):
    """发布章节请求"""
    novel_id: int
    chapter_id: Optional[int] = None  # 不指定则发布所有未发布章节
    platform: str = "fanqie"


class PublishAllRequest(BaseModel):
    """批量发布请求"""
    novel_id: int
    platform: str = "fanqie"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None


@router.post("/publish-chapter")
async def publish_chapter(req: PublishChapterRequest, db: Session = Depends(get_db)):
    """发布单个章节"""
    from backend.config import config

    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    if req.platform != "fanqie":
        raise HTTPException(status_code=400, detail=f"不支持的平台: {req.platform}")

    if not config.FANQIE_USERNAME or not config.FANQIE_PASSWORD:
        raise HTTPException(status_code=400, detail="番茄小说账号未配置（请设置 FANQIE_USERNAME 和 FANQIE_PASSWORD）")

    # 获取要发布的章节
    if req.chapter_id:
        chapter = db.query(Chapter).filter(Chapter.id == req.chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")
    else:
        # 发布第一个未发布的章节
        chapter = (
            db.query(Chapter)
            .filter(Chapter.novel_id == req.novel_id, Chapter.status != "published")
            .order_by(Chapter.chapter_number)
            .first()
        )
        if not chapter:
            raise HTTPException(status_code=400, detail="没有待发布的章节")

    # 异步发布
    from backend.publisher.fanqie import FanqiePublisher

    publisher = FanqiePublisher()
    try:
        # 登录
        login_ok = await publisher.login(config.FANQIE_USERNAME, config.FANQIE_PASSWORD)
        if not login_ok:
            raise HTTPException(status_code=401, detail="番茄小说登录失败")

        # 发布
        result = await publisher.publish_chapter(
            novel_platform_id=str(req.novel_id),
            chapter_number=chapter.chapter_number,
            chapter_title=chapter.title or f"第{chapter.chapter_number}章",
            content=chapter.content or "",
        )

        if result.get("success"):
            chapter.status = "published"
            db.commit()

        return {"message": "发布完成", "result": result}

    finally:
        await publisher.close()


@router.post("/publish-batch")
async def publish_batch(req: PublishAllRequest, db: Session = Depends(get_db)):
    """批量发布章节"""
    from backend.config import config
    from backend.tasks.publish_task import batch_publish_task

    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    if not config.FANQIE_USERNAME or not config.FANQIE_PASSWORD:
        raise HTTPException(status_code=400, detail="番茄小说账号未配置")

    task = batch_publish_task.delay(
        novel_id=req.novel_id,
        platform=req.platform,
        start_chapter=req.start_chapter,
        end_chapter=req.end_chapter,
    )

    return {
        "message": "批量发布任务已提交",
        "task_id": task.id,
    }


@router.get("/publish-logs/{novel_id}")
async def get_publish_logs(novel_id: int, db: Session = Depends(get_db)):
    """获取发布日志"""
    from sqlalchemy import text

    result = db.execute(
        text("SELECT * FROM publish_logs WHERE novel_id = :novel_id ORDER BY published_at DESC LIMIT 50"),
        {"novel_id": novel_id},
    ).fetchall()

    logs = []
    for row in result:
        logs.append({
            "id": row[0],
            "novel_id": row[1],
            "chapter_id": row[2],
            "platform": row[3],
            "status": row[4],
            "platform_chapter_id": row[5],
            "error_message": row[6],
            "published_at": str(row[7]) if row[7] else None,
        })

    return {"novel_id": novel_id, "logs": logs}
