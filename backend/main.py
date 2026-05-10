"""
FastAPI 入口 — 小说风格模仿引擎
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import config
from backend.database import init_db, _ensure_story_state_table


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    print("[APP] 正在初始化数据库...")
    init_db()
    _ensure_story_state_table()
    print("[APP] 初始化完成")
    yield
    print("[APP] 关闭中...")


app = FastAPI(
    title="小说风格模仿引擎",
    description="上传参考小说 → 分析风格 → 自动生成同风格小说",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from backend.analyzer.routes import router as analyzer_router
from backend.planner.routes import router as planner_router
from backend.writer.routes import router as writer_router
from backend.publisher.routes import router as publisher_router

app.include_router(analyzer_router, prefix="/api/analyzer", tags=["风格分析"])
app.include_router(planner_router, prefix="/api/planner", tags=["大纲引擎"])
app.include_router(writer_router, prefix="/api/writer", tags=["写作引擎"])
app.include_router(publisher_router, prefix="/api/publisher", tags=["发布引擎"])


@app.get("/")
async def root():
    return {
        "name": "小说风格模仿引擎",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.APP_DEBUG,
    )
