"""Reflex-based 成绩与反馈页面

基于 prototype/grades.html 原型实现，功能：
- 顶部四维度得分卡片（出勤/考试/代码/PR）
- 详情标签页（代码评阅详情 / 考试成绩 / 出勤记录）
- 评阅详情表格：展示每次评阅的任务、得分、批改人、状态
- 评语卡片：展示教师评语、扣分项标签、改进建议条目
- 二次提交入口：允许重新提交的任务显示"前往重新提交"链接
"""

try:
    import reflex as rx
except Exception:
    rx = None

# ── 侧边栏组件 ──


def _sidebar() -> rx.Component:
    """左侧导航栏"""
    return rx.box(
        rx.vstack(
            # Logo
            rx.hstack(
                rx.box(
                    rx.html(
                        '<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" '
                        'd="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 '
                        '3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 '
                        '3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 '
                        '3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 '
                        '3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 '
                        '3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>'
                    ),
                    bg="blue.600",
                    border_radius="lg",
                    p="6px",
                    w="32px",
                    h="32px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text("OA-EPP", font_weight="bold", color="gray.800", font_size="sm"),
                spacing="2.5",
                padding_x="20px",
                padding_y="20px",
            ),
            rx.divider(border_color="gray.100"),
            # Navigation
            rx.vstack(
                rx.link(
                    rx.hstack(
                        rx.text("仪表盘", font_size="sm"),
                        spacing="3",
                    ),
                    href="/dashboard",
                    _hover={"bg": "gray.50"},
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    color="gray.600",
                    font_size="sm",
                    w="100%",
                ),
                rx.link(
                    rx.hstack(
                        rx.text("课程列表", font_size="sm"),
                        spacing="3",
                    ),
                    href="/courses",
                    _hover={"bg": "gray.50"},
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    color="gray.600",
                    font_size="sm",
                    w="100%",
                ),
                rx.link(
                    rx.hstack(
                        rx.text("作业提交", font_size="sm"),
                        spacing="3",
                    ),
                    href="/assignments",
                    _hover={"bg": "gray.50"},
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    color="gray.600",
                    font_size="sm",
                    w="100%",
                ),
                rx.hstack(
                    rx.text("成绩与反馈", font_size="sm", font_weight="medium"),
                    spacing="3",
                    bg="blue.50",
                    color="blue.700",
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    w="100%",
                ),
                rx.link(
                    rx.hstack(
                        rx.text("课堂签到", font_size="sm"),
                        spacing="3",
                    ),
                    href="/attendance",
                    _hover={"bg": "gray.50"},
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    color="gray.600",
                    font_size="sm",
                    w="100%",
                ),
                rx.link(
                    rx.hstack(
                        rx.text("在线考试", font_size="sm"),
                        spacing="3",
                    ),
                    href="/exam",
                    _hover={"bg": "gray.50"},
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    color="gray.600",
                    font_size="sm",
                    w="100%",
                ),
                rx.link(
                    rx.hstack(
                        rx.text("个人资料", font_size="sm"),
                        spacing="3",
                    ),
                    href="/profile",
                    _hover={"bg": "gray.50"},
                    px="12px",
                    py="8px",
                    border_radius="lg",
                    color="gray.600",
                    font_size="sm",
                    w="100%",
                ),
                spacing="1",
                px="12px",
                py="16px",
                w="100%",
            ),
            # User info at bottom
            rx.box(
                rx.divider(border_color="gray.100"),
                rx.hstack(
                    rx.avatar(size="sm", name="张三"),
                    rx.vstack(
                        rx.text("张三", font_size="sm", font_weight="medium", color="gray.800"),
                        rx.text("2021001001", font_size="xs", color="gray.400"),
                        spacing="0",
                        align_items="start",
                    ),
                    spacing="3",
                    padding_x="16px",
                    padding_y="16px",
                ),
                w="100%",
            ),
            spacing="0",
            h="100vh",
            w="224px",
            bg="white",
            border_right="1px",
            border_color="gray.200",
            position="fixed",
            left="0",
            top="0",
        ),
    )


# ── 得分卡片组件 ──


def _score_card(
    label: str,
    score: float,
    total: float,
    color: str,
    sub_text: str = "",
) -> rx.Component:
    """单个得分卡片"""
    pct = (score / total * 100) if total > 0 else 0
    return rx.box(
        rx.hstack(
            rx.text(label, font_size="xs", color="gray.400", font_weight="medium"),
            rx.spacer(),
        ),
        rx.hstack(
            rx.text(
                f"{score:g}",
                font_size="2xl",
                font_weight="bold",
                color=color,
            ),
            rx.text(
                f"/ {total:g}",
                font_size="sm",
                color="gray.400",
            ),
            spacing="1",
            align_items="baseline",
            margin_top="8px",
        ),
        rx.box(
            rx.box(
                bg=color,
                h="6px",
                border_radius="full",
                width=f"{min(pct, 100):.0f}%",
            ),
            bg="gray.100",
            border_radius="full",
            h="6px",
            margin_top="8px",
            w="100%",
        ),
        rx.text(sub_text, font_size="xs", color="gray.400", margin_top="6px"),
        bg="white",
        border_radius="xl",
        border="1px",
        border_color="gray.100",
        box_shadow="sm",
        padding="20px",
    )


# ── 扣分项标签组件 ──


def _deduction_tag(item: dict) -> rx.Component:
    """扣分项标签"""
    return rx.box(
        f"扣分：-{item['points']} · {item['reason']}",
        font_size="xs",
        bg="red.100",
        color="red.600",
        px="8px",
        py="2px",
        border_radius="md",
    )


# ── 改进建议条目组件 ──


def _suggestion_item(text: str) -> rx.Component:
    """改进建议条目"""
    return rx.hstack(
        rx.text("•", color="blue.500", font_weight="bold"),
        rx.text(text, font_size="sm", color="gray.700"),
        spacing="2",
        align_items="start",
    )


# ── 评语卡片组件 ──


def _feedback_card(fb: dict) -> rx.Component:
    """评语详情卡片

    验收标准：
    - 展示教师评语和扣分项
    - 改进建议以条目形式展示
    - 允许二次提交的任务展示重新提交入口
    """
    return rx.box(
        # 头部：教师信息 + 得分
        rx.hstack(
            rx.hstack(
                rx.avatar(size="sm", name=fb.get("grader_name", "教师")),
                rx.vstack(
                    rx.text(
                        f"{fb.get('assignment_title', '')}评语 · {fb.get('grader_name', '教师')}（教师）",
                        font_size="sm",
                        font_weight="semibold",
                        color="gray.800",
                    ),
                    rx.text(
                        f"{fb.get('graded_at', '')} 批改",
                        font_size="xs",
                        color="gray.400",
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
            ),
            rx.spacer(),
            rx.text(
                f"{fb.get('total_score', 0):g}/10",
                font_size="lg",
                font_weight="bold",
                color="green.600",
            ),
        ),
        # 教师评语
        rx.text(
            fb.get("comment", ""),
            font_size="sm",
            color="gray.700",
            line_height="relaxed",
            margin_top="12px",
        ),
        # 扣分项标签
        rx.hstack(
            *[
                _deduction_tag(item)
                for item in (fb.get("deduction_items") or [])
            ],
            spacing="2",
            flex_wrap="wrap",
            margin_top="12px",
        ),
        # 改进建议条目
        rx.vstack(
            *[
                _suggestion_item(s)
                for s in (fb.get("suggestions") or [])
            ],
            spacing="2",
            margin_top="12px",
            align_items="start",
        ),
        # 二次提交入口
        rx.cond(
            fb.get("allow_resubmit", False),
            rx.box(
                rx.divider(border_color="blue.100", margin_top="12px"),
                rx.text(
                    "此任务允许二次提交，可基于以上反馈修改后重新提交",
                    font_size="xs",
                    color="gray.500",
                    margin_top="8px",
                ),
                rx.link(
                    "前往重新提交 →",
                    href="/assignments",
                    font_size="xs",
                    color="blue.500",
                    _hover={"text_decoration": "underline"},
                    margin_top="4px",
                ),
            ),
            rx.box(),
        ),
        bg="blue.50",
        border="1px",
        border_color="blue.100",
        border_radius="xl",
        padding="20px",
        margin_top="24px",
    )


# ── 主页面 ──

grades_page = None
if rx is not None:
    def grades_page() -> rx.Component:
        """成绩与反馈页面 — 基于 prototype/grades.html"""

        # ── 模拟数据（与原型对齐） ──
        # 实际生产环境将从 ScoreState / FeedbackState 获取
        attendance_score = 18.0
        exam_score = 24.0
        code_score = 32.0
        pr_score = 13.5
        total_score = attendance_score + exam_score + code_score + pr_score

        # 评阅详情数据
        grade_details = [
            {
                "task": "第5章 系统架构设计",
                "score": "9 / 10",
                "score_color": "green.600",
                "grader": "李四（教师）",
                "graded_at": "2025-05-02",
                "status_label": "已批改",
                "status_bg": "green.100",
                "status_color": "green.700",
                "has_feedback": True,
                "comment": "整体架构清晰，分层合理，对 Reflex 全栈模式理解到位。建议补充服务层（Service Layer）职责划分说明，避免 State 类过重。组件命名规范性有待提升，参考团队 `.github/copilot-instructions.md` 规范统一命名风格。",
                "deduction_items": [{"points": 1, "reason": "命名规范"}],
                "suggestions": ["补充服务层说明"],
                "allow_resubmit": True,
                "total_score": 9.0,
                "grader_name": "李四",
            },
            {
                "task": "第4章 用例分析",
                "score": "7 / 10",
                "score_color": "orange.500",
                "grader": "李四（教师）",
                "graded_at": "2025-04-25",
                "status_label": "迟交扣分",
                "status_bg": "orange.100",
                "status_color": "orange.600",
                "has_feedback": True,
                "comment": "用例分析基本完整，但部分用例缺少异常流描述。迟交扣1分。",
                "deduction_items": [{"points": 1, "reason": "迟交"}, {"points": 2, "reason": "异常流缺失"}],
                "suggestions": ["补充用例异常流描述", "绘制完整用例图"],
                "allow_resubmit": True,
                "total_score": 7.0,
                "grader_name": "李四",
            },
            {
                "task": "第6章 数据库设计",
                "score": "—",
                "score_color": "gray.400",
                "grader": "—",
                "graded_at": "—",
                "status_label": "待批改",
                "status_bg": "yellow.100",
                "status_color": "yellow.700",
                "has_feedback": False,
                "allow_resubmit": False,
            },
        ]

        return rx.hstack(
            # 侧边栏
            _sidebar(),
            # 主内容区
            rx.box(
                # 标题行
                rx.hstack(
                    rx.vstack(
                        rx.heading("成绩与反馈", size="6", color="gray.800"),
                        rx.text(
                            f"工程实践 4 · 综合总分 {total_score:g} / 100",
                            font_size="sm",
                            color="gray.400",
                            margin_top="2px",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    rx.spacer(),
                    rx.button(
                        "下载成绩单 Excel",
                        bg="green.600",
                        color="white",
                        font_size="sm",
                        px="16px",
                        py="8px",
                        border_radius="lg",
                        _hover={"bg": "green.700"},
                    ),
                    justify_content="space_between",
                    margin_bottom="24px",
                ),

                # 四维度得分卡片
                rx.hstack(
                    _score_card("出勤得分", attendance_score, 20, "green.500", "出勤 18/20 次 · 缺勤 2 次"),
                    _score_card("考试得分", exam_score, 30, "purple.500", "3 次考试均已出分"),
                    _score_card("代码提交", code_score, 40, "orange.400", "5 已批 · 2 待批"),
                    _score_card("PR 贡献", pr_score, 10, "blue.500", "超额加分 · 9 次 PR 审查"),
                    spacing="5",
                    margin_bottom="32px",
                ),

                # 详情区域
                rx.box(
                    # 标签栏
                    rx.hstack(
                        rx.text(
                            "代码评阅详情",
                            font_size="sm",
                            font_weight="medium",
                            color="blue.600",
                            border_bottom="2px",
                            border_color="blue.600",
                            padding_y="12px",
                            padding_x="16px",
                        ),
                        rx.text(
                            "考试成绩",
                            font_size="sm",
                            color="gray.500",
                            padding_y="12px",
                            padding_x="16px",
                            _hover={"color": "gray.700"},
                            cursor="pointer",
                        ),
                        rx.text(
                            "出勤记录",
                            font_size="sm",
                            color="gray.500",
                            padding_y="12px",
                            padding_x="16px",
                            _hover={"color": "gray.700"},
                            cursor="pointer",
                        ),
                        rx.text(
                            "时间线",
                            font_size="sm",
                            color="gray.500",
                            padding_y="12px",
                            padding_x="16px",
                            _hover={"color": "gray.700"},
                            cursor="pointer",
                        ),
                        border_bottom="1px",
                        border_color="gray.100",
                        padding_x="20px",
                    ),

                    # 评阅详情表格
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header("任务", font_size="xs", color="gray.400", font_weight="medium"),
                                    rx.table.column_header("得分", font_size="xs", color="gray.400", font_weight="medium"),
                                    rx.table.column_header("批改人", font_size="xs", color="gray.400", font_weight="medium"),
                                    rx.table.column_header("批改时间", font_size="xs", color="gray.400", font_weight="medium"),
                                    rx.table.column_header("状态", font_size="xs", color="gray.400", font_weight="medium"),
                                    rx.table.column_header(""),
                                ),
                            ),
                            rx.table.body(
                                *[
                                    rx.table.row(
                                        rx.table.cell(
                                            detail["task"],
                                            font_weight="medium",
                                            color="gray.800",
                                            font_size="sm",
                                        ),
                                        rx.table.cell(
                                            detail["score"],
                                            font_weight="bold",
                                            color=detail["score_color"],
                                            font_size="sm",
                                        ),
                                        rx.table.cell(
                                            detail["grader"],
                                            color="gray.500",
                                            font_size="xs",
                                        ),
                                        rx.table.cell(
                                            detail["graded_at"],
                                            color="gray.400",
                                            font_size="xs",
                                        ),
                                        rx.table.cell(
                                            rx.box(
                                                detail["status_label"],
                                                font_size="xs",
                                                bg=detail["status_bg"],
                                                color=detail["status_color"],
                                                px="8px",
                                                py="2px",
                                                border_radius="full",
                                            ),
                                        ),
                                        rx.table.cell(
                                            rx.cond(
                                                detail.get("has_feedback", False),
                                                rx.text(
                                                    "查看评语",
                                                    font_size="xs",
                                                    color="blue.500",
                                                    cursor="pointer",
                                                    _hover={"text_decoration": "underline"},
                                                ),
                                                rx.text("—", font_size="xs", color="gray.300"),
                                            ),
                                            text_align="right",
                                        ),
                                    )
                                    for detail in grade_details
                                ],
                            ),
                            w="100%",
                        ),
                        padding="20px",
                    ),
                    bg="white",
                    border_radius="xl",
                    border="1px",
                    border_color="gray.100",
                    box_shadow="sm",
                ),

                margin_left="224px",
                padding="32px",
                flex="1",
                min_height="100vh",
                bg="gray.50",
            ),
            spacing="0",
            w="100%",
        )
