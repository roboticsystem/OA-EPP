# 开发说明

## 一、项目结构

### OA-EPP 仓库包含两个独立项目

```
OA-EPP/
├── oaepp/         ← Reflex 项目（全部源代码在此目录下）
│   ├── app.py         # 路由注册中心
│   ├── rxconfig.py    # Reflex 配置
│   ├── pages/         # 页面组件（如 login.py）
│   └── requirements.txt
│
├── backend/       ← 另一个 MkDocs 网站的后端，与 Reflex 项目无关
├── docs/          ← MkDocs 文档源文件
└── (其余均为 MkDocs 网站相关的内容)
```

**核心要点：**

- 两个项目虽然在同一仓库下，但代码上完全独立，互不依赖。
- 所有 Reflex 源代码均在 `oaepp/` 目录下。
- `backend/` 是 MkDocs 网站的后端，与 Reflex 项目无关。
- 后续所有关于 Reflex 的讨论、分析和开发均限定在 `oaepp/` 目录内。
- **不要去修改 `/backend` 目录下的文件！**

---

## 二、标准路由添加方式

### 涉及两个文件

| Step | 文件 | 操作 |
|---|---|---|
| 1 | **[`oaepp/pages/`](oaepp/pages/)** 下新建 `.py` 文件 | 编写页面组件（遵循 `login.py` 的模式） |
| 2 | **[`oaepp/app.py`](oaepp/app.py)** | 用 `app.add_page()` 注册路由 |

### 文件命名规范（重要）

**功能文件命名必须与 `/prototype` 目录下的快速原型文件命名一致。**

例如：
- 原型文件为 `editor.html` → 功能文件命名为 `editor.py`
- 原型文件为 `grades.html` → 功能文件命名为 `grades.py`
- 原型文件为 `attendance.html` → 功能文件命名为 `attendance.py`

**禁止**在 `backend/` 目录下创建或修改任何文件（包括 API 路由、静态页面等），这些均由负责人统一维护。

### 具体步骤

**Step 1 — 新建页面文件** `oaepp/pages/dashboard.py`：

```python
try:
    import reflex as rx
except Exception:
    rx = None
dashboard_page = None
if rx is not None:
    def dashboard_page():
        return rx.container(
            rx.heading("仪表盘"),
            rx.text("内容"),
        )
```

**Step 2 — 在 `app.py` 中注册路由**：

```python
try:
    from pages import dashboard as dashboard_mod
except Exception:
    try:
        from oaepp.pages import dashboard as dashboard_mod
    except Exception:
        dashboard_mod = None
if app is not None and dashboard_mod is not None:
    if hasattr(dashboard_mod, "dashboard_page") and callable(getattr(dashboard_mod, "dashboard_page")):
        app.add_page(dashboard_mod.dashboard_page, route="/dashboard")
```

这就是目前项目中**唯一的标准路由添加方式**——Reflex 页面组件放在 `pages/`，路由注册集中在 `app.py`。

---

## 三、测试方式

### reflex run 热启动

在 `oaepp/` 目录下执行：

```bash
cd oaepp/
reflex run
```

Reflex 自带热重载——修改 `pages/` 下的文件或 `app.py` 后，保存文件即自动刷新，无需手动重启。

### 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| 页面空白或 404 | 路由注册时 `route` 参数拼写错误 | 检查 `app.add_page(..., route="/dashboard")` 中的路径 |
| 模块导入错误 | `app.py` 中 `from pages import dashboard` 失败 | 确认 `oaepp/pages/dashboard.py` 文件存在且语法正确 |
| 浏览器访问 localhost:3000 失败 | Reflex 端口被占用或未启动成功 | 检查终端日志，尝试 `reflex run --backend-port 8002 --frontend-port 3001` |
| 页面渲染但样式错乱 | Reflex 版本兼容问题 | 确认 `requirements.txt` 中 `reflex==0.9.4` 已安装 |

---

## 四、全局资源说明

Reflex 是**全栈 Python Web 框架**，前端状态 + 后端服务 + 配置全部统一管理，和数据库一样，**全局资源是唯一的、共享的**。

