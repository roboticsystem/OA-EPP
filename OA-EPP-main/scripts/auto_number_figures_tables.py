#!/usr/bin/env python3
"""
全书图表自动编号脚本
====================
功能：
  1. 扫描 docs/ 下所有章节与附录 Markdown 文件
  2. 识别图（bob/plantuml/mermaid 代码块、<img>、![]()）和表（Markdown 管道表格）
  3. 按章分配编号：图 X-Y / 表 X-Y
  4. 在图下方插入/更新图说，在表上方插入/更新表说
  5. 更新正文中的交叉引用
  6. 可选生成图目录与表目录
  7. 将 <!-- autoplaceholder --> 转换为适当的 fig/tab 标记

用法：
  python scripts/auto_number_figures_tables.py [--dry-run] [--toc] [--refs-only]

标记约定（详见 .github/skills/auto-figure-table-numbering/SKILL.md）：
  图说：<!-- fig:chX-Y 描述 -->  显示为  **图 X-Y** 描述
  表说：<!-- tab:chX-Y 描述 -->  显示为  **表 X-Y** 描述
"""

import re
import sys
import argparse
from pathlib import Path
from collections import OrderedDict

DOCS = Path(__file__).resolve().parents[1] / 'docs'

# ── 章号提取 ──────────────────────────────────────────────────────
def extract_chapter_id(filepath: Path) -> str:
    """从文件名提取章号：chapter3.md→'3', appendix_a.md→'A'"""
    name = filepath.stem
    if name.startswith('chapter'):
        return name.replace('chapter', '')
    elif name.startswith('appendix_'):
        letter = name.replace('appendix_', '').upper()
        return letter
    return None

def get_ordered_files() -> list:
    """按教材顺序返回 (filepath, chapter_id) 列表"""
    files = []
    # 正文章节
    chapters = sorted(DOCS.glob('chapter*.md'),
                      key=lambda p: int(p.stem.replace('chapter', '')))
    for f in chapters:
        cid = extract_chapter_id(f)
        if cid:
            files.append((f, cid))
    # 附录
    appendices = sorted(DOCS.glob('appendix_*.md'))
    for f in appendices:
        cid = extract_chapter_id(f)
        if cid:
            files.append((f, cid))
    return files

# ── 元素检测 ──────────────────────────────────────────────────────
FENCE_START = re.compile(r'^```(bob|plantuml|mermaid)\b')
FENCE_END = re.compile(r'^```\s*$')
IMAGE_LINE = re.compile(r'!\[.*\]\(.*\)')
HTML_IMG = re.compile(r'<img\s', re.I)
TABLE_LINE = re.compile(r'^\|.*\|')
TABLE_SEP = re.compile(r'^\|[\s:]*-+[\s:]*\|')
HEADING = re.compile(r'^(#{1,6})\s')

# 现有标记
FIG_MARKER = re.compile(r'<!--\s*fig(?::ch[\w]+-\d+)?\s*(.*?)\s*-->')
TAB_MARKER = re.compile(r'<!--\s*tab(?::ch[\w]+-\d+)?\s*(.*?)\s*-->')
FIG_BOLD = re.compile(r'^\*\*图\s*[\w]+-\d+\*\*\s*(.*)')
TAB_BOLD = re.compile(r'^\*\*表\s*[\w]+-\d+\*\*\s*(.*)')
AUTOPLACEHOLDER = re.compile(r'<!--\s*autoplaceholder\s*-->')
# 独立描述行（scan window 中遇到时跳过而非中断扫描）
DESC_STANDALONE = re.compile(r'^(上[图表]|该[图表]|从上|通过上|如上|此[图表])')

# 正文引用：图 X-Y 或 表 X-Y（含中文空格变体）
REF_FIG = re.compile(r'图\s*([\w]+)-([\d]+)')
REF_TAB = re.compile(r'表\s*([\w]+)-([\d]+)')


def is_inside_code_fence(lines, idx):
    """判断给定行是否在代码围栏内部（非 bob/plantuml/mermaid 的围栏也算）"""
    in_fence = False
    for i in range(idx):
        ln = lines[i].rstrip()
        if ln.startswith('```'):
            in_fence = not in_fence
    return in_fence


