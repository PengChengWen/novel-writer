"""
配置管理 — 从 .env 文件读取所有配置项
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用全局配置"""

    # === 小米大模型 API ===
    MI_API_KEY: str = os.getenv("MI_API_KEY", "")
    MI_BASE_URL: str = os.getenv("MI_BASE_URL", "https://api.example.com/v1")
    MI_MODEL: str = os.getenv("MI_MODEL", "default-model")

    # === MySQL ===
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "novel_writer")

    @property
    def MYSQL_URL(self) -> str:
        """SQLAlchemy 连接 URL"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    # === Redis ===
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    # === 番茄小说 ===
    FANQIE_USERNAME: str = os.getenv("FANQIE_USERNAME", "")
    FANQIE_PASSWORD: str = os.getenv("FANQIE_PASSWORD", "")

    # === 应用配置 ===
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # === 写作默认参数 ===
    DEFAULT_CHAPTER_WORDS: int = 3000  # 默认每章字数
    MAX_CONTEXT_CHAPTERS: int = 5  # 写作时向前回溯的章节数


config = Config()
