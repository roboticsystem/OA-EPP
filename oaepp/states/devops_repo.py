"""DevOps 仓库初始化状态

对应需求：F-D-001 GitHub仓库初始化
验收标准：仓库设置为私有，.gitignore采用Python模板并涵盖Reflex构建产物，开源协议文件存在"""

try:
    import reflex as rx
except Exception:
    rx = None

if rx is not None:
    class RepoInitState(rx.State):
        repo_url: str = ""
        repo_name: str = ""
        is_private: bool = False
        is_initialized: bool = False

        @rx.var
        def gitignore_template(self) -> str:
            return """# Python
__pycache__/
*.py[cod]
*.env
.env
.DS_Store
venv/
.venv/
*.egg-info/
dist/
build/
.pytest_cache/

# Reflex构建产物
.reflex/
.reflex-build/
static/build/
*.sqlite"""

        async def init_repo(self):
            """初始化仓库状态（TDD 最小实现）。"""
            self.is_initialized = True
            return True

        def set_repo_name(self, value: str):
            self.repo_name = value

        def set_repo_url(self, value: str):
            self.repo_url = value

        def set_is_private(self, value: bool):
            self.is_private = value
