"""
番茄小说 Playwright 自动化发布器
"""

import asyncio
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page

from backend.publisher.base import BasePublisher


class FanqiePublisher(BasePublisher):
    """番茄小说发布器 — 使用 Playwright 浏览器自动化"""

    platform_name = "fanqie"
    BASE_URL = "https://author.sfacg.com"
    LOGIN_URL = "https://passport.sfacg.com/Login.aspx"

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if not self._playwright:
            self._playwright = await async_playwright().start()
        if not self.browser:
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        if not self.page:
            context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
            )
            self.page = await context.new_page()

    async def login(self, username: str, password: str) -> bool:
        """
        登录番茄小说作者后台

        Args:
            username: 用户名/手机号
            password: 密码

        Returns:
            是否登录成功
        """
        await self._ensure_browser()

        try:
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # 输入用户名
            username_input = self.page.locator('input[name="username"], input[placeholder*="账号"], input[placeholder*="手机"]')
            await username_input.first.fill(username)

            # 输入密码
            password_input = self.page.locator('input[name="password"], input[type="password"]')
            await password_input.first.fill(password)

            # 点击登录按钮
            login_btn = self.page.locator('button[type="submit"], input[type="submit"], .login-btn')
            await login_btn.first.click()

            # 等待登录完成
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(3)

            # 检查是否登录成功（通过 URL 或页面元素判断）
            current_url = self.page.url
            if "login" in current_url.lower():
                # 可能登录失败
                return False

            return True

        except Exception as e:
            print(f"[Fanqie] 登录失败: {e}")
            return False

    async def create_novel(self, title: str, description: str, genre: str, **kwargs) -> dict:
        """
        在番茄小说创建新小说

        Args:
            title: 小说标题
            description: 简介
            genre: 题材
            **kwargs: 其他参数（cover_url 等）

        Returns:
            创建结果
        """
        await self._ensure_browser()

        try:
            # 导航到创建小说页面
            await self.page.goto(f"{self.BASE_URL}/NovelManager/CreateNovel", wait_until="networkidle")
            await asyncio.sleep(2)

            # 填写小说信息
            title_input = self.page.locator('input[name="title"], input[placeholder*="标题"], #novelTitle')
            await title_input.first.fill(title)

            desc_input = self.page.locator('textarea[name="description"], textarea[placeholder*="简介"], #novelDesc')
            await desc_input.first.fill(description)

            # 选择题材
            genre_select = self.page.locator('select[name="genre"], select[name="categoryId"], #genreSelect')
            try:
                await genre_select.first.select_option(label=genre)
            except Exception:
                # 如果下拉框不支持直接选择，尝试点击方式
                await genre_select.first.click()
                await asyncio.sleep(0.5)
                genre_option = self.page.locator(f'text="{genre}"')
                await genre_option.first.click()

            # 提交
            submit_btn = self.page.locator('button[type="submit"], .create-btn, text="创建"')
            await submit_btn.first.click()
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            # 尝试获取创建后的小说 ID
            current_url = self.page.url
            novel_id = current_url.split("/")[-1] if "/" in current_url else "unknown"

            return {
                "success": True,
                "platform_novel_id": novel_id,
                "url": current_url,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def publish_chapter(
        self,
        novel_platform_id: str,
        chapter_number: int,
        chapter_title: str,
        content: str,
    ) -> dict:
        """
        发布章节到番茄小说

        Args:
            novel_platform_id: 平台上的小说 ID
            chapter_number: 章节号
            chapter_title: 章节标题
            content: 章节内容

        Returns:
            发布结果
        """
        await self._ensure_browser()

        try:
            # 导航到章节管理页面
            chapter_url = f"{self.BASE_URL}/NovelManager/ChapterManager/{novel_platform_id}"
            await self.page.goto(chapter_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 点击新建章节
            new_chapter_btn = self.page.locator('text="新建章节", text="添加章节", .new-chapter-btn')
            await new_chapter_btn.first.click()
            await asyncio.sleep(2)

            # 填写章节标题
            title_input = self.page.locator('input[name="title"], input[placeholder*="标题"], #chapterTitle')
            await title_input.first.fill(chapter_title)

            # 填写章节内容
            # 注意：番茄可能使用富文本编辑器
            content_area = self.page.locator('textarea[name="content"], .ql-editor, #chapterContent, [contenteditable="true"]')
            await content_area.first.fill(content)
            await asyncio.sleep(1)

            # 点击发布/保存按钮
            publish_btn = self.page.locator('text="发布", text="保存并发布", .publish-btn, button[type="submit"]')
            await publish_btn.first.click()
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)

            return {
                "success": True,
                "chapter_number": chapter_number,
                "title": chapter_title,
            }

        except Exception as e:
            return {
                "success": False,
                "chapter_number": chapter_number,
                "error": str(e),
            }

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            print(f"[Fanqie] 关闭浏览器时出错: {e}")
