# 项目结构说明

## OA-EPP 仓库包含两个独立项目

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

### 核心要点

- **两个项目虽然在同一仓库下，但代码上完全独立，互不依赖。**
- 所有 Reflex 源代码均在 `oaepp/` 目录下。
- `backend/` 是 MkDocs 网站的后端，与 Reflex 项目无关。
- 后续所有关于 Reflex 的讨论、分析和开发均限定在 `oaepp/` 目录内。

### 不要去修改 /backend目录下的文件！
---

## 本项目（`/oaepp`）的标准路由添加方式
### 涉及两个文件
| Step | 文件 | 操作 |
|---|---|---|
| 1 | **[`oaepp/pages/`](/OA-EPP/oaepp/pages/)** 下新建 `.py` 文件 | 编写页面组件（遵循 `login.py` 的模式） |
| 2 | **[`oaepp/app.py`](/OA-EPP/oaepp/app.py#L54-L64)** | 用 `app.add_page()` 注册路由 |
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
在 `login_mod` 注册块（L54-L64）附近追加：
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
这就是目前项目中**唯一的标准路由添加方式**——Reflex 页面组件放在 `pages/`，路由注册集中在 `app.py`。项目当前只注册了首页（`/`）这一个路由，没有其他路由文件或 `rx.page()` 装饰器的使用。

---

## 添加页面后的测试方式

### reflex run 热启动

在 `oaepp/` 目录下执行：

```bash
cd oaepp/
reflex run
```

Reflex 自带热重载 —— 修改 `pages/` 下的文件或 `app.py` 后，保存文件即自动刷新，无需手动重启。

### 测试 dashboard 页面

1. 确保 `reflex run` 正常运行，终端无报错。
2. 浏览器访问 `http://localhost:3000/dashboard`。
3. 预期看到 dashboard 页面内容渲染在浏览器中。

### 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| 页面空白或 404 | 路由注册时 `route` 参数拼写错误 | 检查 `app.add_page(..., route="/dashboard")` 中的路径 |
| 模块导入错误 | `app.py` 中 `from pages import dashboard` 失败 | 确认 `oaepp/pages/dashboard.py` 文件存在且语法正确 |
| 浏览器访问 localhost:3000 失败 | Reflex 端口被占用或未启动成功 | 检查终端日志，尝试 `reflex run --backend-port 8002 --frontend-port 3001` |
| 页面渲染但样式错乱 | Reflex 版本兼容问题 | 确认 `requirements.txt` 中 `reflex==0.9.4` 已安装 |