"""F-T-006 需求文档编辑器 — ReqEditorState

对应原型：教师端需求文档编辑工具
对应测试：tests/reflex/test_F_T_006_req_editor.py
对应需求：docs/ 功能需求文档 F-T-006

验收要点：
- Markdown 编辑器含预置功能需求模板
- Copilot 辅助可自动补全验收标准等属性
- 支持导入外部 md 文件并校验格式合规性
- 文档渲染预览实时更新（preview_html 计算属性）
- 一键提交到 GitHub 仓库
- 学生审阅模式：可评论，教师确认后封存文档

协作规范（来自 学生功能开发指南.md）：
- 独立 rx.State，不修改全局文件
- 通过 oaepp.database.db_sync() 使用公共数据库连接池
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import reflex as rx

# ── 预置功能需求模板 ────────────────────────────────────────────────────
PRESET_TEMPLATE = """# 功能需求文档

## F-XXX: [功能名称]

### 功能描述
[在此描述功能的目标和范围]

### 验收标准
- [ ] 标准1: [具体的验收条件]
- [ ] 标准2: [具体的验收条件]
- [ ] 标准3: [具体的验收条件]

### 安全属性
- **认证要求**: [是否需要登录、多因素认证等]
- **授权要求**: [角色权限控制要求]
- **数据保护**: [数据传输加密、存储安全等]

### 技术约束
- [语言/框架/数据库等技术限制]

### 附加说明
- [其他补充信息、参考资料、关联需求等]
"""

# ── F-xxx 格式校验正则（类级别常量） ──────────────────────────────────
REQ_PATTERN = r'^##\s+F-\d{3}:'

# ── Copilot 自动补全片段 ──────────────────────────────────────────────
COPILOT_SNIPPETS: Dict[str, str] = {
    "验收标准": """### 验收标准
- [ ] 标准1: [具体的验收条件]
- [ ] 标准2: [具体的验收条件]
- [ ] 标准3: [具体的验收条件]
""",
    "安全属性": """### 安全属性
- **认证要求**: [是否需要登录、多因素认证等]
- **授权要求**: [角色权限控制要求]
- **数据保护**: [数据传输加密、存储安全等]
""",
    "技术约束": """### 技术约束
- [语言/框架/数据库等技术限制]
- [性能指标要求]
""",
    "测试要点": """### 测试要点
