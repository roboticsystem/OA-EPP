#!/usr/bin/env python3
"""fix_bob_quotes.py - svgbob 双引号转义工具

自动为 bob 图块中含有 () _ / * 的编程文本添加 "..." 双引号转义，
使 svgbob 将其渲染为纯文本而非绘图元素。

工作原理：
  svgbob 中，双引号 "..." 内的所有字符被视为纯文本。
  每个 " 占 1 个网格单元但不可见。脚本通过"偷取"相邻空格
  来放置 "，从而维持原始对齐宽度。

  同时自动回退上一方案残留的 Unicode 替换字符（∕⟮⟯ˍ∗）。

用法：
  python fix_bob_quotes.py docs/chapter1.md --dry-run     # 预览变更
  python fix_bob_quotes.py docs/chapter1.md --inplace      # 原地修改
  python fix_bob_quotes.py docs/*.md --dry-run             # 批量预览
"""

import re
import sys
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────────

# svgbob 会把这些 ASCII 字符当绘图指令
PROBLEM_CHARS = set('()_/*\\')

# 上一方案残留的 Unicode 替换（需回退为原始 ASCII）
UNICODE_REVERSE = {
    '∕': '/',   # U+2215 DIVISION SLASH
    '⟮': '(',   # U+27EE MATHEMATICAL LEFT FLATTENED PARENTHESIS
    '⟯': ')',   # U+27EF MATHEMATICAL RIGHT FLATTENED PARENTHESIS
    'ˍ': '_',   # U+02CD MODIFIER LETTER LOW MACRON
    '∗': '*',   # U+2217 ASTERISK OPERATOR
}

# 方框绘图字符集
BOX_CHARS = set('─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬━┃┏┓┗┛┣┫┳┻╋')

# 结构绘图字符集（不应出现在引号内）
STRUCTURAL = BOX_CHARS | set('►◄▲▼→←↓↑▸◂▾▴◆●○◎')

# 匹配"单词"的正则：排除空白和结构绘图字符
_excl = ''.join(re.escape(c) for c in sorted(STRUCTURAL))
WORD_RE = re.compile(r'[^\s' + _excl + r']+')

# 文本模式：连续 2+ 字母、2+ 数字、字母数字混合、或 CJK
TEXT_PATTERN = re.compile(
    r'[a-zA-Z]{2,}|\d{2,}|[a-zA-Z]\d|\d[a-zA-Z]'
    r'|[\u2E80-\u9FFF\u3400-\u4DBF\uF900-\uFAFF]'
)


# ── 核心函数 ──────────────────────────────────────────────────────────

def has_problem(text):
    """文本是否含有会被 svgbob 当绘图指令的字符"""
    return any(c in PROBLEM_CHARS for c in text)


def needs_quoting_strict(word):
    """严格判定：需同时含文本字符和问题字符。

    用于非框内上下文（独立行 / 框外部分），避免引号破坏绘图结构线。
    文本字符 = 2+ 连续字母、2+ 数字、字母数字混合、或含 CJK。
    单个字母（如 svgbob 的 o 圆点、v 箭头）不视为文本。
    """
    return bool(TEXT_PATTERN.search(word)) and has_problem(word)


def is_border(line):
    """判断是否为纯边框线（─┌┐└┘├ 等，不含文本内容）"""
    s = line.strip()
    if not s:
        return True
    return all(c in BOX_CHARS or c in ' -+=|' for c in s)


def reverse_unicode(text):
    """回退上一方案的 Unicode 字符替换"""
    for u, a in UNICODE_REVERSE.items():
        text = text.replace(u, a)
    return text


def quote_segments(content, strict=False):
    """为含问题字符的文本段添加 "..." 引号。

    策略：
    1. 以 WORD_RE 匹配独立单词（排除结构绘图字符）
    2. strict=False（框内）：任何含问题字符的单词都加引号
       strict=True （框外）：仅对含文本字符+问题字符的单词加引号
    3. 相邻（间距≤2）的引号段合并；括号对 (...) 也合并为一个段
    4. 开引号偷取前方空格，闭引号偷取后方空格
       （因 " 在 svgbob 中不可见但占 1 格，与空格视觉等价）
    """
    segments = list(WORD_RE.finditer(content))

    if strict:
        to_quote = [(m.start(), m.end()) for m in segments
                     if needs_quoting_strict(m.group())]
    else:
        to_quote = [(m.start(), m.end()) for m in segments
                     if has_problem(m.group())]

    if not to_quote:
        return content

    # 合并相邻段（间距 ≤ 2），避免 "" 丢失空格
    merged = []
    for s, e in to_quote:
        if merged and s - merged[-1][1] <= 2:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append([s, e])

    # 合并括号对：如果某段有不匹配的 ( ，找后续段中不匹配的 ) 合并
    i = 0
    while i < len(merged):
        first_text = content[merged[i][0]:merged[i][1]]
        if '(' in first_text and ')' not in first_text:
            for j in range(i + 1, len(merged)):
                later_text = content[merged[j][0]:merged[j][1]]
                if ')' in later_text and '(' not in later_text:
                    merged[i] = [merged[i][0], merged[j][1]]
                    del merged[i + 1:j + 1]
                    break
        i += 1

    to_quote = [(s, e) for s, e in merged]

    # 构建结果，偷取空格放置引号
    result = []
    pos = 0

    for start, end in to_quote:
        prefix = content[pos:start]

        # 开引号偷取 prefix 末尾空格
        if prefix and prefix[-1] == ' ':
            prefix = prefix[:-1]
        result.append(prefix)

        # 添加 "segment"
        result.append('"')
        result.append(content[start:end])
        result.append('"')

        # 闭引号偷取后方空格
        pos = end
        if pos < len(content) and content[pos] == ' ':
            pos += 1

    result.append(content[pos:])

    # 修复 \" 转义：svgbob 把 \" 当作转义引号，导致 " 不关闭文本模式
    # 在 \ 和 " 之间插入空格：\"  →  \ "
    final = ''.join(result)
    final = final.replace('\\"', '\\ "')
    return final