class Element:
    """表示一个图或表元素"""
    def __init__(self, kind, start_line, end_line, caption='', marker_line=None, bold_line=None):
        self.kind = kind            # 'fig' or 'tab'
        self.start_line = start_line
        self.end_line = end_line
        self.caption = caption
        self.marker_line = marker_line  # <!-- fig/tab:... --> 所在行号
        self.bold_line = bold_line      # **图/表 X-Y** 所在行号
        self.number = None              # 将被分配
        self.chapter_id = None


def scan_elements(lines: list) -> list:
    """扫描 Markdown 行列表，返回 Element 列表（按文件顺序）"""
    elements = []
    n = len(lines)
    i = 0

    while i < n:
        ln = lines[i].rstrip()

        # ── 代码块图（bob/plantuml/mermaid）──
        m_fence = FENCE_START.match(ln)
        if m_fence:
            start = i
            j = i + 1
            while j < n and not FENCE_END.match(lines[j].rstrip()):
                j += 1
            end = j  # ``` 结束行
            # 查找图说标记：在 end+1..end+8 范围内查找
            caption = ''
            marker_line = None
            bold_line = None
            for k in range(end + 1, min(end + 9, n)):
                lk = lines[k].strip()
                if not lk:
                    continue
                mf = FIG_MARKER.search(lk)
                if mf:
                    if not caption:  # bold 行描述优先
                        caption = mf.group(1).strip()
                    marker_line = k
                    continue
                mb = FIG_BOLD.match(lk)
                if mb:
                    bold_line = k
                    bold_caption = mb.group(1).strip()
                    if bold_caption:
                        caption = bold_caption
                    continue
                if AUTOPLACEHOLDER.search(lk):
                    marker_line = k
                    if not caption:
                        caption = '（请补充图说）'
                    break
                if DESC_STANDALONE.match(lk):
                    continue  # 跳过独立描述行
                break  # 遇到其他内容则停止

            elements.append(Element('fig', start, end, caption, marker_line, bold_line))
            i = end + 1
            continue

        # ── 图片行 ──
        if IMAGE_LINE.search(ln) or HTML_IMG.search(ln):
            if not is_inside_code_fence(lines, i):
                caption = ''
                marker_line = None
                bold_line = None
                for k in range(i + 1, min(i + 9, n)):
                    lk = lines[k].strip()
                    if not lk:
                        continue
                    mf = FIG_MARKER.search(lk)
                    if mf:
                        if not caption:
                            caption = mf.group(1).strip()
                        marker_line = k
                        continue
                    mb = FIG_BOLD.match(lk)
                    if mb:
                        bold_line = k
                        bold_caption = mb.group(1).strip()
                        if bold_caption:
                            caption = bold_caption
                        continue
                    if AUTOPLACEHOLDER.search(lk):
                        marker_line = k
                        if not caption:
                            caption = '（请补充图说）'
                        break
                    if DESC_STANDALONE.match(lk):
                        continue  # 跳过独立描述行
                    break
                elements.append(Element('fig', i, i, caption, marker_line, bold_line))
            i += 1
            continue

        # ── Markdown 管道表格 ──
        if TABLE_LINE.match(ln) and not is_inside_code_fence(lines, i):
            # 确认是真正的表格（需要有分隔行）
            start = i
            j = i
            has_sep = False
            while j < n and TABLE_LINE.match(lines[j].rstrip()):
                if TABLE_SEP.match(lines[j].rstrip()):
                    has_sep = True
                j += 1
            if has_sep:
                end = j - 1  # 最后一个表格行
                # 查找表说标记：在 start-1..start-4 范围内（表说在上方）
                caption = ''
                marker_line = None
                bold_line = None
                for k in range(start - 1, max(start - 9, -1), -1):
                    lk = lines[k].strip()
                    if not lk:
                        continue
                    mt = TAB_MARKER.search(lk)
                    if mt:
                        if not caption:  # bold 行描述优先
                            caption = mt.group(1).strip()
                        marker_line = k
                        continue
                    mb = TAB_BOLD.match(lk)
                    if mb:
                        bold_line = k
                        bold_caption = mb.group(1).strip()
                        if bold_caption:
                            caption = bold_caption
                        continue
                    if AUTOPLACEHOLDER.search(lk):
                        marker_line = k
                        if not caption:
                            caption = '（请补充表说）'
                        break
                    if DESC_STANDALONE.match(lk):
                        continue  # 跳过独立描述行
                    break
                # 也检查表格后的 autoplaceholder（之前脚本插入在后方的）
                if not marker_line:
                    for k in range(end + 1, min(end + 9, n)):
                        lk = lines[k].strip()
                        if not lk:
                            continue
                        if AUTOPLACEHOLDER.search(lk):
                            marker_line = k
                            if not caption:
                                caption = '（请补充表说）'
                            break
                        mt = TAB_MARKER.search(lk)
                        if mt:
                            if not caption:
                                caption = mt.group(1).strip()
                            marker_line = k
                            break
                        break

                elements.append(Element('tab', start, end, caption, marker_line, bold_line))
                i = j
                continue

        i += 1

    return elements


