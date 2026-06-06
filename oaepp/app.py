"""OA-EPP Reflex 应用入口 — rx.App 实例 + 路由注册

F-T-012 (成绩权重配置) 状态已在 oaepp/states/teacher_grade_weight.py 实现。
"""

import reflex as rx

app = rx.App(
    title="OA-EPP 考试系统",
    description="研究生课程《机器人系统》在线考试与成绩管理平台",
)
