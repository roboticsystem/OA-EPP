"""
ProfileState — Reflex state for the student profile page (F-S-002).

继承 rx.State（不继承 GlobalState，符合 PR 审查规范）。
使用 hashlib + sqlmodel 实现本地密码哈希和资料持久化。
"""

import hashlib
import logging
import os
import secrets

import reflex as rx
import sqlmodel

logger = logging.getLogger("oaepp.profile")

# ── Database setup (SQLite, per test/reflex/conftest.py 风格) ───────────

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "profile.db")

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        db_url = os.environ.get("REFLEX_DB_URL", f"sqlite:///{DB_PATH}")
        _engine = sqlmodel.create_engine(db_url, connect_args={"check_same_thread": False})
    return _engine

def _init_db():
    engine = _get_engine()
    # 轻量级建表：仅 profile 功能需要的 users 表（假用户数据）
    with engine.begin() as conn:
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS profile (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            email      TEXT NOT NULL DEFAULT '',
            phone      TEXT NOT NULL DEFAULT '',
            student_class TEXT NOT NULL DEFAULT '',
            bio        TEXT NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL DEFAULT ''
        )
        """)


# ── Password helpers (hashlib pbkdf2, stdlib only) ──────────────────────

def _hash_password(password: str) -> str:
    """Return iteration:salt:hexdigest string."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"100000:{salt}:{dk.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    """Check password against stored iteration:salt:hexdigest."""
    if not stored or ":" not in stored:
        return False
    parts = stored.split(":")
    if len(parts) != 3:
        return False
    iterations, salt, digest = parts
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        int(iterations),
    )
    return dk.hex() == digest


# ── ProfileState ────────────────────────────────────────────────────────

