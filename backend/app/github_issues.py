import os
import re
import threading
import uuid
import time
from typing import List, Dict, Any

import requests

# In-memory task store: task_id -> {items: [...], status: {...}}
# 注意：进程重启后所有任务状态丢失，后端对未知 task_id 会返回 404（任务未找到或不属于当前会话）。
# 长期方案应落库到 SQLite（项目已有 database.py 框架）。
_TASKS: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


# ── 原型页面映射表：F-xxx 编号 → (页面文件名, 页面名称) ──────────────────────────
# 来源：prototype/生成面向Reflex的静态快速原型提示词.md §3.1–3.2
PROTOTYPE_MAP: Dict[str, tuple[str, str]] = {
    'F-S-001': ('login.html',           '登录页面'),
    'F-S-002': ('profile.html',         '个人资料'),
    'F-S-003': ('profile.html',         '个人资料'),
    'F-S-010': ('courses.html',         '课程列表'),
    'F-S-011': ('courses.html',         '课程列表'),
    'F-S-012': ('dashboard.html',       '学生仪表盘'),
    'F-S-020': ('assignments.html',     '作业提交'),
    'F-S-021': ('assignments.html',     '作业提交'),
    'F-S-022': ('assignments.html',     '作业提交'),
    'F-S-030': ('grades.html',          '成绩查看'),
    'F-S-031': ('grades.html',          '成绩查看'),
    'F-S-032': ('grades.html',          '成绩查看'),
    'F-S-040': ('dashboard.html',       '学生仪表盘'),
    'F-S-041': ('dashboard.html',       '学生仪表盘'),
    'F-S-052': ('attendance.html',      '课堂签到'),
    'F-S-053': ('exam.html',            '在线考试'),
    'F-T-001': ('admin_students.html',  '学生管理'),
    'F-T-002': ('admin_settings.html',  '系统设置'),
    'F-T-003': ('admin_students.html',  '学生管理'),
    'F-T-004': ('admin_students.html',  '学生管理'),
    'F-T-005': ('admin_settings.html',  '系统设置'),
    'F-T-006': ('admin_settings.html',  '系统设置'),
    'F-T-007': ('admin_devops.html',    '开发运维'),
    'F-T-008': ('admin_grades.html',    '成绩管理'),
    'F-T-009': ('admin_settings.html',  '系统设置'),
    'F-T-010': ('admin_grades.html',    '成绩管理'),
    'F-T-011': ('admin_settings.html',  '系统设置'),
    'F-D-001': ('admin_devops.html',    '开发运维'),
    'F-D-002': ('admin_devops.html',    '开发运维'),
    'F-D-003': ('admin_devops.html',    '开发运维'),
    'F-D-004': ('admin_devops.html',    '开发运维'),
    'F-D-005': ('admin_devops.html',    '开发运维'),
    'F-D-006': ('admin_devops.html',    '开发运维'),
    'F-D-007': ('admin_devops.html',    '开发运维'),
    'F-D-008': ('admin_devops.html',    '开发运维'),
}


def _label_from_prefix(tag: str) -> str:
    # tag like F-T, F-S, F-D
    if tag.startswith('F-S'):
        return 'student-feature'
    if tag.startswith('F-T'):
        return 'teacher-feature'
    if tag.startswith('F-D'):
        return 'devops'
    return 'feature'


def _extract_feature_id(raw_title: str) -> str:
    """Extract the full 3-part feature ID from a raw title line.
    e.g. 'F-T-011 需求转 GitHub Issue' -> 'F-T-011'
    """
    parts = raw_title.split()
    return parts[0] if parts else raw_title


def _append_prototype_link(feature_id: str, body: str) -> str:
    """Append prototype reference link to body if feature_id is known."""
    proto = PROTOTYPE_MAP.get(feature_id)
    if proto:
        page, name = proto
        link = f'\n\n> 📐 原型参考：[{name}](prototype/{page})'
        return body + link
    return body