def assign_numbers(elements: list, chapter_id: str):
    """为元素分配章内序号"""
    fig_count = 0
    tab_count = 0
    for el in elements:
        el.chapter_id = chapter_id
        if el.kind == 'fig':
            fig_count += 1
            el.number = fig_count
        else:
            tab_count += 1
            el.number = tab_count


def apply_numbering(lines: list, elements: list, chapter_id: str) -> list:
    """在行列表中插入/更新编号标记，返回新的行列表。
    策略：收集所有操作后按行号降序执行，高行号先处理不影响低行号索引。"""
    ops = []  # (line_idx, action, content)

    for el in elements:
        label = f'{chapter_id}-{el.number}'
        if el.kind == 'fig':
            bold_text = f'**图 {label}** {el.caption}\n'
            marker_text = f'<!-- fig:ch{label} {el.caption} -->\n'

            if el.bold_line is not None and el.marker_line is not None:
                ops.append((el.bold_line, 'replace', bold_text))
                ops.append((el.marker_line, 'replace', marker_text))
            elif el.marker_line is not None and el.bold_line is None:
                ops.append((el.marker_line, 'replace', f'\n{bold_text}{marker_text}'))
            elif el.bold_line is not None and el.marker_line is None:
                # bold 行存在但无 marker → 替换 bold 并在其后插入 marker
                ops.append((el.bold_line, 'replace', f'{bold_text}{marker_text}'))
            else:
                ops.append((el.end_line + 1, 'insert', f'\n{bold_text}{marker_text}'))

        else:  # tab
            bold_text = f'**表 {label}** {el.caption}\n'
            marker_text = f'<!-- tab:ch{label} {el.caption} -->\n'

            if el.bold_line is not None and el.marker_line is not None:
                ops.append((el.bold_line, 'replace', bold_text))
                ops.append((el.marker_line, 'replace', marker_text))
            elif el.marker_line is not None and el.bold_line is None:
                if el.marker_line > el.start_line:
                    # autoplaceholder 在表下方 → 删除它，在表上方插入
                    ops.append((el.marker_line, 'delete', ''))
                    ops.append((el.start_line, 'insert_before', f'{bold_text}{marker_text}\n'))
                else:
                    ops.append((el.marker_line, 'replace', f'{bold_text}{marker_text}'))
            elif el.bold_line is not None and el.marker_line is None:
                # bold 行存在但无 marker → 替换 bold 并插入 marker
                ops.append((el.bold_line, 'replace', f'{bold_text}{marker_text}'))
            else:
                ops.append((el.start_line, 'insert_before', f'{bold_text}{marker_text}\n'))

    # 按行号降序：高行号先处理，不影响低行号的绝对索引
    ops.sort(key=lambda x: (-x[0], x[1]))

    new_lines = list(lines)
    for line_idx, action, content in ops:
        if action == 'replace':
            if 0 <= line_idx < len(new_lines):
                new_lines[line_idx] = content
        elif action == 'delete':
            if 0 <= line_idx < len(new_lines):
                new_lines[line_idx] = ''
        elif action in ('insert', 'insert_before'):
            new_lines.insert(line_idx, content)

    return new_lines


