"""
sync_exams.py — 扫描 DOCS_DIR 下所有 Markdown 文件，自动维护 exam-meta 与数据库 exams 表的一致性。
由 app/main.py 在 FastAPI 启动时调用。

规则：
1. 发现含 <quiz> 的 .md 文件 → 若缺少 exam-meta div，自动注入
2. 将所有 .md 中的 exam-id 同步到数据库（缺则添加）
3. 数据库中找不到对应 .md 的考试记录 → 删除（孤立记录清理）

exam-id    = 文件名去掉扩展名（如 chapter3.md → chapter3）
exam-title = .md 第一个 "# 标题" + " 测验"
"""

import os
import re
from pathlib import Path
from app.database import db

DOCS_DIR = os.environ.get("DOCS_DIR", "")

# 内置备用文档目录：镜像构建时打包的 docs 副本（/app/docs_baked/）
# 当 DOCS_DIR 挂载失败或为空目录时，自动回退到此目录
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
    """按优先级查找有效的文档目录（含 .md 文件）。"""
    # 优先使用环境变量指定的目录（支持 bind mount 写回）
    if DOCS_DIR:
        candidate = Path(DOCS_DIR)
        if candidate.is_dir() and any(candidate.rglob("*.md")):
            return candidate
        if candidate.is_dir():
            print(f"[sync_exams] DOCS_DIR={DOCS_DIR!r} 目录为空或无 .md 文件，尝试内置备用目录")

    # 回退到镜像内置的备用文档目录（/app/docs_baked/）
    if _BAKED_DOCS_DIR.is_dir() and any(_BAKED_DOCS_DIR.rglob("*.md")):
        print(f"[sync_exams] 使用内置备用文档目录：{_BAKED_DOCS_DIR}")
        return _BAKED_DOCS_DIR

    return None


def sync_exams() -> dict:
    """扫描文档目录，自动修复 .md 文件并同步数据库。返回操作摘要字典。"""
    docs_dir = _find_docs_dir()
    if docs_dir is None:
        print(f"[sync_exams] 未找到有效文档目录（DOCS_DIR={DOCS_DIR!r}），跳过扫描")
        return {}

    found:    dict[str, str] = {}
    injected: list[str]      = []

    for md_path in sorted(docs_dir.glob("**/*.md")):
        content = md_path.read_text(encoding="utf-8")
        if not _QUIZ_RE.search(content):
            continue
        meta = _parse_exam_meta(content)
        if meta:
            exam_id, exam_title = meta
        else:
            exam_id    = md_path.stem
            exam_title = _derive_title(content, exam_id)
            md_path.write_text(_inject_exam_meta(content, exam_id, exam_title), encoding="utf-8")
            injected.append(md_path.name)
            print(f"[sync_exams] 已注入 exam-meta → {md_path.name} (id={exam_id})")
        found[exam_id] = exam_title

    added   = []
    updated = []
    deleted = []
    
    try:
        with db() as conn:
            cursor = conn.cursor()
            
            # 获取现有考试 - 我们使用 title 作为标识
            cursor.execute("SELECT id, title FROM exams")
            existing = {r["title"]: r["id"] for r in cursor.fetchall()}
            
            # 查找默认课程（如果没有就创建一个默认课程）
            cursor.execute("SELECT id FROM courses LIMIT 1")
            course = cursor.fetchone()
            if not course:
                print("[sync_exams] 没有找到课程，跳过数据库同步")
                return {"injected_meta": injected, "db_added": [], "db_updated": [], "db_deleted": [], "exams": []}
            
            course_id = course["id"]
            
            # 查找默认教师
            cursor.execute("SELECT user_id FROM teachers LIMIT 1")
            teacher = cursor.fetchone()
            if not teacher:
                print("[sync_exams] 没有找到教师，跳过数据库同步")
                return {"injected_meta": injected, "db_added": [], "db_updated": [], "db_deleted": [], "exams": []}
            
            teacher_id = teacher["user_id"]
            
            now = "2099-12-31 23:59:59"
            
            for eid, etitle in found.items():
                # 在数据库中查找该考试
                if etitle not in existing:
                    # 插入新考试
                    cursor.execute("""
                        INSERT INTO exams (course_id, title, exam_type, start_at, end_at, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (course_id, etitle, 'quiz', '2024-01-01 00:00:00', '2099-12-31 23:59:59', teacher_id))
                    added.append(eid)
                    print(f"[sync_exams] 数据库新增考试：{eid} - {etitle}")
                else:
                    # 考试已存在，跳过
                    pass
            
            # 不删除考试，因为可能有其他数据关联
            print(f"[sync_exams] 完成：发现 {len(found)} 个考试，注入 {len(injected)} 个文件，DB 新增 {len(added)} 个")
    except Exception as e:
        print(f"[sync_exams] 数据库同步出错：{e}")

    return {"injected_meta": injected, "db_added": added, "db_updated": updated, "db_deleted": deleted, "exams": list(found.keys())}
