"""F-D-005 仓库协作者权限管理 State

通过 GitHub Team 统一管理课程组成员权限，禁止个人直接授权，确保权限管理规范化。
"""

class CollabPermState:
    """协作者权限管理状态类"""
    
    # 状态变量
    members = []
    team_name = ""
    
    # 角色枚举定义 - GitHub 标准角色权限
    ROLE_CHOICES = {
        "Admin": "管理员权限",
        "Write": "写入权限",
        "Triage": "分类权限",
        "Read": "只读权限"
    }
    
    VALID_ROLES = list(ROLE_CHOICES.keys())
    
    role_options = [
        {"value": "Admin", "label": "管理员"},
        {"value": "Write", "label": "写入"},
        {"value": "Triage", "label": "分类"},
        {"value": "Read", "label": "只读"}
    ]
    
    def __init__(self):
        self.members = []
        self.team_name = ""
    
    def add_member(self, user_id: str, role: str = "Read") -> None:
        """
        通过团队添加成员
        
        Args:
            user_id: 用户标识
            role: 角色权限（Admin/Write/Triage/Read）
        """
        if role not in self.VALID_ROLES:
            raise ValueError(f"无效角色: {role}，必须是 {self.VALID_ROLES} 之一")
        
        # 检查成员是否已存在
        existing = next((m for m in self.members if m["user_id"] == user_id), None)
        if existing:
            existing["role"] = role
        else:
            self.members.append({
                "user_id": user_id,
                "role": role,
                "added_at": None  # 实际实现时记录时间戳
            })
    
    def remove_member(self, user_id: str) -> None:
        """
        从团队移除成员
        
        Args:
            user_id: 用户标识
        """
        self.members = [m for m in self.members if m["user_id"] != user_id]
