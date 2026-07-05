#!/usr/bin/env python3
"""svgbob CJK 对齐检查与自动修复工具

扫描 Markdown 文件中的 ```bob 代码块，检测因 CJK（中日韩）字符
导致的竖线对齐问题，并可自动修复。

用法:
    python align_bob.py <file.md>              # 仅检查，报告问题
    python align_bob.py --fix <file.md>        # 检查并自动修复
    python align_bob.py --fix --inplace <f.md> # 原地修改文件
    python align_bob.py --verbose <file.md>    # 显示逐行宽度详情
"""

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


# ── 宽度计算 ──────────────────────────────────────────────


def char_display_width(c: str) -> int:
    """单个字符的显示宽度（等宽字体环境）。

    CJK 表意字符和全角符号宽度为 2，其余为 1。
    """
    eaw = unicodedata.east_asian_width(c)
    return 2 if eaw in ("W", "F") else 1


def display_width(s: str) -> int:
    """字符串在等宽字体下的总显示宽度。"""
    return sum(char_display_width(c) for c in s)


def count_cjk(s: str) -> int:
    """计算字符串中宽度为 2 的字符数量。"""
    return sum(1 for c in s if char_display_width(c) == 2)


# ── Bob 代码块解析 ────────────────────────────────────────


# 匹配右侧结构字符（竖线、右角）前的空格区域
_RIGHT_BORDER_RE = re.compile(r"( +)([│┤┐┘|])\s*$")

# 匹配边框线行（顶/底边框，可能含 ┬ ┴ ╤ ╧ 等中间字符）
_BORDER_LINE_RE = re.compile(r"^(\s*[┌└╔╚])(─+(?:[┬┴╤╧┼]*─+)*)([┐┘╗╝])\s*$")

# 匹配 bob 代码块
_BOB_FENCE_RE = re.compile(r"^```bob\s*$")
_FENCE_CLOSE_RE = re.compile(r"^```\s*$")


@dataclass
class BobBlock:
    """一个 bob 代码块的位置与内容。"""

    start_line: int  # ```bob 所在行号（0-based，在文件中）
    end_line: int  # ``` 关闭行号
    lines: list[str] = field(default_factory=list)  # 代码块内的行（不含围栏）


def extract_bob_blocks(text: str) -> list[BobBlock]:
    """从 Markdown 文本中提取所有 bob 代码块。"""
    blocks: list[BobBlock] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if _BOB_FENCE_RE.match(lines[i]):
            start = i
            i += 1
            block_lines: list[str] = []
            while i < len(lines) and not _FENCE_CLOSE_RE.match(lines[i]):
                block_lines.append(lines[i])
                i += 1
            blocks.append(BobBlock(start_line=start, end_line=i, lines=block_lines))
        i += 1
    return blocks


# ── 对齐分析 ─────────────────────────────────────────────


@dataclass
class LineInfo:
    """一行的宽度分析结果。"""

    index: int  # 行在代码块中的索引
    text: str  # 原始文本
    disp_width: int  # 显示宽度
    n_cjk: int  # CJK 字符数


@dataclass
class AlignIssue:
    """一个对齐问题。"""

    block_index: int  # 第几个 bob 块（0-based）
    file_line: int  # 文件中的行号（1-based）
    expected_width: int
    actual_width: int
    line_text: str


def analyze_block(block: BobBlock) -> tuple[list[LineInfo], int]:
    """分析一个 bob 块，返回 (各行信息, 目标宽度)。

    目标宽度取多数行的显示宽度（通常由 ┌──...──┐ / └──...──┘ 行确定），
    若无明确框线则取最大宽度。
    """
    infos: list[LineInfo] = []
    for i, line in enumerate(block.lines):
        dw = display_width(line)
        nc = count_cjk(line)
        infos.append(LineInfo(index=i, text=line, disp_width=dw, n_cjk=nc))

    if not infos:
        return infos, 0

    # 优先用纯 ASCII 的框线行宽度作为目标
    border_widths: list[int] = []
    for info in infos:
        stripped = info.text.strip()
        if stripped and info.n_cjk == 0 and any(
            c in stripped for c in "┌┐└┘─═"
        ):
            border_widths.append(info.disp_width)

    if border_widths:
        # 取出现最多的边框宽度
        from collections import Counter

        target = Counter(border_widths).most_common(1)[0][0]
    else:
        # 无明确边框，取最大宽度
        target = max(info.disp_width for info in infos) if infos else 0

    return infos, target


