"""
chapters.py — 课程与章节 API（F-S-011 章节内容浏览）
"""

import os
import re
import markdown
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.database import db

router = APIRouter()

DOCS_DIR = os.environ.get("DOCS_DIR", "")
_BAKED_DOCS_DIR = Path(__file__).parent.parent / "docs_baked"


def _find_docs_dir() -> Path | None:
    if DOCS_DIR:
        candidate = Path(DOCS_DIR)
        if candidate.is_dir() and any(candidate.rglob("*.md")):
            return candidate
    if _BAKED_DOCS_DIR.is_dir() and any(_BAKED_DOCS_DIR.rglob("*.md")):
        return _BAKED_DOCS_DIR
    return None


@router.get("/api/courses")
def list_courses():
    """获取所有课程列表（含章节统计）"""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, semester, total_score, deadline_reminder, is_active FROM courses ORDER BY semester"
        ).fetchall()
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
    return result


@router.get("/api/courses/{course_id}/chapters")
def list_chapters(course_id: str):
    """获取某课程的所有章节明细"""
    with db() as conn:
        course = conn.execute(
            "SELECT id, title, semester, total_score, deadline_reminder FROM courses WHERE id=?", (course_id,)
        ).fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        chapters = conn.execute(
            """SELECT id, course_id, chapter_no, title, filename, chapter_type,
                      deadline, status, grading_criteria
               FROM chapters WHERE course_id=? ORDER BY chapter_no""",
            (course_id,)
        ).fetchall()
    return {"course": dict(course), "chapters": [dict(c) for c in chapters]}


@router.get("/api/chapters/{chapter_id}")
def get_chapter(chapter_id: str):
    """获取单个章节详细信息"""
    with db() as conn:
        ch = conn.execute(
            """SELECT id, course_id, chapter_no, title, filename, file_path,
                      chapter_type, deadline, status, grading_criteria
               FROM chapters WHERE id=?""",
            (chapter_id,)
        ).fetchone()
        if not ch:
            raise HTTPException(status_code=404, detail="章节不存在")
    return dict(ch)


@router.get("/api/chapters/{chapter_id}/nav")
def chapter_nav(chapter_id: str):
    """获取章节的上下导航（上一章/下一章）"""
    with db() as conn:
        ch = conn.execute(
            "SELECT id, course_id, chapter_no FROM chapters WHERE id=?", (chapter_id,)
        ).fetchone()
        if not ch:
            raise HTTPException(status_code=404, detail="章节不存在")

        chapters = conn.execute(
            "SELECT id, chapter_no, title FROM chapters WHERE course_id=? ORDER BY chapter_no",
            (ch["course_id"],)
        ).fetchall()

    prev_ch = None
    next_ch = None
    for i, c in enumerate(chapters):
        if c["id"] == chapter_id:
            if i > 0:
                prev_ch = dict(chapters[i - 1])
            if i < len(chapters) - 1:
                next_ch = dict(chapters[i + 1])
            break

    return {"prev": prev_ch, "next": next_ch}


@router.get("/api/chapters/{chapter_id}/content")
def chapter_content(chapter_id: str):
    """获取章节的 Markdown 内容并渲染为 HTML"""
    with db() as conn:
        ch = conn.execute(
            "SELECT id, course_id, chapter_no, title, filename, file_path, chapter_type, grading_criteria FROM chapters WHERE id=?",
            (chapter_id,)
        ).fetchone()
        if not ch:
            raise HTTPException(status_code=404, detail="章节不存在")

    docs_dir = _find_docs_dir()
    if not docs_dir:
        raise HTTPException(status_code=500, detail="文档目录不可用")

    md_path = docs_dir / ch["filename"]
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="章节文件不存在")

    raw = md_path.read_text(encoding="utf-8")
    html_content = markdown.markdown(raw, extensions=["fenced_code", "tables", "codehilite"])

    # 提取章节简介：第一个 `---` 前的文本（去除标题行），转为纯文本预览
    raw_intro = raw
    hr_pos = raw.find("\n---\n")
    if hr_pos != -1:
        raw_intro = raw[:hr_pos]
    # 去除第一行 # 标题
    lines = raw_intro.split("\n")
    lines = [l for l in lines if not l.startswith("# ") and not l.startswith("#")]
    intro_text = " ".join(l.strip() for l in lines if l.strip()).strip()
    if len(intro_text) > 300:
        intro_text = intro_text[:300] + "…"

    return {
        "chapter": dict(ch),
        "content_html": html_content,
        "intro_text": intro_text,
        "content_raw_len": len(raw),
    }


@router.get("/api/chapters/{chapter_id}/resources")
def chapter_resources(chapter_id: str):
    """列出章节的可下载附件资源"""
    with db() as conn:
        filename = conn.execute(
            "SELECT filename FROM chapters WHERE id=?", (chapter_id,)
        ).fetchone()
        if not filename:
            raise HTTPException(status_code=404, detail="章节不存在")

    docs_dir = _find_docs_dir()
    if not docs_dir:
        return []

    stem = Path(filename["filename"]).stem
    pattern = f"{stem}_*"
    resources = []
    for f in sorted(docs_dir.glob(pattern)):
        if f.suffix.lower() in (".md",):
            continue
        resources.append({
            "name": f.name,
            "size": f.stat().st_size,
            "suffix": f.suffix.lower(),
            "url": f"/api/resources/{chapter_id}/{f.name}",
        })

    return resources


@router.get("/api/resources/{chapter_id}/{filename}")
def download_resource(chapter_id: str, filename: str):
    """下载章节附件资源"""
    docs_dir = _find_docs_dir()
    if not docs_dir:
        raise HTTPException(status_code=500, detail="文档目录不可用")

    file_path = docs_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="资源文件不存在")

    return FileResponse(str(file_path), filename=filename)