def parse_markdown_for_features(content: str) -> List[Dict[str, Any]]:
    """Parse markdown content and extract feature items starting with F-XXX.
    Returns list of dicts: {id, feature_id, raw_title, candidate_title, labels,
                            body, module, prototype_page, prototype_name}
    """
    items: List[Dict[str, Any]] = []
    lines = content.splitlines()
    current_module: str | None = None
    # Match feature headings: ### F-T-011 功能名 - 可选描述
    pattern = re.compile(r'^(?:#{1,6}\s*)?(F-[A-Z]-\d{3}[^\n]*)(?:\s*-\s*(.*))?')
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Track module-level (##) headings, but not feature-level (###)
        if stripped.startswith('## ') and not stripped.startswith('### '):
            current_module = stripped.removeprefix('## ').strip()
        m = pattern.match(stripped)
        if m:
            raw = m.group(1).strip()
            rest = m.group(2) or ''
            candidate_title = raw + ((' - ' + rest) if rest else '')
            feature_id = _extract_feature_id(raw)
            prefix = feature_id.rsplit('-', 1)[0] if feature_id.count('-') >= 2 else raw
            labels = [_label_from_prefix(prefix)]
            # collect body until next heading or end of document
            body_lines = []
            for j in range(i+1, len(lines)):
                nl = lines[j]
                if nl.strip().startswith('#'):
                    break
                if nl.strip() == '':
                    if body_lines:
                        break
                    else:
                        continue
                body_lines.append(nl)
            body = '\n'.join(body_lines).strip()
            # Append prototype reference link to body
            body = _append_prototype_link(feature_id, body)
            proto = PROTOTYPE_MAP.get(feature_id)
            items.append({
                'id': str(uuid.uuid4()),
                'feature_id': feature_id,
                'raw_title': raw,
                'candidate_title': candidate_title,
                'labels': labels,
                'body': body,
                'module': current_module or '',
                'prototype_page': proto[0] if proto else '',
                'prototype_name': proto[1] if proto else '',
            })
    return items


def _list_existing_issue_titles(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    per_page = 100
    page = 1
    results = []
    while True:
        url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        params = {'state': 'all', 'per_page': per_page, 'page': page}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            break
        data = r.json()
        if not data:
            break
        for it in data:
            results.append({'number': it.get('number'), 'title': it.get('title'), 'url': it.get('html_url')})
        if len(data) < per_page:
            break
        page += 1
    return results


def _create_issue(owner: str, repo: str, token: str, title: str, body: str, labels: List[str], assignee: str = None, milestone: int | None = None):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github.v3+json'} if token else {'Accept': 'application/vnd.github.v3+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/issues'
    payload = {'title': title, 'body': body or ''}
    if labels:
        payload['labels'] = labels
    if assignee:
        payload['assignee'] = assignee
    if milestone is not None:
        payload['milestone'] = milestone
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    return r


def _update_issue(owner: str, repo: str, token: str, number: int, title: str, body: str, labels: List[str], assignee: str = None, milestone: int | None = None):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github.v3+json'} if token else {'Accept': 'application/vnd.github.v3+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/issues/{number}'
    payload = {'title': title, 'body': body or ''}
    if labels is not None:
        payload['labels'] = labels
    if assignee is not None:
        payload['assignee'] = assignee
    if milestone is not None:
        payload['milestone'] = milestone
    r = requests.patch(url, headers=headers, json=payload, timeout=15)
    return r


def _ensure_milestone(owner: str, repo: str, token: str, name: str) -> int | None:
    """Find or create a milestone by name, return its number (or None on failure)."""
    if not name:
        return None
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github.v3+json'} if token else {'Accept': 'application/vnd.github.v3+json'}
    # List existing milestones (open + closed)
    for state in ('all',):
        url = f'https://api.github.com/repos/{owner}/{repo}/milestones?state={state}&per_page=100'
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                for ms in r.json():
                    if ms.get('title') == name:
                        return ms.get('number')
        except Exception:
            pass
    # Not found — create it
    url = f'https://api.github.com/repos/{owner}/{repo}/milestones'
    try:
        r = requests.post(url, headers=headers, json={'title': name}, timeout=15)
        if r.status_code in (200, 201):
            return r.json().get('number')
    except Exception:
        pass
    return None


def start_create_task(items: List[Dict[str, Any]], repo_full: str, token: str, owner_sub: str, on_conflict: str = 'skip') -> str:
    """Start background task to create issues. Returns task_id."""
    task_id = str(uuid.uuid4())
    owner, repo = repo_full.split('/', 1)
    with _lock:
        _TASKS[task_id] = {'items': [], 'status': 'running', 'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0, 'results': [], 'owner_sub': owner_sub}

    def _worker():
        try:
            existing = _list_existing_issue_titles(owner, repo, token)
            existing_map = {e['title']: e for e in existing}
        except Exception:
            existing_map = {}

        # ── Ensure milestones for all unique modules ────────────────
        module_names = {it.get('module', '') for it in items if it.get('module')}
        milestone_map: Dict[str, int] = {}
        for mod_name in sorted(module_names):
            ms_num = _ensure_milestone(owner, repo, token, mod_name)
            if ms_num is not None:
                milestone_map[mod_name] = ms_num

        for it in items:
            rec = {'id': it.get('id'), 'title': it.get('title'), 'status': 'pending'}
            with _lock:
                _TASKS[task_id]['items'].append(rec)

            milestone = milestone_map.get(it.get('module', ''))

            # conflict check
            if it.get('title') in existing_map:
                if on_conflict == 'update':
                    # Update existing issue body/title/labels
                    existing_info = existing_map[it.get('title')]
                    try:
                        r = _update_issue(owner, repo, token,
                                          existing_info['number'],
                                          it.get('title'), it.get('body'),
                                          it.get('labels', []), it.get('assignee'),
                                          milestone=milestone)
                        if r.status_code in (200, 201):
                            with _lock:
                                rec['status'] = 'updated'
                                rec['number'] = existing_info['number']
                                rec['url'] = existing_info['url']
                                _TASKS[task_id]['updated'] += 1
                        else:
                            with _lock:
                                rec['status'] = 'failed'
                                rec['reason'] = f'{r.status_code} {r.text[:200]}'
                                _TASKS[task_id]['failed'] += 1
                    except Exception as e:
                        with _lock:
                            rec['status'] = 'failed'
                            rec['reason'] = str(e)
                            _TASKS[task_id]['failed'] += 1
                    with _lock:
                        _TASKS[task_id]['results'].append(rec)
                    continue
                else:
                    # skip
                    with _lock:
                        rec['status'] = 'skipped'
                        rec['reason'] = 'exists'
                        rec['existing'] = existing_map[it.get('title')]
                        _TASKS[task_id]['skipped'] += 1
                        _TASKS[task_id]['results'].append(rec)
                    continue

            # create
            try:
                r = _create_issue(owner, repo, token, it.get('title'), it.get('body'),
                                  it.get('labels', []), it.get('assignee'),
                                  milestone=milestone)
                if r.status_code in (200, 201):
                    data = r.json()
                    with _lock:
                        rec['status'] = 'created'
                        rec['number'] = data.get('number')
                        rec['url'] = data.get('html_url')
                        _TASKS[task_id]['created'] += 1
                else:
                    with _lock:
                        rec['status'] = 'failed'
                        rec['reason'] = f'{r.status_code} {r.text[:200]}'
                        _TASKS[task_id]['failed'] += 1
                with _lock:
                    _TASKS[task_id]['results'].append(rec)
            except Exception as e:
                with _lock:
                    rec['status'] = 'failed'
                    rec['reason'] = str(e)
                    _TASKS[task_id]['failed'] += 1
                    _TASKS[task_id]['results'].append(rec)
            # small delay to be nice to API
            time.sleep(0.2)

        with _lock:
            _TASKS[task_id]['status'] = 'finished'

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    return task_id


def get_task_status(task_id: str, owner_sub: str) -> Dict[str, Any] | None:
    """返回任务状态；任务不存在或不属于 owner_sub 时返回 None。"""
    with _lock:
        task = _TASKS.get(task_id)
        if task is None or task.get('owner_sub') != owner_sub:
            return None
        return task
