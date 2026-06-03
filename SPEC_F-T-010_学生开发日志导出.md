# 学生开发日志报告导出功能 - 规格说明书

## 1. 功能概述

### 1.1 功能描述
教师可为任意学生生成包含9个维度的完整开发日志报告，数据实时从平台数据库和GitHub API拉取，支持PDF/HTML/Excel三种格式导出，支持按班级批量导出，并记录操作审计日志。

### 1.2 验收标准
- ✅ 报告包含9个维度数据并按时间轴排列
- ✅ 报告封面自动填写学生基础信息（学号/姓名/班级/课程/学期）
- ✅ 支持PDF/HTML/Excel三种导出格式
- ✅ 支持按班级批量导出压缩包
- ✅ 数据实时从平台数据库+GitHub API拉取
- ✅ 操作记录审计日志（导出人/时间/被查学生/格式）

---

## 2. 技术架构

### 2.1 技术栈
- **后端框架**: FastAPI
- **数据库**: SQLite（现有）
- **PDF生成**: ReportLab / WeasyPrint
- **Excel生成**: openpyxl（已使用）
- **HTTP客户端**: httpx（异步GitHub API调用）
- **模板引擎**: Jinja2（HTML模板）

### 2.2 目录结构
```
backend/
├── app/
│   ├── routers/
│   │   └── teacher.py          # 扩展现有教师路由
│   ├── services/
│   │   ├── github_service.py   # GitHub API集成
│   │   └── report_service.py   # 报告生成服务
│   ├── models/
│   │   └── report_models.py    # Pydantic数据模型
│   ├── templates/
│   │   └── report_template.html # 报告HTML模板
│   └── static/
│       └── teacher.html         # 扩展现有前端
├── database.py                  # 扩展数据库表
└── requirements.txt             # 新增依赖
```

---

## 3. 数据模型设计

### 3.1 数据库表扩展

#### 3.1.1 新增表：teacher_comments（教师评语）
```sql
CREATE TABLE IF NOT EXISTS teacher_comments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  TEXT NOT NULL,
    comment     TEXT NOT NULL,
    teacher     TEXT DEFAULT 'teacher',
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(student_id)
);
```

#### 3.1.2 新增表：student_github_info（学生GitHub信息）
```sql
CREATE TABLE IF NOT EXISTS student_github_info (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT UNIQUE NOT NULL,
    github_username TEXT DEFAULT '',
    repo_name       TEXT DEFAULT '',
    github_token    TEXT DEFAULT '',  -- 教师配置的GitHub Token
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);
```

#### 3.1.3 新增表：audit_logs（审计日志）
```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    action       TEXT NOT NULL,       -- 'export_report', 'view_report', etc.
    operator     TEXT DEFAULT 'teacher',
    target_type  TEXT NOT NULL,       -- 'student', 'class'
    target_id    TEXT,                -- student_id or class_name
    format       TEXT,                 -- 'pdf', 'html', 'excel'
    ip_address   TEXT,
    user_agent   TEXT,
    created_at   TEXT DEFAULT (datetime('now','localtime'))
);
```

#### 3.1.4 新增表：course_settings（课程设置）
```sql
CREATE TABLE IF NOT EXISTS course_settings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT UNIQUE NOT NULL,
    value       TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);
-- 初始数据：
-- ('course_name', '研究生课程《机器人系统》')
-- ('semester', '2024-2025学年第一学期')
```

#### 3.1.5 新增表：attendance（考勤记录）
```sql
CREATE TABLE IF NOT EXISTS attendance (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,
    date         TEXT NOT NULL,
    status       TEXT NOT NULL,  -- 'present', 'absent', 'late', 'leave'
    note         TEXT DEFAULT '',
    created_at   TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(student_id, date)
);
```

---

## 4. 九维度数据结构

### 4.1 维度定义

| # | 维度名称 | 数据来源 | 字段说明 |
|---|---------|---------|---------|
| 1 | 分支记录 | GitHub API | branch_name, created_at, last_commit |
| 2 | 提交历史 | GitHub API | commit_hash, message, author, date, additions, deletions |
| 3 | 代码质量 | GitHub API | languages, total_lines, file_count |
| 4 | PR情况 | GitHub API | pr_number, title, state, created_at, merged_at |
| 5 | PR分析 | GitHub API + 本地 | pr_stats, avg_review_time, merge_rate |
| 6 | 教师评语 | 本地数据库 | comments, created_at, updated_at |
| 7 | 在线考试 | 本地数据库 | exam_records from scores table |
| 8 | 考勤记录 | 本地数据库 | attendance records |
| 9 | 课程得分 | 本地数据库 | total_score, exam_scores, avg_score |

### 4.2 ReportData 数据模型

