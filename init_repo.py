#!/usr/bin/env python3
# F-D-001 #34 合规初始化：不修改项目原有.gitignore
# 方案：新建独立忽略文件 + LICENSE，不触碰原有主干任何配置

# 单独新建Reflex+Python专用忽略文件
ignore_file_name = ".gitignore_python_reflex"
ignore_content = """# F-D-001 独立忽略配置｜不修改原有.gitignore
# Python规则
__pycache__/
*.py[cod]
venv/
.venv/
*.egg-info/
dist/
build/
.env
# Reflex构建产物
.reflex/
.reflex-build/
static/build/
*.sqlite
.pytest_cache/
"""

license_content = """MIT License
Copyright (c) 2025 UWISLAB

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

def init_files():
    # 新建独立忽略文件，不动原.gitignore
    with open(ignore_file_name, "w", encoding="utf-8") as f:
        f.write(ignore_content)
    # 新建LICENSE（项目原本无，合规创建）
    with open("LICENSE", "w", encoding="utf-8") as f:
        f.write(license_content)
    # git配置读取这个新增忽略文件，实现忽略效果
    import subprocess
    subprocess.run(["git", "config", "--local", "core.excludesfile", ignore_file_name])
    print(f"✅ 已创建{ignore_file_name}，原有.gitignore无任何修改")

if __name__ == "__main__":
    init_files()