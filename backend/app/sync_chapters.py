"""
sync_chapters.py — 扫描 DOCS_DIR 下所有 Markdown 文件，自动维护 courses 与 chapters 表。
由 app/main.py 在 FastAPI 启动时调用。

F-S-011 依赖此模块提供课程章节数据。

课程映射规则：
  practice1_*.md     → 工程实践1（EP1）
  practice2_*.md     → 工程实践2（EP2）
  practice3_*.md     → 工程实践3（EP3）
  overview_*.md      → 工程实践4（EP4）
  第*章_*.md         → 工程实践4（EP4）
"""

import os
import re
from pathlib import Path
from app.database import db

DOCS_DIR = os.environ.get("DOCS_DIR", "")
_BAKED_DOCS_DIR = Path(__file__).parent.parent / "docs_baked"

_QUIZ_RE = re.compile(r"<quiz\b", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)

COURSE_MAP: dict[str, tuple[str, str, int]] = {
    # prefix → (course_id, course_title, semester_order)
    "practice1": ("EP1", "工程实践1", 1),
    "practice2": ("EP2", "工程实践2", 2),
    "practice3": ("EP3", "工程实践3", 3),
}

# overview 和 第N章 都归入 EP4
EP4_COURSE_ID = "EP4"
EP4_TITLE = "工程实践4"


def _find_docs_dir() -> Path | None:
    if DOCS_DIR:
        candidate = Path(DOCS_DIR)
        if candidate.is_dir() and any(candidate.rglob("*.md")):
            return candidate
    if _BAKED_DOCS_DIR.is_dir() and any(_BAKED_DOCS_DIR.rglob("*.md")):
        return _BAKED_DOCS_DIR
    return None


def _derive_title(content: str, stem: str) -> str:
    m = _HEADING_RE.search(content)
    if m:
        return re.sub(r"[*_`]", "", m.group(1)).strip()
    return stem


def _detect_chapter_type(content: str) -> str:
    """检测章节类型：含 <quiz> 为考试，其余默认为作业"""
    if _QUIZ_RE.search(content):
        return "考试"
    return "作业"


def _parse_chapter_info(path: Path) -> dict | None:
    """解析文件路径，返回 dict 或 None（不匹配任何课程）。"""
    stem = path.stem
    if stem.startswith("practice") and "_chapter" in stem:
        parts = stem.split("_chapter")
        if len(parts) == 2:
            prefix = parts[0]
            if prefix in COURSE_MAP:
                course_id, course_title, _ = COURSE_MAP[prefix]
                chapter_no = int(parts[1])
                return {
                    "course_id": course_id,
                    "course_title": course_title,
                    "chapter_no": chapter_no,
                }
    # overview 或 第N章 → EP4
    ep4_patterns = [
        re.match(r"overview_chapter(\d+)", stem),
        re.match(r"第(\d+)章_", stem),
    ]
    for m in ep4_patterns:
        if m:
            return {
                "course_id": EP4_COURSE_ID,
                "course_title": EP4_TITLE,
                "chapter_no": int(m.group(1)),
            }
    return None


def sync_chapters() -> dict:
    """扫描文档目录，同步 courses 和 chapters 表。返回操作摘要。"""
    docs_dir = _find_docs_dir()
    if docs_dir is None:
        print(f"[sync_chapters] 未找到有效文档目录（DOCS_DIR={DOCS_DIR!r}），跳过扫描")
        return {}

    chapters_found: list[dict] = []
    courses_seen: dict[str, str] = {}

    for md_path in sorted(docs_dir.glob("*.md")):
        info = _parse_chapter_info(md_path)
        if info is None:
            continue
        content = md_path.read_text(encoding="utf-8")

        cid = info["course_id"]
        courses_seen[cid] = info["course_title"]

        chapter_no = info["chapter_no"]
        title = _derive_title(content, md_path.stem)
        chapter_type = _detect_chapter_type(content)

        chapters_found.append({
            "id": f"{cid}_chapter{chapter_no}",
            "course_id": cid,
            "chapter_no": chapter_no,
            "title": title,
            "filename": md_path.name,
            "file_path": str(md_path.relative_to(docs_dir.parent) if docs_dir.parent else md_path),
            "chapter_type": chapter_type,
            "deadline": "",
            "status": "进行中" if cid == EP4_COURSE_ID else "已完成",
            "grading_criteria": "见评分标准文档" if chapter_type == "作业" else "按正确率评分",
        })

    if not chapters_found:
        print(f"[sync_chapters] 未匹配到课程章节文件")
        return {"courses": 0, "chapters": 0}

    with db() as conn:
        # 同步 courses
        for cid, ctitle in courses_seen.items():
            semester_order = 1
            for prefix, (pcid, _, order) in COURSE_MAP.items():
                if cid == pcid:
                    semester_order = order
                    break
            if cid == EP4_COURSE_ID:
                semester_order = 4
            conn.execute(
                "INSERT OR REPLACE INTO courses (id, title, semester, is_active) VALUES (?,?,?,1)",
                (cid, ctitle, f"EP{semester_order}")
            )

        # 同步 chapters
        existing_ids = {r["id"] for r in conn.execute("SELECT id FROM chapters").fetchall()}
        added = []
        for ch in chapters_found:
            if ch["id"] not in existing_ids:
                conn.execute(
                    """INSERT INTO chapters
                       (id, course_id, chapter_no, title, filename, file_path,
                        chapter_type, deadline, status, grading_criteria)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (ch["id"], ch["course_id"], ch["chapter_no"], ch["title"],
                     ch["filename"], ch["file_path"], ch["chapter_type"],
                     ch["deadline"], ch["status"], ch["grading_criteria"])
                )
                added.append(ch["id"])
            else:
                # 更新标题和类型（文件内容可能变更）
                conn.execute(
                    "UPDATE chapters SET title=?, chapter_type=?, status=? WHERE id=?",
                    (ch["title"], ch["chapter_type"],
                     "进行中" if ch["course_id"] == EP4_COURSE_ID else "已完成",
                     ch["id"])
                )

    print(f"[sync_chapters] 完成：{len(courses_seen)} 门课程，"
          f"{len(chapters_found)} 个章节，新增 {len(added)}")
    return {
        "courses": list(courses_seen.keys()),
        "chapters": len(chapters_found),
        "added": added,
    }