```python
class ReportData(BaseModel):
    # 学生基础信息
    student_info: StudentInfo
    
    # 维度1：分支记录
    branches: List[BranchRecord]
    
    # 维度2：提交历史
    commits: List[CommitRecord]
    
    # 维度3：代码质量
    code_quality: CodeQualityStats
    
    # 维度4：PR情况
    pull_requests: List[PRRecord]
    
    # 维度5：PR分析统计
    pr_analysis: PRAnalysis
    
    # 维度6：教师评语
    teacher_comments: List[TeacherComment]
    
    # 维度7：在线考试成绩
    exam_scores: List[ExamScoreRecord]
    
    # 维度8：考勤记录
    attendance_records: List[AttendanceRecord]
    
    # 维度9：综合得分
    course_summary: CourseSummary
    
    # 元数据
    generated_at: datetime
    semester: str
    course_name: str
```

---

## 5. API 接口设计

### 5.1 新增API端点

#### 5.1.1 获取学生报告数据
```
GET /api/teacher/report/student/{student_id}
Query Parameters:
  - refresh: bool (default: false)  # 是否强制刷新GitHub数据
Response: ReportData (JSON)
```

#### 5.1.2 导出报告
```
GET /api/teacher/report/export
Query Parameters:
  - student_id: str (required)
  - format: str (required)  # 'pdf', 'html', 'excel'
  - refresh: bool (default: false)
Response: File (StreamingResponse)
```

#### 5.1.3 批量导出
```
POST /api/teacher/report/batch
Body:
{
  "class_name": str,
  "format": str,  # 'pdf', 'html', 'excel'
  "student_ids": List[str]  # 可选，不传则导出整个班级
}
Response: ZIP File (StreamingResponse)
```

#### 5.1.4 获取审计日志
```
GET /api/teacher/report/logs
Query Parameters:
  - page: int (default: 1)
  - page_size: int (default: 20)
  - student_id: str (optional)
  - start_date: str (optional)
  - end_date: str (optional)
Response: PaginatedAuditLogs
```

#### 5.1.5 管理教师评语
```
POST /api/teacher/report/comments
PUT /api/teacher/report/comments/{student_id}
GET /api/teacher/report/comments/{student_id}
DELETE /api/teacher/report/comments/{student_id}
```

#### 5.1.6 管理考勤记录
```
POST /api/teacher/report/attendance
PUT /api/teacher/report/attendance/{student_id}
GET /api/teacher/report/attendance/{student_id}
```

#### 5.1.7 管理学生GitHub信息
```
POST /api/teacher/report/github-info
PUT /api/teacher/report/github-info/{student_id}
GET /api/teacher/report/github-info/{student_id}
```

#### 5.1.8 课程设置
```
GET /api/teacher/report/settings
PUT /api/teacher/report/settings
Body: {"course_name": str, "semester": str}
```

#### 5.1.9 获取班级列表
```
GET /api/teacher/report/classes
Response: List[str]  # 所有班级名称
```

---

## 6. 报告格式设计

### 6.1 PDF报告结构

```
┌─────────────────────────────────────┐
│         [课程LOGO/标题]             │
│                                     │
│  ══════ 学生开发日志报告 ══════      │
│                                     │
│  姓名：张三    学号：20230001        │
│  班级：2023级软工1班                │
│  学期：2024-2025学年第一学期        │
│  生成时间：2024-01-15 10:30        │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                     │
│  📊 一、分支记录 (3个分支)          │
│     • main - 2024-01-10            │
│     • feature/login - 2024-01-12    │
│     • dev/experiment - 2024-01-14  │
│                                     │
│  📝 二、提交历史 (28次提交)         │
│     [时间线图表]                    │
│                                     │
│  💻 三、代码质量                    │
│     总行数: 3,500 | 文件数: 45     │
│     语言分布: Python 60%, JS 30%... │
│                                     │
│  🔀 四、Pull Request (5个PR)       │
│     [PR列表表格]                    │
│                                     │
│  📈 五、PR分析统计                  │
│     合并率: 80% | 平均评审时间: 2天 │
│                                     │
│  💬 六、教师评语                    │
│     "代码规范较好，建议加强测试..." │
│                                     │
│  📋 七、在线考试 (3次考试)          │
│     [成绩单]                        │
│                                     │
│  ✅ 八、考勤记录 (出勤率: 95%)      │
│     [考勤统计]                      │
│                                     │
│  🏆 九、课程总评                    │
│     综合得分: 88分                  │
│     排名: 第5名/32人               │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  报告由系统自动生成                 │
│  成都信息工程大学 软件工程学院       │
└─────────────────────────────────────┘
```

### 6.2 Excel报告结构

使用多个Sheet：
- **封面**: 学生信息汇总
- **分支记录**: 所有分支详情
- **提交历史**: 按时间排序的提交列表
- **代码质量**: 语言统计、文件统计
- **PR情况**: 所有PR列表
- **PR分析**: 统计图表数据
- **教师评语**: 评语历史
- **考试成绩**: 所有考试成绩
- **考勤记录**: 考勤统计
- **综合得分**: 汇总数据

