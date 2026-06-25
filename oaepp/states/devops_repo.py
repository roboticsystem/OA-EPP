"""DevOps 仓库初始化状态"""

from __future__ import annotations


class RepoInitState:
    repo_url: str = ""
    repo_name: str = ""
    is_private: bool = False
    is_initialized: bool = False

    GITIGNORE_TEMPLATE: str = """# Python
__pycache__/
*.py[cod]
*.env
.env
.DS_Store
"""

    def __init__(self):
        self.repo_url = str(self.repo_url)
        self.repo_name = str(self.repo_name)
        self.is_private = bool(self.is_private)
        self.is_initialized = bool(self.is_initialized)

    async def init_repo(self):
        """初始化仓库状态（TDD 最小实现）。"""
        self.is_initialized = True
        return True

    def generate_gitignore(self) -> str:
        return self.GITIGNORE_TEMPLATE