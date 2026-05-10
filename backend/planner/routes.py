"""
大纲引擎 API 路由
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.novel import Novel
from backend.models.outline import Outline

router = APIRouter()


class GenerateMasterRequest(BaseModel):
    """生成总纲请求"""
    novel_id: int


class GenerateVolumeRequest(BaseModel):
    """生成分卷大纲请求"""
    novel_id: int
    volume_number: int


class CreateNovelRequest(BaseModel):
    """创建新小说（不上传文件，直接填写信息）"""
    title: str
    genre: str = "玄幻"
    description: Optional[str] = None
    target_words: int = 300000
    sell_points: list[str] = []


@router.post("/create")
async def create_novel(req: CreateNovelRequest, db: Session = Depends(get_db)):
    """创建新小说（不上传参考文本，直接进入大纲阶段）"""
    novel = Novel(
        title=req.title,
        genre=req.genre,
        description=req.description or "",
        target_words=req.target_words,
        sell_points=req.sell_points,
        status="planning",
    )
    db.add(novel)
    db.commit()
    db.refresh(novel)

    return {"message": "小说创建成功", "novel": novel.to_dict()}


@router.post("/generate-master")
async def generate_master_outline(req: GenerateMasterRequest, db: Session = Depends(get_db)):
    """生成总纲"""
    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    from backend.planner.generator import generate_master_outline

    # 获取风格总结
    from backend.models.style_profile import StyleProfile
    profile = db.query(StyleProfile).filter(StyleProfile.novel_id == novel.id).first()
    style_summary = profile.style_summary if profile else ""

    result = generate_master_outline(
        genre=novel.genre,
        title=novel.title,
        description=novel.description or "",
        target_words=novel.target_words or 300000,
        sell_points=novel.sell_points or [],
        style_summary=style_summary,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {result.get('raw', result['error'])}")

    # 保存总纲
    outline = Outline(
        novel_id=novel.id,
        level="master",
        title=f"{novel.title} - 总纲",
        content=json.dumps(result, ensure_ascii=False),
        key_events=result.get("volumes", []),
        word_target=novel.target_words,
    )
    db.add(outline)
    novel.status = "outline_master"
    db.commit()

    return {"message": "总纲生成成功", "outline": result}


@router.post("/generate-volume")
async def generate_volume_outline(req: GenerateVolumeRequest, db: Session = Depends(get_db)):
    """生成分卷大纲"""
    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    # 获取总纲
    master = db.query(Outline).filter(
        Outline.novel_id == novel.id,
        Outline.level == "master",
    ).first()
    if not master:
        raise HTTPException(status_code=400, detail="请先生成总纲")

    from backend.planner.generator import generate_volume_outline

    result = generate_volume_outline(
        master_outline=master.content,
        volume_number=req.volume_number,
        style_guide=novel.style_guide or "",
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=f"分卷大纲生成失败: {result.get('raw', result['error'])}")

    # 保存分卷大纲
    volume_outline = Outline(
        novel_id=novel.id,
        level="volume",
        volume_number=req.volume_number,
        title=result.get("volume_title", f"第{req.volume_number}卷"),
        content=json.dumps(result, ensure_ascii=False),
        word_target=sum(
            ch.get("word_target", 3000)
            for ch in result.get("chapter_outlines", [])
        ),
    )
    db.add(volume_outline)

    # 保存每章大纲
    for ch in result.get("chapter_outlines", []):
        chapter_outline = Outline(
            novel_id=novel.id,
            level="chapter",
            volume_number=req.volume_number,
            chapter_number=ch.get("chapter_number"),
            title=ch.get("title", ""),
            content=ch.get("summary", ""),
            key_events=ch.get("key_events", []),
            hook_plan=ch.get("hook_plan"),
            word_target=ch.get("word_target", 3000),
            sort_order=ch.get("chapter_number", 0),
        )
        db.add(chapter_outline)

    novel.status = "outline_done"
    db.commit()

    return {
        "message": f"第 {req.volume_number} 卷大纲生成成功",
        "chapter_count": len(result.get("chapter_outlines", [])),
        "outline": result,
    }


@router.get("/list/{novel_id}")
async def list_outlines(novel_id: int, level: Optional[str] = None, db: Session = Depends(get_db)):
    """获取小说的大纲列表"""
    query = db.query(Outline).filter(Outline.novel_id == novel_id)
    if level:
        query = query.filter(Outline.level == level)
    outlines = query.order_by(Outline.sort_order).all()

    return {
        "novel_id": novel_id,
        "outlines": [o.to_dict() for o in outlines],
    }


@router.get("/genres")
async def list_genres():
    """获取支持的题材列表"""
    from backend.planner.templates import list_genres, GENRE_TEMPLATES

    genres = []
    for key, template in GENRE_TEMPLATES.items():
        genres.append({
            "key": key,
            "name": template["name"],
            "power_system": template["power_system"],
        })
    return {"genres": genres}
