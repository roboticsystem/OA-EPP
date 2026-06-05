"""F-S-040 学生任务完成状态看板状态管理"""

try:
    import reflex as rx
except Exception:
    rx = None

from typing import List, Dict, Optional

# 使用项目提供的数据库连接
from database import db


class DashboardState(rx.State if rx is not None else object):
    """学生任务完成状态看板状态管理"""
    
    # ── 配置状态 ──
    highlight_count: int = 5
    selected_course: Optional[int] = 1  # 默认选中第一个课程
    selected_term: str = "2026-春"
    sort_order: str = "asc"  # asc=完成率升序（落后置顶）, desc=完成率降序
    sort_label: str = "按完成率升序（落后置顶）"
    
    # ── 数据状态 ──
    courses: List[dict] = []
    course_options: List[str] = []  # 课程选项列表（用于select组件）
    terms: List[str] = ["2026-春", "2026-秋", "2025-春", "2025-秋"]
    students: List[dict] = []  # 学生列表
    assignments: List[dict] = []  # 作业列表
    submission_matrix: Dict[str, Dict[str, str]] = {}  # {student_id: {assignment_id: status}}
    completion_rates: List[dict] = []  # 学生完成率
    assignment_completion_rates: List[dict] = []  # 作业完成率（用于柱状图）
    highlighted_student_ids: List[int] = []  # 高亮学生ID
    heatmap_html: str = ""  # 热力图HTML
    barchart_html: str = ""  # 柱状图HTML
    
    async def load_courses(self):
        """加载课程列表"""
        try:
            async with db() as cur:
                await cur.execute("SELECT id, code, name, term FROM courses WHERE status = 'open'")
                self.courses = await cur.fetchall()
                
                # 更新课程选项列表
                self.course_options = [f"{c['code']} - {c['name']}" for c in self.courses]
                
                # 如果没有选中的课程，默认选中第一个
                if self.selected_course is None and self.courses:
                    self.selected_course = self.courses[0]["id"]
        except Exception as e:
            print(f"Error loading courses: {e}")
            self.courses = []
            self.course_options = []
    
    async def load_students(self):
        """加载所有学生列表"""
        try:
            async with db() as cur:
                await cur.execute("""
                    SELECT u.id, u.full_name, u.student_no, s.class_name
                    FROM users u
                    JOIN students s ON u.id = s.user_id
                    ORDER BY u.full_name
                """)
                self.students = await cur.fetchall()
        except Exception as e:
            print(f"Error loading students: {e}")
            self.students = []
    
    async def load_assignments(self):
        """加载所有课程的作业列表"""
        try:
            async with db() as cur:
                await cur.execute("""
                    SELECT id, title, deadline, created_at
                    FROM assignments
                    ORDER BY id ASC
                """)
                self.assignments = await cur.fetchall()
        except Exception as e:
            print(f"Error loading assignments: {e}")
            self.assignments = []
    
    async def load_submission_matrix(self):
        """加载学生提交状态矩阵"""
        if not self.students or not self.assignments:
            self.submission_matrix = {}
            return
        
        try:
            async with db() as cur:
                # 获取所有提交记录
                assignment_ids = [a["id"] for a in self.assignments]
                if not assignment_ids:
                    self.submission_matrix = {}
                    return
                
                placeholders = ",".join(["%s"] * len(assignment_ids))
                await cur.execute(f"""
                    SELECT student_user_id, assignment_id, is_late, submitted_at, version_no
                    FROM submissions
                    WHERE assignment_id IN ({placeholders})
                """, tuple(assignment_ids))
                
                submissions = await cur.fetchall()
                
                # 构建提交矩阵，默认所有任务为未提交
                self.submission_matrix = {}
                for student in self.students:
                    student_id = str(student["id"])
                    self.submission_matrix[student_id] = {}
                    for assignment in self.assignments:
                        assignment_id = str(assignment["id"])
                        self.submission_matrix[student_id][assignment_id] = "not_submitted"
                
                # 构建作业ID到截止时间的映射
                assignment_deadlines = {str(a["id"]): a["deadline"] for a in self.assignments}
                
                # 填充提交状态
                for sub in submissions:
                    student_id = str(sub["student_user_id"])
                    assignment_id = str(sub["assignment_id"])
                    if student_id in self.submission_matrix and assignment_id in self.submission_matrix[student_id]:
                        # 根据提交时间和截止时间判断是否迟交
                        submitted_at = sub["submitted_at"]
                        deadline = assignment_deadlines.get(assignment_id)
                        
                        if submitted_at and deadline:
                            if submitted_at > deadline:
                                self.submission_matrix[student_id][assignment_id] = "late"
                            else:
                                self.submission_matrix[student_id][assignment_id] = "submitted"
                        else:
                            self.submission_matrix[student_id][assignment_id] = "submitted"
                
                # 更新完成率
                self._calculate_completion_rates()
        except Exception as e:
            print(f"Error loading submissions: {e}")
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
        
        # 更新高亮学生
        self.highlighted_student_ids = [r["student_id"] for r in self.completion_rates[:self.highlight_count]]
        
        # 计算作业完成率
        self._calculate_assignment_completion_rates()
    
    def _calculate_assignment_completion_rates(self):
        """计算每个作业的完成率"""
        self.assignment_completion_rates = []
        total_students = len(self.students)
        
        # 生成柱状图HTML
        barchart_html = "<div style='padding: 16px;'>"
        
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
            
            # 计算颜色
            if rate >= 80:
                color = "#22c55e"
            elif rate >= 60:
                color = "#eab308"
            else:
                color = "#ef4444"
            
            self.assignment_completion_rates.append({
                "assignment_id": assignment["id"],
                "title": assignment["title"],
                "deadline": assignment["deadline"],
                "completion_rate": rate,
                "submitted_count": submitted_count,
                "total_students": total_students,
                "completion_text": f"{rate}%",
                "bar_color": color,
                "count_text": f"{submitted_count}/{total_students}"
            })
        
        # 生成竖直柱状图HTML
        self._generate_barchart_html()
        
        # 生成热力图HTML
        self._generate_heatmap_html()
    
    def _generate_heatmap_html(self):
        """生成热力图HTML"""
        html = "<div style='overflow-x: auto;'><table style='border-collapse: collapse; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; width: 100%;'>"
        
        # 表头
        html += "<thead><tr>"
        html += "<th style='padding: 12px; background-color: #3b82f6; color: white; text-align: left; font-weight: bold; min-width: 120px;'>姓名</th>"
        html += "<th style='padding: 12px; background-color: #3b82f6; color: white; text-align: center; font-weight: bold; width: 100px;'>完成率</th>"
        for assign in self.assignments:
            html += f"<th style='padding: 12px; background-color: #3b82f6; color: white; text-align: center; font-weight: bold; width: 60px;'>{assign['id']}</th>"
        html += "</tr></thead><tbody>"
        
        # 数据行
        for idx, student in enumerate(self.completion_rates):
            # 判断是否是置顶的前N名学生
            is_highlighted = idx < self.highlight_count
            row_bg = "background-color: #fffbeb;" if is_highlighted else ""
            
            html += f"<tr style='{row_bg}'>"
            html += f"<td style='padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; font-weight: bold;'>{student['full_name']}</td>"
            html += f"<td style='padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb; font-weight: bold;'>{student['completion_rate']}%</td>"
            
            for assign in self.assignments:
                status = self.get_submission_status(student['student_id'], assign['id'])
                if status == "submitted":
                    bg_color = "#22c55e"
                    text = "✓"
                elif status == "late":
                    bg_color = "#eab308"
                    text = "!"
                elif status == "not_submitted":
                    bg_color = "#ef4444"
                    text = "×"
                else:
                    bg_color = "#9ca3af"
                    text = "-"
                
                html += f"<td style='padding: 8px; text-align: center; border-bottom: 1px solid #e5e7eb;'>"
                html += f"<div style='width: 40px; height: 40px; background-color: {bg_color}; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer;'>"
                html += f"<span style='font-size: 16px; color: white; font-weight: bold;'>{text}</span>"
                html += "</div></td>"
            html += "</tr>"
        
        html += "</tbody></table></div>"
        self.heatmap_html = html
    
    def get_assignment_completion_rates(self):
        """获取每个作业的完成率"""
        result = []
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
            
            # 计算颜色
            if rate >= 80:
                color = "#22c55e"
            elif rate >= 60:
                color = "#eab308"
            else:
                color = "#ef4444"
            
            result.append({
                "assignment_id": assignment["id"],
                "title": assignment["title"],
                "deadline": assignment["deadline"],
                "completion_rate": rate,
                "submitted_count": submitted_count,
                "total_students": total_students,
                "completion_text": f"{rate}%",
                "bar_width": f"{rate * 3}px",
                "bar_color": color,
                "count_text": f"{submitted_count}/{total_students}"
            })
        
        return result
    
    def get_student_by_id(self, student_id):
        """根据ID获取学生信息"""
        for student in self.students:
            if student["id"] == student_id:
                return student
        return None
    
    def get_assignment_by_id(self, assignment_id):
        """根据ID获取作业信息"""
        for assignment in self.assignments:
            if assignment["id"] == assignment_id:
                return assignment
        return None
    
    def get_submission_status(self, student_id, assignment_id):
        """获取学生对作业的提交状态"""
        student_id_str = str(student_id)
        assignment_id_str = str(assignment_id)
        
        if student_id_str in self.submission_matrix:
            if assignment_id_str in self.submission_matrix[student_id_str]:
                return self.submission_matrix[student_id_str][assignment_id_str]
        return "not_submitted"
    
    def get_heatmap_html(self):
        """生成热力图HTML字符串"""
        html = "<div style='overflow-x: auto;'><table style='border-collapse: collapse; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;'>"
        
        # 表头
        html += "<thead><tr>"
        html += "<th style='padding: 12px; background-color: #3b82f6; color: white; text-align: left; font-weight: bold; width: 120px;'>姓名</th>"
        html += "<th style='padding: 12px; background-color: #3b82f6; color: white; text-align: center; font-weight: bold; width: 100px;'>完成率</th>"
        for assign in self.assignments:
            html += f"<th style='padding: 12px; background-color: #3b82f6; color: white; text-align: center; font-weight: bold; width: 60px;'>{assign['id']}</th>"
        html += "</tr></thead><tbody>"
        
        # 数据行
        for idx, student in enumerate(self.completion_rates):
            # 判断是否是置顶的前N名学生
            is_highlighted = idx < self.highlight_count
            row_bg = "background-color: #fffbeb;" if is_highlighted else ""
            
            html += f"<tr style='{row_bg}'>"
            html += f"<td style='padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; font-weight: bold;'>{student['full_name']}</td>"
            html += f"<td style='padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb; font-weight: bold;'>{student['completion_rate']}%</td>"
            
            for assign in self.assignments:
                status = self.get_submission_status(student['student_id'], assign['id'])
                if status == "submitted":
                    bg_color = "#22c55e"
                    text = "✓"
                elif status == "late":
                    bg_color = "#eab308"
                    text = "!"
                elif status == "not_submitted":
                    bg_color = "#ef4444"
                    text = "×"
                else:
                    bg_color = "#9ca3af"
                    text = "-"
                
                html += f"<td style='padding: 8px; text-align: center; border-bottom: 1px solid #e5e7eb;'>"
                html += f"<div style='width: 40px; height: 40px; background-color: {bg_color}; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer;'>"
                html += f"<span style='font-size: 16px; color: white; font-weight: bold;'>{text}</span>"
                html += "</div></td>"
            html += "</tr>"
        
        html += "</tbody></table></div>"
        return html
    
    def get_barchart_html(self):
        """生成柱状图HTML字符串"""
        html = "<div style='padding: 16px;'>"
        total_students = len(self.students)
        
        for stat in self.assignment_completion_rates:
            if stat['completion_rate'] >= 80:
                color = "#22c55e"
            elif stat['completion_rate'] >= 60:
                color = "#eab308"
            else:
                color = "#ef4444"
            
            html += "<div style='display: flex; align-items: center; margin-bottom: 8px;'>"
            html += f"<span style='width: 120px; font-size: 12px; text-align: right; margin-right: 12px;'>{stat['title']}</span>"
            html += f"<div style='width: {stat['completion_rate'] * 3}px; height: 32px; background-color: {color}; border-radius: 4px; display: flex; align-items: center; padding-left: 8px; min-width: 40px;'>"
            html += f"<span style='font-size: 12px; color: white; font-weight: bold;'>{stat['completion_rate']}%</span>"
            html += "</div>"
            html += f"<span style='width: 60px; font-size: 12px; color: #6b7280; text-align: left; margin-left: 8px;'>{stat['submitted_count']}/{total_students}</span>"
            html += "</div>"
        
        html += "</div>"
        return html
    
    def handle_course_change(self, course_id):
        """处理课程选择变化"""
        self.selected_course = course_id
        return self.refresh_data()
    
    def handle_term_change(self, term):
        """处理学期选择变化"""
        self.selected_term = term
        return self.refresh_data()
    
    def handle_highlight_count_change(self, count):
        """处理高亮数量变化"""
        self.highlight_count = max(1, min(20, count))
        self._calculate_completion_rates()
    
    def handle_sort_change(self, order):
        """处理排序方式变化"""
        self.sort_order = order
        self._calculate_completion_rates()
    
    def get_course_options(self):
        """获取课程选项列表（用于select组件）"""
        return [f"{c['code']} - {c['name']}" for c in self.courses]
    
    async def refresh_data(self):
        """刷新所有数据"""
        await self.load_students()
        await self.load_assignments()
        await self.load_submission_matrix()
    
    async def _load_all_data(self):
        """实际加载所有数据的方法（内部使用）"""
        await self.load_courses()
        await self.refresh_data()
    
    async def on_load(self):
        """页面加载时初始化数据"""
        await self._load_all_data()
    
    def _generate_barchart_html(self):
        """生成竖直柱状图HTML"""
        total_students = len(self.students)
        max_bar_height = 200  # 最大柱状图高度
        
        # 创建包含纵轴的柱状图
        html = '<div style="display: flex; padding: 16px; background-color: #f9fafb; border-radius: 8px;">'
        
        # 纵轴刻度
        html += '<div style="display: flex; flex-direction: column; justify-content: space-between; height: 200px; margin-right: 12px;">'
        html += '<span style="font-size: 10px; color: #6b7280; text-align: right; width: 40px;">100%</span>'
        html += '<span style="font-size: 10px; color: #6b7280; text-align: right; width: 40px;">75%</span>'
        html += '<span style="font-size: 10px; color: #6b7280; text-align: right; width: 40px;">50%</span>'
        html += '<span style="font-size: 10px; color: #6b7280; text-align: right; width: 40px;">25%</span>'
        html += '<span style="font-size: 10px; color: #6b7280; text-align: right; width: 40px;">0%</span>'
        html += '</div>'
        
        # 纵轴线
        html += '<div style="border-left: 1px solid #d1d5db; height: 200px; margin-right: 12px;"></div>'
        
        # 柱状图区域
        html += '<div style="display: flex; align-items: flex-end; height: 200px; gap: 16px;">'
        
        for stat in self.assignment_completion_rates:
            bar_height = int((stat['completion_rate'] / 100) * max_bar_height)
            
            html += '<div style="display: flex; flex-direction: column; align-items: center;">'
            # 完成率文字
            html += f'<span style="font-size: 11px; font-weight: bold; color: #374151; margin-bottom: 4px;">{stat["completion_rate"]}%</span>'
            # 柱子
            html += f'<div style="width: 40px; background-color: {stat["bar_color"]}; border-radius: 4px 4px 0 0; display: flex; align-items: flex-start; justify-content: center; min-height: 4px;" title="{stat["title"]} ({stat["completion_rate"]}%)">'
            html += '</div>'
            # 提交数
            html += f'<span style="font-size: 9px; color: #6b7280; margin-top: 4px;">{stat["submitted_count"]}/{total_students}</span>'
            # 作业名称
            html += f'<span style="font-size: 10px; color: #374151; margin-top: 4px; text-align: center;">{stat["title"]}</span>'
            html += '</div>'
        
        html += '</div>'
        html += '</div>'
        
        # 底部统计信息
        html += f'<div style="text-align: center; margin-top: 16px; font-size: 12px; color: #6b7280;">'
        html += f'共 {total_students} 名学生 · {len(self.assignment_completion_rates)} 个活跃任务'
        html += '</div>'
        
        self.barchart_html = html