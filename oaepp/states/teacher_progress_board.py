"""F-T-013 教师进度看板状态管理"""

try:
    import reflex as rx
except Exception:
    rx = None

from typing import Optional, List, Dict, Any
from oaepp.database import db


class ProgressBoardState(rx.State if rx is not None else object):
    """学生任务完成状态看板状态管理（教师视图）"""

    # ── 配置状态 ──
    highlight_count: int = 5
    selected_course: Optional[int] = None
    sort_order: str = "asc"  # asc=完成率升序（落后置顶）, desc=完成率降序
    sort_label: str = "按完成率升序（落后置顶）"

    # ── 数据状态 ──
    heatmap_data: List[Dict[str, Any]] = []  # 热力图数据
    completion_rate_chart: List[Dict[str, Any]] = []  # 完成率图表数据
    students: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    submission_matrix: Dict[str, Dict[str, str]] = {}
    completion_rates: List[Dict[str, Any]] = []

    # ── 热力图状态常量 ──
    HEATMAP_STATUS = {
        "submitted": "已提交（准时）",
        "late": "迟交",
        "missing": "未提交",
        "not_published": "任务未发布"
    }

    # ── 计算属性 ──
    @rx.var
    def heatmap_status_options(self) -> List[str]:
        """获取热力图状态选项"""
        return ["submitted", "late", "missing", "not_published"]

    @rx.var
    def total_students(self) -> int:
        """学生总数"""
        return len(self.students)

    @rx.var
    def total_assignments(self) -> int:
        """作业总数"""
        return len(self.assignments)

    async def load_progress(self):
        """加载进度数据（学生、作业、提交矩阵）"""
        try:
            async with db() as cur:
                # 加载所有学生
                await cur.execute("""
                    SELECT u.id, u.full_name, u.student_no, s.class_name
                    FROM users u
                    JOIN students s ON u.id = s.user_id
                    ORDER BY u.full_name
                """)
                self.students = await cur.fetchall()

                # 加载所有作业
                await cur.execute("""
                    SELECT id, title, deadline, created_at
                    FROM assignments
                    ORDER BY id ASC
                """)
                self.assignments = await cur.fetchall()

                # 构建提交矩阵
                await self._load_submission_matrix()
        except Exception as e:
            print(f"Error loading progress: {e}")
            self.students = []
            self.assignments = []
            self.submission_matrix = {}

    async def _load_submission_matrix(self):
        """加载学生提交状态矩阵"""
        if not self.students or not self.assignments:
            self.submission_matrix = {}
            return

        try:
            async with db() as cur:
                assignment_ids = [a["id"] for a in self.assignments]
                if not assignment_ids:
                    self.submission_matrix = {}
                    return

                placeholders = ",".join(["%s"] * len(assignment_ids))
                await cur.execute(f"""
                    SELECT student_user_id, assignment_id, submitted_at, version_no
                    FROM submissions
                    WHERE assignment_id IN ({placeholders})
                """, tuple(assignment_ids))

                submissions = await cur.fetchall()

                # 构建作业ID到截止时间的映射
                assignment_deadlines = {str(a["id"]): a["deadline"] for a in self.assignments}

                # 构建提交矩阵，默认所有任务为未提交
                self.submission_matrix = {}
                for student in self.students:
                    student_id = str(student["id"])
                    self.submission_matrix[student_id] = {}
                    for assignment in self.assignments:
                        assignment_id = str(assignment["id"])
                        self.submission_matrix[student_id][assignment_id] = "missing"

                # 填充提交状态
                for sub in submissions:
                    student_id = str(sub["student_user_id"])
                    assignment_id = str(sub["assignment_id"])
                    if student_id in self.submission_matrix and assignment_id in self.submission_matrix[student_id]:
                        submitted_at = sub["submitted_at"]
                        deadline = assignment_deadlines.get(assignment_id)

                        if submitted_at and deadline:
                            if submitted_at > deadline:
                                self.submission_matrix[student_id][assignment_id] = "late"
                            else:
                                self.submission_matrix[student_id][assignment_id] = "submitted"
                        else:
                            self.submission_matrix[student_id][assignment_id] = "submitted"

                # 计算完成率
                self._calculate_completion_rates()

                # 生成热力图数据
                self._generate_heatmap_data()

                # 生成完成率图表数据
                self._generate_completion_rate_chart()
        except Exception as e:
            print(f"Error loading submission matrix: {e}")
            self.submission_matrix = {}

    def _calculate_completion_rates(self):
        """计算每个学生的完成率"""
        self.completion_rates = []
        total_assignments = len(self.assignments)

        for student in self.students:
            student_id = str(student["id"])
            submitted_count = 0

            if student_id in self.submission_matrix:
                for assignment_id in self.submission_matrix[student_id]:
                    status = self.submission_matrix[student_id][assignment_id]
                    if status in ("submitted", "late"):
                        submitted_count += 1

            rate = 0
            if total_assignments > 0:
                rate = int((submitted_count / total_assignments) * 100)

            self.completion_rates.append({
                "student_id": student["id"],
                "full_name": student["full_name"],
                "completion_rate": rate,
                "submitted_count": submitted_count,
                "total_assignments": total_assignments
            })

        # 按完成率排序
        if self.sort_order == "asc":
            self.completion_rates.sort(key=lambda x: x["completion_rate"])
        else:
            self.completion_rates.sort(key=lambda x: x["completion_rate"], reverse=True)

    def _generate_heatmap_data(self):
        """生成热力图数据"""
        self.heatmap_data = []
        for student in self.completion_rates:
            student_row = {
                "student_id": student["student_id"],
                "full_name": student["full_name"],
                "completion_rate": student["completion_rate"],
                "assignments": []
            }
            for assignment in self.assignments:
                status = self.get_submission_status(student["student_id"], assignment["id"])
                student_row["assignments"].append({
                    "assignment_id": assignment["id"],
                    "title": assignment["title"],
                    "status": status
                })
            self.heatmap_data.append(student_row)

    def _generate_completion_rate_chart(self):
        """生成完成率图表数据"""
        self.completion_rate_chart = []
        total_students = len(self.students)

        for assignment in self.assignments:
            assignment_id = str(assignment["id"])
            submitted_count = 0

            for student in self.students:
                student_id = str(student["id"])
                if student_id in self.submission_matrix and assignment_id in self.submission_matrix[student_id]:
                    status = self.submission_matrix[student_id][assignment_id]
                    if status in ("submitted", "late"):
                        submitted_count += 1

            rate = 0
            if total_students > 0:
                rate = int((submitted_count / total_students) * 100)

            # 根据完成率确定颜色
            if rate >= 80:
                bar_color = "#22c55e"  # 绿色
            elif rate >= 60:
                bar_color = "#eab308"  # 黄色
            else:
                bar_color = "#ef4444"  # 红色

            self.completion_rate_chart.append({
                "assignment_id": assignment["id"],
                "title": assignment["title"],
                "deadline": assignment["deadline"],
                "submitted_count": submitted_count,
                "total_students": total_students,
                "completion_rate": rate,
                "bar_color": bar_color
            })

    def get_submission_status(self, student_id, assignment_id):
        """获取学生对作业的提交状态"""
        student_id_str = str(student_id)
        assignment_id_str = str(assignment_id)

        if student_id_str in self.submission_matrix:
            if assignment_id_str in self.submission_matrix[student_id_str]:
                return self.submission_matrix[student_id_str][assignment_id_str]
        return "missing"

    async def filter_by_course(self, course_id: Optional[int] = None):
        """按课程筛选数据"""
        self.selected_course = course_id
        await self.load_progress()