def find_issues(
    blocks: list[BobBlock],
    cjk_only: bool = True,
) -> list[AlignIssue]:
    """检测所有 bob 块中的对齐问题。

    Args:
        blocks: 已提取的 bob 代码块列表。
        cjk_only: 若为 True（默认），仅报告含 CJK 字符的行的对齐问题，
                  以避免序列图生命线等非方框结构的误报。
    """
    issues: list[AlignIssue] = []
    for bi, block in enumerate(blocks):
        infos, target = analyze_block(block)
        if target == 0:
            continue

        # 若整个块无 CJK 字符且处于 cjk_only 模式，跳过
        block_has_cjk = any(info.n_cjk > 0 for info in infos)
        if cjk_only and not block_has_cjk:
            continue

        for info in infos:
            line_stripped = info.text.strip()
            # 跳过空行
            if not line_stripped:
                continue
            # 只检查含右侧边界字符的行（这些行需要对齐）
            if not _RIGHT_BORDER_RE.search(info.text):
                continue
            if info.disp_width != target:
                # cjk_only 模式下，仅报告含 CJK 字符的行
                if cjk_only and info.n_cjk == 0:
                    continue
                issues.append(
                    AlignIssue(
                        block_index=bi,
                        file_line=block.start_line + 1 + info.index + 1,  # 1-based
                        expected_width=target,
                        actual_width=info.disp_width,
                        line_text=info.text,
                    )
                )
    return issues


# ── 自动修复 ─────────────────────────────────────────────


def fix_line(line: str, target_width: int) -> str:
    """调整行内右侧边界字符前的空格数，使显示宽度等于 target_width。

    仅修改右侧结构字符（│┤┐┘|）左侧的空格区域。
    """
    m = _RIGHT_BORDER_RE.search(line)
    if not m:
        return line  # 无右边界字符，不修改

    spaces_start = m.start(1)
    border_char = m.group(2)

    # 左半部分（不含尾部空格和边界字符）
    left = line[:spaces_start]
    # 右半部分（边界字符之后，通常为空或换行）
    right_rest = line[m.end(2) :]

    left_width = display_width(left)
    border_width = char_display_width(border_char)
    rest_width = display_width(right_rest.rstrip())

    needed_spaces = target_width - left_width - border_width - rest_width
    if needed_spaces < 0:
        # 内容本身已超宽，无法仅靠删空格修复
        needed_spaces = 1  # 至少保留 1 个空格

    return left + " " * needed_spaces + border_char + right_rest


def widen_border_line(line: str, extra: int) -> str:
    """在边框线中追加 extra 个 ─ 字符以加宽。

    将 extra 个 ─ 插入到右侧角字符（┐┘╗╝）之前。
    """
    m = _BORDER_LINE_RE.match(line)
    if not m:
        return line
    prefix = m.group(1)   # 如 " ┌" 或 " └"
    dashes = m.group(2)   # 中间的 ─...─
    suffix = m.group(3)   # 右角如 ┐ ┘
    return prefix + dashes + "─" * extra + suffix


def fix_block(block: BobBlock) -> list[str]:
    """修复一个 bob 块内的所有行，返回修复后的行列表。

    两阶段策略：
      1. 若有内容行的显示宽度 > 边框目标宽度（CJK 导致），
         先将边框线加宽以容纳最宽内容行。
      2. 对宽度不足的行，增加右侧边界字符前的空格。
    """
    infos, target = analyze_block(block)
    if target == 0:
        return block.lines[:]

    # 找出所有含右边界字符的行的最大显示宽度
    max_content_width = target
    for info in infos:
        if _RIGHT_BORDER_RE.search(info.text) and info.n_cjk > 0:
            max_content_width = max(max_content_width, info.disp_width)

    # 阶段1：如果最宽内容行超过边框，扩展边框
    new_target = max_content_width if max_content_width > target else target
    extra = new_target - target

    widened: list[str] = []
    for info in infos:
        line = info.text
        if extra > 0 and _BORDER_LINE_RE.match(line):
            line = widen_border_line(line, extra)
        widened.append(line)

    # 阶段2：对宽度不匹配的行调整空格
    fixed: list[str] = []
    for line in widened:
        dw = display_width(line)
        if _RIGHT_BORDER_RE.search(line) and dw != new_target:
            fixed.append(fix_line(line, new_target))
        else:
            fixed.append(line)
    return fixed


