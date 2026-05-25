import os
import re
import threading
import uuid
import time
from typing import List, Dict, Any

import requests

# In-memory task store: task_id -> {items: [...], status: {...}}
_TASKS: Dict[str, Dict[str, Any]] = {}


def _label_from_prefix(tag: str) -> str:
    # tag like F-T, F-S, F-D
    if tag.startswith('F-S'):
        return 'student-feature'
    if tag.startswith('F-T'):
        return 'teacher-feature'
    if tag.startswith('F-D'):
        return 'devops'
    return 'feature'


def parse_markdown_for_features(content: str) -> List[Dict[str, Any]]:
    """Parse markdown content and extract feature items starting with F-XXX.
    Returns list of dicts: {id, raw_title, candidate_title, labels, body}
    """
    items: List[Dict[str, Any]] = []
    lines = content.splitlines()
    # look for headings or lines that start with F-
    pattern = re.compile(r'^(?:#{1,6}\s*)?(F-[A-Z]-\d{3}[^\n]*)(?:\s*-\s*(.*))?')
    for i, line in enumerate(lines):
        m = pattern.match(line.strip())
        if m:
            raw = m.group(1).strip()
            rest = m.group(2) or ''
            candidate_title = raw + ((' - ' + rest) if rest else '')
            prefix = raw.split('-')[0] + '-' + raw.split('-')[1] if len(raw.split('-'))>=2 else raw
            labels = [_label_from_prefix(prefix)]
            # collect following paragraph as body until next blank line or heading
            body_lines = []
            for j in range(i+1, min(i+20, len(lines))):
                nl = lines[j]
                if nl.strip().startswith('#') and j!=i+1:
                    break
                if nl.strip() == '':
                    if body_lines:
                        break
                    else:
                        continue
                body_lines.append(nl)
            body = '\n'.join(body_lines).strip()
            items.append({
                'id': str(uuid.uuid4()),
                'raw_title': raw,
                'candidate_title': candidate_title,
                'labels': labels,
                'body': body,
            })
    return items


def _list_existing_issue_titles(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    headers = {'Authorization': f'token {token}'} if token else {}
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


def _create_issue(owner: str, repo: str, token: str, title: str, body: str, labels: List[str], assignee: str = None):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'} if token else {'Accept': 'application/vnd.github.v3+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/issues'
    payload = {'title': title, 'body': body or ''}
    if labels:
        payload['labels'] = labels
    if assignee:
        payload['assignee'] = assignee
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    return r


def _update_issue(owner: str, repo: str, token: str, number: int, title: str, body: str, labels: List[str], assignee: str = None):
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'} if token else {'Accept': 'application/vnd.github.v3+json'}
    url = f'https://api.github.com/repos/{owner}/{repo}/issues/{number}'
    payload = {'title': title, 'body': body or ''}
    if labels is not None:
        payload['labels'] = labels
    if assignee is not None:
        payload['assignee'] = assignee
    r = requests.patch(url, headers=headers, json=payload, timeout=15)
    return r


def start_create_task(items: List[Dict[str, Any]], repo_full: str, token: str, on_conflict: str = 'skip') -> str:
    """Start background task to create issues. Returns task_id."""
    task_id = str(uuid.uuid4())
    owner, repo = repo_full.split('/', 1)
    _TASKS[task_id] = {'items': [], 'status': 'running', 'created': 0, 'skipped': 0, 'failed': 0, 'results': []}

    def _worker():
        try:
            existing = _list_existing_issue_titles(owner, repo, token)
            existing_map = {e['title']: e for e in existing}
        except Exception:
            existing_map = {}

        for it in items:
            rec = {'id': it.get('id'), 'title': it.get('title'), 'status': 'pending'}
            _TASKS[task_id]['items'].append(rec)
            # conflict check
            if it.get('title') in existing_map:
                rec['status'] = 'skipped'
                rec['reason'] = 'exists'
                rec['existing'] = existing_map[it.get('title')]
                _TASKS[task_id]['skipped'] += 1
                _TASKS[task_id]['results'].append(rec)
                continue
            # create
            try:
                r = _create_issue(owner, repo, token, it.get('title'), it.get('body'), it.get('labels', []), it.get('assignee'))
                if r.status_code in (200, 201):
                    data = r.json()
                    rec['status'] = 'created'
                    rec['number'] = data.get('number')
                    rec['url'] = data.get('html_url')
                    _TASKS[task_id]['created'] += 1
                else:
                    rec['status'] = 'failed'
                    rec['reason'] = f'{r.status_code} {r.text[:200]}'
                    _TASKS[task_id]['failed'] += 1
                _TASKS[task_id]['results'].append(rec)
            except Exception as e:
                rec['status'] = 'failed'
                rec['reason'] = str(e)
                _TASKS[task_id]['failed'] += 1
                _TASKS[task_id]['results'].append(rec)
            # small delay to be nice to API
            time.sleep(0.2)
        _TASKS[task_id]['status'] = 'finished'

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    return task_id


def get_task_status(task_id: str) -> Dict[str, Any]:
    return _TASKS.get(task_id, {'status': 'unknown'})
