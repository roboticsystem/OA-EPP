#!/usr/bin/env python3
"""
自动修复三类可机械化处理的规范违规：
1. §3.1 中英文/数字间缺空格
2. §5.1 裸代码块缺语言标注（推断语言或标注 text）
3. §6 $$ 公式未独占行
"""
import re, sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / 'docs'
TARGETS = sorted(
    list(DOCS.glob('chapter*.md')) + list(DOCS.glob('appendix_*.md'))
)
DRY = '--dry-run' in sys.argv

# ==================== §3.1 中英文空格 ====================

# 中文 → 英文/数字
CN_EN = re.compile(r'([\u4e00-\u9fff\u3400-\u4dbf])([A-Za-z0-9\$`])')
# 英文/数字 → 中文
EN_CN = re.compile(r'([A-Za-z0-9%\$`\)\]])( ?)([\u4e00-\u9fff\u3400-\u4dbf])')

def fix_cn_en_spacing(line):
    """在中英文/数字间插入空格。跳过 URLs、HTML 标签、Markdown 链接内部。"""
    # skip lines that are mostly code/links/html
    stripped = line.strip()
    if stripped.startswith('<!--') or stripped.startswith('<') or stripped.startswith('|'):
        return line
    if stripped.startswith('```') or stripped.startswith('---'):
        return line

    result = CN_EN.sub(r'\1 \2', line)
    result = EN_CN.sub(lambda m: m.group(1) + ' ' + m.group(3) if not m.group(2) else m.group(0), result)
    return result

# ==================== §5.1 裸代码块 ====================

def infer_language(lines, fence_idx):
    """Try to infer language from content after a bare ``` fence."""
    for i in range(fence_idx + 1, min(fence_idx + 10, len(lines))):
        ln = lines[i].strip()
        if ln.startswith('```'):
            break
        if ln.startswith('#include') or ln.startswith('void ') or ln.startswith('int ') or 'HAL_' in ln or ln.startswith('typedef'):
            return 'c'
        if ln.startswith('import ') or ln.startswith('from ') or ln.startswith('def ') or ln.startswith('class '):
            return 'python'
        if ln.startswith('$') or ln.startswith('sudo') or ln.startswith('cd ') or ln.startswith('git ') or ln.startswith('mkdir') or ln.startswith('pip') or ln.startswith('apt'):
            return 'bash'
        if ln.startswith('apiVersion:') or ln.startswith('services:') or ln.startswith('version:'):
            return 'yaml'
        if '<' in ln and '>' in ln and ('xml' in ln.lower() or 'html' in ln.lower()):
            return 'xml'
        if ln.startswith('{') or ln.startswith('"'):
            return 'json'
        if ln.startswith('@start') or ln.startswith('@end'):
            return 'plantuml'
    return 'text'

# ==================== §6 $$ 公式独占行 ====================

def fix_math_blocks(lines):
    """Split $$ ... $$ on single line into three lines."""
    new_lines = []
    i = 0
    changes = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        # Check if inside fence
        fence_count = sum(1 for j in range(i) if lines[j].strip().startswith('```'))
        if fence_count % 2 == 1:
            new_lines.append(ln)
            i += 1
            continue
        # Single line $$ ... $$ (both open and close on same line)
        if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 4:
            content = stripped[2:-2].strip()
            indent = ln[:len(ln) - len(ln.lstrip())]
            new_lines.append(indent + '$$\n')
            new_lines.append(indent + content + '\n')
            new_lines.append(indent + '$$\n')
            changes += 1
            i += 1
            continue
        new_lines.append(ln)
        i += 1
    return new_lines, changes

# ==================== main ====================

stats = {'spacing': 0, 'bare_fence': 0, 'math': 0}

for fpath in TARGETS:
    lines = fpath.read_text(encoding='utf-8').splitlines(keepends=True)
    changed = False

    # --- Fix bare code fences (§5.1) ---
    new_lines = []
    in_fence = False
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith('```'):
            if not in_fence:
                # opening fence
                if stripped == '```':
                    lang = infer_language(lines, i)
                    new_lines.append(ln.replace('```', f'```{lang}', 1))
                    stats['bare_fence'] += 1
                    changed = True
                    in_fence = True
                    continue
                else:
                    in_fence = True
            else:
                in_fence = False
        new_lines.append(ln)
    lines = new_lines

    # --- Fix $$ math blocks (§6) ---
    lines, math_changes = fix_math_blocks(lines)
    if math_changes:
        stats['math'] += math_changes
        changed = True

    # --- Fix CN-EN spacing (§3.1) ---
    new_lines = []
    in_fence = False
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith('```'):
            in_fence = not in_fence
            new_lines.append(ln)
            continue
        if in_fence:
            new_lines.append(ln)
            continue
        fixed = fix_cn_en_spacing(ln)
        if fixed != ln:
            stats['spacing'] += 1
            changed = True
        new_lines.append(fixed)
    lines = new_lines

    if changed and not DRY:
        fpath.write_text(''.join(lines), encoding='utf-8')
        print(f'✓ {fpath.name}')
    elif changed:
        print(f'[dry] {fpath.name}')

print(f"\n修复统计：")
print(f"  中英文空格: {stats['spacing']} 行")
print(f"  裸代码块: {stats['bare_fence']} 个")
print(f"  $$ 公式: {stats['math']} 处")