- [ ] 单元测试: [覆盖的关键函数]
- [ ] 集成测试: [模块间交互验证]
- [ ] 端到端测试: [用户场景验证]
""",
}


class ReqEditorState(rx.State):
    """需求文档编辑器状态 (F-T-006)

    支持：
    - Markdown 编辑与实时 HTML 预览
    - 预置模板加载
    - F-xxx 格式校验
    - 外部 .md 文件导入
    - Copilot 自动补全辅助
    - 一键保存到数据库
    - 学生审阅评论
    - 文档封存锁定
    """

    # ── 核心状态变量 ──────────────────────────────────────────────
    content: str = ""
    """当前编辑器中的 Markdown 内容"""

    is_sealed: bool = False
    """文档是否已封存（封存后禁止修改）"""

    imported_filename: str = ""
    """导入文件的文件名"""

    # ── 校验与提示 ────────────────────────────────────────────────
    validation_errors: List[str] = []
    """格式校验错误列表（空列表表示通过）"""

    save_message: str = ""
    """保存/操作的反馈消息"""

    # ── 审阅评论 ──────────────────────────────────────────────────
    comments: List[Dict[str, Any]] = []
    """审阅评论列表 [{"content": "...", "time": "..."}]"""

    new_comment: str = ""
    """正在输入的新评论"""

    # ── 文档元信息 ────────────────────────────────────────────────
    document_title: str = ""
    """文档标题（用于保存时写入数据库）"""

    course_id: int = 0
    """关联课程 ID"""

    document_id: Optional[int] = None
    """当前编辑的文档数据库 ID（新建为 None）"""

    # ── Copilot ───────────────────────────────────────────────────
    copilot_suggestions: List[str] = []
    """Copilot 可插入片段的关键词列表"""

    show_copilot_panel: bool = False
    """是否显示 Copilot 建议面板"""

    # ── 计算属性：实时 Markdown → HTML 预览 ──────────────────────

    @rx.var
    def preview_html(self) -> str:
        """实时将 Markdown 内容转为 HTML 预览。

        Reflex 计算属性：content 变化时自动重新计算，
        无需手动调用 render_preview()。
        """
        if not self.content:
            return (
                '<p style="color: var(--gray-9); text-align: center; '
                'padding: 48px 0; font-size: 14px;">'
                "暂无内容，请编辑或点击「加载模板」开始</p>"
            )
        try:
            import markdown

            return markdown.markdown(
                self.content,
                extensions=["fenced_code", "tables", "toc", "codehilite"],
            )
        except Exception as exc:
            return f'<p style="color: red;">Markdown 渲染失败: {exc}</p>'

    @rx.var
    def has_validation_errors(self) -> bool:
        """是否有格式校验错误"""
        return len(self.validation_errors) > 0

    @rx.var
    def comment_count(self) -> int:
        """审阅评论数量"""
        return len(self.comments)

    # ═══════════════════════════════════════════════════════════════
    #  编辑器操作
    # ═══════════════════════════════════════════════════════════════

    async def load_template(self):
        """加载预置功能需求模板到编辑器"""
        if self.is_sealed:
            self.save_message = "文档已封存，无法加载模板"
            return
        self.content = PRESET_TEMPLATE
        self.imported_filename = ""
        self.validation_errors = []
        self.save_message = "已加载预置模板"

    async def update_content(self, new_content: str):
        """更新编辑器内容（绑定到 textarea on_change）

        封存状态下忽略更新。
        """
        if self.is_sealed:
            return
        self.content = new_content

    async def clear_content(self):
        """清空编辑器内容"""
        if self.is_sealed:
            return
        self.content = ""
        self.validation_errors = []
        self.save_message = ""

    # ═══════════════════════════════════════════════════════════════
    #  Copilot 自动补全辅助
    # ═══════════════════════════════════════════════════════════════

    def toggle_copilot(self):
        """切换 Copilot 建议面板显示"""
        self.show_copilot_panel = not self.show_copilot_panel
        if self.show_copilot_panel:
            self.copilot_suggestions = list(COPILOT_SNIPPETS.keys())

    async def insert_snippet(self, snippet_key: str):
        """插入 Copilot 片段到编辑器末尾"""
        if self.is_sealed:
            return
        snippet = COPILOT_SNIPPETS.get(snippet_key, "")
        if snippet:
            self.content += "\n" + snippet
            self.save_message = f"已插入: {snippet_key}"

    # ═══════════════════════════════════════════════════════════════
    #  外部 .md 文件导入
    # ═══════════════════════════════════════════════════════════════

    async def import_md(self, file_content: str, filename: str = ""):
        """导入外部 .md 文件内容

        Args:
            file_content: 上传文件的文本内容
            filename: 文件名（用于显示）
        """
        if self.is_sealed:
            self.save_message = "文档已封存，无法导入"
            return
        self.content = file_content
        self.imported_filename = filename or "imported.md"
        self.validation_errors = []
        self.save_message = f"已导入: {self.imported_filename}"
        # 导入后自动校验格式
        self.validate_format()

    # ═══════════════════════════════════════════════════════════════
    #  格式校验
    # ═══════════════════════════════════════════════════════════════

    def validate_format(self) -> bool:
        """校验需求文档格式合规性

        检查项：
        1. F-xxx 功能编号格式（## F-XXX: 标题）
        2. 验收标准部分存在
        3. 安全属性部分存在

        Returns:
            True 表示格式完全合规，False 表示存在不合规项
        """
        self.validation_errors = []

        # 检查 F-xxx 编号格式
        if not re.search(REQ_PATTERN, self.content, re.MULTILINE):
            self.validation_errors.append(
                "缺少 F-xxx 功能编号格式（如: ## F-001: 功能名称）"
            )

        # 检查验收标准
        if "验收标准" not in self.content:
            self.validation_errors.append("缺少「验收标准」部分（### 验收标准）")

        # 检查安全属性
        if "安全属性" not in self.content:
            self.validation_errors.append("缺少「安全属性」部分（### 安全属性）")

        return len(self.validation_errors) == 0

    # ═══════════════════════════════════════════════════════════════
    #  保存与提交
    # ═══════════════════════════════════════════════════════════════

    async def save_and_commit(self):
        """保存文档到数据库

        流程：
        1. 校验格式合规性
        2. 写入 req_documents 表
        3. 返回保存结果反馈
        """
        if self.is_sealed:
            self.save_message = "文档已封存，无法保存"
            return

        # 格式校验
        if not self.validate_format():
            self.save_message = "格式校验未通过，请修正后再保存"
            return

        try:
            try:
                from database import db_sync
            except ImportError:
                from oaepp.database import db_sync

            title = self.document_title or "未命名需求文档"

            with db_sync() as cur:
                if self.document_id:
                    # 更新已有文档
                    cur.execute(
                        """UPDATE req_documents
                           SET title = %s, content_md = %s, updated_at = NOW()
                           WHERE id = %s""",
                        (title, self.content, self.document_id),
                    )
                else:
                    # 新建文档
                    cur.execute(
                        """INSERT INTO req_documents
                           (course_id, title, content_md, status, version_no, created_by)
                           VALUES (%s, %s, %s, 'draft', 1, %s)""",
                        (self.course_id or 0, title, self.content, 1),
                    )
                    # 获取自增 ID
                    self.document_id = cur.lastrowid

            self.save_message = "文档已保存"
        except Exception as exc:
            self.save_message = f"保存失败: {exc}"

    # ═══════════════════════════════════════════════════════════════
    #  文档封存
    # ═══════════════════════════════════════════════════════════════

    async def seal_document(self):
        """封存文档 — 设置 is_sealed=True，禁止后续所有修改

        TDD: test_F_T_006_TC03_seal_document
        要求：await seal_document() 后 is_sealed 必须为 True
        """
        self.is_sealed = True
        self.save_message = "文档已封存，所有更改已锁定"

        # 同步更新数据库状态
        if self.document_id:
            try:
                try:
                    from database import db_sync
                except ImportError:
                    from oaepp.database import db_sync

                with db_sync() as cur:
                    cur.execute(
                        """UPDATE req_documents
                           SET status = 'sealed', updated_at = NOW()
                           WHERE id = %s""",
                        (self.document_id,),
                    )
            except Exception:
                pass  # 数据库更新失败不阻止封存操作

    # ═══════════════════════════════════════════════════════════════
    #  审阅评论
    # ═══════════════════════════════════════════════════════════════

    def set_new_comment(self, comment: str):
        """设置正在输入的新评论内容"""
        self.new_comment = comment

    async def add_comment(self):
        """添加审阅评论（学生审阅模式）"""
        if not self.new_comment.strip():
            return
        self.comments.append(
            {
                "content": self.new_comment.strip(),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        self.new_comment = ""
        self.save_message = "评论已添加"

    async def clear_comments(self):
        """清空所有评论"""
        self.comments = []
        self.save_message = "评论已清空"

    # ═══════════════════════════════════════════════════════════════
    #  文档元信息设置
    # ═══════════════════════════════════════════════════════════════

    def set_document_title(self, title: str):
        """设置文档标题"""
        self.document_title = title

    def set_course_id(self, course_id: str):
        """设置关联课程 ID"""
        try:
            self.course_id = int(course_id) if course_id else 0
        except (ValueError, TypeError):
            self.course_id = 0

    # ═══════════════════════════════════════════════════════════════
    #  handle_upload — Reflex 文件上传入口
    # ═══════════════════════════════════════════════════════════════

    async def handle_upload(self, files: list):
        """处理 Reflex 文件上传组件传入的文件列表

        Args:
            files: Reflex upload 组件传入的文件列表，
                   每个元素包含 filename, content 等字段
        """
        if self.is_sealed:
            self.save_message = "文档已封存，无法导入"
            return
        if not files:
            return

        file = files[0]
        filename = getattr(file, "filename", "uploaded.md")
        # Reflex upload file content
        content = ""
        if hasattr(file, "read"):
            try:
                content = file.read().decode("utf-8")
            except Exception:
                self.save_message = "文件编码错误，仅支持 UTF-8 编码的 .md 文件"
                return
        elif hasattr(file, "content"):
            content = file.content

        if content:
            await self.import_md(content, filename)
