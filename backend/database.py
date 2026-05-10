"""
数据库连接 + 建表
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import config

# 创建引擎
engine = create_engine(
    config.MYSQL_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=config.APP_DEBUG,
)

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Celery 任务用：获取数据库 session（非生成器）"""
    return SessionLocal()


def init_db():
    """
    初始化数据库：创建数据库（如果不存在）+ 建表
    """
    # 先确保数据库存在
    import pymysql

    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    # 导入所有模型以注册到 Base.metadata
    from backend.models import novel, chapter, outline, style_profile, character  # noqa: F401

    # 建表
    Base.metadata.create_all(bind=engine)
    print("[DB] 所有表已创建/更新完毕")


def _ensure_story_state_table():
    """确保 story_state 表存在（不在 models 中定义，直接 SQL 创建）"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS story_state (
                id INT AUTO_INCREMENT PRIMARY KEY,
                novel_id INT NOT NULL,
                current_chapter INT DEFAULT 0,
                world_state JSON,
                active_plotlines JSON,
                pending_hooks JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
                INDEX idx_novel (novel_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS publish_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                novel_id INT NOT NULL,
                chapter_id INT,
                platform VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                platform_chapter_id VARCHAR(100),
                error_message TEXT,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
                INDEX idx_novel (novel_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        conn.commit()
