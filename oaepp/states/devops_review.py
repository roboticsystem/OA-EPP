"""
F-D-007 PR 审查与提示词模板管理 — PRReviewState

模板文件目录：.github/review-prompts/（纳入 Git）
Dry-Run 状态：.github/review-prompts/.dry-run-state.json（本地临时，不提交）
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import reflex as rx

    _StateBase = rx.State
except Exception:
    rx = None

    class _StateBase:  # type: ignore[no-redef]
        pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _prompts_dir() -> Path:
    return _repo_root() / ".github" / "review-prompts"


def _manifest_path() -> Path:
    return _prompts_dir() / "manifest.json"


def _dry_run_state_path() -> Path:
    return _prompts_dir() / ".dry-run-state.json"


def _active_prompt_path() -> Path:
    return _prompts_dir() / "code-review.prompt.md"


def _slugify(name: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", name.strip().lower())
    return s.strip("-") or "custom"


_SAMPLE_DIFF = """diff --git a/oaepp/states/example.py b/oaepp/states/example.py
--- a/oaepp/states/example.py
+++ b/oaepp/states/example.py
@@ -1,3 +1,5 @@
 def handler():
-    pass
+    result = fetch_data()  # 阻塞 I/O 示例
+    return result
"""


def _builtin_content(template_id: str) -> str:
    path = _prompts_dir() / f"{template_id.replace('_', '-')}.prompt.md"
    if template_id == "engineering-practices":
        path = _prompts_dir() / "engineering-practices.prompt.md"
    elif template_id == "security-audit":
        path = _prompts_dir() / "security-audit.prompt.md"
    elif template_id == "general-review":
        path = _prompts_dir() / "general-review.prompt.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


_BUILTIN_TEMPLATE_LIST: list[dict[str, Any]] = [
    {
        "id": "general-review",
        "name": "通用代码审查",
        "description": "代码质量、命名规范、潜在 Bug 与可读性",
        "file": "general-review.prompt.md",
        "builtin": True,
        "kind": "code-review",
    },
    {
        "id": "engineering-practices",
        "name": "工程实践规范检查",
        "description": "单元测试、依赖管理、提交规范与架构分层",
        "file": "engineering-practices.prompt.md",
        "builtin": True,
        "kind": "code-review",
    },
    {
        "id": "security-audit",
        "name": "安全全面审查",
        "description": "注入、密钥泄露、权限与敏感数据处理",
        "file": "security-audit.prompt.md",
        "builtin": True,
        "kind": "code-review",
    },
]

# 模块级别名，供测试与外部引用
BUILTIN_TEMPLATES = _BUILTIN_TEMPLATE_LIST


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.is_file():
        return {
            "version": 1,
            "default_template_id": "general-review",
            "ignore_patterns": [],
            "templates": [dict(t) for t in _BUILTIN_TEMPLATE_LIST],
            "dry_run_audit": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _save_manifest(data: dict[str, Any]) -> None:
    _prompts_dir().mkdir(parents=True, exist_ok=True)
    _manifest_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_template_file(filename: str) -> str:
    path = _prompts_dir() / filename
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def _write_template_file(filename: str, content: str) -> None:
    _prompts_dir().mkdir(parents=True, exist_ok=True)
    (_prompts_dir() / filename).write_text(content, encoding="utf-8")


def _template_by_id(manifest: dict[str, Any], template_id: str) -> dict[str, Any] | None:
    for t in manifest.get("templates", []):
        if t.get("id") == template_id:
            return t
    return None


def _sync_active_prompt(content: str) -> None:
    _write_template_file("code-review.prompt.md", content)


def _substitute_placeholders(
    text: str,
    *,
    diff: str,
    pr_title: str,
    pr_description: str,
    author: str,
) -> str:
    return (
        text.replace("{diff}", diff)
        .replace("{pr_title}", pr_title)
        .replace("{pr_description}", pr_description)
        .replace("{author}", author)
    )


def _fetch_latest_pr_context() -> dict[str, str]:
    """Best-effort: load latest open PR metadata from GitHub API."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB__USER_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        return {
            "diff": _SAMPLE_DIFF,
            "pr_title": "[Dry-Run] 示例 PR — 平台配置验证",
            "pr_description": "用于验证 pr-agent 提示词模板，不提交到 GitHub。",
            "author": "oaepp-dry-run",
        }
    owner, name = repo.split("/", 1)
    api = f"https://api.github.com/repos/{owner}/{name}/pulls?state=open&per_page=1"
    req = urllib.request.Request(
        api,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            pulls = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        pulls = []
    if not pulls:
        return {
            "diff": _SAMPLE_DIFF,
            "pr_title": "[Dry-Run] 无开放 PR — 使用示例 diff",
            "pr_description": "仓库中暂无 open 状态的 PR，已回退到内置样例。",
            "author": "oaepp-dry-run",
        }
    pr = pulls[0]
    pr_number = pr.get("number")
    diff_text = _SAMPLE_DIFF
    if pr_number:
        diff_url = (
            f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}"
        )
        diff_req = urllib.request.Request(
            diff_url,
            headers={
                "Accept": "application/vnd.github.v3.diff",
                "Authorization": f"Bearer {token}",
            },
        )
        try:
            with urllib.request.urlopen(diff_req, timeout=20) as dresp:
                raw = dresp.read().decode("utf-8", errors="replace")
                diff_text = raw[:12000] if raw else _SAMPLE_DIFF
        except (urllib.error.URLError, TimeoutError):
            pass
    return {
        "diff": diff_text,
        "pr_title": pr.get("title") or "[Dry-Run] PR",
        "pr_description": pr.get("body") or "",
        "author": (pr.get("user") or {}).get("login") or "unknown",
    }


