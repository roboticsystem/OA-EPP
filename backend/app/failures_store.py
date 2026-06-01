"""
failures_store.py — commitlint 校验失败记录的本地存储

MySQL 中无 commitlint_failures 表，因此使用本地 JSON 文件存储最近 5 条记录。
"""

import os
import json
from pathlib import Path

_FAILURES_FILE = Path(os.environ.get("FAILURES_FILE", str(
    Path(__file__).resolve().parent.parent.parent / ".local_exam_data" / "commitlint_failures.json"
)))
_MAX_RECORDS = 5


def _ensure_file():
    _FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not _FAILURES_FILE.exists():
        _FAILURES_FILE.write_text("[]", encoding="utf-8")


def get_failures() -> list:
    _ensure_file()
    try:
        data = json.loads(_FAILURES_FILE.read_text(encoding="utf-8"))
        return data[: _MAX_RECORDS]
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def add_failure(commit_sha: str, commit_msg: str, author: str = "",
                branch: str = "", pr_number: int = 0, error_msg: str = ""):
    _ensure_file()
    records = get_failures()
    records.insert(0, {
        "id": len(records) + 1,
        "commit_sha": commit_sha,
        "commit_msg": commit_msg,
        "author": author,
        "branch": branch,
        "pr_number": pr_number,
        "failed_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error_msg": error_msg,
    })
    records = records[:_MAX_RECORDS]
    _FAILURES_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
