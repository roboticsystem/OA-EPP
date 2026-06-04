"""
认证状态管理
"""
import reflex as rx
from sqlmodel import Session, select
from models.database import User, Student
import hashlib


class AuthState(rx.State):
    """认证状态管理"""
    
    # 当前登录用户信息
    user_id: int = 0
    student_no: str = ""
    full_name: str = ""
    email: str = ""
    class_name: str = ""
    is_authenticated: bool = False
    
    # 登录表单
    username: str = ""
    password: str = ""
    login_error: str = ""
    
    def _hash_password(self, password: str) -> str:
        """密码哈希 (简单SHA256, 生产环境应使用bcrypt)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def do_login(self):
        """执行登录"""
        self.login_error = ""
        
        if not self.username or not self.password:
            self.login_error = "请输入学号和密码"
            return
        
        # 连接数据库验证
        with Session(rx.get_engine()) as session:
            # 查询用户
            statement = select(User).where(
                (User.student_no == self.username) | (User.email == self.username)
            )
            user = session.exec(statement).first()
            
            if not user:
                self.login_error = "用户不存在"
                return
            
            if not user.is_active:
                self.login_error = "账号已被禁用"
                return
            
            # 验证密码
            if user.password_hash != self._hash_password(self.password):
                self.login_error = "密码错误"
                return
            
            # 登录成功,保存用户信息
            self.user_id = user.id
            self.student_no = user.student_no or ""
            self.full_name = user.full_name
            self.email = user.email
            self.is_authenticated = True
            
            # 获取学生班级信息
            if user.role == "student":
                student_stmt = select(Student).where(Student.user_id == user.id)
                student = session.exec(student_stmt).first()
                if student:
                    self.class_name = student.class_name
        
        # 跳转到个人资料页
        return rx.redirect("/profile")
    
    def do_logout(self):
        """退出登录"""
        self.user_id = 0
        self.student_no = ""
        self.full_name = ""
        self.email = ""
        self.class_name = ""
        self.is_authenticated = False
        self.username = ""
        self.password = ""
        return rx.redirect("/")
    
    def set_username(self, value: str):
        """设置用户名"""
        self.username = value
    
    def set_password(self, value: str):
        """设置密码"""
        self.password = value
