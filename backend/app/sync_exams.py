"""
sync_exams.py — 扫描 DOCS_DIR 下所有 Markdown 文件，自动维护 exam-meta 与数据库 exams 表的一致性。
由 app/main.py 在 FastAPI 启动时调用。

当前数据库 schema 不支持自动同步考试（exams.id 为 BIGINT 自增），跳过。
"""

import os
import re
from pathlib import Path
from app.database import db

DOCS_DIR = os.environ.get("DOCS_DIR", "")

_BAKED_DOCS_DIR = Path(__file__).parent.parent / "docs_baked"

_QUIZ_RE       = re.compile(r"<quiz\b",                              re.IGNORECASE)
_META_DIV_RE   = re.compile(r'<div[^>]+id=["\']exam-meta["\']',     re.IGNORECASE)
_META_ID_RE    = re.compile(r'data-exam-id=["\']([^"\']+)["\']',    re.IGNORECASE)
_META_TITLE_RE = re.compile(r'data-exam-title=["\']([^"\']+)["\']', re.IGNORECASE)
_HEADING_RE    = re.compile(r'^#\s+(.+)',                            re.MULTILINE)

INTRO_MARKER   = "<!-- mkdocs-quiz intro -->"
RESULTS_MARKER = "<!-- mkdocs-quiz results -->"


def _derive_title(content: str, exam_id: str) -> str:
    m = _HEADING_RE.search(content)
    if m:
        return re.sub(r"[*_`]", "", m.group(1)).strip() + " 测验"
    return f"{exam_id} 测验"


def _parse_exam_meta(content: str):
    if not _META_DIV_RE.search(content):
        return None
    mid    = _META_ID_RE.search(content)
    mtitle = _META_TITLE_RE.search(content)
    if mid:
        return mid.group(1), (mtitle.group(1) if mtitle else mid.group(1))
    return None


def _inject_exam_meta(content: str, exam_id: str, exam_title: str) -> str:
    meta_line = (
        f'<div id="exam-meta" data-exam-id="{exam_id}" '
        f'data-exam-title="{exam_title}" style="display:none"></div>'
    )
    if INTRO_MARKER in content:
        idx = content.index(INTRO_MARKER)
        return content[:idx] + meta_line + "\n\n" + content[idx:]
    m = _QUIZ_RE.search(content)
    if not m:
        return content
    insert_at   = m.start()
    new_content = content[:insert_at] + meta_line + "\n\n" + INTRO_MARKER + "\n\n" + content[insert_at:]
    if RESULTS_MARKER not in new_content:
        last = new_content.rfind("</quiz>")
        if last != -1:
            end         = last + len("</quiz>")
            new_content = new_content[:end] + "\n\n" + RESULTS_MARKER + new_content[end:]
    return new_content


def _find_docs_dir() -> "Path | None":
    if DOCS_DIR:
        candidate = Path(DOCS_DIR)
        if candidate.is_dir() and any(candidate.rglob("*.md")):
            return candidate
        if candidate.is_dir():
            print(f"[sync_exams] DOCS_DIR={DOCS_DIR!r} 目录为空或无 .md 文件，尝试内置备用目录")

    if _BAKED_DOCS_DIR.is_dir() and any(_BAKED_DOCS_DIR.rglob("*.md")):
        print(f"[sync_exams] 使用内置备用文档目录: {_BAKED_DOCS_DIR}")
        return _BAKED_DOCS_DIR

    return None


def sync_exams() -> dict:
    print("[sync_exams] 当前数据库 schema 不支持自动同步考试，跳过")
    return {}
