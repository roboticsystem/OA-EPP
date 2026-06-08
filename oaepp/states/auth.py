"""F-S-001 登录/退出状态 — AuthState

职责：
- login(username, password) — 验证学号+密码，设置全局用户信息
- logout() — 清除登录状态
- 连续失败锁定（5次失败锁定5分钟）

数据库表：users（id, student_no, full_name, role, password_hash, email）
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

try:
    import reflex as rx
except Exception:
    rx = None


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    """使用 bcrypt 对密码进行哈希。"""
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, stored: str) -> bool:
    """验证密码，支持 bcrypt（$2b$...）、SHA-256 salt:hash、纯 SHA-256 三种格式。"""
    if not stored:
        return False
    # bcrypt 格式
    if stored.startswith("$2b$") or stored.startswith("$2a$"):
        import bcrypt as _bcrypt
        return _bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    # SHA-256 salt:hash 格式
    if ":" in stored:
        try:
            salt, expected_hash = stored.split(":", 1)
            actual = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
            return hmac.compare_digest(actual, expected_hash)
        except (ValueError, AttributeError):
            return False
    # 纯 SHA-256（无 salt，兼容旧数据）
    actual = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(actual, stored)


AuthState = None

if rx is not None:
    class AuthState(rx.State):
        """登录/退出状态管理"""

        is_authenticated: bool = False
        current_user_id: Optional[int] = None
        current_student_no: str = ""
        current_full_name: str = ""
        current_role: str = ""
        error_message: str = ""
        is_locked: bool = False

        form_username: str = ""
        form_password: str = ""

        _fail_count: int = 0
        _lock_until: float = 0.0

        MAX_FAILS: int = 5
        LOCK_SECONDS: int = 300

        def set_form_username(self, val: str):
            self.form_username = val

        def set_form_password(self, val: str):
            self.form_password = val

        async def handle_login(self):
            """UI 绑定用：从表单字段读取用户名密码。"""
            await self.login()

        async def login(self, username: str = "", password: str = ""):
            """验证学号/用户名 + 密码。

            支持两种调用方式：
            - login() — 从 form_username / form_password 读取（UI 绑定）
            - login("user", "pwd") — 直接传参（测试 / API 调用）
            """
            self.error_message = ""
            username = (username or self.form_username).strip()
            password = password or self.form_password

            if not username or not password:
                self.error_message = "请输入学号和密码"
                return

            now = time.time()
            if self._fail_count >= self.MAX_FAILS and now < self._lock_until:
                remaining = int(self._lock_until - now)
                self.error_message = f"账号已锁定，请 {remaining} 秒后重试"
                self.is_locked = True
                return

            self.is_locked = False

            try:
                try:
                    from database import db_sync
                except ImportError:
                    from oaepp.database import db_sync

                with db_sync() as cur:
                    cur.execute(
                        "SELECT id, student_no, full_name, role, password_hash "
                        "FROM users WHERE student_no = %s",
                        (username,),
                    )
                    row = cur.fetchone()
            except Exception as e:
                self.error_message = f"数据库连接失败: {e}"
                return

            if row is None:
                self._record_fail()
                self.error_message = "学号或密码错误"
                return

            stored_hash = row.get("password_hash", "")
            if not stored_hash or not _verify_password(password, stored_hash):
                self._record_fail()
                self.error_message = "学号或密码错误"
                return

            self._fail_count = 0
            self.is_authenticated = True
            self.current_user_id = row["id"]
            self.current_student_no = row["student_no"]
            self.current_full_name = row.get("full_name", "")
            self.current_role = row.get("role", "student")

        async def logout(self):
            """清除登录状态。"""
            self.is_authenticated = False
            self.current_user_id = None
            self.current_student_no = ""
            self.current_full_name = ""
            self.current_role = ""
            self.error_message = ""

        def _record_fail(self):
            self._fail_count += 1
            if self._fail_count >= self.MAX_FAILS:
                self._lock_until = time.time() + self.LOCK_SECONDS
                self.is_locked = True