def extract_old_label(element, lines):
    """从 element 的 marker 行提取旧编号标签，返回 (kind, old_label_str) 或 None。
    例如 <!-- fig:ch10-3 ... --> → ('fig', '10-3')"""
    if element.marker_line is None:
        return None
    ln = lines[element.marker_line].strip()
    m = re.search(r'<!--\s*(fig|tab):ch([\w]+-\d+)', ln)
    if m:
        return (m.group(1), m.group(2))
    return None


def build_renumber_map(old_labels, new_labels):
    """构建 old_label→new_label 映射字典。
    old_labels 和 new_labels 是平行列表，每项为 (kind, label_str)。"""
    fig_map = {}
    tab_map = {}
    for old, new in zip(old_labels, new_labels):
        if old is None:
            continue
        kind, old_str = old
        _, new_str = new
        if old_str != new_str:
            if kind == 'fig':
                fig_map[old_str] = new_str
            else:
                tab_map[old_str] = new_str
    return fig_map, tab_map


def update_cross_refs(filepath: Path, fig_map: dict, tab_map: dict, dry_run: bool = False) -> int:
    """更新单个文件中正文的交叉引用。返回替换计数。
    排除：代码围栏内、bold/marker 行、HTML 注释内。"""
    if not fig_map and not tab_map:
        return 0

    text = filepath.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    n = len(lines)
    in_fence = False
    total_replacements = 0
    warnings = []
    new_lines = []

    for i, ln in enumerate(lines):
        stripped = ln.rstrip()
        # 跟踪代码围栏
        if stripped.startswith('```'):
            in_fence = not in_fence
            new_lines.append(ln)
            continue
        if in_fence:
            new_lines.append(ln)
            continue
        # 排除 bold/marker 行
        if FIG_BOLD.match(stripped) or TAB_BOLD.match(stripped):
            new_lines.append(ln)
            continue
        if FIG_MARKER.search(stripped) or TAB_MARKER.search(stripped):
            new_lines.append(ln)
            continue

        # 替换图引用
        new_ln = ln
        if fig_map:
            def replace_fig(m):
                nonlocal total_replacements
                old_label = f'{m.group(1)}-{m.group(2)}'
                if old_label in fig_map:
                    total_replacements += 1
                    return f'图 {fig_map[old_label]}'
                return m.group(0)
            new_ln = REF_FIG.sub(replace_fig, new_ln)

        if tab_map:
            def replace_tab(m):
                nonlocal total_replacements
                old_label = f'{m.group(1)}-{m.group(2)}'
                if old_label in tab_map:
                    total_replacements += 1
                    return f'表 {tab_map[old_label]}'
                return m.group(0)
            new_ln = REF_TAB.sub(replace_tab, new_ln)

        new_lines.append(new_ln)

    if total_replacements > 0 and not dry_run:
        filepath.write_text(''.join(new_lines), encoding='utf-8')

    return total_replacements


def build_toc(all_figs: list, all_tabs: list) -> str:
    """生成图目录与表目录的 Markdown 文本"""
    out = []
    out.append('# 图目录\n')
    out.append('| 编号 | 说明 | 位置 |')
    out.append('|------|------|------|')
    for f, cid, el in all_figs:
        label = f'图 {cid}-{el.number}'
        fname = f.name
        out.append(f'| {label} | {el.caption} | [{fname}]({fname}) |')

    out.append('\n# 表目录\n')
    out.append('| 编号 | 说明 | 位置 |')
    out.append('|------|------|------|')
    for f, cid, el in all_tabs:
        label = f'表 {cid}-{el.number}'
        fname = f.name
        out.append(f'| {label} | {el.caption} | [{fname}]({fname}) |')

    return '\n'.join(out) + '\n'


