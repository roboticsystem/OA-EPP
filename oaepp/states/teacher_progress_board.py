"""F-T-013 进度看板 — Reflex State

ProgressBoardState 负责教师端进度看板的数据管理与状态更新。
数据来源：MySQL 数据库 (oaepp_dev)，通过 oaepp.database 模块连接。
"""
from datetime import datetime
from oaepp.database import db as _get_db


class ProgressBoardState:
    """教师端进度看板 State。

    Reflex 事件处理器实现 F-T-013 进度看板功能：
    - 热力图展示「学生 × 任务」二维完成状态矩阵
    - 柱状图展示各任务完成率趋势
    - 支持按课程、学期筛选
    - 完成率最低前N名学生置顶高亮
    """

    # ── 状态变量（Reflex var） ──
    heatmap_data: dict = {}
    completion_rate_chart: dict = {}

    # ── 热力图状态定义 ──
    HEATMAP_STATUS = {
        "submitted": "已提交",
        "late": "迟交",
        "missing": "未提交",
        "not_published": "未发布",
    }

    # ── 筛选条件 ──
    current_course: str = ""
    current_semester: str = ""
    bottom_n: int = 5

    @classmethod
    def load_progress(cls, course_id=None, semester=None, bottom_n=5):
        """从数据库加载进度数据，更新热力图和柱状图状态。"""
        cls.bottom_n = bottom_n
        cls.current_course = course_id or ""
        cls.current_semester = semester or ""

        with _get_db() as conn:
            # 查询学生列表
            student_query = """
                SELECT s.user_id AS student_id, u.full_name AS name, 
                       u.student_no, COALESCE(s.class_name, '') AS class_name
                FROM students s
                JOIN users u ON s.user_id = u.id
                WHERE u.role = 'student'
            """
            students = conn.execute(student_query).fetchall()

            # 查询作业列表
            assignment_query = """
                SELECT a.id, a.title, a.deadline, a.created_at, a.course_id
                FROM assignments a
                JOIN courses c ON a.course_id = c.id
            """
            params = []
            if course_id:
                assignment_query += " WHERE a.course_id = %s"
                params.append(course_id)
            if semester:
                assignment_query += " AND c.term = %s" if course_id else " WHERE c.term = %s"
                params.append(semester)
            assignment_query += " ORDER BY a.deadline"

            assignments = conn.execute(assignment_query, params).fetchall()

            if not assignments or not students:
                cls.heatmap_data = {
                    "students": [],
                    "exams": [],
                    "matrix": []
                }
                cls.completion_rate_chart = {"tasks": []}
                return

            # 查询提交状态
            assignment_ids = [a["id"] for a in assignments]
            student_ids = [s["student_id"] for s in students]

            placeholders_a = ",".join(["%s"] * len(assignment_ids))
            placeholders_s = ",".join(["%s"] * len(student_ids))

            submissions = conn.execute(f"""
                SELECT sub.assignment_id, sub.student_user_id, sub.is_late, 
                       sub.submitted_at, sub.version_no, sub.grading_status
                FROM submissions sub
                WHERE sub.assignment_id IN ({placeholders_a})
                AND sub.student_user_id IN ({placeholders_s})
                AND sub.version_no = (
                    SELECT MAX(s2.version_no) 
                    FROM submissions s2 
                    WHERE s2.assignment_id = sub.assignment_id 
                    AND s2.student_user_id = sub.student_user_id
                )
            """, assignment_ids + student_ids).fetchall()

            # 构建提交映射
            submission_map = {
                (str(s["assignment_id"]), str(s["student_user_id"])): dict(s)
                for s in submissions
            }

            # 构建矩阵数据
            now = datetime.now()
            matrix = []

            for student in students:
                row_cells = []
                completed = 0
                past_deadline = 0

                for assignment in assignments:
                    key = (str(assignment["id"]), str(student["student_id"]))
                    sub = submission_map.get(key)

                    if sub:
                        status = "late" if sub["is_late"] else "submitted"
                        completed += 1
                        past_deadline += 1
                    elif assignment["deadline"] < now:
                        status = "missing"
                        past_deadline += 1
                    else:
                        status = "not_published"

                    row_cells.append({
                        "assignment_id": assignment["id"],
                        "student_id": student["student_id"],
                        "status": status,
                        "submitted_at": sub["submitted_at"].isoformat() if sub and sub["submitted_at"] else None,
                        "version_no": sub["version_no"] if sub else None,
                        "grading_status": sub["grading_status"] if sub else None
                    })

                completion_rate = completed / past_deadline if past_deadline > 0 else 1.0

                matrix.append({
                    "student_id": student["student_id"],
                    "name": student["name"],
                    "student_no": student["student_no"],
                    "class_name": student["class_name"],
                    "completion_rate": round(completion_rate, 3),
                    "cells": row_cells
                })

            # 转换为前端期望的格式（exams 字段）
            exams = []
            for assn in assignments:
                deadline = assn.get("deadline", "")
                is_active = False
                if deadline:
                    if isinstance(deadline, datetime):
                        is_active = now >= deadline
                    else:
                        try:
                            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
                            is_active = now >= deadline_dt
                        except:
                            pass
                deadline_str = deadline.strftime("%Y-%m-%d %H:%M:%S") if isinstance(deadline, datetime) else str(deadline)

                exams.append({
                    "id": f"hw{assn['id']}",
                    "title": assn["title"],
                    "deadline": deadline_str,
                    "published_at": assn.get("created_at", ""),
                    "semester": semester or "2024-2025-2",
                    "is_active": is_active,
                    "total_students": len(students),
                    "submitted": 0,
                    "completion_rate": 0.0
                })

            # 构建学生数据（包含statuses）
            students_result = []
            for row in matrix:
                statuses = {}
                for idx, cell in enumerate(row["cells"]):
                    exam_id = f"hw{assignments[idx]['id']}"
                    status_info = {"status": cell["status"]}
                    if cell.get("submitted_at"):
                        status_info["submitted_at"] = cell["submitted_at"]
                    statuses[exam_id] = status_info

                students_result.append({
                    "student_id": row["student_id"],
                    "name": row["name"],
                    "student_no": row["student_no"],
                    "class_name": row["class_name"],
                    "completion_rate": row["completion_rate"],
                    "highlight": False,
                    "statuses": statuses
                })

            # 排序并高亮
            students_result.sort(key=lambda x: x["completion_rate"])
            for i, s in enumerate(students_result):
                s["highlight"] = i < bottom_n and s["completion_rate"] < 1.0

            # 更新exams完成率
            for exam in exams:
                submitted = sum(1 for s in students_result 
                              if s["statuses"].get(exam["id"], {}).get("status") in ["submitted", "late"])
                exam["submitted"] = submitted
                exam["completion_rate"] = round(submitted / len(students_result), 3) if students_result else 0.0

            cls.heatmap_data = {
                "students": students_result,
                "exams": exams,
                "matrix": matrix
            }

            # 构建柱状图数据
            chart_tasks = []
            for exam in exams:
                if exam["is_active"]:
                    chart_tasks.append({
                        "id": exam["id"],
                        "title": exam["title"],
                        "deadline": exam["deadline"],
                        "published_at": exam["published_at"],
                        "completion_rate": exam["completion_rate"],
                        "submitted": exam["submitted"],
                        "total_students": exam["total_students"]
                    })

            cls.completion_rate_chart = {"tasks": chart_tasks}

    @classmethod
    def filter_by_course(cls, course_id):
        """按课程筛选进度数据。"""
        cls.load_progress(course_id=course_id, semester=cls.current_semester, bottom_n=cls.bottom_n)

    @classmethod
    def filter_by_semester(cls, semester):
        """按学期筛选进度数据。"""
        cls.load_progress(course_id=cls.current_course, semester=semester, bottom_n=cls.bottom_n)

    @classmethod
    def update_bottom_n(cls, bottom_n):
        """更新置顶倒数前N名的配置。"""
        cls.bottom_n = bottom_n
        cls.load_progress(course_id=cls.current_course, semester=cls.current_semester, bottom_n=bottom_n)
