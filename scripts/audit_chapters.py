#!/usr/bin/env python3
"""
全书规范审计脚本 — 依据 contributing.md 检查 docs/ 下所有章节文件。
输出 JSON 报告，按文件→规则分组列出违规项。
"""
import re, json, sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / 'docs'
TARGETS = sorted(
    list(DOCS.glob('chapter*.md')) + list(DOCS.glob('appendix_*.md'))
)

# --- helpers ---
def is_in_fence(lines, idx):
    """Check if line idx is inside a fenced code block."""
    count = 0
    for i in range(idx):
        if lines[i].strip().startswith('```'):
            count += 1
    return count % 2 == 1

# --- checks ---
def check_frontmatter(fname, lines):
    """§1.1: YAML frontmatter with number headings."""
    issues = []
    if not lines or lines[0].strip() != '---':
        issues.append({'line': 1, 'rule': '§1.1', 'msg': '缺少 YAML frontmatter'})
        return issues
    end = -1
    for i in range(1, min(10, len(lines))):
        if lines[i].strip() == '---':
            end = i
            break
    if end == -1:
        issues.append({'line': 1, 'rule': '§1.1', 'msg': 'frontmatter 未闭合'})
        return issues
    fm = '\n'.join(lines[1:end])
    if 'number headings' not in fm:
        issues.append({'line': 1, 'rule': '§1.1', 'msg': 'frontmatter 缺少 number headings'})
    # check start-at matches chapter number
    m = re.search(r'start-at\s+(\d+)', fm)
    chm = re.search(r'chapter(\d+)', fname)
    if m and chm and m.group(1) != chm.group(1):
        issues.append({'line': 2, 'rule': '§1.1', 'msg': f'start-at {m.group(1)} 与文件名 chapter{chm.group(1)} 不匹配'})
    return issues

def check_headings(fname, lines):
    """§2: 标题层级与编号。"""
    issues = []
    for i, ln in enumerate(lines):
        if is_in_fence(lines, i):
            continue
        s = ln.strip()
        if s.startswith('# ') and not s.startswith('## '):
            issues.append({'line': i+1, 'rule': '§2', 'msg': '使用了禁止的 H1 标题'})
    return issues

def check_cn_en_spacing(fname, lines):
    """§3.1: 中英文之间加空格。抽样检查（不逐行，只报总数）。"""
    issues = []
    pat = re.compile(r'[\u4e00-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u4e00-\u9fff]')
    count = 0
    samples = []
    for i, ln in enumerate(lines):
        if is_in_fence(lines, i):
            continue
        s = ln.strip()
        # skip headings, links, html comments, frontmatter
        if s.startswith('#') or s.startswith('<!--') or s.startswith('|') or s.startswith('```') or s.startswith('---') or s.startswith('[') or s.startswith('**'):
            continue
        matches = pat.findall(s)
        if matches:
            count += len(matches)
            if len(samples) < 5:
                samples.append({'line': i+1, 'text': s[:80]})
    if count > 0:
        issues.append({'line': 0, 'rule': '§3.1', 'msg': f'中英文/数字间缺空格 {count} 处', 'samples': samples})
    return issues

def check_code_blocks(fname, lines):
    """§5.1: 代码块须标注语言；§12: 不用 svgbob。"""
    issues = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == '```':
            # bare code fence — check if it's opening (not closing)
            # count previous fences
            prev_fences = sum(1 for j in range(i) if lines[j].strip().startswith('```'))
            if prev_fences % 2 == 0:  # opening fence
                issues.append({'line': i+1, 'rule': '§5.1', 'msg': '裸代码块缺少语言标注'})
        if s.startswith('```svgbob'):
            issues.append({'line': i+1, 'rule': '§12', 'msg': '应使用 ```bob 而非 ```svgbob'})
    return issues

