"""
分析器 API 路由
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.novel import Novel
from backend.models.style_profile import StyleProfile

router = APIRouter()


@router.get("/novels")
async def list_novels(db: Session = Depends(get_db)):
    """获取所有小说列表"""
    novels = db.query(Novel).order_by(Novel.created_at.desc()).all()
    return [n.to_dict() for n in novels]


@router.get("/novel/{novel_id}")
async def get_novel(novel_id: int, db: Session = Depends(get_db)):
    """获取单个小说详情"""
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    return novel.to_dict()


@router.post("/create")
async def create_novel(
    title: str = Form(...),
    genre: str = Form("玄幻"),
    description: Optional[str] = Form(None),
    target_words: int = Form(300000),
    db: Session = Depends(get_db),
):
    """
    创建小说记录（不包含文件上传）
    """
    novel = Novel(
        title=title,
        genre=genre,
        description=description or "",
        target_words=target_words,
        status="draft",
    )
    db.add(novel)
    db.commit()
    db.refresh(novel)

    # 创建对应的风格档案
    profile = StyleProfile(novel_id=novel.id, status="pending")
    db.add(profile)
    db.commit()

    return {
        "message": "创建成功",
        "novel_id": novel.id,
        "novel": novel.to_dict(),
    }


@router.post("/upload")
async def upload_novel(
    file: UploadFile = File(...),
    title: str = Form(...),
    genre: str = Form("玄幻"),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    上传参考小说文本文件（.txt）

    Args:
        file: 小说文本文件
        title: 小说标题
        genre: 题材类型
        description: 简介
    """
    # 读取文件内容
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("gbk")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8 或 GBK 编码")

    if len(text) < 100:
        raise HTTPException(status_code=400, detail="文本内容过少，至少需要 100 字")

    # 创建小说记录
    novel = Novel(
        title=title,
        genre=genre,
        description=description or "",
        reference_text=text,
        status="uploaded",
    )
    db.add(novel)
    db.commit()
    db.refresh(novel)

    # 创建对应的风格档案
    profile = StyleProfile(novel_id=novel.id, status="pending")
    db.add(profile)
    db.commit()

    return {
        "message": "上传成功",
        "novel_id": novel.id,
        "text_length": len(text),
        "novel": novel.to_dict(),
    }


@router.post("/upload-text/{novel_id}")
async def upload_text(
    novel_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    向已有小说上传参考文本
    """
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    if len(text) < 100:
        raise HTTPException(status_code=400, detail="文本内容过少，至少需要 100 字")

    novel.reference_text = text
    novel.status = "uploaded"
    db.commit()

    return {
        "message": "文本上传成功",
        "novel_id": novel.id,
        "text_length": len(text),
    }


@router.post("/analyze/{novel_id}")
async def trigger_analysis(novel_id: int, db: Session = Depends(get_db)):
    """
    触发风格分析（异步任务）

    提交到 Celery 后台执行，返回任务 ID
    """
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    if not novel.reference_text:
        raise HTTPException(status_code=400, detail="该小说没有上传参考文本")

    # 更新状态
    novel.status = "analyzing"
    db.commit()

    profile = db.query(StyleProfile).filter(StyleProfile.novel_id == novel_id).first()
    if profile:
        profile.status = "analyzing"
        db.commit()

    # 提交异步任务
    from backend.tasks.analyze_task import analyze_novel_task

    task = analyze_novel_task.delay(novel_id)

    return {
        "message": "风格分析已提交",
        "task_id": task.id,
        "novel_id": novel_id,
    }


@router.post("/analyze-sync/{novel_id}")
async def trigger_analysis_sync(novel_id: int, db: Session = Depends(get_db)):
    """
    同步执行风格分析（用于调试，不推荐生产使用）
    """
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    if not novel.reference_text:
        raise HTTPException(status_code=400, detail="该小说没有上传参考文本")

    from backend.analyzer.style_parser import analyze_style, quick_style_stats
    from backend.analyzer.hook_parser import analyze_hooks
    from backend.analyzer.style_guide import generate_style_guide

    text = novel.reference_text

    # 1. 基础统计
    stats = quick_style_stats(text)

    # 2. AI 风格分析
    style_dna = analyze_style(text)

    # 3. 爽点分析
    hook_result = analyze_hooks(text)

    # 4. 生成风格指南
    style_guide = generate_style_guide(style_dna, hook_result)

    # 5. 保存结果
    profile = db.query(StyleProfile).filter(StyleProfile.novel_id == novel_id).first()
    if not profile:
        profile = StyleProfile(novel_id=novel_id)
        db.add(profile)

    profile.sentence_analysis = style_dna.get("sentence_analysis")
    profile.vocabulary_analysis = style_dna.get("vocabulary_analysis")
    profile.rhythm_analysis = style_dna.get("rhythm_analysis")
    profile.description_analysis = style_dna.get("description_analysis")
    profile.dialogue_analysis = style_dna.get("dialogue_analysis")
    profile.tone_analysis = style_dna.get("tone_analysis")
    profile.hook_analysis = hook_result.get("hooks")
    profile.hook_distribution = hook_result.get("distribution")
    profile.hook_templates = hook_result.get("hook_templates")
    profile.style_summary = style_dna.get("style_summary", "")
    profile.raw_analysis = {"style_dna": style_dna, "hook_result": hook_result, "stats": stats}
    profile.status = "completed"

    # 更新小说状态和风格指南
    novel.style_guide = style_guide
    novel.status = "analyzed"
    db.commit()

    return {
        "message": "风格分析完成",
        "novel_id": novel_id,
        "stats": stats,
        "style_summary": style_dna.get("style_summary", ""),
        "style_guide": style_guide,
    }


@router.get("/result/{novel_id}")
async def get_analysis_result(novel_id: int, db: Session = Depends(get_db)):
    """获取风格分析结果"""
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    profile = db.query(StyleProfile).filter(StyleProfile.novel_id == novel_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="风格档案不存在")

    return {
        "novel_id": novel_id,
        "status": profile.status,
        "profile": profile.to_dict(),
        "style_guide": novel.style_guide,
    }


@router.get("/hook-types")
async def list_hook_types():
    """获取所有爽点类型定义"""
    from backend.analyzer.hook_parser import get_all_hook_types

    return {"hook_types": get_all_hook_types()}