### 1. 全局状态（Global State）—— 最重要的共享资源

Reflex 自带**应用级全局状态**，所有页面、所有组件、所有同学写的功能都能访问/修改。

典型共享场景：

- 当前登录用户信息（`user`）
- 全局主题、语言、配置
- 全局加载状态、通知消息
- 全局权限、角色

```python
# rxconfig.py 或 state.py 中，全团队共享的全局状态
class GlobalState(rx.State):
    # 所有同学功能都要用的登录用户
    current_user: dict = {}
    # 全局加载状态
    is_loading: bool = False
    # 全局消息提示
    toast_message: str = ""
```

✅ **任何同学的功能都可能读取/修改这个状态**，必须统一管理。

### 2. 全局变量 / 全局常量

硬编码、配置类的共享变量，比如：

- 数据库连接配置（已统一）
- API 地址、超时时间
- 分页大小、文件上传限制
- 业务固定枚举（性别、状态、角色）

```python
# constants.py 全团队共享
PAGE_SIZE = 10
UPLOAD_LIMIT_MB = 10
USER_ROLES = ["student", "teacher", "admin"]
```

### 3. 全局工具函数 / 单例服务

工具函数只会初始化**一次**，全项目共用：

- 数据验证（学号、邮箱、GitHub 用户名）
- 得分格式化
- 文件名清理
- PR Preview URL 生成

```python
# 使用方式：从 utils 导入
from utils.helpers import validate_student_no, generate_preview_url

if validate_student_no("2021001"):
    print("学号格式正确")

url = generate_preview_url(118, "/grades")
# 结果：https://118.oaepp-reflex.uwis.cn/grades
```

### 4. 预置公共文件说明

项目 `/oaepp/` 目录下已预置以下公共文件，学生功能模块可直接使用：

| 文件路径 | 用途 | 学生可操作 |
|----------|------|-----------|
| `states/__init__.py` | 全局状态基类 `GlobalState` | ✅ 继承使用 |
| `states/deadline.py` | 截止规则状态（F-S-022） | ✅ 参考使用 |
| `constants.py` | 全局常量（分页、角色、枚举等） | ✅ 导入使用 |
| `utils/helpers.py` | 通用工具函数 | ✅ 导入使用 |
| `routes.json` | 功能路由映射表 | ✅ 查阅参考 |

**学生使用示例**：

```python
# pages/dashboard.py
try:
    import reflex as rx
except Exception:
    rx = None

# 继承全局状态基类
from states import GlobalState

# 导入全局常量
from constants import PAGE_SIZE

class DashboardState(GlobalState):
    """课程主页状态"""
    courses: list = []
    
    def load_courses(self):
        """加载课程列表"""
        self.is_loading = True
        # 使用全局常量
        page_size = PAGE_SIZE
        # ...
```
- 缓存工具
- 认证、权限校验函数

```python
# utils/db.py 全局数据库工具
def get_user_by_id(user_id: int):
    # 所有同学调用同一个函数
    ...
```

### 4. 路由注册（全局路由表）

Reflex 的路由表是**全局唯一**的：

```python
# 所有同学的页面都在这里注册，不能冲突
app.add_page(student1.page, route="/func1")
app.add_page(student2.page, route="/func2")
```

---

## 五、43 人协作规范

### 核心原则

**全局资源统一维护 + 个人功能隔离 + 合并前必须检查 + 禁止直接改主分支**

---

### 1. 架构划分 —— 从根源隔离功能

43 人，每人一个功能，必须做**目录隔离**，**只允许修改自己的目录**，全局文件统一由负责人维护。

#### 推荐 `/oaepp` 项目结构

```
/oaepp
├── /oaepp              # 主包
│   ├── state.py        # ✅ 全局状态（专人维护，禁止普通同学修改）
│   ├── constants.py    # ✅ 全局常量（专人维护）
│   ├── utils/          # ✅ 全局工具（专人维护）
│   ├── db.py           # ✅ 数据库（专人维护）
│   ├── pages/          # 公共页面
│   └── features/       # 🚀 所有同学功能在这里，一人一个子目录
│       ├── feature_01/  # 同学1
│       ├── feature_02/  # 同学2
│       └── ...
└── rxconfig.py         # ✅ 配置文件（专人维护）
```