def fix_text(text: str) -> str:
    """修复 Markdown 文本中所有 bob 块的对齐问题。"""
    blocks = extract_bob_blocks(text)
    if not blocks:
        return text

    lines = text.splitlines(keepends=True)
    # 从后往前替换，避免行号偏移
    for block in reversed(blocks):
        fixed_lines = fix_block(block)
        # 替换块内行（保留原始换行符）
        for i, fl in enumerate(fixed_lines):
            orig_idx = block.start_line + 1 + i
            if orig_idx < len(lines):
                # 保留原始行尾
                ending = ""
                if lines[orig_idx].endswith("\n"):
                    ending = "\n"
                lines[orig_idx] = fl + ending

    return "".join(lines)


# ── 报告输出 ─────────────────────────────────────────────


def print_report(
    filepath: str,
    blocks: list[BobBlock],
    issues: list[AlignIssue],
    verbose: bool = False,
) -> None:
    """打印检查报告。"""
    print(f"\n{'='*60}")
    print(f"文件: {filepath}")
    print(f"发现 {len(blocks)} 个 bob 代码块")
    print(f"{'='*60}")

    if verbose:
        for bi, block in enumerate(blocks):
            infos, target = analyze_block(block)
            print(f"\n--- bob 块 #{bi+1} (第 {block.start_line+1} 行, 目标宽度={target}) ---")
            for info in infos:
                marker = "  " if info.disp_width == target or target == 0 else "✗ "
                cjk_note = f" [CJK×{info.n_cjk}]" if info.n_cjk > 0 else ""
                print(f"  {marker}W={info.disp_width:3d}{cjk_note}  {info.text}")

    if not issues:
        print("\n✓ 所有 bob 块对齐正确，未发现问题。")
    else:
        print(f"\n✗ 发现 {len(issues)} 处对齐问题：\n")
        for issue in issues:
            diff = issue.actual_width - issue.expected_width
            direction = "宽" if diff > 0 else "窄"
            print(
                f"  第 {issue.file_line} 行: "
                f"显示宽度 {issue.actual_width} (期望 {issue.expected_width}, "
                f"偏{direction} {abs(diff)} 列)"
            )
            print(f"    | {issue.line_text}")
            print()


# ── CLI ───────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="svgbob CJK 对齐检查与自动修复工具"
    )
    parser.add_argument("files", nargs="+", help="要检查的 Markdown 文件")
    parser.add_argument("--fix", action="store_true", help="自动修复对齐问题")
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="原地修改文件（需配合 --fix）",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="显示逐行宽度详情")
    parser.add_argument(
        "--all",
        action="store_true",
        help="报告所有对齐问题（默认仅报告 CJK 相关问题）",
    )
    args = parser.parse_args()

    total_issues = 0

    for filepath in args.files:
        path = Path(filepath)
        if not path.is_file():
            print(f"错误: 文件不存在 — {filepath}", file=sys.stderr)
            total_issues += 1
            continue

        text = path.read_text(encoding="utf-8")
        blocks = extract_bob_blocks(text)
        issues = find_issues(blocks, cjk_only=not args.all)
        total_issues += len(issues)

        print_report(filepath, blocks, issues, verbose=args.verbose)

        if args.fix and issues:
            fixed_text = fix_text(text)
            if args.inplace:
                path.write_text(fixed_text, encoding="utf-8")
                print(f"  → 已原地修复: {filepath}")
            else:
                # 输出到 stdout 或同名 .fixed.md
                fixed_path = path.with_suffix(".fixed.md")
                fixed_path.write_text(fixed_text, encoding="utf-8")
                print(f"  → 修复结果写入: {fixed_path}")

    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
