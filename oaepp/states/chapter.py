"""ChapterState — F-S-011 章节内容浏览状态（Reflex 实现）

提供课程列表、章节明细、内容渲染、导航等功能。
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

import reflex as rx

# 确保 backend 包可导入（使 from app.database import db 可用）
_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend")
)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from app.database import db

DOCS_DIR = os.environ.get("DOCS_DIR", "")
_BAKED_DOCS_DIR = Path(__file__).parent.parent.parent / "backend" / "docs_baked"
_HEADING_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)


def _find_docs_dir() -> Path | None:
    if DOCS_DIR:
        candidate = Path(DOCS_DIR)
        if candidate.is_dir() and any(candidate.rglob("*.md")):
            return candidate
    if _BAKED_DOCS_DIR.is_dir() and any(_BAKED_DOCS_DIR.rglob("*.md")):
        return _BAKED_DOCS_DIR
    return None


class ChapterState(rx.State):
    """章节内容浏览状态"""

    # ── 课程列表 ──
    courses: list[dict] = []
    courses_loading: bool = False

    # ── 当前课程 ──
    current_course: Optional[dict] = None
    chapters: list[dict] = []
    chapters_loading: bool = False

    # ── 当前章节 ──
    current_chapter: Optional[dict] = None
    chapter_content_html: str = ""
    chapter_loading: bool = False

    # ── 导航 ──
    prev_chapter: Optional[dict] = None
    next_chapter: Optional[dict] = None

    # ── 资源 ──
    resources: list[dict] = []
    attachments: list[dict] = []
    error_message: str = ""

    # ── 权限 ──
    current_user_id: Optional[str] = None
    is_enrolled: bool = False

    async def load_courses(self):
        """加载所有课程列表（含章节统计）"""
        self.courses_loading = True
        self.courses = []
        try:
            with db() as conn:
                try:
                    rows = conn.execute(
                        "SELECT id, title, semester, total_score, deadline_reminder, is_active "
                        "FROM courses ORDER BY semester"
                    ).fetchall()
                except Exception:
                    self.error_message = "课程表不存在，请先同步章节数据"
                    self.courses_loading = False
                    return

                result = []
                for c in rows:
                    ch_count = conn.execute(
                        "SELECT COUNT(*) FROM chapters WHERE course_id=?", (c["id"],)
                    ).fetchone()[0]
                    done_count = conn.execute(
                        "SELECT COUNT(*) FROM chapters WHERE course_id=? AND status='已完成'",
                        (c["id"],)
                    ).fetchone()[0]
                    result.append({
                        "id": c["id"],
                        "title": c["title"],
                        "semester": c["semester"],
                        "total_score": c["total_score"],
                        "deadline_reminder": c["deadline_reminder"] or "",
                        "is_active": c["is_active"],
                        "total_chapters": ch_count,
                        "completed_chapters": done_count,
                    })
                self.courses = result
        except Exception as e:
            self.error_message = f"加载课程失败: {e}"
        finally:
            self.courses_loading = False

    async def load_chapters(self, course_id: str):
        """加载某课程的所有章节"""
        self.chapters_loading = True
        self.current_course = None
        self.chapters = []
        self.current_chapter = None
        self.chapter_content_html = ""
        try:
            with db() as conn:
                course = conn.execute(
                    "SELECT id, title, semester, total_score, deadline_reminder "
                    "FROM courses WHERE id=?",
                    (course_id,)
                ).fetchone()
                if not course:
                    self.error_message = "课程不存在"
                    self.chapters_loading = False
                    return

                self.current_course = dict(course)
                ch_rows = conn.execute(
                    "SELECT id, course_id, chapter_no, title, filename, chapter_type, "
                    "deadline, status, grading_criteria "
                    "FROM chapters WHERE course_id=? ORDER BY chapter_no",
                    (course_id,)
                ).fetchall()
                self.chapters = [dict(r) for r in ch_rows]
        except Exception as e:
            self.error_message = f"加载章节失败: {e}"
        finally:
            self.chapters_loading = False

    async def load_chapter(self, chapter_id: int):
        """加载指定章节详细信息和内容"""
        self.chapter_loading = True
        self.current_chapter = None
        self.chapter_content_html = ""
        self.prev_chapter = None
        self.next_chapter = None
        self.resources = []
        self.attachments = []

        try:
            with db() as conn:
                # 章节基本信息
                ch = conn.execute(
                    "SELECT id, course_id, chapter_no, title, filename, file_path, "
                    "chapter_type, deadline, status, grading_criteria "
                    "FROM chapters WHERE id=?",
                    (str(chapter_id),)
                ).fetchone()
                if not ch:
                    self.error_message = "章节不存在"
                    self.chapter_loading = False
                    return

                self.current_chapter = dict(ch)

                # 导航（上一章/下一章）
                course_chapters = conn.execute(
                    "SELECT id, chapter_no, title FROM chapters "
                    "WHERE course_id=? ORDER BY chapter_no",
                    (ch["course_id"],)
                ).fetchall()
                for i, c in enumerate(course_chapters):
                    if c["id"] == str(chapter_id) or c["id"] == chapter_id:
                        if i > 0:
                            self.prev_chapter = dict(course_chapters[i - 1])
                        if i < len(course_chapters) - 1:
                            self.next_chapter = dict(course_chapters[i + 1])
                        break

            # 渲染 Markdown 内容
            self._render_chapter_content()

        except Exception as e:
            self.error_message = f"加载章节失败: {e}"
        finally:
            self.chapter_loading = False

    def _render_chapter_content(self):
        """读取并渲染章节 Markdown 内容"""
        if not self.current_chapter:
            return

        docs_dir = _find_docs_dir()
        if not docs_dir:
            self.error_message = "文档目录不可用"
            return

        filename = self.current_chapter.get("filename", "")
        md_path = docs_dir / filename
        if not md_path.exists():
            self.error_message = f"章节文件不存在: {filename}"
            return

        try:
            raw = md_path.read_text(encoding="utf-8")

            # 尝试用 markdown 库渲染；fallback 为纯文本
            try:
                import markdown
                self.chapter_content_html = markdown.markdown(
                    raw, extensions=["fenced_code", "tables", "codehilite"]
                )
            except ImportError:
                self.chapter_content_html = f"<pre>{raw}</pre>"
        except Exception as e:
            self.error_message = f"读取章节文件失败: {e}"

    async def load_chapter_nav(self, chapter_id: int):
        """仅加载章节导航（不重新加载内容）"""
        try:
            with db() as conn:
                ch = conn.execute(
                    "SELECT id, course_id, chapter_no FROM chapters WHERE id=?",
                    (str(chapter_id),)
                ).fetchone()
                if not ch:
                    return
                chapters = conn.execute(
                    "SELECT id, chapter_no, title FROM chapters "
                    "WHERE course_id=? ORDER BY chapter_no",
                    (ch["course_id"],)
                ).fetchall()
                self.prev_chapter = None
                self.next_chapter = None
                for i, c in enumerate(chapters):
                    if c["id"] == str(chapter_id):
                        if i > 0:
                            self.prev_chapter = dict(chapters[i - 1])
                        if i < len(chapters) - 1:
                            self.next_chapter = dict(chapters[i + 1])
                        break
        except Exception as e:
            self.error_message = f"加载导航失败: {e}"

    async def load_resources(self, chapter_id: int):
        """列出章节附件资源"""
        try:
            with db() as conn:
                row = conn.execute(
                    "SELECT filename FROM chapters WHERE id=?",
                    (str(chapter_id),)
                ).fetchone()
                if not row:
                    return

            docs_dir = _find_docs_dir()
            if not docs_dir:
                return

            stem = Path(row["filename"]).stem
            pattern = f"{stem}_*"
            result = []
            for f in sorted(docs_dir.glob(pattern)):
                if f.suffix.lower() in (".md",):
                    continue
                result.append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "suffix": f.suffix.lower(),
                })
            self.resources = result
        except Exception as e:
            self.error_message = f"加载资源失败: {e}"
