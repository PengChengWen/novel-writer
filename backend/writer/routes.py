"""
写作引擎 API 路由
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.novel import Novel
from backend.models.chapter import Chapter
from backend.models.character import Character
from backend.models.outline import Outline

router = APIRouter()


class WriteChapterRequest(BaseModel):
    """写作单章请求"""
    novel_id: int
    chapter_number: int
    volume_number: int = 1


class BatchWriteRequest(BaseModel):
    """批量写作请求"""
    novel_id: int
    start_chapter: int
    end_chapter: int
    volume_number: int = 1


class CreateCharacterRequest(BaseModel):
    """创建人物请求"""
    novel_id: int
    name: str
    role: str = "配角"
    personality: str = ""
    speaking_style: str = ""
    combat_style: str = ""
    appearance: str = ""
    background: str = ""
    bottom_line: str = ""
    relationships: Optional[dict] = None


class UpdateCharacterRequest(BaseModel):
    """更新人物请求"""
    personality: Optional[str] = None
    speaking_style: Optional[str] = None
    combat_style: Optional[str] = None
    appearance: Optional[str] = None
    background: Optional[str] = None
    bottom_line: Optional[str] = None
    relationships: Optional[dict] = None
    status: Optional[str] = None


@router.post("/write-chapter")
async def write_chapter(req: WriteChapterRequest, db: Session = Depends(get_db)):
    """写一章小说（同步）"""
    from backend.writer.engine import write_chapter as do_write

    result = do_write(
        novel_id=req.novel_id,
        chapter_number=req.chapter_number,
        volume_number=req.volume_number,
        db_session=db,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {"message": "章节写作完成", **result}


@router.post("/write-chapter-async")
async def write_chapter_async(req: WriteChapterRequest, db: Session = Depends(get_db)):
    """写一章小说（异步任务）"""
    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    from backend.tasks.write_task import write_chapter_task

    task = write_chapter_task.delay(
        novel_id=req.novel_id,
        chapter_number=req.chapter_number,
        volume_number=req.volume_number,
    )

    return {
        "message": "写作任务已提交",
        "task_id": task.id,
        "novel_id": req.novel_id,
        "chapter_number": req.chapter_number,
    }


@router.post("/batch-write")
async def batch_write(req: BatchWriteRequest, db: Session = Depends(get_db)):
    """批量写作多章（异步任务）"""
    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    from backend.tasks.write_task import batch_write_task

    task = batch_write_task.delay(
        novel_id=req.novel_id,
        start_chapter=req.start_chapter,
        end_chapter=req.end_chapter,
        volume_number=req.volume_number,
    )

    return {
        "message": f"批量写作任务已提交（第 {req.start_chapter}-{req.end_chapter} 章）",
        "task_id": task.id,
    }


@router.get("/chapters/{novel_id}")
async def list_chapters(
    novel_id: int,
    volume_number: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取章节列表"""
    query = db.query(Chapter).filter(Chapter.novel_id == novel_id)
    if volume_number is not None:
        query = query.filter(Chapter.volume_number == volume_number)
    chapters = query.order_by(Chapter.chapter_number).all()

    return {
        "novel_id": novel_id,
        "chapters": [c.to_dict() for c in chapters],
        "total": len(chapters),
    }


@router.get("/chapter/{chapter_id}")
async def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """获取单个章节详情"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return {"chapter": chapter.to_dict()}


# === 人物管理 ===

@router.post("/characters")
async def create_character(req: CreateCharacterRequest, db: Session = Depends(get_db)):
    """创建人物"""
    novel = db.query(Novel).filter(Novel.id == req.novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    character = Character(
        novel_id=req.novel_id,
        name=req.name,
        role=req.role,
        personality=req.personality,
        speaking_style=req.speaking_style,
        combat_style=req.combat_style,
        appearance=req.appearance,
        background=req.background,
        bottom_line=req.bottom_line,
        relationships=req.relationships,
    )
    db.add(character)
    db.commit()
    db.refresh(character)

    return {"message": "人物创建成功", "character": character.to_dict()}


@router.get("/characters/{novel_id}")
async def list_characters(novel_id: int, db: Session = Depends(get_db)):
    """获取人物列表"""
    characters = db.query(Character).filter(Character.novel_id == novel_id).all()
    return {
        "novel_id": novel_id,
        "characters": [c.to_dict() for c in characters],
    }


@router.put("/characters/{character_id}")
async def update_character(character_id: int, req: UpdateCharacterRequest, db: Session = Depends(get_db)):
    """更新人物"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="人物不存在")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(character, field, value)

    db.commit()
    db.refresh(character)

    return {"message": "人物更新成功", "character": character.to_dict()}


@router.post("/extract-characters/{novel_id}")
async def extract_characters(novel_id: int, db: Session = Depends(get_db)):
    """从小说文本中自动提取人物"""
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel or not novel.reference_text:
        raise HTTPException(status_code=400, detail="小说没有参考文本")

    from backend.writer.characters import extract_characters_from_text

    characters = extract_characters_from_text(novel.reference_text)

    # 保存到数据库
    saved = []
    for char_data in characters:
        character = Character(
            novel_id=novel_id,
            name=char_data.get("name", ""),
            role=char_data.get("role", "配角"),
            personality=char_data.get("personality", ""),
            speaking_style=char_data.get("speaking_style", ""),
            combat_style=char_data.get("combat_style", ""),
        )
        db.add(character)
        saved.append(char_data.get("name", ""))

    db.commit()

    return {"message": f"提取了 {len(saved)} 个人物", "characters": characters}


@router.post("/check-consistency")
async def check_consistency(chapter_id: int, db: Session = Depends(get_db)):
    """检查章节的人物一致性"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    characters = db.query(Character).filter(
        Character.novel_id == chapter.novel_id,
        Character.status == "active",
    ).all()

    from backend.writer.characters import check_character_consistency

    result = check_character_consistency(
        chapter.content,
        [c.to_dict() for c in characters],
    )

    return {"chapter_id": chapter_id, "consistency": result}