### 6.3 HTML报告

交互式HTML报告，支持：
- 折叠/展开各维度
- 时间线可视化
- 图表展示（使用Chart.js）
- 打印友好样式

---

## 7. 审计日志设计

### 7.1 日志字段
```python
{
    "id": int,
    "action": str,        # 'export_pdf', 'export_html', 'export_excel', 'export_batch', 'view_report'
    "operator": str,      # 'teacher'
    "target_type": str,   # 'student' or 'class'
    "target_id": str,     # student_id or class_name
    "format": str,        # 'pdf', 'html', 'excel', 'zip'
    "ip_address": str,
    "user_agent": str,
    "created_at": str,
    "details": str        # JSON字符串，额外信息
}
```

### 7.2 日志查询
支持按以下条件筛选：
- 时间范围
- 操作类型
- 学生学号
- 班级
- 导出格式

---

## 8. 前端界面设计

### 8.1 新增菜单项
在教师后台导航栏添加：
```
📊 开发日志报告
├── 📄 生成报告
├── 📦 批量导出
├── 💬 教师评语管理
├── ✅ 考勤管理
├── 🔗 GitHub信息管理
├── ⚙️ 课程设置
└── 📋 审计日志
```

### 8.2 生成报告页面
- 学生搜索/选择器
- 报告预览（实时数据）
- 导出格式选择（PDF/HTML/Excel）
- 刷新数据按钮
- 导出按钮

### 8.3 批量导出页面
- 班级选择下拉框
- 学生列表勾选
- 全选/反选
- 导出格式选择
- 批量导出按钮（下载ZIP）

### 8.4 审计日志页面
- 筛选条件表单
- 日志列表表格
- 分页控件
- 导出日志按钮（Excel）

---

## 9. GitHub API集成

### 9.1 认证方式
使用Personal Access Token (PAT)进行认证：
- 存储在环境变量或数据库
- 支持多个仓库配置

### 9.2 API调用限制
- 使用httpx异步客户端
- 实现请求缓存（5分钟TTL）
- 错误重试机制（最多3次）
- 速率限制处理

### 9.3 获取的数据
```python
# 分支列表
GET /repos/{owner}/{repo}/branches

# 提交历史
GET /repos/{owner}/{repo}/commits

# PR列表
GET /repos/{owner}/{repo}/pulls

# 仓库语言统计
GET /repos/{owner}/{repo}/languages

# 提交详情
GET /repos/{owner}/{repo}/commits/{sha}
```

---

## 10. 配置项

### 10.1 环境变量
```bash
GITHUB_TOKEN=ghp_xxxxx          # GitHub访问令牌
GITHUB_API_BASE=https://api.github.com
REPORT_CACHE_TTL=300            # 缓存过期时间（秒）
MAX_EXPORT_STUDENTS=100         # 单次批量导出最大人数
```

### 10.2 数据库配置
```sql
-- 课程设置初始数据
INSERT INTO course_settings (key, value) VALUES 
    ('course_name', '研究生课程《机器人系统》'),
    ('semester', '2024-2025学年第一学期'),
    ('github_token', '');
```

---

## 11. 错误处理

### 11.1 错误码定义
| 错误码 | 说明 | HTTP状态 |
|-------|------|---------|
| 1001 | 学生不存在 | 404 |
| 1002 | GitHub仓库不存在 | 404 |
| 1003 | GitHub API调用失败 | 502 |
| 1004 | 导出格式不支持 | 400 |
| 1005 | 批量导出人数超限 | 400 |
| 1006 | 数据库操作失败 | 500 |

### 11.2 降级策略
- GitHub API不可用时，显示"数据获取失败"占位
- 部分维度数据缺失时，其他维度正常显示
- 导出失败时返回错误信息而非空白文件

---

## 12. 性能优化

### 12.1 缓存策略
- GitHub API响应缓存：5分钟
- 学生报告数据缓存：5分钟
- 班级列表缓存：10分钟

### 12.2 异步处理
- 大批量导出使用后台任务
- 提供任务进度查询接口
- 支持邮件通知完成

### 12.3 数据库优化
- 为常用查询添加索引
- 使用WAL模式提升并发性能

---

## 13. 安全性

### 13.1 认证授权
- 所有接口需要教师Token验证
- GitHub Token加密存储
- 敏感操作记录审计日志

### 13.2 数据保护
- 学生敏感信息脱敏处理
- 导出文件添加水印
- 下载链接时效限制

### 13.3 输入验证
- 学生ID格式验证
- GitHub仓库名格式验证
- SQL注入防护

---

## 14. 部署说明

### 14.1 依赖安装
```bash
pip install reportlab weasyprint httpx jinja2
```

### 14.2 数据库迁移
首次部署时自动创建新表。

### 14.3 配置检查
启动时检查必要配置项，缺失时提示警告。
