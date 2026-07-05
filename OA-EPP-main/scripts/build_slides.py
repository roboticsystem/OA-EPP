"""MkDocs hook：在构建前将 docs/slides_src/*.md 用 Marp CLI 转换为独立 HTML。

注册方式（mkdocs.yml）：
    hooks:
      - scripts/build_slides.py
"""

import shutil
import subprocess
import sys
from pathlib import Path


def on_pre_build(config, **kwargs):
    """MkDocs pre-build hook：docs/slides_src/*.md → docs/slides/*.html"""
    docs_dir = Path(config["docs_dir"])
    slides_src = docs_dir / "slides_src"   # Marp 源文件（被 exclude_docs 排除）
    slides_out = docs_dir / "slides"       # 生成的独立 HTML

    if not slides_src.exists():
        return  # 无幻灯片源目录，静默跳过

    # 找到 marp 可执行文件（全局安装位置因平台而异）
    marp_bin = (
        shutil.which("marp")
        or shutil.which("marp-cli")
        or "/usr/local/bin/marp"   # Alpine npm global 默认路径
    )
    if not Path(marp_bin).exists():
        print(
            "[build_slides] ⚠️  marp 未安装，跳过幻灯片转换。"
            "请执行：npm install -g @marp-team/marp-cli",
            file=sys.stderr,
        )
        return

    slides_out.mkdir(parents=True, exist_ok=True)

    md_files = sorted(slides_src.glob("*.md"))
    if not md_files:
        return

    print(f"[build_slides] 发现 {len(md_files)} 个幻灯片源文件，开始转换…")

    for md_file in md_files:
        out_file = slides_out / (md_file.stem + ".html")
        try:
            result = subprocess.run(
                [
                    marp_bin,
                    "--html",              # 允许 HTML 标签（用于自定义样式）
                    "--allow-local-files", # 允许引用本地图片
                    str(md_file),
                    "--output",
                    str(out_file),
                ],
                capture_output=True,
                text=True,
                timeout=120,               # 防止单文件转换超时挂住整个构建
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f"[build_slides] ⚠️  跳过 {md_file.name}：{exc}", file=sys.stderr)
            continue

        if result.returncode != 0:
            print(
                f"[build_slides] ❌ 转换失败: {md_file.name}\n{result.stderr}",
                file=sys.stderr,
            )
        else:
            size_kb = out_file.stat().st_size // 1024 if out_file.exists() else 0
            print(f"[build_slides] ✅ {md_file.name} → slides/{out_file.name} ({size_kb} KB)")

