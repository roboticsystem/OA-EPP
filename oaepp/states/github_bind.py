"""
F-S-003 GitHub 账号绑定功能 - State 类

功能概述：
- 学生登录后可填写 GitHub 用户名，系统通过 GitHub API 自动校验账号有效性
- 绑定申请需教师审核确认，每个学生只允许绑定一个账号
- 已绑定账号修改需向教师申请解除旧绑定

数据库表：github_bindings
"""

try:
    import reflex as rx
    import httpx
    from database import db, transaction
except Exception:
    rx = None


class GitHubBindState(rx.State):
    """GitHub 账号绑定状态管理（独立状态，不继承全局 State）"""

    # ── 用户信息 ──
    current_user: dict = {}
    """当前登录用户信息：{"student_no": "", "name": ""}"""

    # ── 表单数据 ──
    github_username: str = ""
    """用户输入的 GitHub 用户名"""

    # ── 绑定状态信息 ──
    bind_status: str = "unbound"
    """当前绑定状态：unbound（未绑定）/ pending（待审核）/ approved（已绑定）/ rejected（已拒绝）"""

    github_info: dict = {}
    """GitHub API 返回的用户信息：{"username": "", "name": "", "avatar_url": "", "exists": False}"""

    # ── UI 状态 ──
    is_validating: bool = False
    """是否正在验证 GitHub 账号"""

    is_submitting: bool = False
    """是否正在提交绑定申请"""

    validation_message: str = ""
    """验证结果提示信息"""

    # ── Setter 方法 ──
    def set_github_username(self, username: str):
        """设置 GitHub 用户名"""
        self.github_username = username

    # ── 方法：查询并显示当前绑定状态 ──
    async def show_current_status(self):
        """查询数据库并显示当前用户的绑定状态"""
        if not self.current_user or not self.current_user.get("student_no"):
            self.show_toast("请先登录", "warning")
            return
        
        student_no = self.current_user["student_no"]
        
        try:
            async with db() as cur:
                await cur.execute(
                    """
                    SELECT gb.verify_status, gb.github_username, gb.github_name
                    FROM github_bindings gb
                    JOIN students s ON gb.student_user_id = s.user_id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.student_no = %s
                    """,
                    (student_no,),
                )
                result = await cur.fetchone()
                
                if result:
                    self.bind_status = result["verify_status"]
                    self.github_username = result["github_username"]
                    self.github_info = {
                        "username": result["github_username"],
                        "name": result.get("github_name", "") or "",
                        "exists": True,
                    }
                else:
                    self.bind_status = "unbound"
                    
        except Exception as e:
            self.show_toast(f"查询失败：{str(e)}", "error")
            print(f"[ERROR] show_current_status 异常: {e}")

    # ── 方法：加载当前用户的 GitHub 绑定状态 ──
    async def load_bind_status(self):
        """从数据库加载当前用户的 GitHub 绑定状态"""
        if not self.current_user or not self.current_user.get("student_no"):
            self.show_toast("请先登录", "warning")
            return

        student_no = self.current_user["student_no"]

        async with db() as cur:
            await cur.execute(
                """
                SELECT gb.github_username, gb.verify_status, gb.github_name, gb.verified_at
                FROM github_bindings gb
                JOIN students s ON gb.student_user_id = s.user_id
                JOIN users u ON s.user_id = u.id
                WHERE u.student_no = %s
                """,
                (student_no,),
            )
            row = await cur.fetchone()

            if row:
                self.bind_status = row["verify_status"]
                self.github_username = row["github_username"]
                self.github_info = {
                    "username": row["github_username"],
                    "name": row["github_name"] or "",
                    "exists": True,
                }
            else:
                self.bind_status = "unbound"
                self.github_username = ""
                self.github_info = {}

    # ── 方法：验证 GitHub 用户名（调用 GitHub API） ──
    async def validate_github_username(self):
        """通过 GitHub API 验证用户名是否存在"""
        if not self.github_username or not self.github_username.strip():
            self.validation_message = "请输入 GitHub 用户名"
            self.github_info = {"exists": False}
            return

        self.is_validating = True
        username = self.github_username.strip()

        try:
            # 调用 GitHub API 检查用户是否存在
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/users/{username}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    self.github_info = {
                        "username": data.get("login", username),
                        "name": data.get("name", ""),
                        "avatar_url": data.get("avatar_url", ""),
                        "exists": True,
                    }
                    self.validation_message = f"✅ GitHub 账号存在：{data.get('login', username)}"
                elif response.status_code == 404:
                    self.github_info = {"exists": False}
                    self.validation_message = "❌ GitHub 账号不存在，请检查用户名是否正确"
                else:
                    self.validation_message = f"⚠️ GitHub API 请求失败（状态码：{response.status_code}），请稍后重试"
                    self.github_info = {"exists": False}

        except httpx.TimeoutException:
            self.validation_message = "⚠️ GitHub API 请求超时，请检查网络连接"
            self.github_info = {"exists": False}
        except Exception as e:
            self.validation_message = f"⚠️ 验证失败：{str(e)}"
            self.github_info = {"exists": False}
        finally:
            self.is_validating = False

    # ── 方法：提交绑定申请 ──
    async def submit_bind_request(self):
        """提交 GitHub 账号绑定申请（需教师审核）"""
        # 1. 检查是否已登录
        if not self.current_user or not self.current_user.get("student_no"):
            self.show_toast("请先登录", "warning")
            return
        
        student_no = self.current_user.get("student_no")

        # 2. 检查 GitHub 用户名是否已验证
        if not self.github_info.get("exists"):
            self.show_toast("请先验证 GitHub 用户名", "warning")
            return

        username = self.github_info["username"]
        name = self.github_info.get("name", "")

        self.is_submitting = True

        try:
            async with transaction() as cur:
                # 3. 检查该学生是否已经有绑定记录
                await cur.execute(
                    """
                    SELECT gb.id, gb.verify_status
                    FROM github_bindings gb
                    JOIN students s ON gb.student_user_id = s.user_id
                    JOIN users u ON s.user_id = u.id
                    WHERE u.student_no = %s
                    """,
                    (student_no,),
                )
                existing = await cur.fetchone()

                if existing:
                    # 已有绑定记录
                    if existing["verify_status"] == "approved":
                        self.show_toast("您已绑定 GitHub 账号，如需修改请联系教师解除旧绑定", "warning")
                        self.is_submitting = False
                        return
                    elif existing["verify_status"] == "pending":
                        self.show_toast("您的绑定申请正在审核中，请耐心等待", "warning")
                        self.is_submitting = False
                        return
                    else:
                        # rejected 状态，更新为新的申请
                        await cur.execute(
                            """
                            UPDATE github_bindings
                            SET github_username = %s,
                                github_name = %s,
                                verify_status = 'pending',
                                verified_at = NULL,
                                verified_by = NULL
                            WHERE id = %s
                            """,
                            (username, name, existing["id"]),
                        )
                        self.bind_status = "pending"
                        self.show_toast("绑定申请已重新提交，等待教师审核", "success")
                else:
                    # 首次绑定，插入新记录
                    # 先获取 student 的 user_id
                    await cur.execute(
                        "SELECT s.user_id FROM students s JOIN users u ON s.user_id = u.id WHERE u.student_no = %s",
                        (student_no,),
                    )
                    student_row = await cur.fetchone()

                    if not student_row:
                        self.show_toast("学生账号不存在，请联系管理员", "error")
                        self.is_submitting = False
                        return

                    user_id = student_row["user_id"]

                    await cur.execute(
                        """
                        INSERT INTO github_bindings
                            (student_user_id, github_username, github_name, verify_status)
                        VALUES (%s, %s, %s, 'pending')
                        """,
                        (user_id, username, name),
                    )
                    self.bind_status = "pending"
                    self.show_toast("绑定申请已提交，等待教师审核", "success")

        except Exception as e:
            error_msg = str(e)
            
            # 判断是否是表不存在的错误
            if "doesn't exist" in error_msg or "1146" in error_msg:
                self.show_toast("数据库表不存在，请联系管理员创建 github_bindings 表", "error")
            else:
                self.show_toast(f"提交失败：{error_msg}", "error")
        finally:
            self.is_submitting = False

    # ── 方法：解除绑定（仅用于 UI 提示，实际需教师操作） ──
    def request_unbind(self):
        """提示用户联系教师解除绑定"""
        self.show_toast("请联系教师解除当前 GitHub 账号绑定", "info")