def _call_review_llm(prompt: str) -> tuple[str, str]:
    """Return (status, snippet). status: success | timeout | error | simulated."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("MODELS_API_KEY")
    base = os.environ.get(
        "OPENAI_API_BASE", "https://models.inference.ai.azure.com"
    )
    if not api_key:
        snippet = (
            "## Dry-Run 模拟审查（未配置 OPENAI_API_KEY / MODELS_API_KEY）\n\n"
            "已使用当前模板与 PR 上下文完成占位符替换。配置 API Key 后将调用真实模型。\n\n"
            "### 审查片段预览\n\n"
            + prompt[:2000]
            + ("\n…" if len(prompt) > 2000 else "")
        )
        return "simulated", snippet

    url = base.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": os.environ.get("PR_REVIEW_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": "你是 PR 代码审查助手，输出简洁的中文 Markdown。",
                },
                {"role": "user", "content": prompt[:24000]},
            ],
            "max_tokens": 1500,
            "temperature": 0.2,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = (
            (data.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not content:
            return "error", "模型返回为空响应"
        return "success", content[:4000]
    except TimeoutError:
        return "timeout", "AI 调用超时（>90s），请稍后重试或检查网络。"
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        return "error", f"AI 调用失败 HTTP {e.code}: {detail}"
    except Exception as e:
        return "error", f"AI 调用异常: {e}"


class PRReviewState(_StateBase):
    """F-D-007：PR 审查提示词模板与 Dry-Run 验证。"""

    BUILTIN_TEMPLATES: list[dict[str, Any]] = _BUILTIN_TEMPLATE_LIST

    templates: list[dict[str, Any]] = []
    active_template: str = "general-review"
    dry_run_result: dict[str, Any] = {}
    editor_content: str = ""
    new_template_name: str = ""
    rename_target_name: str = ""
    status_message: str = ""
    is_validating: bool = False
    dry_run_preview: str = ""
    dry_run_status_label: str = "尚未执行验证"
    prompt_save_path: str = ".github/review-prompts/code-review.prompt.md"

    def on_load(self):
        self.load_templates()

    def load_templates(self):
        manifest = _load_manifest()
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for t in manifest.get("templates", []):
            tid = t.get("id", "")
            if tid and tid not in seen:
                merged.append(dict(t))
                seen.add(tid)
        for b in _BUILTIN_TEMPLATE_LIST:
            if b["id"] not in seen:
                merged.append(dict(b))
        self.templates = merged
        default_id = manifest.get("default_template_id") or "general-review"
        self.active_template = default_id
        meta = _template_by_id(manifest, default_id)
        if meta:
            self.editor_content = _read_template_file(meta.get("file", ""))
            self.prompt_save_path = f".github/review-prompts/{meta.get('file', 'code-review.prompt.md')}"
        else:
            self.editor_content = _builtin_content(default_id)
        self.status_message = "模板已加载"

    def select_template(self, template_id: str):
        manifest = _load_manifest()
        meta = _template_by_id(manifest, template_id)
        if not meta:
            for b in _BUILTIN_TEMPLATE_LIST:
                if b["id"] == template_id:
                    meta = b
                    break
        if not meta:
            self.status_message = f"未找到模板: {template_id}"
            return
        self.active_template = template_id
        self.editor_content = _read_template_file(meta.get("file", "")) or _builtin_content(
            template_id
        )
        self.prompt_save_path = f".github/review-prompts/{meta.get('file', '')}"

    def set_editor_content(self, value: str):
        self.editor_content = value

    def set_new_template_name(self, value: str):
        self.new_template_name = value

    def set_rename_target_name(self, value: str):
        self.rename_target_name = value

    def save_template(self):
        manifest = _load_manifest()
        meta = _template_by_id(manifest, self.active_template)
        if not meta:
            self.status_message = "请先选择有效模板"
            return
        filename = meta.get("file") or f"{self.active_template}.prompt.md"
        _write_template_file(filename, self.editor_content)
        if meta.get("kind", "code-review") == "code-review" or meta.get("id") in {
            "general-review",
            "engineering-practices",
            "security-audit",
        }:
            if manifest.get("default_template_id") == self.active_template:
                _sync_active_prompt(self.editor_content)
        self.prompt_save_path = f".github/review-prompts/{filename}"
        self.status_message = f"已保存至 {self.prompt_save_path}（纳入 Git）"

    def set_default_template(self, template_id: str | None = None):
        tid = template_id or self.active_template
        manifest = _load_manifest()
        if not _template_by_id(manifest, tid):
            self.status_message = f"模板不存在: {tid}"
            return
        manifest["default_template_id"] = tid
        _save_manifest(manifest)
        meta = _template_by_id(manifest, tid) or {}
        content = _read_template_file(meta.get("file", "")) or self.editor_content
        _sync_active_prompt(content)
        self.active_template = tid
        self.status_message = f"已将「{meta.get('name', tid)}」设为默认审查模板"

    def copy_template(self, source_id: str | None = None):
        sid = source_id or self.active_template
        manifest = _load_manifest()
        src = _template_by_id(manifest, sid)
        if not src:
            self.status_message = "复制失败：源模板不存在"
            return
        base_name = self.new_template_name.strip() or f"{src.get('name', sid)} 副本"
        slug = _slugify(base_name)
        new_id = f"custom-{slug}"
        idx = 1
        while _template_by_id(manifest, new_id):
            new_id = f"custom-{slug}-{idx}"
            idx += 1
        filename = f"{new_id}.prompt.md"
        content = _read_template_file(src.get("file", "")) or self.editor_content
        _write_template_file(filename, content)
        entry = {
            "id": new_id,
            "name": base_name,
            "description": f"复制自 {src.get('name', sid)}",
            "file": filename,
            "builtin": False,
            "kind": src.get("kind", "code-review"),
        }
        manifest.setdefault("templates", []).append(entry)
        _save_manifest(manifest)
        self.load_templates()
        self.select_template(new_id)
        self.status_message = f"已复制为「{base_name}」"

    def rename_template(self, template_id: str | None = None):
        tid = template_id or self.active_template
        manifest = _load_manifest()
        meta = _template_by_id(manifest, tid)
        if not meta:
            self.status_message = "重命名失败：模板不存在"
            return
        if meta.get("builtin"):
            self.status_message = "内置模板不可重命名"
            return
        new_name = self.rename_target_name.strip()
        if not new_name:
            self.status_message = "请输入新名称"
            return
        meta["name"] = new_name
        _save_manifest(manifest)
        self.load_templates()
        self.status_message = f"已重命名为「{new_name}」"

    def delete_template(self, template_id: str | None = None):
        tid = template_id or self.active_template
        manifest = _load_manifest()
        meta = _template_by_id(manifest, tid)
        if not meta:
            self.status_message = "删除失败：模板不存在"
            return
        if meta.get("builtin"):
            self.status_message = "内置模板不可删除"
            return
        if manifest.get("default_template_id") == tid:
            self.status_message = "不能删除当前默认模板，请先切换默认"
            return
        filename = meta.get("file")
        if filename:
            path = _prompts_dir() / filename
            if path.is_file():
                path.unlink()
        manifest["templates"] = [
            t for t in manifest.get("templates", []) if t.get("id") != tid
        ]
        _save_manifest(manifest)
        self.load_templates()
        self.select_template(manifest.get("default_template_id", "general-review"))
        self.status_message = f"已删除模板「{meta.get('name', tid)}」"

    def dry_run_review(self):
        self.is_validating = True
        self.dry_run_status_label = "验证中…"
        manifest = _load_manifest()
        meta = _template_by_id(manifest, self.active_template) or {}
        prompt_raw = self.editor_content or _read_template_file(
            meta.get("file", "code-review.prompt.md")
        )
        ctx = _fetch_latest_pr_context()
        filled = _substitute_placeholders(
            prompt_raw,
            diff=ctx["diff"],
            pr_title=ctx["pr_title"],
            pr_description=ctx["pr_description"],
            author=ctx["author"],
        )
        status, snippet = _call_review_llm(filled)
        version = f"{meta.get('id', self.active_template)} @ {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        result = {
            "status": status,
            "prompt_version": version,
            "snippet": snippet,
            "pr_title": ctx["pr_title"],
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "draft_comment_ids": [],
            "submitted_to_github": False,
        }
        dry_path = _dry_run_state_path()
        dry_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.dry_run_result = result
        self.dry_run_preview = snippet
        labels = {
            "success": "AI 调用成功",
            "simulated": "模拟成功（未配置 API Key）",
            "timeout": "AI 调用超时",
            "error": "AI 调用错误",
        }
        self.dry_run_status_label = labels.get(status, status)
        self.is_validating = False
        self.status_message = f"Dry-Run 完成：{self.dry_run_status_label}"

    def clear_dry_run_traces(self):
        manifest = _load_manifest()
        now = datetime.now(timezone.utc).isoformat()
        prev = self.dry_run_result.get("ran_at")
        manifest.setdefault("dry_run_audit", []).append(
            {
                "verified_at": prev or now,
                "operator": os.environ.get("OAEPP_USER", "teacher"),
                "cleared_at": now,
            }
        )
        _save_manifest(manifest)
        path = _dry_run_state_path()
        if path.is_file():
            path.unlink()
        self.dry_run_result = {}
        self.dry_run_preview = ""
        self.dry_run_status_label = "尚未执行验证"
        self.status_message = "已清除验证痕迹（含 Dry-Run 缓存与预览区）"
