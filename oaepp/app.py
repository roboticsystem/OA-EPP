import reflex as rx
from oaepp.states.course_state import CourseState
from oaepp.states.auth_state import AuthState
from oaepp.pages import courses, login

# 初始化应用
app = rx.App()

# 注册路由
app.add_page(login.index)
app.add_page(courses.courses)

# 如需要在其他页面中使用，可以继续添加:
# app.add_page(dashboard)
# app.add_page(assignments)
# app.add_page(grades)
# ...

if __name__ == "__main__":
    pass  # rxrun 会自动处理
