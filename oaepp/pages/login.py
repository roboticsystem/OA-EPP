"""
Reflex-based login page adapted from prototype/login.html.
Provides `login_page` when Reflex is available; otherwise exposes `render()` fallback.
"""
try:
    import reflex as rx
except Exception:
    rx = None

def _html_fallback():
    return """
<div class="oaepp-login-card">
  <h1>工程实践管理平台</h1>
  <p>OA-EPP · 登录</p>
  <form action="/dashboard" method="get">
    <div><label>学号</label><input name="username" placeholder="请输入学号" /></div>
    <div><label>密码</label><input type="password" name="password" placeholder="请输入密码" /></div>
    <div><button type="submit">登 录</button></div>
  </form>
  <p style="text-align:center;font-size:12px;color:#888;margin-top:8px;">初始密码为学号，请登录后及时修改</p>
  <div style="text-align:center;margin-top:12px;">
    <a href="/dashboard">学生端</a> · <a href="/admin_students.html">教师端</a>
  </div>
</div>
"""

login_page = None
if rx is not None:
    try:
        from states.auth import AuthState
    except ImportError:
        from oaepp.states.auth import AuthState

    def _login_form():
        return rx.vstack(
            rx.text("学号", weight="medium"),
            rx.input(
                placeholder="请输入学号",
                value=AuthState.form_username,
                on_change=AuthState.set_form_username,
                width="100%",
            ),
            rx.text("密码", weight="medium"),
            rx.input(
                type_="password",
                placeholder="请输入密码",
                value=AuthState.form_password,
                on_change=AuthState.set_form_password,
                width="100%",
            ),
            rx.cond(
                AuthState.error_message != "",
                rx.box(
                    rx.text(AuthState.error_message, color="red", size="2"),
                    padding="8px 12px",
                    background="#fef2f2",
                    border_radius="8px",
                    border="1px solid #fecaca",
                ),
                rx.box(),
            ),
            rx.button(
                "登 录",
                width="100%",
                on_click=AuthState.handle_login,
            ),
            rx.text("初始密码为学号，请登录后及时修改", color="gray", size="1"),
            spacing="3",
            width="100%",
            align="stretch",
        )

    def login_page():
        """A Reflex login page with real authentication.

        默认已登录，学生可直接访问功能页面；登录表单保留，可切换账号。
        """
        return rx.center(
            rx.box(
                rx.vstack(
                    rx.heading("工程实践管理平台", size="6"),
                    rx.text("OA-EPP · 登录", color="gray"),
                    # 开发模式提示
                    rx.cond(
                        AuthState.is_authenticated,
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    f"当前用户: {AuthState.current_full_name} ({AuthState.current_student_no})",
                                    color="green",
                                    weight="medium",
                                ),
                                rx.text(
                                    "开发模式 — 可直接访问功能页面",
                                    color="gray",
                                    size="1",
                                ),
                                rx.hstack(
                                    rx.link("Dashboard", href="/dashboard"),
                                    rx.link("成绩", href="/grades"),
                                    rx.link("作业", href="/assignments"),
                                    rx.link("考勤", href="/attendance"),
                                    rx.link("资料", href="/profile"),
                                    spacing="2",
                                    justify="center",
                                ),
                                spacing="1",
                                align="center",
                            ),
                            padding="10px 14px",
                            background="#f0fdf4",
                            border_radius="8px",
                            border="1px solid #bbf7d0",
                        ),
                    ),
                    # 登录表单（始终显示，方便切换账号）
                    _login_form(),
                    rx.hstack(
                        rx.link("学生端", href="/dashboard"),
                        rx.link("教师端", href="/admin_students.html"),
                        spacing="5",
                        justify="center",
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                class_name="oaepp-login-card",
            ),
            class_name="oaepp-login-page",
            min_height="100vh",
            width="100%",
            background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
            padding="20px",
        )

def render():
    """Return HTML fallback string (used when Reflex not installed)."""
    return _html_fallback()
