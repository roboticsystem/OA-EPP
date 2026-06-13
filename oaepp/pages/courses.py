"""
课程主页 (F-S-010)
展示学生已选课程与当前学习进度
"""

try:
    import reflex as rx
except Exception:
    rx = None

# 仅在 Reflex 可用时导入 State
# 优先使用相对导入（运行在 oaepp/ 目录内），fallback 绝对导入（运行在仓库根目录）
if rx is not None:
    try:
        from states.course_state import CourseState, CourseProgress
    except ImportError:
        from oaepp.states.course_state import CourseState, CourseProgress


def course_card(course: "CourseProgress") -> "rx.Component":
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
                    course.course_name,
                    size="4",
                    color_scheme="blue",
                ),
                rx.badge(
                    course.course_code,
                    color_scheme="gray",
                    variant="soft",
                ),
                justify="between",
                width="100%",
            ),
            rx.divider(),

            # 课程统计信息
            rx.grid(
                # 章节数
                rx.vstack(
                    rx.text("章节数", color="gray", size="2"),
                    rx.heading(
                        course.total_chapters,
                        size="6",
                        color_scheme="blue",
                    ),
                    align="center",
                ),
                # 已完成任务
                rx.vstack(
                    rx.text("已完成任务", color="gray", size="2"),
                    rx.heading(
                        f"{course.completed_tasks}/{course.total_tasks}",
                        size="6",
                        color_scheme="green",
                    ),
                    align="center",
                ),
                # 进度百分比
                rx.vstack(
                    rx.text("完成度", color="gray", size="2"),
                    rx.heading(
                        f"{course.progress_percentage:.0f}%",
                        size="6",
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
                value=course.progress_percentage,
                width="100%",
            ),

            # 截止提醒
            rx.cond(
                course.has_due_date,
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="timer"),
                        rx.text(
                            f"下一截止: {course.next_due_date_str}",
                            color="orange",
                            size="2",
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
                    on_click=lambda: CourseState.select_course(course.course_id),
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
        variant="classic",
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
                size="8",
                color_scheme="blue",
            ),
            rx.text(
                "查看您已选课程的学习进度和截止提醒",
                color="gray",
                size="4",
            ),

            # 刷新按钮
            rx.button(
                "刷新数据",
                on_click=CourseState.refresh_courses,
                color_scheme="gray",
                variant="outline",
                size="2",
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
                    CourseState.error_message,
                    icon="file_warning",
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
                    "暂无已选课程，请先选择课程或联系管理员",
                    icon="circle_help",
                    color_scheme="blue",
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
