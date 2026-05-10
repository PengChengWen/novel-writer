"""
发布器基类
"""

from abc import ABC, abstractmethod
from typing import Optional


class BasePublisher(ABC):
    """发布器基类 — 所有平台发布器都继承此类"""

    platform_name: str = "unknown"

    @abstractmethod
    async def login(self, username: str, password: str) -> bool:
        """
        登录平台

        Args:
            username: 用户名
            password: 密码

        Returns:
            是否登录成功
        """
        pass

    @abstractmethod
    async def create_novel(self, title: str, description: str, genre: str, **kwargs) -> dict:
        """
        在平台上创建小说

        Args:
            title: 小说标题
            description: 简介
            genre: 题材

        Returns:
            创建结果（含平台小说 ID）
        """
        pass

    @abstractmethod
    async def publish_chapter(
        self,
        novel_platform_id: str,
        chapter_number: int,
        chapter_title: str,
        content: str,
    ) -> dict:
        """
        发布章节

        Args:
            novel_platform_id: 平台上的小说 ID
            chapter_number: 章节号
            chapter_title: 章节标题
            content: 章节内容

        Returns:
            发布结果
        """
        pass

    @abstractmethod
    async def close(self):
        """关闭浏览器/连接"""
        pass

    async def batch_publish(
        self,
        novel_platform_id: str,
        chapters: list[dict],
    ) -> dict:
        """
        批量发布章节

        Args:
            novel_platform_id: 平台上的小说 ID
            chapters: 章节列表 [{"chapter_number": 1, "title": "...", "content": "..."}]

        Returns:
            批量发布结果
        """
        results = []
        errors = []

        for ch in chapters:
            try:
                result = await self.publish_chapter(
                    novel_platform_id=novel_platform_id,
                    chapter_number=ch["chapter_number"],
                    chapter_title=ch.get("title", f"第{ch['chapter_number']}章"),
                    content=ch["content"],
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    "chapter_number": ch["chapter_number"],
                    "error": str(e),
                })

        return {
            "total": len(chapters),
            "success": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }
