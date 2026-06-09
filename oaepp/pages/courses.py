"""
课程主页 (F-S-010)
展示学生已选课程与当前学习进度
"""

try:
    import reflex as rx
except Exception:
    rx = None

# 仅在 Reflex 可用时导入 State
if rx is not None:
    from oaepp.states.course_state import CourseState


def course_card(course) -> "rx.Component":
    """
    单门课程卡片组件
    展示课程名称、章节数、完成进度、截止提醒
    """
    if rx is None:
        return None

    return rx.card(
        rx.vstack(
            # 课程标题和代码
            rx.hstack(
                rx.heading(
                    course["course_name"],
                    size="md",
                    color_scheme="blue",
                ),
                rx.badge(
                    course["course_code"],
                    color_scheme="gray",
                    variant="subtle",
                ),
                justify="between",
                width="100%",
            ),
            rx.divider(),

            # 课程统计信息
            rx.grid(
                # 章节数
                rx.vstack(
                    rx.text("章节数", color="gray", size="sm"),
                    rx.heading(
                        course["total_chapters"],
                        size="lg",
                        color_scheme="blue",
                    ),
                    align="center",
                ),
                # 已完成任务
                rx.vstack(
                    rx.text("已完成任务", color="gray", size="sm"),
                    rx.heading(
                        f"{course['completed_tasks']}/{course['total_tasks']}",
                        size="lg",
                        color_scheme="green",
                    ),
                    align="center",
                ),
                # 进度百分比
                rx.vstack(
                    rx.text("完成度", color="gray", size="sm"),
                    rx.heading(
                        f"{course['progress_percentage']:.0f}%",
                        size="lg",
                        color_scheme="purple",
                    ),
                    align="center",
                ),
                columns="3",
                spacing="4",
                width="100%",
            ),

            # 进度条
            rx.progress(
                value=course["progress_percentage"] / 100,
                width="100%",
            ),

            # 截止提醒
            rx.cond(
                course["has_due_date"],
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="clock"),
                        rx.text(
                            f"下一截止: {course['next_due_date_str']}",
                            color="orange",
                            size="sm",
                        ),
                        spacing="2",
                    ),
                    width="100%",
                ),
                rx.box(),
            ),

            # 操作按钮
            rx.hstack(
                rx.button(
                    "查看详情",
                    color_scheme="blue",
                    on_click=lambda: CourseState.select_course(course["course_id"]),
                ),
                rx.button(
                    "继续学习",
                    color_scheme="green",
                    variant="outline",
                ),
                width="100%",
                spacing="2",
            ),

            spacing="4",
            width="100%",
        ),
        width="100%",
        variant="elevated",
    )


def courses_page_content() -> "rx.Component":
    """
    课程主页核心内容 (F-S-010)
    展示学生已选课程与当前学习进度
    """
    if rx is None:
        return None

    return rx.box(
        rx.vstack(
            # 页面标题
            rx.heading(
                "我的课程",
                size="xl",
                color_scheme="blue",
            ),
            rx.text(
                "查看您已选课程的学习进度和截止提醒",
                color="gray",
                size="md",
            ),

            # 刷新按钮
            rx.button(
                "刷新数据",
                on_click=CourseState.refresh_courses,
                color_scheme="gray",
                variant="outline",
                size="sm",
            ),

            # 加载状态
            rx.cond(
                CourseState.loading,
                rx.hstack(
                    rx.spinner(color="blue"),
                    rx.text("加载中..."),
                    spacing="2",
                ),
                rx.box(),
            ),

            # 错误提示
            rx.cond(
                CourseState.error_message != "",
                rx.callout(
                    rx.text(CourseState.error_message),
                    icon="alert_circle",
                    color_scheme="red",
                ),
                rx.box(),
            ),

            # 课程列表
            rx.cond(
                CourseState.courses.length() > 0,
                rx.vstack(
                    rx.foreach(
                        CourseState.courses,
                        course_card,
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.callout(
                    rx.text("暂无已选课程"),
                    icon="info",
                    color_scheme="gray",
                ),
            ),

            spacing="6",
            width="100%",
            padding="6",
            max_width="1200px",
            margin="0 auto",
        ),
        width="100%",
        min_height="100vh",
        background_color="var(--gray-1)",
    )


# 对外暴露的页面组件
courses_page = courses_page_content if rx is not None else None