def check_math(fname, lines):
    """§6: $$ 须独占行。"""
    issues = []
    for i, ln in enumerate(lines):
        if is_in_fence(lines, i):
            continue
        s = ln.strip()
        # line contains $$ but also has other content
        if '$$' in s and s != '$$' and not s.startswith('<!--'):
            # allow $$ at start/end with content (block formula inline)
            if s.startswith('$$') and len(s) > 2 and not s.endswith('$$'):
                pass  # opening $$ with formula start — ok in some renderers
            elif s.endswith('$$') and len(s) > 2 and not s.startswith('$$'):
                pass
            elif s.count('$$') >= 2 and s.startswith('$$') and s.endswith('$$'):
                issues.append({'line': i+1, 'rule': '§6', 'msg': '$$ 公式未独占行（单行内开闭）'})
    return issues

def check_chapter_structure(fname, lines):
    """§1.2: 检查是否有小结和测验节。"""
    issues = []
    text = '\n'.join(lines)
    if 'chapter' not in fname:
        return issues
    if '小结' not in text and '本章小结' not in text:
        issues.append({'line': 0, 'rule': '§1.2', 'msg': '缺少"本章小结"节'})
    if '测验' not in text and '本章测验' not in text:
        issues.append({'line': 0, 'rule': '§1.2', 'msg': '缺少"本章测验"节'})
    return issues

def check_tables_figures_desc(fname, lines):
    """§0.3/§4: 表格和图后须有正文描述。检查 <!-- desc-auto --> 占位是否仍存在。"""
    issues = []
    count = 0
    for i, ln in enumerate(lines):
        if '<!-- desc-auto -->' in ln:
            count += 1
    if count > 0:
        issues.append({'line': 0, 'rule': '§0.3', 'msg': f'仍有 {count} 处自动占位描述（<!-- desc-auto -->）需替换为有意义的正文'})
    return issues

def check_quiz_format(fname, lines):
    """§8: 测验格式（quiz 标签配对）。"""
    issues = []
    opens = 0
    closes = 0
    for i, ln in enumerate(lines):
        if '<quiz>' in ln.lower():
            opens += 1
        if '</quiz>' in ln.lower():
            closes += 1
    if opens != closes:
        issues.append({'line': 0, 'rule': '§8', 'msg': f'quiz 标签不配对（开 {opens} 个，闭 {closes} 个）'})
    return issues

def check_desc_auto_placeholders(fname, lines):
    """检查自动生成的描述占位是否过于模板化。"""
    issues = []
    pat = re.compile(r'<!-- desc-auto -->')
    count = sum(1 for ln in lines if pat.search(ln))
    if count > 0:
        issues.append({'line': 0, 'rule': '§0.3-auto', 'msg': f'{count} 处 desc-auto 占位需人工审核'})
    return issues

# --- main ---
def audit_file(fpath):
    lines = fpath.read_text(encoding='utf-8').splitlines()
    fname = fpath.name
    results = []
    for check_fn in [check_frontmatter, check_headings, check_cn_en_spacing,
                     check_code_blocks, check_math, check_chapter_structure,
                     check_tables_figures_desc, check_quiz_format]:
        results.extend(check_fn(fname, lines))
    return results

report = {}
total = 0
for fpath in TARGETS:
    issues = audit_file(fpath)
    if issues:
        report[fpath.name] = issues
        total += len(issues)

# summary
print(f"\n{'='*60}")
print(f"审计完成：{len(TARGETS)} 个文件，发现 {total} 项违规")
print(f"{'='*60}\n")

for fname, issues in sorted(report.items()):
    print(f"\n📄 {fname} ({len(issues)} 项)")
    for it in issues:
        line_str = f"L{it['line']}" if it['line'] else "全局"
        print(f"  [{it['rule']}] {line_str}: {it['msg']}")
        if 'samples' in it:
            for s in it['samples'][:3]:
                print(f"    → L{s['line']}: {s['text']}")

# write JSON
out = Path(__file__).resolve().parent / 'audit_report.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n详细报告已写入: {out}")
