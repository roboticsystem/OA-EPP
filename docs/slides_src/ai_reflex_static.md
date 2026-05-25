---
marp: true
theme: default
paginate: true
header: '工程实践4 · AI 驱动 Reflex 静态页面生成'
footer: '成都信息工程大学 软件工程学院 · 2025'
style: |
  section {
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;
    font-size: 22px;
    padding: 40px 60px;
    background: #ffffff;
    color: #1a1a2e;
  }
  section.title-slide {
    background: linear-gradient(135deg, #312e81 0%, #4f46e5 60%, #7c3aed 100%);
    color: white;
    text-align: center;
    justify-content: center;
  }
  section.title-slide h1 {
    font-size: 2.2em;
    font-weight: 800;
    margin-bottom: 0.3em;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  section.title-slide p {
    font-size: 1.1em;
    opacity: 0.85;
  }
  section.section-title {
    background: #f0f0ff;
    border-left: 8px solid #4f46e5;
    display: flex;
    align-items: center;
  }
  section.section-title h2 {
    font-size: 2em;
    color: #312e81;
    font-weight: 700;
  }
  h1 { color: #312e81; border-bottom: 3px solid #4f46e5; padding-bottom: 0.3em; }
  h2 { color: #4f46e5; margin-top: 0; }
  h3 { color: #7c3aed; }
  code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.88em; color: #be185d; }
  pre { background: #1e1e2e !important; border-radius: 8px; padding: 1.2em !important; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
  pre code { background: transparent; color: #cdd6f4; font-size: 0.8em; padding: 0; }
  table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 0.9em; }
  th { background: #4f46e5; color: white; padding: 0.5em 0.8em; text-align: left; }
  td { padding: 0.4em 0.8em; border-bottom: 1px solid #e5e7eb; }
  tr:nth-child(even) td { background: #f9fafb; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.78em; font-weight: 600; }
  .tag-blue { background: #dbeafe; color: #1d4ed8; }
  .tag-green { background: #d1fae5; color: #065f46; }
  .tag-orange { background: #ffedd5; color: #9a3412; }
  .tag-purple { background: #ede9fe; color: #5b21b6; }
  blockquote { border-left: 4px solid #4f46e5; background: #eef2ff; padding: 0.8em 1.2em; margin: 1em 0; border-radius: 0 8px 8px 0; color: #374151; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5em; margin-top: 1em; }
  .card { background: #f8faff; border: 1px solid #c7d2fe; border-radius: 10px; padding: 1em 1.2em; }
  .card h3 { margin-top: 0; font-size: 1em; }
  .highlight-box { background: #fef3c7; border: 1px solid #fbbf24; border-radius: 8px; padding: 0.8em 1.2em; margin: 1em 0; }
  header { font-size: 0.7em; color: #6b7280; }
  footer { font-size: 0.7em; color: #6b7280; }
  section::after { font-size: 0.7em; color: #9ca3af; }
---

<!-- _class: title-slide -->
<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: false -->

# 🤖 AI 驱动 Reflex 静态页面生成

## 从需求描述到 Python 全栈应用的完整构建流程

---

工程实践4 · 第12讲 &emsp;|&emsp; 2025 春季学期

---

## 目录

<div class="grid-2">
<div>

**Part 1：基础概念**

1. Reflex 是什么
2. 技术选型对比（vs Vaadin / Spring Boot+Vue）
3. Reflex 架构剖析
4. 静态导出 vs 动态运行

</div>
<div>

**Part 2：AI 协作流程**

4. AI 生成 Reflex 页面的方法论
5. Copilot 指令规范
6. 典型代码示例

**Part 3：构建与部署**

7. `reflex export` 完整流程
8. Docker 多阶段构建
9. Nginx 静态服务与 CI/CD

</div>
</div>

---

<!-- _class: section-title -->
<!-- _paginate: false -->

## Part 1 &nbsp;·&nbsp; 基础概念

---

## Reflex 是什么？

> **Reflex** 是一个纯 Python 全栈框架，让你无需编写 HTML/CSS/JavaScript，仅用 Python 即可构建交互式 Web 应用。

<div class="grid-2">
<div class="card">

### 🐍 纯 Python 开发
```python
import reflex as rx

def index():
    return rx.text(
        "Hello, World!",
        color="indigo",
        font_size="2em",
    )
```

</div>
<div class="card">

### ⚡ 编译为 React 前端
- Python 组件 → React 组件
- Python 状态 → WebSocket 同步
- 自动处理 hydration
- 内置 Tailwind CSS

</div>
</div>

<div class="highlight-box">

🎯 **本课程使用场景**：OA-EPP 平台（课程管理 + 成绩分析 + GitHub 工作流集成）

</div>

---

## 技术选型对比：Reflex vs Vaadin vs Spring Boot + Vue

| 维度 | **Reflex** | Vaadin | Spring Boot + Vue |
|------|-----------|--------|-------------------|
| **开发语言** | 纯 Python | Java（+ HTML/CSS 可选） | Java 后端 + JS/TS 前端 |
| **学习门槛** | 🟢 低（Python 入门友好） | 🟡 中（需 Java OOP） | 🔴 高（双语言双框架）|
| **前后端分离** | 一体（Python 写全部 UI） | 一体（Java 描述 UI） | 分离（两套独立项目）|
| **AI 代码生成** | 🟢 优（Python 训练数据最多） | 🟡 中（Java 冗长）| 🟡 中（需维护两端）|
| **静态导出** | ✅ `reflex export` | ❌ 依赖 JVM 运行时 | ⚠️ Vue 可静态，后端仍需 JVM |
| **部署镜像体积** | **~25 MB**（Nginx）| ~500 MB+（JVM + JRE）| ~200 MB（JVM + Node）|
| **原型→产品衔接** | ✅ 无缝（同一套代码）| ⚠️ 需重构 | ⚠️ 前后端分别重构 |
| **课程适配度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

<div class="highlight-box">

🏆 **选择 Reflex 的四大理由**：
① **一人全栈**——学生只需掌握 Python，无需同时学 Java + JS/TS 两套体系；
② **AI 友好**——Python 代码在 LLM 训练集中占比最高，生成质量更稳定；
③ **轻量部署**——静态导出后 Nginx 镜像仅 25MB，显著优于 JVM 方案；
④ **原型无缝升级**——`prototype/*.html` → `reflex export` → `reflex run`，同一套设计，三阶段递进，无需重写。

</div>

---

## Reflex 架构剖析

```
┌──────────────────────────────────────────────────────────────────┐
│                        开发者（Python）                           │
│   rx.State  +  rx.Component  →  app.compile()                    │
└──────────────────┬───────────────────────────────────────────────┘
                   │ reflex run / reflex export
         ┌─────────▼─────────┐
         │   Reflex 编译器    │
         │  Python → Next.js │   .web/ 目录（临时构建产物）
         └─────────┬─────────┘
                   │
        ┌──────────▼──────────────────────────────┐
        │           运行模式选择                    │
        │                                          │
        │  ① reflex run       ② reflex export      │
        │    动态模式             静态导出模式       │
        │  FastAPI后端          纯静态 HTML/JS/CSS  │
        │  WebSocket 同步        无需后端进程        │
        │  支持 State 变更        适合无状态页面      │
        └─────────────────────────────────────────┘
```

---

## 静态导出 vs 动态运行

| 对比项 | `reflex run`（动态） | `reflex export`（静态） |
|--------|---------------------|------------------------|
| **后端进程** | 需要 FastAPI 持续运行 | ❌ 不需要 |
| **WebSocket** | ✅ 实时双向通信 | ❌ 无 |
| **State 更新** | ✅ 完整支持 | ⚠️ 仅初始状态 |
| **部署复杂度** | 中（需管理进程） | 低（Nginx 直接伺服） |
| **适用场景** | 交互式仪表盘、表单 | 展示型页面、文档、原型 |
| **本课程原型** | 最终产品 | **当前阶段（原型验证）** |

<div class="highlight-box">

📌 **本讲重点**：用 `reflex export --no-zip` 生成静态资源包，配合 Nginx 零成本部署原型演示站

</div>

---

<!-- _class: section-title -->
<!-- _paginate: false -->

## Part 2 &nbsp;·&nbsp; AI 协作流程

---

## AI 生成 Reflex 页面的方法论

**三步工作法：描述 → 生成 → 约束**

```
1. 写需求描述（自然语言）
        ↓
2. AI 生成 Reflex Python 代码
        ↓
3. 用约束文件（copilot-instructions.md）保证代码风格统一
```

<div class="grid-2">
<div class="card">

### ✅ 好的需求描述
```
帮我创建一个 Reflex 页面，
显示学生成绩统计卡片：
- 左侧：班级平均分（大字体）
- 右侧：成绩分布饼图
- 颜色：indigo 系
- 使用 rx.flex 布局
```

</div>
<div class="card">

### ❌ 不好的描述
```
帮我做一个成绩页面
（太模糊，AI 会猜测框架、
样式、布局，容易不符合
项目已有规范）
```

</div>
</div>

---

## Copilot 指令规范（copilot-instructions.md）

项目根目录的 `.github/copilot-instructions.md` 控制 AI 输出风格：

```markdown
# 技术栈约束

## 前端
- 框架：Reflex（纯 Python，禁止直接写 HTML/CSS/JS）
- 样式：Tailwind CSS v3（通过 rx 组件的 class_name 参数传入）
- 图标：rx.icon()，Lucide 图标库
- 布局：优先使用 rx.flex、rx.grid，避免裸 div

## 命名规范
- State 类：PascalCase，继承 rx.State
- 页面函数：snake_case，返回 rx.Component
- 事件处理器：动词开头（handle_submit, toggle_modal）

## 禁止事项
- 禁止使用 JavaScript（含 rx.script）
- 禁止内联样式（style= 参数）
- 禁止 rx.html()（除非有正当理由）
```

---

## 典型 Reflex 页面结构

```python
import reflex as rx
from ..components.navbar import navbar  # 公共导航栏

# ① 状态类（数据 + 事件）
class GradeState(rx.State):
    avg_score: float = 87.5
    score_dist: list[dict] = [
        {"grade": "A", "count": 8},
        {"grade": "B", "count": 14},
        {"grade": "C", "count": 7},
    ]

    def refresh(self):   # 事件处理器
        """从后端拉取最新成绩数据"""
        pass  # 接入 API 时实现

# ② 子组件
def score_card(label: str, value: rx.Var) -> rx.Component:
    return rx.box(
        rx.text(label, color="gray", font_size="sm"),
        rx.text(value, font_size="3xl", font_weight="bold",
                color="indigo"),
        class_name="p-6 bg-white rounded-xl shadow-sm",
    )

# ③ 页面入口函数
def grades_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        score_card("班级平均分", GradeState.avg_score),
        spacing="4",
        padding="6",
    )
```

---

## AI 生成流程实战演示

**提示词模板（复制即用）**：

```
请用 Reflex 框架（Python）创建一个【页面名称】页面。

技术要求：
- 遵循 .github/copilot-instructions.md 规范
- 布局：三段式（顶部导航 + 左侧边栏 w-56 + 右侧主内容 flex-1）
- 配色：indigo-700/600（教师端）或 blue-600/500（学生端）
- 禁用 JavaScript，禁用内联样式

页面内容：
【在此描述你需要的 UI 元素、数据字段、交互行为】

参考文件：
- prototype/【对应原型文件名】.html（UI 原型参考）
- backend/models.py（数据模型参考）
```

<div class="highlight-box">

💡 **关键**：将 `prototype/*.html` 作为「1:1 目标」给 AI，让 AI 对照原型用 Reflex 重写，准确率显著提升

</div>

---

<!-- _class: section-title -->
<!-- _paginate: false -->

## Part 3 &nbsp;·&nbsp; 构建与部署

---

## `reflex export` 完整流程

```bash
# 在项目根目录执行
reflex export --no-zip
```

**内部执行步骤**：

```
Step 1: 收集所有 pages/*.py 中的页面函数
         ↓
Step 2: 生成 Next.js 项目到 .web/ 目录
         ↓
Step 3: 执行 next build（编译 React 组件）
         ↓
Step 4: 执行 next export（输出静态 HTML/JS/CSS）
         ↓
Step 5: 将产物复制到 .web/out/ 目录
```

**产物结构**：
```
.web/out/
├── index.html          # 首页
├── _next/
│   ├── static/css/     # 样式文件（Hash 命名）
│   └── static/chunks/  # JS 代码块（按路由分割）
└── dashboard/
    └── index.html      # /dashboard 路由页面
```

---

## Docker 多阶段构建集成

```dockerfile
# ── Stage 1: 构建 ──────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app

# 安装系统依赖（Node.js 用于 Reflex 前端编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 核心步骤：生成静态资源
RUN reflex export --no-zip        # 输出到 .web/out/

# ── Stage 2: 运行 ──────────────────────────────────────────
FROM nginx:alpine AS runner

# 只拷贝静态产物，丢弃 Python/Node 环境（镜像体积：~25MB）
COPY --from=builder /app/.web/out /usr/share/nginx/html

# 自定义 Nginx 配置（SPA 路由支持）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**镜像体积对比**：

| 方案 | 镜像大小 |
|------|---------|
| 单阶段（含 Python + Node） | ~1.2 GB |
| **多阶段构建（仅 Nginx）** | **~25 MB** |

---

## Nginx 配置：SPA 路由支持

```nginx
# nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # 关键：所有路由回退到 index.html（SPA 路由）
    location / {
        try_files $uri $uri/ $uri.html /index.html;
    }

    # 静态资源强缓存（带 Hash 的文件永久缓存）
    location /_next/static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
}
```

> ⚠️ **`try_files` 的作用**：当用户直接访问 `/dashboard` 时，先找 `/dashboard.html`，找不到则回退到 `index.html` 让前端路由接管

---

## CI/CD 自动化流程

```yaml
# .github/workflows/deploy.yml
name: 构建并部署到 Coolify

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 安装 Python 依赖
        run: pip install -r requirements.txt

      - name: 生成静态资源
        run: reflex export --no-zip   # 核心步骤

      - name: 触发 Coolify 部署
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}" \
            "${{ secrets.COOLIFY_WEBHOOK_URL }}"
```

**自动化链路**：

```
git push main
    → GitHub Actions 触发
    → reflex export --no-zip
    → 静态产物上传
    → Coolify Webhook 触发重新部署
    → Nginx 服务更新
    → 🌐 https://oaepp.uwis.cn 上线新版本
```

---

## 本讲要点总结

<div class="grid-2">
<div>

### 🎯 核心结论

1. **Reflex = Python 全栈**，编译为 React，无需写 HTML/JS

2. **静态导出**（`reflex export`）= 零后端部署，适合原型验证阶段

3. **AI 生成效率**取决于提示词质量：
   - 引用原型文件
   - 引用 `copilot-instructions.md`
   - 描述具体 UI 元素

4. **多阶段 Docker** 将镜像从 1.2GB 压缩到 25MB

</div>
<div>

### 📋 实践检查清单

- [ ] `.github/copilot-instructions.md` 已设置技术栈约束
- [ ] `prototype/` 目录已有对应 HTML 原型
- [ ] `requirements.txt` 包含 `reflex>=0.6`
- [ ] `Dockerfile` 使用多阶段构建
- [ ] `nginx.conf` 配置了 `try_files` SPA 路由
- [ ] CI/CD 中 `reflex export --no-zip` 在正确目录执行

</div>
</div>

---

## 🖥️ 原型预览：VS Code 端口转发 + start_prototype.sh

**核心原则**：`prototype/*.html` 与 Reflex 编译输出 **1:1 完全一致**

> 原型 HTML 仅使用 Reflex 内置组件对应的 HTML 结构 + Tailwind CSS，  
> 因此无需运行 Python，直接用浏览器打开静态 HTML 即可验证 UI 效果。

**一行命令启动预览服务器**：

```bash
bash start_prototype.sh          # 默认端口 8088
# 或指定端口
bash start_prototype.sh 9000
```

脚本自动完成三件事：

| 步骤 | 内容 |
|------|------|
| ① 检查端口占用 | 若 8088 已占用，自动改用 8089 |
| ② 启动静态服务 | `python3 -m http.server 8088 --bind 0.0.0.0` |
| ③ 打印端口转发指引 | 告知 VS Code 端口面板操作路径 |

**VS Code 端口转发（Remote / Codespaces 场景）**：

```
① 终端运行：bash start_prototype.sh
② Ctrl+Shift+P → "Forward a Port" → 输入 8088
③ VS Code 底部「端口」面板 → 点击「在浏览器中打开」🌐
```

<div class="highlight-box">

💡 **开发建议**：先在 `prototype/` 中用纯 HTML + Tailwind 敲定 UI，  
再让 AI 对照原型文件 1:1 翻译为 Reflex Python 代码，效率最高。

</div>

---

<!-- _class: title-slide -->
<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: false -->

# 🙋 Q & A

## 课后练习

用 AI（Copilot）将 `prototype/admin_grades.html`  
重写为一个可运行的 Reflex 页面，  
并用 `reflex export` 导出静态版本。

---

**参考资料**

- Reflex 官方文档：https://reflex.dev/docs
- Marp 幻灯片文档：https://marp.app
- 项目仓库：https://github.com/roboticsystem/OA-EPP
