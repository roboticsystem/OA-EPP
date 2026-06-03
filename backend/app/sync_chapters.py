"""
sync_chapters.py — 扫描 DOCS_DIR 下所有 Markdown 文件，自动维护 courses 与 chapters 表。
由 app/main.py 在 FastAPI 启动时调用。

课程映射规则：
  practice1_*.md     → 工程实践1（EP1）
  practice2_*.md     → 工程实践2（EP2）
  practice3_*.md     → 工程实践3（EP3）
  overview_*.md      → 工程实践4（EP4）
  第*章_*.md         → 工程实践4（EP4）
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from app.database import db

DOCS_DIR = os.environ.get("DOCS_DIR", "")
_BAKED_DOCS_DIR = Path(__file__).parent.parent / "docs_baked"

_QUIZ_RE = re.compile(r"<quiz\b", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)

COURSE_MAP: dict[str, tuple[str, str, int, int]] = {
    "practice1": ("EP1", "工程实践1", 1, 100),
    "practice2": ("EP2", "工程实践2", 2, 100),
    "practice3": ("EP3", "工程实践3", 3, 100),
}

EP4_COURSE_ID = "EP4"
EP4_TITLE = "工程实践4"
EP4_TOTAL_SCORE = 100

EP4_DEADLINE_OFFSETS: dict[str, int] = {
    "overview_chapter1": 0,
    "overview_chapter2": 14,
    "第10章_": 28,
    "第11章_": 42,
    "第12章_": 56,
}


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


def _detect_chapter_type(filename: str, content: str, chapter_no: int) -> str:
    """检测章节类型：含<quiz>为考试；intro第一章为签到；其余为作业"""
    if _QUIZ_RE.search(content):
        return "考试"
    if filename == "overview_chapter1.md" and chapter_no == 1:
        return "签到"
    return "作业"


def _get_deadline(filename: str, base_date: datetime) -> str:
    for key, offset in EP4_DEADLINE_OFFSETS.items():
        if key in filename or filename.startswith(key):
            deadline = base_date + timedelta(days=offset)
            return deadline.strftime("%Y-%m-%d 23:59")
    return ""


def _get_grading_criteria(chapter_type: str) -> str:
    mapping = {
        "考试": "按正确率评分，60 分及格",
        "签到": "按时签到即得满分，迟到扣 50%，缺勤 0 分",
        "作业": "按代码质量/文档完整性/提交及时性综合评分",
    }
    return mapping.get(chapter_type, "见评分标准文档")


def _get_course_deadline_reminder(course_id: str) -> str:
    return {"EP4": "当前学期 · 请按时完成各章节任务"}.get(course_id, "")


def _parse_chapter_info(path: Path) -> dict | None:
    stem = path.stem
    if stem.startswith("practice") and "_chapter" in stem:
        parts = stem.split("_chapter")
        if len(parts) == 2:
            prefix = parts[0]
            if prefix in COURSE_MAP:
                course_id, course_title, _, score = COURSE_MAP[prefix]
                return {"course_id": course_id, "course_title": course_title,
                        "chapter_no": int(parts[1]), "total_score": score}
    for pattern in [re.match(r"overview_chapter(\d+)", stem),
                    re.match(r"第(\d+)章_", stem)]:
        if pattern:
            return {"course_id": EP4_COURSE_ID, "course_title": EP4_TITLE,
                    "chapter_no": int(pattern.group(1)), "total_score": EP4_TOTAL_SCORE}
    return None


def sync_chapters() -> dict:
    docs_dir = _find_docs_dir()
    if docs_dir is None:
        print(f"[sync_chapters] 未找到有效文档目录（DOCS_DIR={DOCS_DIR!r}），跳过扫描")
        return {}

    chapters_found, courses_data = [], {}
    base_date = datetime.now()

    for md_path in sorted(docs_dir.glob("*.md")):
        info = _parse_chapter_info(md_path)
        if info is None:
            continue
        content = md_path.read_text(encoding="utf-8")
        cid = info["course_id"]
        if cid not in courses_data:
            courses_data[cid] = {"title": info["course_title"], "total_score": info["total_score"]}

        ch_type = _detect_chapter_type(md_path.name, content, info["chapter_no"])
        is_ep4 = cid == EP4_COURSE_ID
        chapters_found.append({
            "id": f"{cid}_chapter{info['chapter_no']}",
            "course_id": cid,
            "chapter_no": info["chapter_no"],
            "title": _derive_title(content, md_path.stem),
            "filename": md_path.name,
            "file_path": str(md_path.relative_to(docs_dir.parent) if docs_dir.parent else md_path),
            "chapter_type": ch_type,
            "deadline": _get_deadline(md_path.stem, base_date) if is_ep4 else "",
            "status": "进行中" if is_ep4 else "已完成",
            "grading_criteria": _get_grading_criteria(ch_type),
        })

    if not chapters_found:
        return {"courses": 0, "chapters": 0}

    with db() as conn:
        for cid, cdata in courses_data.items():
            sem = 4 if cid == EP4_COURSE_ID else next(
                (o for _, (pcid, _, o, _) in COURSE_MAP.items() if cid == pcid), 1)
            conn.execute(
                "REPLACE INTO courses (id,title,semester,total_score,deadline_reminder,is_active) VALUES (%s,%s,%s,%s,%s,1)",
                (cid, cdata["title"], f"EP{sem}", cdata["total_score"], _get_course_deadline_reminder(cid)))

        existing = {r["id"] for r in conn.execute("SELECT id FROM chapters").fetchall()}
        added = []
        for ch in chapters_found:
            if ch["id"] not in existing:
                conn.execute(
                    "INSERT INTO chapters (id,course_id,chapter_no,title,filename,file_path,chapter_type,deadline,status,grading_criteria) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (ch["id"], ch["course_id"], ch["chapter_no"], ch["title"], ch["filename"],
                     ch["file_path"], ch["chapter_type"], ch["deadline"], ch["status"], ch["grading_criteria"]))
                added.append(ch["id"])
            else:
                conn.execute(
                    "UPDATE chapters SET title=%s,chapter_type=%s,status=%s,deadline=%s,grading_criteria=%s WHERE id=%s",
                    (ch["title"], ch["chapter_type"],
                     "进行中" if ch["course_id"] == EP4_COURSE_ID else "已完成",
                     ch["deadline"], ch["grading_criteria"], ch["id"]))

    print(f"[sync_chapters] 完成：{len(courses_data)} 门课程，{len(chapters_found)} 个章节，新增 {len(added)}")
    return {"courses": list(courses_data.keys()), "chapters": len(chapters_found), "added": added}
