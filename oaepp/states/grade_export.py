"""F-S-032 成绩导出（学生端）— GradeExportState

提供学生一键下载本人全期成绩单（.xlsx 格式）：
- 内容包含学号/姓名/各任务得分/总评成绩/提交时间/批改时间
- 仅包含本人数据
- 文件名格式：学号_姓名_成绩单_课程名称.xlsx
"""

import datetime
import io
from typing import Any, Dict, List, Optional

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except Exception:
    openpyxl = None


class GradeExportState:
    """学生成绩导出状态管理

    对应验收标准：
    - 导出文件符合标准 Excel 模板格式
    - 仅包含本人成绩数据，不含他人数据
    - 文件名格式：学号_姓名_成绩单_课程名称.xlsx
    - 导出内容完整（学号/姓名/各任务得分/总评/时间）
    """

    # ── 状态变量 ──
    is_exporting: bool = False
    export_error: str = ""
    current_user_id: int = 0
    export_filename: str = ""

    def __init__(self):
        self.is_exporting = False
        self.export_error = ""
        self.current_user_id = 0
        self.export_filename = ""

    # ── 公共方法 ──

    def export_my_grades(self, student_no: str) -> Optional[bytes]:
        """查询数据库并生成 .xlsx 成绩单文件。

        Args:
            student_no: 学生学号

        Returns:
            .xlsx 文件 bytes；失败时返回 None 并设置 export_error
        """
        self.is_exporting = True
        self.export_error = ""

        try:
            # 1. 查询数据
            data = self._query_student_grades(student_no)
            if data is None:
                self.is_exporting = False
                return None

            # 2. 生成 Excel
            file_bytes = self._build_workbook(data, student_no)
            self.is_exporting = False
            return file_bytes

        except Exception as e:
            self.export_error = f"导出失败: {e}"
            self.is_exporting = False
            return None

    def get_export_filename(self, student_no: str) -> str:
        """根据学号生成导出文件名。

        格式：学号_姓名_成绩单_课程名称.xlsx
        若有多门课程，使用第一门课程名称。
        """
        try:
            conn = self._get_mysql_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT u.student_no, u.full_name, c.name AS course_name
                       FROM users u
                       JOIN enrollments e ON e.student_user_id = u.id
                       JOIN courses c ON c.id = e.course_id
                       WHERE u.student_no = %s AND u.role = 'student'
                       LIMIT 1""",
                    (student_no,),
                )
                row = cur.fetchone()
            conn.close()

            if row:
                sno = row["student_no"] or student_no
                name = row["full_name"] or ""
                course = row["course_name"] or ""
                self.export_filename = f"{sno}_{name}_成绩单_{course}.xlsx"
            else:
                self.export_filename = f"{student_no}_成绩单.xlsx"

        except Exception:
            self.export_filename = f"{student_no}_成绩单.xlsx"

        return self.export_filename

    # ── 内部方法 ──

    def _query_student_grades(self, student_no: str) -> Optional[Dict[str, Any]]:
        """查询学生全部成绩数据。

        Returns:
            dict with keys: student_info, courses (list of course dicts)
        """
        conn = self._get_mysql_connection()
        try:
            with conn.cursor() as cur:
                # 查学生基本信息
                cur.execute(
                    """SELECT id, student_no, full_name, email
                       FROM users
                       WHERE student_no = %s AND role = 'student'""",
                    (student_no,),
                )
                user = cur.fetchone()
                if not user:
                    self.export_error = f"学生 {student_no} 不存在"
                    return None

                self.current_user_id = user["id"]
                student_info = {
                    "user_id": user["id"],
                    "student_no": user["student_no"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                }

                # 查所有选课
                cur.execute(
                    """SELECT c.id, c.code, c.name, c.term
                       FROM courses c
                       JOIN enrollments e ON e.course_id = c.id
                       WHERE e.student_user_id = %s
                       ORDER BY c.term, c.code""",
                    (self.current_user_id,),
                )
                course_rows = cur.fetchall()

                courses = []
                for c_row in course_rows:
                    course_data = {
                        "course_id": c_row["id"],
                        "course_code": c_row["code"],
                        "course_name": c_row["name"],
                        "course_term": c_row["term"],
                        "tasks": [],
                        "score_items": [],
                        "total_score": None,
                    }

                    # 查作业提交与批改记录
                    cur.execute(
                        """SELECT
                            a.id AS assignment_id,
                            a.title AS assignment_title,
                            a.deadline,
                            s.id AS submission_id,
                            s.version_no,
                            s.submitted_at,
                            s.is_late,
                            s.grading_status,
                            gr.id AS grading_id,
                            gr.attendance_score,
                            gr.exam_score,
                            gr.code_score,
                            gr.pr_score,
                            gr.total_score AS grading_total,
                            gr.comment_md,
                            gr.graded_at
                           FROM assignments a
                           LEFT JOIN submissions s
                             ON s.assignment_id = a.id
                             AND s.student_user_id = %s
                           LEFT JOIN grading_records gr
                             ON gr.submission_id = s.id
                           WHERE a.course_id = %s
                           ORDER BY a.deadline ASC""",
                        (self.current_user_id, c_row["id"]),
                    )
                    task_rows = cur.fetchall()

                    for t_row in task_rows:
                        task = {
                            "assignment_id": t_row["assignment_id"],
                            "assignment_title": t_row["assignment_title"],
                            "deadline": t_row["deadline"],
                            "submission_id": t_row["submission_id"],
                            "version_no": t_row["version_no"],
                            "submitted_at": t_row["submitted_at"],
                            "is_late": bool(t_row["is_late"]) if t_row["is_late"] is not None else False,
                            "grading_status": t_row["grading_status"],
                            "grading_id": t_row["grading_id"],
                            "attendance_score": t_row["attendance_score"],
                            "exam_score": t_row["exam_score"],
                            "code_score": t_row["code_score"],
                            "pr_score": t_row["pr_score"],
                            "grading_total": t_row["grading_total"],
                            "comment_md": t_row["comment_md"],
                            "graded_at": t_row["graded_at"],
                        }
                        course_data["tasks"].append(task)

                    # 查 score_items（考勤/考试/代码/PR 各项得分）
                    cur.execute(
                        """SELECT
                            si.score_type,
                            si.score,
                            si.scored_at
                           FROM score_items si
                           WHERE si.course_id = %s
                             AND si.student_user_id = %s
                           ORDER BY si.scored_at ASC""",
                        (c_row["id"], self.current_user_id),
                    )
                    si_rows = cur.fetchall()
                    for si_row in si_rows:
                        course_data["score_items"].append({
                            "score_type": si_row["score_type"],
                            "score": float(si_row["score"]),
                            "scored_at": si_row["scored_at"],
                        })

                    # 查成绩权重配置
                    cur.execute(
                        """SELECT attendance_weight, exam_weight, code_weight, pr_weight
                           FROM grade_weight_configs
                           WHERE course_id = %s
                           LIMIT 1""",
                        (c_row["id"],),
                    )
                    gw = cur.fetchone()
                    if gw:
                        course_data["weights"] = {
                            "attendance": float(gw["attendance_weight"]),
                            "exam": float(gw["exam_weight"]),
                            "code": float(gw["code_weight"]),
                            "pr": float(gw["pr_weight"]),
                        }
                    else:
                        course_data["weights"] = None

                    # 计算总评成绩
                    course_data["total_score"] = self._compute_total_score(course_data)

                    courses.append(course_data)

            return {
                "student_info": student_info,
                "courses": courses,
            }

        except Exception as e:
            self.export_error = f"查询数据失败: {e}"
            return None
        finally:
            conn.close()

    def _compute_total_score(self, course_data: dict) -> Optional[float]:
        """根据权重配置和 score_items 计算总评成绩。"""
        scores_by_type = {"attendance": 0.0, "exam": 0.0, "code": 0.0, "pr": 0.0}
        counts_by_type = {"attendance": 0, "exam": 0, "code": 0, "pr": 0}

        for si in course_data.get("score_items", []):
            st = si["score_type"]
            if st in scores_by_type:
                scores_by_type[st] += si["score"]
                counts_by_type[st] += 1

        weights = course_data.get("weights")
        if not weights:
            # 无权重配置时简单求和
            total = sum(si["score"] for si in course_data.get("score_items", []))
            return total if course_data.get("score_items") else None

        # 按权重计算
        weighted_total = 0.0
        for dim in ("attendance", "exam", "code", "pr"):
            avg = scores_by_type[dim] / counts_by_type[dim] if counts_by_type[dim] > 0 else 0.0
            weight_pct = weights.get(dim, 0.0) / 100.0
            weighted_total += avg * weight_pct

        return round(weighted_total, 2)

    def _build_workbook(self, data: dict, student_no: str) -> bytes:
        """生成 Excel 工作簿并返回 bytes。"""
        if openpyxl is None:
            raise ImportError("openpyxl 未安装，无法生成 Excel 文件")

        wb = openpyxl.Workbook()
        # 删除默认 sheet
        wb.remove(wb.active)

        student_info = data["student_info"]
        courses = data["courses"]

        # ── 定义样式 ──
        header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell_alignment_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        title_font = Font(name="微软雅黑", size=14, bold=True)

        for course in courses:
            course_name = course["course_name"]
            # sheet 名称限制 31 字符
            sheet_name = course_name[:31]
            ws = wb.create_sheet(title=sheet_name)

            # ── 标题行 ──
            ws.merge_cells("A1:H1")
            title_cell = ws["A1"]
            title_cell.value = f"{course_name} — 成绩单"
            title_cell.font = title_font
            title_cell.alignment = Alignment(horizontal="center", vertical="center")

            # ── 学生信息 ──
            ws.merge_cells("A2:H2")
            ws["A2"].value = (
                f"学号：{student_info['student_no']}    姓名：{student_info['full_name']}"
                f"    学期：{course['course_term']}    课程编号：{course['course_code']}"
            )
            ws["A2"].alignment = Alignment(horizontal="left", vertical="center")
            ws["A2"].font = Font(name="微软雅黑", size=10)

            # ── 表头 (row 4) ──
            headers = ["序号", "任务名称", "任务类型", "得分", "提交时间", "批改时间", "迟交", "评语"]
            col_widths = [6, 30, 12, 10, 20, 20, 8, 30]

            header_row = 4
            for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
                cell = ws.cell(row=header_row, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border
                ws.column_dimensions[get_column_letter(col_idx)].width = width

            # ── 数据行 ──
            row = header_row + 1
            seq = 1

            # 写入各任务（作业提交 + 批改）
            for task in course["tasks"]:
                # 确定任务类型标签
                task_type = "作业"

                # 得分：优先取 grading_records.total_score
                score_value = task.get("grading_total")
                if score_value is not None:
                    score_value = float(score_value)

                # 提交时间
                submitted_at = task.get("submitted_at")
                if submitted_at and not isinstance(submitted_at, str):
                    submitted_at = submitted_at.strftime("%Y-%m-%d %H:%M") if submitted_at else ""
                elif submitted_at is None:
                    submitted_at = "未提交"

                # 批改时间
                graded_at = task.get("graded_at")
                if graded_at and not isinstance(graded_at, str):
                    graded_at = graded_at.strftime("%Y-%m-%d %H:%M") if graded_at else ""
                elif graded_at is None:
                    graded_at = "未批改"

                # 迟交标记
                is_late = "是" if task.get("is_late") else "否"

                # 评语
                comment = task.get("comment_md") or ""

                values = [seq, task["assignment_title"], task_type, score_value,
                          submitted_at, graded_at, is_late, comment]
                for col_idx, val in enumerate(values, start=1):
                    cell = ws.cell(row=row, column=col_idx, value=val)
                    cell.border = thin_border
                    cell.alignment = cell_alignment if col_idx != 8 else cell_alignment_left
                    cell.font = Font(name="微软雅黑", size=10)

                row += 1
                seq += 1

            # 写入 score_items 行
            for si in course["score_items"]:
                type_label_map = {
                    "attendance": "考勤",
                    "exam": "考试",
                    "code": "代码",
                    "pr": "PR",
                }
                task_type = type_label_map.get(si["score_type"], si["score_type"])
                scored_at = si.get("scored_at")
                if scored_at and not isinstance(scored_at, str):
                    scored_at = scored_at.strftime("%Y-%m-%d %H:%M")

                values = [seq, f"{task_type}成绩", task_type, si["score"],
                          "", scored_at or "", "", ""]
                for col_idx, val in enumerate(values, start=1):
                    cell = ws.cell(row=row, column=col_idx, value=val)
                    cell.border = thin_border
                    cell.alignment = cell_alignment
                    cell.font = Font(name="微软雅黑", size=10)

                row += 1
                seq += 1

            # ── 空行 ──
            row += 1

            # ── 总评成绩 ──
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
            total_label_cell = ws.cell(row=row, column=1, value="总评成绩（按权重计算）")
            total_label_cell.font = Font(name="微软雅黑", size=11, bold=True)
            total_label_cell.alignment = Alignment(horizontal="right", vertical="center")
            total_label_cell.border = thin_border
            for c in range(2, 4):
                ws.cell(row=row, column=c).border = thin_border

            total_score = course.get("total_score")
            total_cell = ws.cell(row=row, column=4, value=total_score if total_score is not None else "N/A")
            total_cell.font = Font(name="微软雅黑", size=12, bold=True, color="C00000")
            total_cell.alignment = cell_alignment
            total_cell.border = thin_border
            for c in range(5, 9):
                ws.cell(row=row, column=c).border = thin_border

            # ── 权重说明 ──
            row += 1
            weights = course.get("weights")
            if weights:
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
                weight_text = (
                    f"权重配置：出勤 {weights['attendance']}%  |  "
                    f"考试 {weights['exam']}%  |  "
                    f"代码 {weights['code']}%  |  "
                    f"PR {weights['pr']}%"
                )
                ws.cell(row=row, column=1, value=weight_text).font = Font(name="微软雅黑", size=9, color="666666")

            # ── 导出时间 ──
            row += 1
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
            export_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.cell(row=row, column=1, value=f"导出时间：{export_time}").font = Font(
                name="微软雅黑", size=9, color="999999"
            )

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def _get_mysql_connection():
        """获取 MySQL 连接（生产环境）。"""
        import os
        from urllib.parse import urlparse, unquote

        try:
            import pymysql
        except ImportError:
            raise ImportError("pymysql 未安装")

        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            parsed = urlparse(db_url)
            return pymysql.connect(
                host=parsed.hostname or "127.0.0.1",
                port=parsed.port or 3306,
                user=parsed.username or "root",
                password=unquote(parsed.password) if parsed.password else "",
                database=parsed.path.lstrip("/") or "oaepp_dev",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        else:
            return pymysql.connect(
                host=os.environ.get("DB_HOST", "156.239.252.40"),
                port=int(os.environ.get("DB_PORT", "13306")),
                user=os.environ.get("DB_USER", "student_dev"),
                password=os.environ.get("DB_PASSWORD", "OaEpp@Dev2026"),
                database=os.environ.get("DB_NAME", "oaepp_dev"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
