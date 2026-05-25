"""MkDocs hook：在构建前将 slides_src/*.md 用 Marp CLI 转换为独立 HTML。

注册方式（mkdocs.yml）：
    hooks:
      - scripts/build_slides.py
"""

import subprocess
import sys
from pathlib import Path


def on_pre_build(config, **kwargs):
    """MkDocs pre-build hook：slides_src/*.md → docs/slides/*.html"""
    project_root = Path(config["docs_dir"]).parent
    slides_src = project_root / "slides_src"
    slides_out = Path(config["docs_dir"]) / "slides"

    if not slides_src.exists():
        return  # 无幻灯片源目录，静默跳过

    slides_out.mkdir(parents=True, exist_ok=True)

    md_files = sorted(slides_src.glob("*.md"))
    if not md_files:
        return

    print(f"[build_slides] 发现 {len(md_files)} 个幻灯片源文件，开始转换…")

    for md_file in md_files:
        out_file = slides_out / (md_file.stem + ".html")
        result = subprocess.run(
            [
                "marp",
                "--html",              # 允许 HTML 标签（用于自定义样式）
                "--allow-local-files", # 允许引用本地图片
                str(md_file),
                "--output",
                str(out_file),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(
                f"[build_slides] ❌ 转换失败: {md_file.name}\n{result.stderr}",
                file=sys.stderr,
            )
        else:
            size_kb = out_file.stat().st_size // 1024
            print(f"[build_slides] ✅ {md_file.name} → slides/{out_file.name} ({size_kb} KB)")
