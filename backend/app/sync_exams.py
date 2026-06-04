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
        print(f"[sync_exams] 使用内置备用文档目录: {_BAKED_DOCS_DIR}")
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
    with db() as conn:
        existing = {r["id"]: r["title"] for r in conn.execute("SELECT id, title FROM exams")}
        for eid, etitle in found.items():
            if eid not in existing:
                conn.execute("INSERT INTO exams (id, title, is_active) VALUES (?,?,1)", (eid, etitle))
                added.append(eid)
                print(f"[sync_exams] 数据库新增考试：{eid} - {etitle}")
            else:
                # 如果文档中 exam-title 与数据库中不一致，更新数据库中的标题
                if existing.get(eid) != etitle:
                    conn.execute("UPDATE exams SET title=? WHERE id=?", (etitle, eid))
                    updated.append(eid)
                    print(f"[sync_exams] 数据库更新考试标题：{eid} - {etitle}")
        # 只有在确实扫描到考试文档时才清理孤立记录，防止挂载目录为空时误删所有考试
        if found:
            for eid in list(existing):
                if eid not in found:
                    conn.execute("DELETE FROM exams WHERE id=?", (eid,))
                    deleted.append(eid)
                    print(f"[sync_exams] 数据库删除孤立考试：{eid}")
        elif existing:
            print(f"[sync_exams] ⚠️  文档扫描结果为空，跳过孤立记录清理（保留 {len(existing)} 条现有记录）")

    print(f"[sync_exams] 完成：发现 {len(found)} 个考试，"
          f"注入 {len(injected)} 个文件，DB 新增 {len(added)}，更新 {len(updated)}，删除 {len(deleted)}")
    return {"injected_meta": injected, "db_added": added, "db_updated": updated, "db_deleted": deleted,
            "exams": list(found.keys())}