#### 权限规则（必须遵守）

1. **普通同学**
   - 只能修改 `/features/自己的文件夹` 内代码
   - **只能读取**全局状态/工具，**禁止直接修改** `state.py`/`constants.py`
2. **全局负责人（课代表/老师）**
   - 维护所有全局文件
   - 审核所有 PR
   - 统一合并代码

---

### 2. 全局状态的安全协作规则

全局状态是**共享资源**，不能谁都改，否则功能会互相干扰。

#### （1）全局状态只提供"读"权限

所有同学**只能读取**全局状态（如当前用户）：

```python
# 你的功能里，正确用法：读取全局状态
def my_feature():
    if rx.State.current_user:
        return rx.text(f"欢迎 {rx.State.current_user['name']}")
```

#### （2）修改全局状态必须通过"方法"，禁止直接赋值

❌ 禁止：

```python
# 错误！直接修改全局状态，会造成冲突
rx.State.current_user = {}
```

✅ 正确：

全局状态里**提前写好方法**，同学只能调用：

```python
# state.py 由负责人维护
class GlobalState(rx.State):
    current_user: dict = {}

    # 唯一允许修改用户的方法
    def set_user(self, user):
        self.current_user = user
```

同学在自己功能里**调用**，不直接改：

```python
# 你的代码
GlobalState.set_user(new_user)
```

#### （3）全局变量/常量禁止覆盖、禁止重复定义

- 所有常量统一放在 `constants.py`
- 同学**只能导入使用**，不能重新定义同名变量
- 工具函数、数据库接口**只能调用，不能重写**

---

### 3. Git + PR 协作流程（43 人标准流程）

这是班级项目**不崩、不冲突、能顺利合并**的核心流程。

#### （1）分支规范（简单好记）

- `main`：主分支，永远稳定，**任何人不能直接提交**
- `dev`：开发分支，用于合并所有功能
- **每个人自己的分支**：`feature/学号-功能名`

例子：

```
feature/2025001-login
feature/2025002-score-query
```

#### （2）开发流程（每个人都必须遵守）

1. **从 dev 拉取最新代码**

   ```bash
   git checkout dev
   git pull
   ```

2. **创建自己的功能分支**

   ```bash
   git checkout -b feature/xxx
   ```

3. **只写自己的功能**，不碰全局文件
4. **本地测试无问题**再提交
5. **提交到远程**
6. **提交 PR：请求合并到 dev 分支**

#### （3）PR 合并规则（老师/负责人执行）

1. **必须检查**：是否修改了全局文件（`state.py`/`constants.py`/`utils`）
   - 普通同学修改 → **直接打回**
2. **检查是否有变量名冲突**
3. **检查路由是否重复**
4. **检查是否直接修改全局状态**
5. 无问题 → **合并**
6. 有问题 → **评论打回**，同学修改后重新提交

#### （4）冲突解决

如果出现合并冲突（极少，因为目录隔离）：

- 只解决**自己文件**的冲突
- 全局文件冲突由**负责人**解决
- 禁止强行覆盖他人代码

---

## 六、铁律（直接发给班级用）

1. **一人一个文件夹，绝不越界**
2. **全局状态只能读，不能直接改**
3. **全局变量、工具、路由统一维护**
4. **绝不直接 push 到 main/dev，必须提 PR**
5. **修改全局文件必须由负责人审批**

遵守这 5 条，43 人开发完全不会互相干扰，和共用数据库一样安全。

---

## 总结

1. **Reflex 存在全局状态/全局变量**，和统一数据库一样，是全团队共享资源
2. 43 人协作核心：**目录隔离 + 权限控制 + 禁止直接修改全局资源**
3. 协作流程：**功能分支 → 只改自己代码 → 提 PR → 负责人审核合并**
4. 全局状态必须通过**方法调用**修改，不能直接赋值