class ProfileState(rx.State):
    """个人资料状态 — 仅继承 rx.State，不继承 GlobalState."""

    # ── 数据隔离 ──
    current_user_id: int = 1

    # ── Profile 字段（测试要求：TC01） ──
    username: str = ""
    email: str = ""
    phone: str = ""
    student_class: str = ""
    bio: str = ""

    # ── 编辑表单（双向绑定） ──
    edit_username: str = ""
    edit_email: str = ""
    edit_phone: str = ""
    edit_class: str = ""
    edit_bio: str = ""

    # ── 密码字段 ──
    old_password: str = ""
    new_password: str = ""
    confirm_password: str = ""

    # ── UI 反馈 ──
    profile_message: str = ""
    profile_error: str = ""
    password_message: str = ""
    password_error: str = ""
    error_message: str = ""   # 通用错误（测试用）

    @rx.var(cache=False)
    def display_name_initial(self) -> str:
        name = self.username
        return name[0] if name else "?"

    @rx.var(cache=False)
    def profile_has_changes(self) -> bool:
        return (
            self.edit_username != self.username
            or self.edit_email != self.email
            or self.edit_phone != self.phone
            or self.edit_class != self.student_class
            or self.edit_bio != self.bio
        )

    # ── 事件处理器 ───────────────────────────────────────────────────

    def _ensure_seed(self):
        """确保数据库初始化并有种子用户。"""
        _init_db()
        engine = _get_engine()
        with sqlmodel.Session(engine) as session:
            row = session.exec(
                sqlmodel.text("SELECT id FROM profile WHERE id = :uid"),
                {"uid": self.current_user_id},
            ).first()
            if row is None:
                session.exec(sqlmodel.text("""
                    INSERT INTO profile (id, username, email, phone, student_class, bio, password_hash)
                    VALUES (:id, :un, :em, :ph, :sc, :bio, :pw)
                """), {
                    "id": self.current_user_id,
                    "un": "示例用户",
                    "em": "user@example.edu.cn",
                    "ph": "13800000000",
                    "sc": "工程实践班",
                    "bio": "",
                    "pw": _hash_password("Test@123456"),
                })
                session.commit()

    def _load_from_db(self):
        engine = _get_engine()
        with sqlmodel.Session(engine) as session:
            row = session.exec(
                sqlmodel.text(
                    "SELECT username, email, phone, student_class, bio "
                    "FROM profile WHERE id = :uid"
                ),
                {"uid": self.current_user_id},
            ).first()
        if row:
            self.username = row[0] or ""
            self.email = row[1] or ""
            self.phone = row[2] or ""
            self.student_class = row[3] or ""
            self.bio = row[4] or ""
            self.edit_username = self.username
            self.edit_email = self.email
            self.edit_phone = self.phone
            self.edit_class = self.student_class
            self.edit_bio = self.bio

    def _save_to_db(self):
        engine = _get_engine()
        with sqlmodel.Session(engine) as session:
            session.exec(sqlmodel.text(
                "UPDATE profile SET username=:un, email=:em, phone=:ph, "
                "student_class=:sc, bio=:bio WHERE id=:uid"
            ), {
                "un": self.edit_username,
                "em": self.edit_email,
                "ph": self.edit_phone,
                "sc": self.edit_class,
                "bio": self.edit_bio,
                "uid": self.current_user_id,
            })
            session.commit()

    async def load_profile(self):
        """页面挂载时加载数据。"""
        self.reset()
        try:
            self._ensure_seed()
            self._load_from_db()
        except Exception as e:
            self.profile_error = f"加载失败：{e}"

    async def update_profile(self):
        """保存编辑后的资料（测试要求 TC02）。"""
        self.profile_message = ""
        self.profile_error = ""
        self.error_message = ""
        try:
            self._save_to_db()
            self.username = self.edit_username
            self.email = self.edit_email
            self.phone = self.edit_phone
            self.student_class = self.edit_class
            self.bio = self.edit_bio
            self.profile_message = "✅ 个人资料已保存"
        except Exception as e:
            msg = f"保存失败：{e}"
            self.profile_error = msg
            self.error_message = msg

    async def save_profile(self):
        """update_profile 的别名（UI 按钮使用）。"""
        await self.update_profile()

    async def change_password(self, old_pw="", new_pw="", confirm_pw=""):
        """验证旧密码并更新密码（测试要求 TC03/TC04）。

        接受可选参数便于测试：
          change_password("old", "new", "new")
        UI 无参调用时使用表单字段。
        """
        _old = old_pw or self.old_password
        _new = new_pw or self.new_password
        _confirm = confirm_pw or self.confirm_password

        self.password_message = ""
        self.password_error = ""
        self.error_message = ""

        if len(_new) < 8:
            msg = "新密码至少需要 8 位"
            self.password_error = msg
            self.error_message = msg
            return
        if _new != _confirm:
            msg = "两次输入的新密码不一致"
            self.password_error = msg
            self.error_message = msg
            return
        if _old == _new:
            msg = "新密码不能与旧密码相同"
            self.password_error = msg
            self.error_message = msg
            return

        try:
            engine = _get_engine()
            with sqlmodel.Session(engine) as session:
                row = session.exec(
                    sqlmodel.text("SELECT password_hash FROM profile WHERE id = :uid"),
                    {"uid": self.current_user_id},
                ).first()
                if not row or not _verify_password(_old, row[0]):
                    msg = "当前密码不正确"
                    self.password_error = msg
                    self.error_message = msg
                    return

                new_hash = _hash_password(_new)
                session.exec(sqlmodel.text(
                    "UPDATE profile SET password_hash = :pw WHERE id = :uid"
                ), {"pw": new_hash, "uid": self.current_user_id})
                session.commit()

            self.password_message = "✅ 密码修改成功"
            self.old_password = ""
            self.new_password = ""
            self.confirm_password = ""
        except Exception as e:
            msg = f"修改失败：{e}"
            self.password_error = msg
            self.error_message = msg

    # ── 输入变更回调 ─────────────────────────────────────────────────

    async def set_edit_username(self, value: str):
        self.edit_username = value

    async def set_edit_email(self, value: str):
        self.edit_email = value

    async def set_edit_phone(self, value: str):
        self.edit_phone = value

    async def set_edit_class(self, value: str):
        self.edit_class = value

    async def set_edit_bio(self, value: str):
        self.edit_bio = value

    async def set_old_password(self, value: str):
        self.old_password = value

    async def set_new_password(self, value: str):
        self.new_password = value

    async def set_confirm_password(self, value: str):
        self.confirm_password = value
