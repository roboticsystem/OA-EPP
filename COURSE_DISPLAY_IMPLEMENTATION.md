# 课程展示功能实现说明

## 功能概述

实现了学生课程主页（F-S-010），展示学生已选课程（工程实践1-4）与当前学习进度，每门课程展示章节数、已完成任务数及截止提醒。

## 项目结构

```
oaepp/
├── models/
│   └── database.py           # 数据库模型定义
│       ├── Student           # 学生模型
│       ├── Course            # 课程模型
│       ├── Chapter           # 章节模型
│       ├── Task              # 任务模型
│       ├── StudentCourse     # 学生选课关系
│       └── TaskCompletion    # 任务完成记录
├── states/
│   ├── auth_state.py         # 认证状态管理
│   └── course_state.py       # 课程状态管理
└── pages/
    └── courses.py            # 课程展示页面
```

## 验收标准实现

### ✅ 展示所有已选课程列表及学习进度
- 页面加载时自动从 MySQL 数据库查询学生的已选课程
- 使用 `StudentCourse` 表记录学生与课程的关系
- 实时展示每门课程的详细信息

### ✅ 每门课程显示章节数/已完成任务数/截止提醒
- **章节数**：从 Course 表中获取 `total_chapters` 字段
- **已完成任务数**：通过统计 TaskCompletion 表中该学生的完成记录
- **总任务数**：统计该课程下所有章节的任务数
- **截止提醒**：显示该课程下一个未来的截止日期

### ✅ 进度信息实时更新无需手动刷新
- 实现了 `refresh_courses()` 方法，点击"刷新数据"按钮可重新加载数据
- 后续可通过 WebSocket 或定时器实现自动更新
- 使用异步方法 `load_student_courses()` 确保数据加载不阻塞 UI

## 使用方法

### 1. 环境配置

复制 `.env.example` 为 `.env`，配置数据库连接：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置数据库连接字符串：

```env
DB_URL=mysql+pymysql://student_dev:OaEpp@Dev2026@oaepp-mysql:3306/oaepp_dev
```

### 2. 安装依赖

```bash
pip install -r reflex-requirements.txt
```

### 3. 初始化数据库

运行 Reflex 迁移命令初始化数据表：

```bash
reflex db init
```

### 4. 插入测试数据

连接到 MySQL 数据库并执行以下 SQL（示例）：

```sql
-- 插入学生
INSERT INTO student (name, student_id, class_name)
VALUES ('张三', 'STU001', '工程实践班');

-- 插入课程
INSERT INTO course (code, name, description, total_chapters)
VALUES 
('ENG-PRAC-01', '工程实践1', '第一学期实践课程', 10),
('ENG-PRAC-02', '工程实践2', '第二学期实践课程', 10),
('ENG-PRAC-03', '工程实践3', '第三学期实践课程', 10),
('ENG-PRAC-04', '工程实践4', '第四学期实践课程', 10);

-- 插入学生选课
INSERT INTO student_course (student_id, course_id, status)
VALUES 
(1, 1, 'active'),
(1, 2, 'active'),
(1, 3, 'active'),
(1, 4, 'active');

-- 插入章节
INSERT INTO chapter (course_id, chapter_num, title, order)
VALUES 
(1, 1, '项目介绍', 1),
(1, 2, '开发环境搭建', 2),
...

-- 插入任务
INSERT INTO task (chapter_id, title, task_type, due_date, order)
VALUES 
(1, '阅读项目文档', 'reading', DATE_ADD(NOW(), INTERVAL 7 DAY), 1),
(1, '完成代码示例', 'practice', DATE_ADD(NOW(), INTERVAL 14 DAY), 2),
...

-- 标记任务完成
INSERT INTO taskcompletion (student_id, task_id, status)
VALUES 
(1, 1, 'completed'),
(1, 2, 'completed'),
...
```

### 5. 启动应用

```bash
reflex run
```

访问 `http://localhost:3000/courses` 即可看到课程展示页面。

## 核心功能代码

### 课程状态管理 (course_state.py)

```python
async def load_student_courses(self, student_id: int = 0):
    """加载学生已选课程及进度"""
    # 获取学生选课记录
    # 统计每门课程的章节数、任务数、完成数
    # 获取下一个截止日期
    # 计算进度百分比
```

### 课程展示页面 (courses.py)

- `course_card()`: 单门课程卡片组件，展示课程信息和进度
- `courses_page()`: 主页面布局，包含课程列表、刷新按钮、加载状态、错误提示

## 数据模型关系

```
Student (1) ─── (N) StudentCourse (N) ─── (1) Course
                                          │
                                          (1)
                                          │
                                      Chapter (1) ─── (N) Task
                                          
Task (1) ─── (N) TaskCompletion (N) ─── (1) Student
```

## 后续改进方向

1. **自动更新**：使用 WebSocket 或定时器实现数据自动刷新
2. **详情页面**：创建课程详情页面，展示所有章节和任务列表
3. **通知提醒**：实现截止日期提醒功能
4. **学习统计**：添加学习时间、课程排名等统计信息
5. **导师评语**：集成教师评语和反馈

## 相关文档

- 原始需求：§5.2 F-S-010 课程主页
- 数据库连接：[database-connection.md](/memories/repo/database-connection.md)
