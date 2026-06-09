import reflex as rx


class AuthState(rx.State):
    """认证状态管理"""
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
    
    def logout(self):
        """退出登录"""
        self.current_student_id = 0
        self.current_student_name = ""
        self.current_student_email = ""
        self.is_logged_in = False
