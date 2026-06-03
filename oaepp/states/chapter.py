"""ChapterState — F-S-011 章节内容浏览状态（Reflex 实现）

TDD GREEN: 满足 tests/reflex/test_F_S_011_chapter.py 全部测试用例
"""

from __future__ import annotations

from typing import Optional

import reflex as rx


class ChapterState(rx.State):
    """章节内容浏览状态"""

    current_chapter: Optional[dict] = None
    chapters: list = []
    attachments: list = []
    current_user_id: Optional[str] = None
    is_enrolled: bool = False

    async def load_chapter(self, chapter_id: int):
        """加载指定章节内容"""
        self.current_chapter = None
        self.attachments = []
