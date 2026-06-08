"""Reflex Pages 子包

导出：
- login_page：登录页面
- profile_page：个人资料页面
- workflow_page：工作流管理页面（教师端）

使用方式：
    from pages import login_page, profile_page, workflow_page
"""

try:
    from .login import login_page
except Exception:
    login_page = None

try:
    from .profile import profile_page
except Exception:
    profile_page = None

try:
    from .workflow import workflow_page
except Exception:
    workflow_page = None

__all__ = ["login_page", "profile_page", "workflow_page"]