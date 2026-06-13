"""
课程主页状态管理 — 重导出模块
对齐 tests/reflex/test_F_S_010_course_home.py 的导入路径
"""
try:
    from states.course_state import CourseState, CourseProgress  # 本地/容器运行
except ImportError:
    from oaepp.states.course_state import CourseState, CourseProgress  # 仓库根目录运行

__all__ = ["CourseState", "CourseProgress"]
