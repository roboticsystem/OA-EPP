"""认证状态管理 - 基于 users 表的学生身份管理"""
import reflex as rx


class AuthState(rx.State):
    """认证状态管理

    current_student_id 对应 users.id（远程数据库中的用户 ID）
    例如：users 表中 role='student' 的记录，id=57 是张三
    """
    current_student_id: int = 0
    current_student_name: str = ""
    current_student_email: str = ""
    is_logged_in: bool = False

    def set_student(self, student_id: int, name: str, email: str = ""):
        """设置当前学生信息"""
        self.current_student_id = student_id
        self.current_student_name = name
        self.current_student_email = email
        self.is_logged_in = True

    def login_by_user_id(self, user_id: int):
        """通过 users.id 快速登录（开发/测试用）"""
        self.current_student_id = user_id
        self.is_logged_in = True

    def logout(self):
        """退出登录"""
        self.current_student_id = 0
        self.current_student_name = ""
        self.current_student_email = ""
        self.is_logged_in = False
