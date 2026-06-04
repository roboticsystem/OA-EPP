"""
教师端 — 学生开发日志导出页面 (F-T-010)。
"""
try:
    import reflex as rx
except Exception:
    rx = None


class ExportState(rx.State if rx else object):
    """导出页面状态。"""
    search_query: str = ""
    search_results: list = []
    selected_student_no: str = ""
    selected_student_name: str = ""
    export_format: str = "excel"
    class_name: str = ""
    class_list: list = []
    audit_logs: list = []
    status_msg: str = ""
    is_loading: bool = False

    async def search_students(self):
        if not self.search_query.strip():
            self.search_results = []
            return
        try:
            from export_api import search_students
            self.search_results = search_students(self.search_query.strip())
        except Exception as e:
            self.status_msg = f"搜索失败: {e}"

    async def select_student(self, d: dict):
        self.selected_student_no = str(d.get("student_no", ""))
        self.selected_student_name = str(d.get("full_name", ""))
        self.status_msg = f"已选择: {self.selected_student_name} ({self.selected_student_no})"

    async def set_export_format(self, fmt: str):
        self.export_format = fmt

    async def set_class_name(self, name: str):
        self.class_name = name

    async def load_classes(self):
        try:
            from export_api import get_all_classes
            self.class_list = get_all_classes()
        except Exception as e:
            self.status_msg = f"加载班级失败: {e}"

    async def load_audit_logs(self):
        try:
            from export_api import get_audit_logs
            logs = get_audit_logs(50)
            self.audit_logs = []
            for log in logs:
                detail = log.get("detail_json", "{}")
                import json as _json
                try:
                    d = _json.loads(detail) if isinstance(detail, str) else detail
                except Exception:
                    d = {}
                self.audit_logs.append({
                    "action_at": str(log.get("action_at", "")),
                    "exporter_no": str(log.get("exporter_no", "")),
                    "target_id": str(log.get("target_id", "")),
                    "export_format": d.get("format", ""),
                    "class_name": d.get("class_name", ""),
                })
        except Exception as e:
            self.status_msg = f"加载日志失败: {e}"

    async def export_single(self):
        if not self.selected_student_no:
            self.status_msg = "请先选择学生"
            return
        self.is_loading = True
        try:
            from export_api import export_report
            content = export_report(self.selected_student_no, self.export_format, exporter_no="teacher")
            self.status_msg = f"导出成功: {self.selected_student_name} ({len(content)} bytes)"
        except Exception as e:
            self.status_msg = f"导出失败: {e}"
        self.is_loading = False

    async def export_batch(self):
        if not self.class_name:
            self.status_msg = "请先选择班级"
            return
        self.is_loading = True
        try:
            from export_api import export_batch_by_class
            content = export_batch_by_class(self.class_name, self.export_format, exporter_no="teacher")
            self.status_msg = f"批量导出成功: {self.class_name} ({len(content)} bytes)"
        except Exception as e:
            self.status_msg = f"批量导出失败: {e}"
        self.is_loading = False


def _student_row(r: dict):
    """Render a single search result row."""
    label = f"{r.get('full_name','')} ({r.get('student_no','')}) - {r.get('class_name','')}"
    return rx.hstack(
        rx.text(label),
        rx.button("选择", on_click=ExportState.select_student(r), size="1"),
        spacing="2",
        padding="4px 0",
    )


def _audit_row(log: dict):
    """Render a single audit log row."""
    text = f"{log.get('action_at','')} | {log.get('exporter_no','')} | student#{log.get('target_id','')} | {log.get('export_format','')}"
    return rx.text(text, padding="2px 0", font_size="12px")


def teacher_export_page():
    """教师端 — 学生开发日志导出页面。"""
    return rx.center(
        rx.box(
            rx.vstack(
                rx.heading("学生开发日志导出", size="6"),
                rx.text("F-T-010 · 9维度报告生成（分支/提交/代码质量/PR/PR分析/教师评语/在线考试/考勤/课程得分）", color="gray", font_size="12px"),

                # ── 搜索学生 ──
                rx.hstack(
                    rx.input(
                        placeholder="搜索学号/姓名...",
                        value=ExportState.search_query,
                        on_change=ExportState.set_search_query,
                        width="300px",
                    ),
                    rx.button("搜索", on_click=ExportState.search_students),
                    spacing="3",
                ),

                # ── 搜索结果 ──
                rx.cond(
                    ExportState.search_results.length() > 0,
                    rx.box(
                        rx.foreach(ExportState.search_results, _student_row),
                        border="1px solid #e5e7eb",
                        border_radius="8px",
                        padding="8px",
                        max_height="200px",
                        overflow_y="auto",
                        width="100%",
                    ),
                ),

                # ── 已选学生 ──
                rx.cond(
                    ExportState.selected_student_no != "",
                    rx.box(
                        rx.text(f"已选学生: {ExportState.selected_student_name} ({ExportState.selected_student_no})"),
                        padding="8px 12px",
                        background="#f0f4ff",
                        border_radius="6px",
                        width="100%",
                    ),
                ),

                # ── 导出格式 ──
                rx.vstack(
                    rx.text("导出格式", weight="medium"),
                    rx.select(
                        ["excel", "html", "pdf"],
                        value=ExportState.export_format,
                        on_change=ExportState.set_export_format,
                    ),
                    spacing="2",
                    align="start",
                ),

                # ── 操作按钮 ──
                rx.hstack(
                    rx.button("导出单个报告", on_click=ExportState.export_single, color_scheme="blue"),
                    rx.button("加载审计日志", on_click=ExportState.load_audit_logs, variant="soft"),
                    spacing="3",
                ),

                # ── 批量导出 ──
                rx.divider(),
                rx.text("批量导出（按班级）", weight="medium"),
                rx.button("加载班级列表", on_click=ExportState.load_classes, variant="soft"),
                rx.cond(
                    ExportState.class_list.length() > 0,
                    rx.select(
                        ExportState.class_list,
                        placeholder="选择班级",
                        on_change=ExportState.set_class_name,
                    ),
                ),
                rx.button(
                    "批量导出班级",
                    on_click=ExportState.export_batch,
                    color_scheme="green",
                ),

                # ── 状态消息 ──
                rx.cond(
                    ExportState.status_msg != "",
                    rx.box(
                        rx.text(ExportState.status_msg),
                        padding="8px 12px",
                        background="#f9fafb",
                        border_radius="6px",
                        width="100%",
                    ),
                ),

                # ── 加载指示 ──
                rx.cond(
                    ExportState.is_loading,
                    rx.text("正在生成报告...", color="blue"),
                ),

                # ── 审计日志 ──
                rx.divider(),
                rx.text("操作审计日志", weight="medium"),
                rx.cond(
                    ExportState.audit_logs.length() > 0,
                    rx.box(
                        rx.foreach(ExportState.audit_logs, _audit_row),
                        border="1px solid #e5e7eb",
                        border_radius="8px",
                        padding="8px",
                        max_height="200px",
                        overflow_y="auto",
                        width="100%",
                    ),
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            max_width="800px",
            width="100%",
            padding="28px",
            border_radius="12px",
            box_shadow="0 10px 30px rgba(0,0,0,0.08)",
            background="white",
            margin="40px auto",
        ),
        min_height="100vh",
        width="100%",
        background="linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
        padding="20px",
    )


__all__ = ["teacher_export_page", "ExportState"]