def process_file(filepath: Path, chapter_id: str, dry_run: bool = False):
    """处理单个文件，返回 (fig_elements, tab_elements, old_labels, new_labels)"""
    text = filepath.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)

    elements = scan_elements(lines)

    # 提取旧标签（编号前）
    old_labels = [extract_old_label(e, lines) for e in elements]

    assign_numbers(elements, chapter_id)

    # 构建新标签
    new_labels = [(e.kind, f'{chapter_id}-{e.number}') for e in elements]

    figs = [e for e in elements if e.kind == 'fig']
    tabs = [e for e in elements if e.kind == 'tab']

    if dry_run:
        for e in elements:
            label = f'{chapter_id}-{e.number}'
            kind_cn = '图' if e.kind == 'fig' else '表'
            print(f'  {kind_cn} {label}: L{e.start_line+1} {e.caption or "(无说明)"}')
        return figs, tabs, old_labels, new_labels

    new_lines = apply_numbering(lines, elements, chapter_id)
    new_text = ''.join(new_lines)

    # 清理连续空行（最多保留 2 个）
    new_text = re.sub(r'\n{4,}', '\n\n\n', new_text)

    if new_text != text:
        filepath.write_text(new_text, encoding='utf-8')
        print(f'  ✓ 已更新 {filepath.name}：{len(figs)} 图，{len(tabs)} 表')
    else:
        print(f'  - {filepath.name}：无变更（{len(figs)} 图，{len(tabs)} 表）')

    return figs, tabs, old_labels, new_labels


def main():
    parser = argparse.ArgumentParser(description='全书图表自动编号与交叉引用同步')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不修改文件')
    parser.add_argument('--toc', action='store_true', help='生成图/表目录文件')
    parser.add_argument('--refs-only', action='store_true', help='仅更新交叉引用')
    args = parser.parse_args()

    files = get_ordered_files()
    all_figs = []
    all_tabs = []
    all_old_labels = []
    all_new_labels = []

    # ── Pass 1：编号（或 --refs-only 时仅收集映射） ──
    if not args.refs_only:
        print(f'Pass 1: 扫描并编号 {len(files)} 个文件...\n')
        for filepath, chapter_id in files:
            print(f'[第{chapter_id}章] {filepath.name}')
            figs, tabs, old_labels, new_labels = process_file(
                filepath, chapter_id, dry_run=args.dry_run)
            for e in figs:
                all_figs.append((filepath, chapter_id, e))
            for e in tabs:
                all_tabs.append((filepath, chapter_id, e))
            all_old_labels.extend(old_labels)
            all_new_labels.extend(new_labels)
        print(f'\n总计：{len(all_figs)} 个图，{len(all_tabs)} 个表')
    else:
        # refs-only 模式：仅扫描不修改编号
        print(f'收集编号映射...\n')
        for filepath, chapter_id in files:
            text = filepath.read_text(encoding='utf-8')
            lines = text.splitlines(keepends=True)
            elements = scan_elements(lines)
            old_labels = [extract_old_label(e, lines) for e in elements]
            assign_numbers(elements, chapter_id)
            new_labels = [(e.kind, f'{chapter_id}-{e.number}') for e in elements]
            all_old_labels.extend(old_labels)
            all_new_labels.extend(new_labels)
            for e in elements:
                if e.kind == 'fig':
                    all_figs.append((filepath, chapter_id, e))
                else:
                    all_tabs.append((filepath, chapter_id, e))

    # ── Pass 2：交叉引用更新 ──
    fig_map, tab_map = build_renumber_map(all_old_labels, all_new_labels)
    if fig_map or tab_map:
        print(f'\nPass 2: 更新交叉引用...')
        print(f'  图编号变更: {len(fig_map)} 项')
        print(f'  表编号变更: {len(tab_map)} 项')
        if args.dry_run:
            for old, new in fig_map.items():
                print(f'    图 {old} → 图 {new}')
            for old, new in tab_map.items():
                print(f'    表 {old} → 表 {new}')
        else:
            total_refs = 0
            # 更新所有 docs 文件（含非章节文件如 index.md、contributing.md）
            for md in sorted(DOCS.glob('*.md')):
                if md.name == 'figure_table_index.md':
                    continue
                count = update_cross_refs(md, fig_map, tab_map, dry_run=args.dry_run)
                if count:
                    print(f'  ✓ {md.name}: 更新 {count} 处引用')
                    total_refs += count
            print(f'  共更新 {total_refs} 处引用')
    else:
        print('\nPass 2: 编号无变化，无需更新引用')

    if args.toc:
        toc_text = build_toc(all_figs, all_tabs)
        toc_path = DOCS / 'figure_table_index.md'
        toc_path.write_text(toc_text, encoding='utf-8')
        print(f'\n已生成图表目录：{toc_path}')


if __name__ == '__main__':
    main()
