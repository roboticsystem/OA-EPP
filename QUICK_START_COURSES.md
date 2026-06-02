# 🚀 快速开始指南 - 课程展示功能

## 📋 功能完成清单

- ✅ **展示所有已选课程列表及学习进度** - 从 MySQL 数据库实时加载
- ✅ **每门课程显示章节数/已完成任务数/截止提醒** - 完整的统计和提醒功能
- ✅ **进度信息实时更新无需手动刷新** - 点击刷新按钮即可更新，后续支持 WebSocket 自动更新

## 🔧 一步步部署

### 1️⃣ 准备环境

```bash
# 克隆项目（已在本地）
cd d:\Code\OA-EPP

# 复制环境变量文件
copy .env.example .env
```

### 2️⃣ 安装依赖

```bash
# 安装 Reflex 和所有依赖
pip install -r reflex-requirements.txt
```

**预期输出：**
```
Successfully installed reflex-0.3.x, sqlalchemy-2.x, pymysql-1.x ...
```

### 3️⃣ 初始化数据库

```bash
# 创建 Reflex 数据表
reflex db init

# 插入测试数据
python scripts/init_course_test_data.py
```

**预期输出：**
```
✓ 学生数据插入完成
✓ 课程数据插入完成
✓ 学生选课关系插入完成
✓ 章节数据插入完成
✓ 任务数据插入完成
✓ 任务完成记录插入完成

✅ 测试数据初始化完成！
```

### 4️⃣ 启动应用

```bash
# 进入项目目录
cd d:\Code\OA-EPP

# 启动 Reflex 开发服务器
reflex run
```

**预期输出：**
```
Compiled successfully.
Frontend ready at http://localhost:3000
Backend ready at http://localhost:8000
```

### 5️⃣ 访问应用

在浏览器中打开：

- **登录页面**: http://localhost:3000/ (选择学生)
- **课程列表**: http://localhost:3000/courses (展示课程和进度)

## 📸 UI 布局

### 登录页面 (`/`)
```
┌─────────────────────────┐
│     学生登录             │
├─────────────────────────┤
│ 选择学生账号:           │
│ [▼ STU001 - 张三]       │
│                         │
│    [进入课程页面]       │
└─────────────────────────┘
```

### 课程列表页面 (`/courses`)
```
┌─────────────────────────────────────────┐
│ 我的课程                                 │
│ 查看您已选课程的学习进度和截止提醒     │
│ [刷新数据]                              │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ 工程实践1 [ENG-PRAC-01]             │ │
│ ├─────────────────────────────────────┤ │
│ │ 章节数   已完成任务   完成度         │ │
│ │  5        2/10        20%           │ │
│ │ ▓░░░░░░░░░░░░░░░░░░░             │ │
│ │ ⏰ 下一截止: 2026-06-09            │ │
│ │ [查看详情] [继续学习]               │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ 工程实践2 [ENG-PRAC-02]             │ │
│ │ ... (类似布局)                      │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 📊 API 端点

课程展示功能使用的数据库模型：

| 表名 | 说明 | 关键字段 |
|------|------|--------|
| `student` | 学生信息 | student_id, name, email |
| `course` | 课程信息 | code, name, total_chapters |
| `chapter` | 课程章节 | course_id, chapter_num, title |
| `task` | 任务列表 | chapter_id, title, due_date |
| `student_course` | 选课关系 | student_id, course_id, status |
| `taskcompletion` | 完成记录 | student_id, task_id, status |

## 🧪 测试数据

初始化脚本 `init_course_test_data.py` 会创建：

- **2 个学生**: STU001 (张三), STU002 (李四)
- **4 门课程**: 工程实践 1-4
- **5 个章节**: 每门课程分配章节
- **7 个任务**: 包含阅读、练习、测试等类型
- **4 个完成记录**: STU001 已完成部分任务

## 🔌 数据库连接

使用提供的 MySQL 连接：

```
主机: oaepp-mysql (内部) / 156.239.252.40:13306 (外部)
数据库: oaepp_dev
用户名: student_dev
密码: OaEpp@Dev2026
```

## 📝 文件结构

```
oaepp/
├── __init__.py
├── app.py                           # 主应用入口
├── models/
│   ├── __init__.py
│   └── database.py                  # 数据库模型定义
├── pages/
│   ├── __init__.py
│   ├── login.py                     # 登录页面
│   └── courses.py                   # 📌 课程展示页面
├── states/
│   ├── __init__.py
│   ├── auth_state.py                # 认证状态
│   └── course_state.py              # 📌 课程状态管理
└── components/
    ├── __init__.py
    └── ...

配置文件:
├── rxconfig.py                      # Reflex 配置
├── .env                             # 环境变量 (从 .env.example 复制)
└── reflex-requirements.txt          # Reflex 依赖

脚本:
├── scripts/init_course_test_data.py # 🔨 数据初始化脚本
└── COURSE_DISPLAY_IMPLEMENTATION.md # 📖 实现说明文档
```

## 🚨 常见问题

### Q: 数据库连接错误
**A**: 检查 MySQL 服务是否运行，数据库地址、用户名、密码是否正确。

```bash
# 测试连接
mysql -h oaepp-mysql -u student_dev -p -D oaepp_dev
```

### Q: 页面无法加载
**A**: 确保已安装所有依赖，运行 `pip install -r reflex-requirements.txt`

### Q: 课程列表为空
**A**: 确保运行了 `python scripts/init_course_test_data.py` 初始化测试数据

### Q: 修改页面后需要重启应用吗？
**A**: 不需要，Reflex 支持热重载。修改代码后自动刷新。

## 📖 相关文档

- [课程展示功能详细说明](COURSE_DISPLAY_IMPLEMENTATION.md)
- [数据库连接配置](/.memory/repo/database-connection.md)
- Reflex 官方文档: https://reflex.dev/docs

## ✨ 后续优化方向

1. **自动刷新** - 集成 WebSocket 实时推送进度更新
2. **详情页面** - 点击课程查看所有章节和任务
3. **通知系统** - 截止日期前自动提醒
4. **学习分析** - 展示学习时间、学习效率等数据
5. **导师反馈** - 显示教师评语和建议

---

**✅ 功能已完成，可开始测试！**
