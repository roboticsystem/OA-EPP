"""F-T-001 学生-GitHub账号对应表管理 (教师功能)

功能：
- 管理全班学生与GitHub账号的完整映射表
- 支持CSV批量导入（学号/姓名/GitHub用户名）并自动校验
- 支持单条手动新增/编辑/删除
- 变更后关联学生历史成绩自动重算
- 支持按班级/课程筛选与导出

验收标准：
- 支持CSV格式批量导入并自动校验合法性
- 支持单条手动新增/编辑/删除
- 变更后关联历史成绩自动重算
- 支持按班级/课程筛选并导出CSV
- 同一学生只允许绑定一个账号，账号共用时系统提示冲突
"""
import reflex as rx
from typing import List, Dict, Optional
from sqlmodel import select, func
from datetime import datetime
import csv
import io
import re

try:
    from oaepp.models import User, Student, GithubBinding, Course, Enrollment, GradingRecord, ScoreItem, Submission
except ImportError:
    from models import User, Student, GithubBinding, Course, Enrollment, GradingRecord, ScoreItem, Submission


class StudentGitHubState(rx.State):
    """学生-GitHub账号对应表管理状态"""
    
    # 数据列表 - 测试期望的属性名: student_github_map
    student_github_map: List[Dict] = []
    bindings: List[Dict] = []  # 保留别名兼容
    courses: List[Dict] = []
    class_names: List[str] = []
    
    # 筛选条件
    selected_course_id: Optional[int] = None
    selected_class_name: str = ""
    search_keyword: str = ""
    
    # 加载状态 - 测试期望的属性名: is_loading
    is_loading: bool = False
    loading: bool = False  # 保留别名兼容
    import_loading: bool = False
    
    # 错误/成功消息
    error_message: str = ""
    success_message: str = ""
    import_error: str = ""  # 测试期望的属性名
    
    # 导入结果
    import_results: Dict[str, List] = {
        "success": [],
        "failed": [],
        "conflicts": []
    }
    import_conflicts: List[Dict] = []  # 测试期望的属性名
    duplicate_count: int = 0  # 测试期望的属性名
    
    # 导入结果计数（用于前端显示）
    @rx.var
    def import_success_count(self) -> int:
        return len(self.import_results["success"])
    
    @rx.var
    def import_failed_count(self) -> int:
        return len(self.import_results["failed"])
    
    @rx.var
    def import_conflicts_count(self) -> int:
        return len(self.import_results["conflicts"])
    
    @rx.var
    def import_success_message(self) -> str:
        return f"成功导入 {len(self.import_results['success'])} 条记录"
    
    @rx.var
    def import_failed_message(self) -> str:
        return f"导入失败 {len(self.import_results['failed'])} 条记录"
    
    @rx.var
    def import_failed_list(self) -> List[Dict]:
        """返回导入失败的列表，用于前端显示"""
        return self.import_results.get("failed", [])
    
    @rx.var
    def import_conflicts_message(self) -> str:
        return f"发现冲突 {len(self.import_results['conflicts'])} 条记录"
    
    # 编辑对话框状态
    show_edit_dialog: bool = False
    editing_binding: Dict = {}
    is_new_binding: bool = False
    
    # 冲突提示对话框
    show_conflict_dialog: bool = False
    conflict_message: str = ""
    pending_binding: Optional[Dict] = None
    
    # 表单字段
    form_student_no: str = ""
    form_full_name: str = ""
    form_github_username: str = ""
    form_github_name: str = ""
    form_class_name: str = ""
    
    # CSV文件上传内容
    csv_content: str = ""
    csv_filename: str = ""
    
    def clear_messages(self):
        """清除消息"""
        self.error_message = ""
        self.success_message = ""
        self.import_error = ""
    
    async def set_selected_course(self, course_id: str):
        """设置选中的课程"""
        self.selected_course_id = int(course_id) if course_id else None
        await self.load_bindings()
    
    async def set_selected_class(self, class_name: str):
        """设置选中的班级"""
        self.selected_class_name = class_name
        await self.load_bindings()
    
    def set_search_keyword(self, keyword: str):
        """设置搜索关键词"""
        self.search_keyword = keyword
    
    async def do_search(self):
        """执行搜索"""
        await self.load_bindings()
    
    async def load_courses(self):
        """加载课程列表"""
        try:
            with rx.session() as session:
                courses = session.exec(select(Course)).all()
                self.courses = [
                    {
                        "id": c.id,
                        "code": c.code,
                        "name": c.name,
                        "term": c.term
                    }
                    for c in courses
                ]
        except Exception as e:
            self.error_message = f"加载课程列表失败: {e}"
    
    async def load_class_names(self):
        """加载班级列表"""
        try:
            with rx.session() as session:
                result = session.exec(select(Student.class_name).distinct()).all()
                self.class_names = [c for c in result if c]
        except Exception as e:
            self.error_message = f"加载班级列表失败: {e}"
    
    async def load_bindings(self):
        """加载GitHub绑定列表"""
        self.loading = True
        self.is_loading = True
        self.error_message = ""
        
        try:
            with rx.session() as session:
                # 构建基础查询
                query = select(
                    GithubBinding,
                    User,
                    Student
                ).join(
                    User, GithubBinding.student_user_id == User.id
                ).join(
                    Student, Student.user_id == User.id
                )
                
                # 按班级筛选
                if self.selected_class_name:
                    query = query.where(Student.class_name == self.selected_class_name)
                
                # 按课程筛选（通过enrollments关联）
                if self.selected_course_id:
                    query = query.join(
                        Enrollment, Enrollment.student_user_id == User.id
                    ).where(Enrollment.course_id == self.selected_course_id)
                
                # 按搜索关键词筛选
                if self.search_keyword:
                    keyword = f"%{self.search_keyword}%"
                    query = query.where(
                        (User.student_no.like(keyword)) |
                        (User.full_name.like(keyword)) |
                        (GithubBinding.github_username.like(keyword))
                    )
                
                results = session.exec(query).all()
                
                # 调试信息
                print(f"load_bindings 查询到 {len(results)} 条记录")
                
                self.bindings = []
                self.student_github_map = []
                for binding, user, student in results:
                    # 获取该学生的成绩数量
                    grade_count = session.exec(
                        select(func.count(GradingRecord.id))
                        .join(Submission, GradingRecord.submission_id == Submission.id)
                        .where(Submission.student_user_id == user.id)
                    ).first() or 0
                    
                    item = {
                        "id": binding.id,
                        "student_user_id": binding.student_user_id,
                        "student_no": user.student_no,
                        "full_name": user.full_name,
                        "class_name": student.class_name,
                        "github_username": binding.github_username,
                        "github_name": binding.github_name,
                        "verify_status": binding.verify_status,
                        "verified_at": binding.verified_at,
                        "grade_count": grade_count
                    }
                    self.bindings.append(item)
                    self.student_github_map.append(item)
                    
        except Exception as e:
            self.error_message = f"加载数据失败: {e}"
        finally:
            self.loading = False
            self.is_loading = False
    
    def open_add_dialog(self):
        """打开新增对话框"""
        self.is_new_binding = True
        self.editing_binding = {}
        self.form_student_no = ""
        self.form_full_name = ""
        self.form_github_username = ""
        self.form_github_name = ""
        self.form_class_name = ""
        self.show_edit_dialog = True
        self.clear_messages()
    
    def open_edit_dialog(self, binding: Dict):
        """打开编辑对话框"""
        self.is_new_binding = False
        self.editing_binding = binding.copy()
        self.form_student_no = binding.get("student_no", "")
        self.form_full_name = binding.get("full_name", "")
        self.form_github_username = binding.get("github_username", "")
        self.form_github_name = binding.get("github_name", "")
        self.form_class_name = binding.get("class_name", "")
        self.show_edit_dialog = True
        self.clear_messages()
    
    def close_edit_dialog(self):
        """关闭编辑对话框"""
        self.show_edit_dialog = False
        self.editing_binding = {}
        self.clear_messages()
    
    def set_form_student_no(self, value: str):
        self.form_student_no = value
    
    def set_form_full_name(self, value: str):
        self.form_full_name = value
    
    def set_form_github_username(self, value: str):
        self.form_github_username = value
    
    def set_form_github_name(self, value: str):
        self.form_github_name = value
    
    def set_form_class_name(self, value: str):
        self.form_class_name = value
    
    def _validate_github_username(self, username: str) -> bool:
        """验证GitHub用户名格式"""
        if not username:
            return False
        # GitHub用户名规则：字母数字开头，可包含连字符，最长39字符
        pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'
        return bool(re.match(pattern, username))
    
    def _check_binding_conflicts(self, session, student_user_id: int, github_username: str, exclude_id: Optional[int] = None) -> Optional[str]:
        """检查绑定冲突
        
        返回：冲突信息，无冲突返回None
        """
        # 检查学生是否已绑定其他账号
        student_query = select(GithubBinding).where(
            GithubBinding.student_user_id == student_user_id
        )
        if exclude_id:
            student_query = student_query.where(GithubBinding.id != exclude_id)
        existing = session.exec(student_query).first()
        if existing:
            return f"该学生已绑定GitHub账号: {existing.github_username}"
        
        # 检查GitHub账号是否已被其他学生使用
        github_query = select(GithubBinding).where(
            GithubBinding.github_username == github_username
        )
        if exclude_id:
            github_query = github_query.where(GithubBinding.id != exclude_id)
        existing = session.exec(github_query).first()
        if existing:
            return f"该GitHub账号已被其他学生使用"
        
        return None
    
    async def save_binding(self):
        """保存绑定（新增或编辑）"""
        await self._do_save_binding(force=False)
    
    async def _do_save_binding(self, force: bool = False):
        """实际保存绑定的内部方法"""
        self.error_message = ""
        self.success_message = ""
        
        # 验证输入
        if not self.form_student_no.strip():
            self.error_message = "请输入学号"
            return
        if not self.form_full_name.strip():
            self.error_message = "请输入姓名"
            return
        if not self.form_github_username.strip():
            self.error_message = "请输入GitHub用户名"
            return
        
        github_username = self.form_github_username.strip()
        if not self._validate_github_username(github_username):
            self.error_message = "GitHub用户名格式不正确"
            return
        
        try:
            with rx.session() as session:
                # 查找学生
                student = session.exec(
                    select(User, Student)
                    .join(Student, Student.user_id == User.id)
                    .where(User.student_no == self.form_student_no.strip())
                ).first()
                
                if not student:
                    self.error_message = f"未找到学号为 {self.form_student_no} 的学生"
                    return
                
                user, student_info = student
                
                # 检查姓名是否匹配
                if user.full_name != self.form_full_name.strip():
                    self.error_message = f"姓名不匹配，系统中该学号对应姓名为: {user.full_name}"
                    return
                
                exclude_id = self.editing_binding.get("id") if not self.is_new_binding else None
                
                # 检查冲突
                conflict = self._check_binding_conflicts(
                    session, user.id, github_username, exclude_id
                )
                
                if conflict and not force:
                    self.conflict_message = conflict
                    self.pending_binding = {
                        "student_user_id": user.id,
                        "github_username": github_username,
                        "github_name": self.form_github_name.strip() or None
                    }
                    self.show_conflict_dialog = True
                    return
                
                # 保存绑定
                if self.is_new_binding:
                    binding = GithubBinding(
                        student_user_id=user.id,
                        github_username=github_username,
                        github_name=self.form_github_name.strip() or None,
                        verify_status="approved",
                        verified_at=datetime.now(),
                        verified_by=None  # TODO: 从AuthState获取当前教师ID
                    )
                    session.add(binding)
                else:
                    binding = session.exec(
                        select(GithubBinding).where(GithubBinding.id == exclude_id)
                    ).first()
                    if binding:
                        old_username = binding.github_username
                        binding.github_username = github_username
                        binding.github_name = self.form_github_name.strip() or None
                        binding.verified_at = datetime.now()
                        
                        # 如果GitHub账号变更，触发成绩重算
                        if old_username != github_username:
                            await self._recalculate_grades(session, user.id)
                
                session.commit()
                self.success_message = "保存成功"
                self.show_edit_dialog = False
                await self.load_bindings()
                
        except Exception as e:
            self.error_message = f"保存失败: {e}"
    
    async def confirm_conflict(self):
        """确认覆盖冲突"""
        self.show_conflict_dialog = False
        await self._do_save_binding(force=True)
    
    async def cancel_conflict(self):
        """取消冲突处理"""
        self.show_conflict_dialog = False
        self.pending_binding = None
    
    async def delete_binding(self, binding_id: int):
        """删除绑定"""
        self.error_message = ""
        self.success_message = ""
        
        try:
            with rx.session() as session:
                binding = session.exec(
                    select(GithubBinding).where(GithubBinding.id == binding_id)
                ).first()
                
                if binding:
                    student_user_id = binding.student_user_id
                    session.delete(binding)
                    session.commit()
                    
                    # 触发成绩重算（移除GitHub关联后）
                    await self._recalculate_grades(session, student_user_id)
                    
                    self.success_message = "删除成功"
                    await self.load_bindings()
                else:
                    self.error_message = "未找到该绑定记录"
                    
        except Exception as e:
            self.error_message = f"删除失败: {e}"
    
    async def _recalculate_grades(self, session, student_user_id: int):
        """重算学生成绩
        
        当GitHub账号变更时，需要重新计算与该学生相关的成绩
        """
        try:
            # 获取该学生的所有成绩记录
            grading_records = session.exec(
                select(GradingRecord)
                .join(Submission, GradingRecord.submission_id == Submission.id)
                .where(Submission.student_user_id == student_user_id)
            ).all()
            
            # TODO: 根据实际业务逻辑重新计算成绩
            # 这里可以调用成绩重算服务或触发异步任务
            
            # 示例：更新成绩记录的时间戳，表示已重新评估
            for record in grading_records:
                record.graded_at = datetime.now()
            
            session.commit()
            
        except Exception as e:
            # 记录错误但不中断主流程
            print(f"成绩重算失败: {e}")
    
    def set_csv_content(self, content: str):
        """设置CSV文件内容"""
        self.csv_content = content
    
    @rx.event
    async def handle_csv_upload(self, files: list[rx.UploadFile]):
        """处理CSV文件上传"""
        if not files:
            return
        
        try:
            # 读取上传的文件内容
            file = files[0]
            content = await file.read()
            self.csv_content = content.decode('utf-8')
            self.csv_filename = file.name
            self.error_message = ""
        except Exception as e:
            self.error_message = f"文件读取失败: {str(e)}"
    
    async def import_csv(self, csv_content: Optional[str] = None):
        """导入CSV文件
        
        Args:
            csv_content: CSV文件内容，如果为None则使用 self.csv_content
        """
        content = csv_content if csv_content is not None else self.csv_content
        if not content:
            self.error_message = "请选择CSV文件"
            self.import_error = "请选择CSV文件"
            return
        
        self.import_loading = True
        self.is_loading = True
        self.error_message = ""
        self.import_error = ""
        self.success_message = ""
        self.import_results = {
            "success": [],
            "failed": [],
            "conflicts": []
        }
        self.import_conflicts = []
        self.duplicate_count = 0
        
        try:
            # 解析CSV
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)
            
            # 验证表头
            expected_headers = ["学号", "姓名", "GitHub用户名"]
            headers = reader.fieldnames or []
            
            # 支持多种表头格式
            header_mapping = {}
            for h in headers:
                h_lower = h.lower().strip()
                if h_lower in ["学号", "student_no", "student id", "学号/student_no"]:
                    header_mapping["学号"] = h
                elif h_lower in ["姓名", "name", "full_name", "姓名/full_name"]:
                    header_mapping["姓名"] = h
                elif h_lower in ["github用户名", "github_username", "github", "github用户名/github_username"]:
                    header_mapping["GitHub用户名"] = h
            
            if not all(k in header_mapping for k in expected_headers):
                error_msg = f"CSV表头格式不正确，需要包含: 学号, 姓名, GitHub用户名。当前表头: {headers}"
                self.error_message = error_msg
                self.import_error = error_msg
                self.import_loading = False
                self.is_loading = False
                return
            
            with rx.session() as session:
                for row in reader:
                    try:
                        student_no = row.get(header_mapping.get("学号", "学号"), "").strip()
                        full_name = row.get(header_mapping.get("姓名", "姓名"), "").strip()
                        github_username = row.get(header_mapping.get("GitHub用户名", "GitHub用户名"), "").strip()
                        
                        if not student_no or not full_name or not github_username:
                            self.import_results["failed"].append({
                                "row": row,
                                "reason": "数据不完整"
                            })
                            continue
                        
                        # 验证GitHub用户名格式
                        if not self._validate_github_username(github_username):
                            self.import_results["failed"].append({
                                "row": row,
                                "reason": "GitHub用户名格式不正确"
                            })
                            continue
                        
                        # 查找学生
                        student = session.exec(
                            select(User, Student)
                            .join(Student, Student.user_id == User.id)
                            .where(User.student_no == student_no)
                        ).first()
                        
                        if not student:
                            self.import_results["failed"].append({
                                "row": row,
                                "reason": f"未找到学号为 {student_no} 的学生"
                            })
                            continue
                        
                        user, student_info = student
                        
                        # 检查姓名匹配（去除前后空格）
                        db_full_name = (user.full_name or "").strip()
                        csv_full_name = full_name.strip()
                        
                        if db_full_name != csv_full_name:
                            self.import_results["failed"].append({
                                "row": row,
                                "reason": f"姓名不匹配，CSV中为 '{csv_full_name}'，系统中为 '{db_full_name}'"
                            })
                            continue
                        
                        # 检查冲突
                        conflict = self._check_binding_conflicts(session, user.id, github_username)
                        if conflict:
                            self.import_results["conflicts"].append({
                                "row": row,
                                "reason": conflict,
                                "student_user_id": user.id,
                                "github_username": github_username
                            })
                            self.import_conflicts.append({
                                "row": row,
                                "reason": conflict,
                                "student_user_id": user.id,
                                "github_username": github_username
                            })
                            self.duplicate_count += 1
                            continue
                        
                        # 检查是否已存在绑定（更新或新增）
                        existing = session.exec(
                            select(GithubBinding).where(
                                GithubBinding.student_user_id == user.id
                            )
                        ).first()
                        
                        if existing:
                            # 更新现有绑定
                            old_username = existing.github_username
                            existing.github_username = github_username
                            existing.verify_status = "approved"
                            existing.verified_at = datetime.now()
                            existing.verified_by = None  # TODO: 从AuthState获取当前教师ID
                            
                            # 触发成绩重算
                            if old_username != github_username:
                                await self._recalculate_grades(session, user.id)
                        else:
                            # 新增绑定
                            binding = GithubBinding(
                                student_user_id=user.id,
                                github_username=github_username,
                                github_name=None,
                                verify_status="approved",
                                verified_at=datetime.now(),
                                verified_by=None  # TODO: 从AuthState获取当前教师ID
                            )
                            session.add(binding)
                        
                        self.import_results["success"].append({
                            "student_no": student_no,
                            "full_name": full_name,
                            "github_username": github_username
                        })
                        
                    except Exception as e:
                        self.import_results["failed"].append({
                            "row": row,
                            "reason": str(e)
                        })
                
                session.commit()
            
            total = len(self.import_results["success"]) + len(self.import_results["failed"]) + len(self.import_results["conflicts"])
            self.success_message = f"导入完成: 成功 {len(self.import_results['success'])} 条, 失败 {len(self.import_results['failed'])} 条, 冲突 {len(self.import_results['conflicts'])} 条"
            
            # 清除CSV内容和文件名，防止重复导入
            self.csv_content = ""
            self.csv_filename = ""
            
            # 重新加载数据
            await self.load_bindings()
            
            # 调试信息
            print(f"导入完成，当前绑定数: {len(self.bindings)}")
            
        except Exception as e:
            error_msg = f"导入失败: {e}"
            self.error_message = error_msg
            self.import_error = error_msg
        finally:
            self.import_loading = False
            self.is_loading = False
            if not self.csv_content:
                self.csv_content = ""
    
    async def export_csv(self):
        """导出CSV文件"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(["学号", "姓名", "班级", "GitHub用户名", "GitHub显示名", "审核状态", "验证时间"])
            
            # 写入数据
            for binding in self.bindings:
                writer.writerow([
                    binding.get("student_no", ""),
                    binding.get("full_name", ""),
                    binding.get("class_name", ""),
                    binding.get("github_username", ""),
                    binding.get("github_name", ""),
                    binding.get("verify_status", ""),
                    binding.get("verified_at", "")
                ])
            
            # 使用 rx.download 触发文件下载
            csv_content = output.getvalue()
            yield rx.download(data=csv_content.encode('utf-8-sig'), filename="github_bindings.csv")
            
        except Exception as e:
            self.error_message = f"导出失败: {e}"
    
    async def on_mount(self):
        """页面加载时初始化"""
        await self.load_courses()
        await self.load_class_names()
        await self.load_bindings()
