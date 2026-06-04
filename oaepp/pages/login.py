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
  <h1>工程实践管理平台</h1>
  <p>OA-EPP · 登录</p>
  <form action="/dashboard" method="get">
    <div><label>学号 / 邮箱</label><input name="username" placeholder="请输入学号或邮箱" /></div>
    <div><label>密码</label><input type="password" name="password" placeholder="请输入密码" /></div>
    <div><button type="submit">登 录</button></div>
  </form>
  <div style="text-align:center;margin-top:12px;">
    <a href="/dashboard">学生端</a> · <a href="/admin_students.html">教师端</a>
  </div>
</div>
"""

login_page = None
if rx is not None:
  def login_page():
    """A minimal Reflex-compatible login page."""
    return rx.center(
      rx.box(
        rx.vstack(
          rx.heading("工程实践管理平台", size="6"),
          rx.text("OA-EPP · 登录", color="gray"),
          rx.vstack(
            rx.text("学号 / 邮箱", weight="medium"),
            rx.input(placeholder="请输入学号或邮箱", name="username", width="100%"),
            rx.text("密码", weight="medium"),
            rx.input(type_="password", placeholder="请输入密码", name="password", width="100%"),
            rx.button("登 录", width="100%"),
            spacing="3",
            width="100%",
            align="stretch",
          ),
          rx.hstack(
            rx.link("学生端", href="/dashboard"),
            rx.link("教师端", href="/grading"),
            spacing="5",
            justify="center",
          ),
          spacing="4",
          width="100%",
          align="stretch",
        ),
        max_width="460px",
        width="100%",
        padding="28px",
        border_radius="12px",
        box_shadow="0 10px 30px rgba(0,0,0,0.08)",
        background="white",
      ),
      min_height="100vh",
      width="100%",
      background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
      padding="20px",
    )

def render():
    """Return HTML fallback string (used when Reflex not installed)."""
    return _html_fallback()
