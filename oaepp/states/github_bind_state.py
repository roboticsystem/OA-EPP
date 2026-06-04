"""
GitHub账号绑定状态管理 - F-S-003
"""
import reflex as rx
from sqlmodel import Session, select
from models.database import GithubBinding
from states.auth_state import AuthState
import httpx
from datetime import datetime


class GithubBindState(rx.State):
    """GitHub绑定状态管理"""
    
    # GitHub绑定信息
    github_username: str = ""
    github_name: str = ""
    verify_status: str = "not_bound"  # not_bound/pending/approved/rejected
    binding_exists: bool = False
    
    # 表单输入
    input_github_username: str = ""
    
    # 状态提示
    status_message: str = ""
    status_type: str = ""  # success/error/warning/info
    is_loading: bool = False
    
    # GitHub验证结果
    github_account_exists: bool = False
    github_account_name: str = ""
    validation_message: str = ""
    
    async def load_github_binding(self):
        """加载当前用户的GitHub绑定信息"""
        auth = self.get_value(AuthState)
        if not auth.is_authenticated:
            return
        
        student_user_id = auth.user_id
        
        # 查询数据库
        with Session(rx.get_engine()) as session:
            statement = select(GithubBinding).where(
                GithubBinding.student_user_id == student_user_id
            )
            binding = session.exec(statement).first()
            
            if binding:
                self.github_username = binding.github_username
                self.github_name = binding.github_name or ""
                self.verify_status = binding.verify_status
                self.binding_exists = True
                self.input_github_username = binding.github_username
            else:
                self.verify_status = "not_bound"
                self.binding_exists = False
                self.github_username = ""
                self.github_name = ""
    
    async def validate_github_username(self, username: str):
        """验证GitHub用户名是否存在"""
        self.is_loading = True
        self.validation_message = ""
        self.github_account_exists = False
        self.github_account_name = ""
        
        # 调用GitHub API验证
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/users/{username}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.github_account_exists = True
                    self.github_account_name = data.get("name", "")
                    self.validation_message = f"✓ 账号存在, 实名: {self.github_account_name or '未设置'}"
                elif response.status_code == 404:
                    self.github_account_exists = False
                    self.validation_message = "✗ GitHub账号不存在"
                else:
                    self.validation_message = f"✗ 验证失败 (HTTP {response.status_code})"
        except Exception as e:
            self.validation_message = f"✗ 网络错误: {str(e)}"
        finally:
            self.is_loading = False
    
    def set_input_username(self, value: str):
        """设置输入的GitHub用户名"""
        self.input_github_username = value
    
    async def submit_binding(self):
        """提交绑定申请"""
        # 验证输入
        if not self.input_github_username:
            self.status_message = "请输入GitHub用户名"
            self.status_type = "error"
            return
        
        if not self.github_account_exists:
            self.status_message = "请先验证GitHub用户名"
            self.status_type = "error"
            return
        
        auth = self.get_value(AuthState)
        if not auth.is_authenticated:
            return
        
        student_user_id = auth.user_id
        
        # 检查是否已绑定
        with Session(rx.get_engine()) as session:
            existing = session.exec(
                select(GithubBinding).where(
                    GithubBinding.student_user_id == student_user_id
                )
            ).first()
            
            if existing and existing.verify_status == "approved":
                self.status_message = "您已绑定GitHub账号,如需修改请向教师申请解除"
                self.status_type = "warning"
                return
            
            # 创建或更新绑定记录
            if existing:
                existing.github_username = self.input_github_username
                existing.github_name = self.github_account_name
                existing.verify_status = "pending"
                existing.verified_at = None
                existing.verified_by = None
            else:
                new_binding = GithubBinding(
                    student_user_id=student_user_id,
                    github_username=self.input_github_username,
                    github_name=self.github_account_name,
                    verify_status="pending"
                )
                session.add(new_binding)
            
            session.commit()
            
            self.status_message = "✓ 绑定申请已提交,等待教师审核"
            self.status_type = "success"
            self.verify_status = "pending"
            self.github_username = self.input_github_username
            self.github_name = self.github_account_name
            self.binding_exists = True
    
    async def clear_status(self):
        """清除状态消息"""
        import asyncio
        await asyncio.sleep(3)
        self.status_message = ""
        self.status_type = ""
