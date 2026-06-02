# 如何提交此 Issue 的实现

根据项目 commit message 规范 ([commit-message.instructions.md](.github/instructions/commit-message.instructions.md))，使用以下 commit message:

## 方案 A: 单个完整 commit

```
feat(课程与章节学习模块): 实现学生课程主页与进度展示 F-S-010

新增 Reflex 前端框架支持，实现学生课程主页展示功能：
- 展示已选课程列表（工程实践1-4）及学习进度
- 每门课程显示章节数、已完成任务数、下一个截止日期
- 支持手动刷新数据，后续支持 WebSocket 自动更新

新增文件：
- oaepp/ 项目结构（模型、状态管理、页面）
- rxconfig.py Reflex 项目配置
- reflex-requirements.txt 依赖清单
- 数据初始化脚本 scripts/init_course_test_data.py

数据库模型：Student, Course, Chapter, Task, StudentCourse, TaskCompletion

Close #IssueNumber: 7位commit哈希
```

## 方案 B: 分步 commits（推荐）

### Commit 1: 初始化 Reflex 项目结构
```
feat(基础设施): 初始化 Reflex 前端项目

- 创建 Reflex 项目配置 (rxconfig.py)
- 建立 oaepp 项目目录结构
- 配置 MySQL 数据库连接
- 添加环境变量模板 (.env.example)

Close #IssueNumber: xxxxxxx
```

### Commit 2: 创建数据库模型
```
feat(数据库): 创建课程学习模块数据模型

新增 6 个 SQLAlchemy 模型：
- Student: 学生基本信息
- Course: 课程信息（含章节数）
- Chapter: 课程章节
- Task: 任务列表（含截止日期）
- StudentCourse: 学生选课关系
- TaskCompletion: 任务完成记录

建立关系：Student ─ StudentCourse ─ Course ─ Chapter ─ Task ─ TaskCompletion

Close #IssueNumber: xxxxxxx
```

### Commit 3: 实现课程状态管理
```
feat(状态管理): 实现课程数据加载与状态管理

新增 CourseState：
- async load_student_courses(): 加载学生已选课程及进度
- select_course(): 选择查看课程
- async refresh_courses(): 刷新课程数据

统计逻辑：
- 每门课程的总章节数、总任务数
- 学生的已完成任务数和进度百分比
- 下一个截止任务日期

Close #IssueNumber: xxxxxxx
```

### Commit 4: 创建课程展示页面
```
feat(课程页面): 实现课程主页展示 F-S-010

- courses.py: 课程列表页面 (/courses)
- course_card(): 单门课程卡片组件
- 展示课程信息、进度条、截止提醒
- 实现刷新按钮和加载状态提示

页面布局：
- 课程卡片网格展示
- 实时进度统计
- 错误处理和加载状态

Close #IssueNumber: xxxxxxx
```

### Commit 5: 配置测试与文档
```
chore(测试与文档): 添加数据初始化脚本和文档

- scripts/init_course_test_data.py: 测试数据初始化
- COURSE_DISPLAY_IMPLEMENTATION.md: 实现说明
- QUICK_START_COURSES.md: 快速开始指南
- ACCEPTANCE_CRITERIA_VERIFICATION.md: 验收标准检查表
- reflex-requirements.txt: Reflex 依赖清单

Close #IssueNumber: xxxxxxx
```

## 本地提交命令

```bash
# 方案 A: 单个 commit
git add .
git commit -m "feat(课程与章节学习模块): 实现学生课程主页与进度展示 F-S-010

新增 Reflex 前端框架支持，实现学生课程主页展示功能：
- 展示已选课程列表（工程实践1-4）及学习进度
- 每门课程显示章节数、已完成任务数、下一个截止日期
- 支持手动刷新数据

Close #IssueNumber: 7位commit哈希"

# 方案 B: 分步提交（如需要）
git add oaepp/ rxconfig.py .env.example
git commit -m "feat(基础设施): 初始化 Reflex 前端项目

..."

# 后续提交...
```

## 提交前检查清单

- [ ] 所有新文件已添加
- [ ] 代码遵循项目规范
- [ ] 测试数据脚本可正常运行
- [ ] 文档完整准确
- [ ] commit message 使用中文
- [ ] Issue 号码已填入 commit message

## 相关文件

- 规范文档: [commit-message.instructions.md](.github/instructions/commit-message.instructions.md)
- 实现说明: [COURSE_DISPLAY_IMPLEMENTATION.md](COURSE_DISPLAY_IMPLEMENTATION.md)
- 快速开始: [QUICK_START_COURSES.md](QUICK_START_COURSES.md)
- 验收清单: [ACCEPTANCE_CRITERIA_VERIFICATION.md](ACCEPTANCE_CRITERIA_VERIFICATION.md)