def process_boxed_line(line):
    """处理有 │ 边框的内容行。

    将行按 │ 拆分为单元格：
    - 内部单元格：宽松模式（任何问题字符都引号化）
    - 外部部分（首│前、末│后）：严格模式（需兼有文本和问题字符）
    """
    parts = line.split('│')
    if len(parts) < 3:  # 至少要有 │content│
        return line

    new_parts = []

    for i, part in enumerate(parts):
        if i == 0 or i == len(parts) - 1:
            # 框外：严格模式，避免破坏绘图结构
            if has_problem(part):
                new_parts.append(quote_segments(part, strict=True))
            else:
                new_parts.append(part)
        else:
            # 框内：宽松模式，问题字符都是文本
            if has_problem(part):
                new_parts.append(quote_segments(part, strict=False))
            else:
                new_parts.append(part)

    return '│'.join(new_parts)


def is_text_heavy(line):
    """判断行内容是否以文本为主（vs 以绘图字符为主）。

    阈值 30%：超过 30% 的非空字符为字母/数字/CJK 即视为文本行。
    """
    chars = [c for c in line if not c.isspace()]
    if not chars:
        return False
    alpha_cjk = sum(1 for c in chars if c.isalnum() or ord(c) > 0x2E80)
    return alpha_cjk / len(chars) > 0.3


def process_standalone_line(line):
    """处理无边框的独立文本行。

    - 文本为主的行（>30% 字母/数字/CJK）：宽松模式，所有问题字符都引号化
    - 绘图为主的行（如 /-o-/--）：严格模式，仅引号化明确的编程文本
    """
    if not has_problem(line):
        return line
    if is_text_heavy(line):
        return quote_segments(line, strict=False)
    return quote_segments(line, strict=True)


def process_block(content):
    """处理一个 bob 块：清除旧引号 → 回退 Unicode → 添加新引号"""
    # 幂等性：先清除上次运行添加的引号和 \" 修补空格
    content = content.replace('\\ "', '\\')   # 撤销 \" 修补
    content = content.replace('"', ' ')        # 引号还原为空格（每个 " 偷取了一个空格）

    content = reverse_unicode(content)

    lines = content.split('\n')
    result = []

    for line in lines:
        if is_border(line):
            result.append(line)
        elif '│' in line:
            result.append(process_boxed_line(line))
        else:
            result.append(process_standalone_line(line))

    return '\n'.join(result)


# ── 文件处理 ──────────────────────────────────────────────────────────

def process_file(filepath, dry_run=False, inplace=False):
    """处理 markdown 文件"""
    text = Path(filepath).read_text('utf-8')

    stats = {'blocks': 0, 'quotes': 0, 'unicode_reverted': 0}

    # 统计待回退的 Unicode 字符数
    for u in UNICODE_REVERSE:
        stats['unicode_reverted'] += text.count(u)

    def replacer(m):
        stats['blocks'] += 1
        old = m.group(2)
        new = process_block(old)
        stats['quotes'] += (new.count('"') - old.count('"')) // 2
        return m.group(1) + new + m.group(3)

    new_text = re.sub(r'(```bob\n)(.*?)(```)', replacer, text, flags=re.DOTALL)

    # 比较时忽略行尾空白差异（\" 修复导致的 1 空格振荡）
    def strip_trailing(s):
        return '\n'.join(line.rstrip() for line in s.split('\n'))
    changed = strip_trailing(text) != strip_trailing(new_text)

    # 无功能变化时（0 引号 + 0 回退）不写文件，避免尾部空白振荡
    functional = stats['quotes'] != 0 or stats['unicode_reverted'] > 0

    print(f'{filepath}:')
    print(f'  {stats["blocks"]} 个 bob 块')
    print(f'  {stats["unicode_reverted"]} 个 Unicode 字符已回退')
    print(f'  {stats["quotes"]} 对双引号已添加')

    if not changed:
        print(f'  无变化')
        return

    if dry_run:
        old_lines = text.split('\n')
        new_lines = new_text.split('\n')
        shown = 0
        for i, (o, n) in enumerate(zip(old_lines, new_lines)):
            if o != n and shown < 20:
                print(f'  L{i+1}:')
                print(f'    - {o[:120]}')
                print(f'    + {n[:120]}')
                shown += 1
        total_diffs = sum(1 for o, n in zip(old_lines, new_lines) if o != n)
        if shown < total_diffs:
            print(f'  ... 共 {total_diffs} 行变化')
    elif inplace:
        if functional:
            Path(filepath).write_text(new_text, 'utf-8')
            print(f'  ✓ 已保存')
        else:
            print(f'  无实质变化')
    else:
        sys.stdout.write(new_text)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='为 bob 图块添加 "..." 双引号转义')
    p.add_argument('files', nargs='+', help='Markdown 文件路径')
    p.add_argument('--dry-run', action='store_true', help='仅预览不修改')
    p.add_argument('--inplace', action='store_true', help='原地修改文件')
    args = p.parse_args()

    for f in args.files:
        process_file(f, args.dry_run, args.inplace)
