"""
个人资料页面 - 包含F-S-003 GitHub账号绑定功能
"""
import reflex as rx
from states.auth_state import AuthState
from states.github_bind_state import GithubBindState
from components.sidebar import sidebar


def profile_card() -> rx.Component:
    """个人资料卡片"""
    return rx.box(
        # 头像和基本信息
        rx.hstack(
            rx.box(
                rx.text(
                    AuthState.full_name.to(str)[0:1],
                    color="rgb(37, 99, 235)",
                    weight="bold",
                    size="6",
                ),
                width="64px",
                height="64px",
                border_radius="50%",
                background="rgb(219, 234, 254)",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.vstack(
                rx.text(AuthState.full_name, size="5", weight="bold", color="rgb(31, 41, 55)"),
                rx.text(
                    f"学号：{AuthState.student_no} · 班级：{AuthState.class_name}",
                    size="2",
                    color="rgb(156, 163, 175)",
                ),
                spacing="1",
                align="start",
            ),
            spacing="5",
            align="center",
            margin_bottom="24px",
        ),
        
        # 表单字段
        rx.grid(
            rx.vstack(
                rx.text("姓名", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    value=AuthState.full_name,
                    size="2",
                    width="100%",
                    border_radius="8px",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.vstack(
                rx.text("学号（只读）", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    value=AuthState.student_no,
                    disabled=True,
                    size="2",
                    width="100%",
                    border_radius="8px",
                    background="rgb(249, 250, 251)",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.vstack(
                rx.text("邮箱", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    value=AuthState.email,
                    size="2",
                    width="100%",
                    border_radius="8px",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.vstack(
                rx.text("班级", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    value=AuthState.class_name,
                    disabled=True,
                    size="2",
                    width="100%",
                    border_radius="8px",
                    background="rgb(249, 250, 251)",
                ),
                spacing="2",
                align="stretch",
            ),
            columns="2",
            spacing="5",
            width="100%",
        ),
        
        # 保存按钮
        rx.flex(
            rx.button(
                "保存修改",
                size="2",
                color_scheme="blue",
                border_radius="8px",
            ),
            justify="end",
            margin_top="20px",
        ),
        
        padding="24px",
        background="white",
        border_radius="12px",
        border="1px solid rgb(243, 244, 246)",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        margin_bottom="24px",
    )


def github_binding_card() -> rx.Component:
    """GitHub账号绑定卡片 - F-S-003核心功能"""
    return rx.box(
        # 标题栏
        rx.hstack(
            rx.hstack(
                rx.html(
                    '<svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>',
                    color="rgb(55, 65, 81)",
                ),
                rx.text("GitHub 账号绑定", size="3", weight="bold", color="rgb(55, 65, 81)"),
                spacing="3",
                align="center",
            ),
            # 状态标签
            rx.cond(
                GithubBindState.verify_status == "approved",
                rx.badge("已绑定 · 审核通过", color_scheme="green", size="1", radius="full"),
                rx.cond(
                    GithubBindState.verify_status == "pending",
                    rx.badge("待审核", color_scheme="orange", size="1", radius="full"),
                    rx.cond(
                        GithubBindState.verify_status == "rejected",
                        rx.badge("已拒绝", color_scheme="red", size="1", radius="full"),
                        rx.badge("未绑定", color_scheme="gray", size="1", radius="full"),
                    ),
                ),
            ),
            justify="between",
            align="center",
            margin_bottom="16px",
        ),
        
        # 绑定状态显示
        rx.cond(
            GithubBindState.verify_status == "approved",
            # 已绑定状态
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("GitHub 用户名", size="1", weight="medium", color="rgb(107, 114, 128)"),
                        rx.hstack(
                            rx.input(
                                value=GithubBindState.github_username,
                                disabled=True,
                                size="2",
                                flex="1",
                                border_radius="8px",
                                background="rgb(249, 250, 251)",
                            ),
                            rx.link(
                                rx.text("访问主页 →", size="1"),
                                href=f"https://github.com/{GithubBindState.github_username}",
                                color="rgb(37, 99, 235)",
                            ),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                        rx.text(
                            f"GitHub 实名：{GithubBindState.github_name} · 核查通过 ✓",
                            size="1",
                            color="rgb(156, 163, 175)",
                            margin_top="4px",
                        ),
                        spacing="2",
                        align="stretch",
                        width="100%",
                    ),
                    width="100%",
                ),
                rx.box(
                    rx.text(
                        "如需修改绑定账号，请向教师申请解除当前绑定后重新提交。",
                        size="1",
                        color="rgb(161, 98, 7)",
                    ),
                    padding="12px 16px",
                    background="rgb(254, 252, 232)",
                    border="1px solid rgb(254, 240, 138)",
                    border_radius="8px",
                    margin_top="12px",
                ),
                spacing="3",
                width="100%",
            ),
            # 未绑定或待审核状态 - 显示表单
            rx.vstack(
                rx.vstack(
                    rx.text("GitHub 用户名", size="1", weight="medium", color="rgb(107, 114, 128)"),
                    rx.hstack(
                        rx.input(
                            placeholder="请输入GitHub用户名",
                            value=GithubBindState.input_github_username,
                            on_change=GithubBindState.set_input_username,
                            size="2",
                            flex="1",
                            border_radius="8px",
                            disabled=GithubBindState.verify_status == "pending",
                        ),
                        rx.button(
                            "验证",
                            size="2",
                            variant="outline",
                            on_click=GithubBindState.validate_github_username(
                                GithubBindState.input_github_username
                            ),
                            loading=GithubBindState.is_loading,
                            disabled=GithubBindState.verify_status == "pending",
                            border_radius="8px",
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    # 验证结果提示
                    rx.cond(
                        GithubBindState.validation_message != "",
                        rx.text(
                            GithubBindState.validation_message,
                            size="1",
                            color=rx.cond(
                                GithubBindState.validation_message.contains("✓"),
                                "rgb(22, 163, 74)",
                                "rgb(220, 38, 38)",
                            ),
                            margin_top="4px",
                        ),
                    ),
                    spacing="2",
                    align="stretch",
                    width="100%",
                ),
                
                # 状态消息
                rx.cond(
                    GithubBindState.status_message != "",
                    rx.box(
                        rx.text(
                            GithubBindState.status_message,
                            size="1",
                            color=rx.cond(
                                GithubBindState.status_type == "success",
                                "rgb(22, 163, 74)",
                                rx.cond(
                                    GithubBindState.status_type == "error",
                                    "rgb(220, 38, 38)",
                                    rx.cond(
                                        GithubBindState.status_type == "warning",
                                        "rgb(217, 119, 6)",
                                        "rgb(37, 99, 235)",
                                    ),
                                ),
                            ),
                        ),
                        padding="12px 16px",
                        background=rx.cond(
                            GithubBindState.status_type == "success",
                            "rgb(240, 253, 244)",
                            rx.cond(
                                GithubBindState.status_type == "error",
                                "rgb(254, 242, 242)",
                                rx.cond(
                                    GithubBindState.status_type == "warning",
                                    "rgb(254, 252, 232)",
                                    "rgb(239, 246, 255)",
                                ),
                            ),
                        ),
                        border=rx.cond(
                            GithubBindState.status_type == "success",
                            "1px solid rgb(187, 247, 208)",
                            rx.cond(
                                GithubBindState.status_type == "error",
                                "1px solid rgb(254, 202, 202)",
                                rx.cond(
                                    GithubBindState.status_type == "warning",
                                    "1px solid rgb(254, 240, 138)",
                                    "1px solid rgb(191, 219, 254)",
                                ),
                            ),
                        ),
                        border_radius="8px",
                        margin_top="12px",
                    ),
                ),
                
                # 提交按钮
                rx.button(
                    "提交绑定申请",
                    size="2",
                    color_scheme="blue",
                    on_click=GithubBindState.submit_binding,
                    disabled=(
                        (GithubBindState.input_github_username == "") |
                        (~GithubBindState.github_account_exists) |
                        (GithubBindState.verify_status == "pending")
                    ),
                    border_radius="8px",
                    margin_top="12px",
                ),
                
                spacing="3",
                width="100%",
            ),
        ),
        
        padding="24px",
        background="white",
        border_radius="12px",
        border="1px solid rgb(243, 244, 246)",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        margin_bottom="24px",
    )


def password_change_card() -> rx.Component:
    """修改密码卡片"""
    return rx.box(
        rx.text("修改密码", size="3", weight="bold", color="rgb(55, 65, 81)", margin_bottom="16px"),
        
        rx.vstack(
            rx.vstack(
                rx.text("当前密码", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    type="password",
                    placeholder="请输入当前密码",
                    size="2",
                    width="100%",
                    max_width="400px",
                    border_radius="8px",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.vstack(
                rx.text("新密码", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    type="password",
                    placeholder="至少 8 位，包含字母和数字",
                    size="2",
                    width="100%",
                    max_width="400px",
                    border_radius="8px",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.vstack(
                rx.text("确认新密码", size="1", weight="medium", color="rgb(107, 114, 128)"),
                rx.input(
                    type="password",
                    placeholder="再次输入新密码",
                    size="2",
                    width="100%",
                    max_width="400px",
                    border_radius="8px",
                ),
                spacing="2",
                align="stretch",
            ),
            rx.button(
                "确认修改密码",
                size="2",
                color_scheme="blue",
                border_radius="8px",
            ),
            spacing="4",
            width="100%",
            max_width="400px",
        ),
        
        padding="24px",
        background="white",
        border_radius="12px",
        border="1px solid rgb(243, 244, 246)",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
    )


def profile_page() -> rx.Component:
    """个人资料页面主组件"""
    return rx.box(
        # 侧边栏
        sidebar(),
        
        # 主内容区
        rx.box(
            # 页面标题
            rx.box(
                rx.text("个人资料", size="6", weight="bold", color="rgb(31, 41, 55)"),
                rx.text("管理账号信息与 GitHub 绑定", size="2", color="rgb(156, 163, 175)", margin_top="2px"),
                margin_bottom="24px",
            ),
            
            # 内容卡片
            profile_card(),
            github_binding_card(),
            password_change_card(),
            
            margin_left="224px",
            padding="32px",
            max_width="960px",
            on_mount=GithubBindState.load_github_binding,
        ),
        
        width="100%",
        min_height="100vh",
        background="rgb(249, 250, 251)",
    )
