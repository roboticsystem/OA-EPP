# Coolify 项目部署配置指南

本文档说明如何在 Coolify 中正确部署机器人系统课程项目。

---

## ⚠️ 重要：必须使用 Docker Compose 方式

**本项目必须选择 `Docker Compose` 构建方式**，而不是 `Dockerfile` 方式。

### 为什么必须使用 Docker Compose？

本项目采用**微服务架构**，包含 **2 个独立容器**：

| 容器名 | 作用 | 技术栈 | 端口 |
|--------|------|--------|------|
| `web` | 前端静态站点服务 | MkDocs + Nginx | 80 |
| `api` | 后端 API 服务 | FastAPI + SQLite | 8000 |

这两个容器：
- **独立构建**：`web` 使用 `Dockerfile`，`api` 使用 `backend/Dockerfile`
- **相互依赖**：`web` 依赖 `api` 提供后端服务
- **共享网络**：通过 `coolify` 网络互联，允许 Caddy 代理访问
- **数据持久化**：`api` 使用 `exam_data` 卷存储 SQLite 数据库

**如果选择 Dockerfile 方式，只会构建单个容器，导致功能不完整！**

### Coolify 构建方式对比

Coolify 提供了 4 种构建方式，不同方式适用于不同的项目类型：

#### 1. Nixpacks（默认）⭐

**适用场景**：绝大多数无 Dockerfile 的项目，自动构建镜像

- 自动检测项目语言/框架（Node.js、Python、Go、Rust 等）
- 自动生成 Dockerfile，无需手动写配置
- 适合：前端框架（React/Vue）、后端服务（FastAPI/Express）、单容器应用

**优点**：
- ✅ 零配置、开箱即用
- ✅ Coolify 默认构建方式
- ✅ 自动优化构建流程

**缺点**：
- ❌ 无法处理多容器应用
- ❌ 自定义能力有限

#### 2. Static

**适用场景**：纯静态网站，无后端服务

- 直接部署 HTML/CSS/JS 静态文件
- 用内置的轻量 Web 服务器（Nginx）提供服务
- 适合：静态博客、文档网站、SPA 打包后的产物

**优点**：
- ✅ 构建速度极快
- ✅ 不需要任何构建步骤
- ✅ 直接部署静态文件

**缺点**：
- ❌ 不支持后端服务
- ❌ 不支持动态内容生成

#### 3. Dockerfile

**适用场景**：项目自带 Dockerfile，需要完全自定义构建流程

- 直接使用项目根目录下的 `Dockerfile` 构建镜像
- 适合：复杂构建流程（多阶段构建、自定义依赖）、需要精确控制镜像内容的场景

**优点**：
- ✅ 完全可控
- ✅ 和本地 `docker build` 流程一致
- ✅ 支持多阶段构建

**缺点**：
- ❌ **只构建单个容器**
- ❌ 不支持多容器编排
- ❌ 无法处理服务依赖

#### 4. Docker Compose（本项目使用）✅

**适用场景**：多容器应用，需要编排多个服务

- 直接使用项目根目录下的 `docker-compose.yml` 启动多容器服务
- 适合：前后端分离、带数据库/缓存的应用（比如 Nginx + FastAPI + Redis）

**优点**：
- ✅ 一键编排多个容器
- ✅ 支持服务依赖（`depends_on`）
- ✅ 支持网络、卷挂载等复杂配置
- ✅ 和本地开发环境一致

**缺点**：
- ❌ 需要手动编写 `docker-compose.yml`
- ❌ 配置相对复杂

---

**本项目为什么选择 Docker Compose？**

| 需求 | Nixpacks | Static | Dockerfile | Docker Compose |
|------|----------|--------|------------|----------------|
| 多容器支持 | ❌ | ❌ | ❌ | ✅ |
| 服务编排 | ❌ | ❌ | ❌ | ✅ |
| 前后端分离 | ❌ | ❌ | ❌ | ✅ |
| 数据持久化 | ⚠️ | ❌ | ⚠️ | ✅ |
| 网络隔离 | ❌ | ❌ | ❌ | ✅ |

**结论**：本项目有 2 个容器（web + api），必须使用 Docker Compose！

---

## 🏗️ 项目架构说明

### 容器架构

```
┌─────────────────────────────────────────────────┐
│              Coolify + Caddy                    │
│            (caddy: robotics.uwis.cn)             │
└────────────────┬────────────────────────────────┘
                 │
                 ├─────────────────┐
                 │                 │
          ┌──────▼──────┐   ┌─────▼──────┐
          │  web:80     │   │  api:8000  │
          │  (Nginx)    │   │ (FastAPI)  │
          │             │   │            │
          │  MkDocs     │   │  SQLite    │
          │  静态站点    │   │  考试系统   │
          └─────────────┘   └────────────┘
                                  │
                            ┌─────▼─────┐
                            │ exam_data │
                            │  (Volume) │
                            └───────────┘
```

### 数据流

1. **用户访问** `http://robotics.uwis.cn`
2. **Caddy 代理**将请求路由到 `web:80`
3. **Nginx** 提供 MkDocs 静态页面
4. **前端页面**通过 `/api/` 路径调用后端 API
5. **Nginx** 将 `/api/` 请求反向代理到 `api:8000`
6. **FastAPI** 处理请求并访问 SQLite 数据库
7. **数据持久化**在 `exam_data` 卷中

---

## 📋 Coolify 部署步骤

### 1. 创建新应用

1. 登录 Coolify: https://coolify.uwis.cn
2. 选择项目（如 `Robotics_Systems_Course`）
3. 点击 **New Resource** → **Public Repository**

### 2. 配置 Git 仓库

| 配置项 | 值 |
|--------|-----|
| Git Repository URL | `https://github.com/uwislab/robotics-systems-course.git` |
| Branch | `main` |
| **Build Pack** | **⚠️ 必须选择 `Docker Compose`** |

### 3. 配置域名

在 **Domains** 标签页：

| Service | Domain |
|---------|--------|
| `web` | `http://robotics.uwis.cn` |
| `api` | （不需要公开域名，内部访问） |

### 4. 配置环境变量

在 **Environment Variables** 标签页添加：

| Key | Value | 说明 |
|-----|-------|------|
| `TEACHER_PASSWORD` | `your_password` | 教师后台密码 |
| `JWT_SECRET` | `random_secret_string` | JWT 签名密钥（建议 32 字符以上随机字符串） |
| `DOCS_DIR` | `/app/docs` | Markdown 文档目录 |
| `DB_PATH` | `/app/data/exam.db` | SQLite 数据库路径 |

**生成随机密钥示例**：
```bash
openssl rand -hex 32
```

### 5. 配置持久化存储

Coolify 会自动创建 `exam_data` 卷，无需手动配置。

---

## ❤️ 健康检查配置（重要！）

### ⚠️ 健康检查关键注意事项

#### 1. 必须使用 HTTPS 访问才能激活健康检查

**重要**：在 Coolify 中，只有通过 **`https://`** 访问你的应用时，健康检查机制才会被正确激活。

- ✅ **正确**：`https://robotics.uwis.cn`
- ❌ **错误**：`http://robotics.uwis.cn`（健康检查可能不生效）

虽然容器内部使用 HTTP (80 端口)，但 Caddy 反向代理会自动提供 HTTPS，并根据健康检查状态决定是否路由流量。

#### 2. 健康检查命令必须在 Docker 镜像中可用

**关键问题**：如果健康检查使用的命令（如 `wget`、`curl`、`nc`）在容器中不存在，健康检查会失败！

**后果**（根据 [Coolify 官方文档](https://coolify.io/docs/knowledge-base/health-checks)）：
```
健康检查失败
    ↓
容器被标记为 unhealthy
    ↓
Traefik 不会路由流量到此容器
    ↓
网站返回 404 Not Found 或 "no available server" 错误
```

**常见错误**：
- ❌ `nginx:alpine` 默认不包含 `wget` 或 `curl`
- ❌ `python:alpine` 默认不包含 `wget` 或 `curl`
- ✅ 大多数 Alpine 镜像**自带 `nc` (netcat)**

**推荐方案**：使用 **`nc` (netcat)** 进行健康检查，避免安装额外工具（~30KB，Alpine 自带）。

---

### 为什么需要健康检查？

默认情况下，Coolify 会提示：

```
⚠️ No health check configured.
The resource may be functioning normally.
Traefik and Caddy will route traffic to this container even without a health check.
However, configuring a health check is recommended to ensure the resource is ready before receiving traffic.
```

**问题**：没有健康检查，Traefik 可能在容器启动完成前就开始路由流量，导致用户看到错误页面。

**解决方案**：为两个容器都添加健康检查配置。根据 [Coolify 官方文档](https://coolify.io/docs/knowledge-base/health-checks)，Docker Compose 项目必须在 `docker-compose.yaml` 中使用 `healthcheck` 属性定义健康检查。

### 添加健康检查

在 `docker-compose.yaml` 中为每个服务添加 `healthcheck` 配置：

#### Web 容器健康检查

```yaml
services:
  web:
    build:
      context: .
      network: host
    expose:
      - "80"
    restart: unless-stopped
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "nc", "-z", "127.0.0.1", "80"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    labels:
      caddy: "robotics.uwis.cn"
      caddy.reverse_proxy: "{{upstreams 80}}"
    networks:
      - coolify
```

#### API 容器健康检查

```yaml
  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
      network: host
    expose:
      - "8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "nc", "-z", "127.0.0.1", "8000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - exam_data:/app/data
      - ./docs:/app/docs:rw
    environment:
      - TEACHER_PASSWORD=${TEACHER_PASSWORD:-admin123}
      - JWT_SECRET=${JWT_SECRET:-please-change-this-secret}
      - DB_PATH=/app/data/exam.db
      - DOCS_DIR=/app/docs
    networks:
      - coolify
```

### 健康检查参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `test` | `nc -z localhost PORT` | 使用 netcat 检查端口是否可访问 |
| `interval` | `30s` | 每 30 秒检查一次 |
| `timeout` | `10s` | 单次检查超时时间 |
| `retries` | `3` | 连续失败 3 次才标记为 unhealthy |
| `start_period` | `40s` | 容器启动后等待 40 秒再开始检查（给服务启动留时间） |

**nc 命令说明**：
- `nc -z`：零 I/O 模式，只检查端口是否打开
- `127.0.0.1`：使用 IPv4 地址（避免 localhost 解析到 IPv6 导致连接失败）
- `80` / `8000`：端口号
- **优点**：Alpine 镜像自带，无需安装额外工具（~30KB）

**为什么不用 wget/curl？**
- `wget`：需要 `apk add wget`（~380KB）
- `curl`：需要 `apk add curl`（~200KB）
- `nc`：Alpine 自带，零安装成本

### 健康检查工作流程

```
容器启动
    ↓
等待 40 秒（start_period）
    ↓
开始每 30 秒检查一次（interval）
    ↓
    ├─ 成功 → 标记为 healthy → Traefik 开始路由流量
    └─ 失败 → 重试 3 次 → 标记为 unhealthy → Traefik 停止路由流量
```

### 验证健康检查

部署完成后，在 Coolify 中应该看到：

```
✅ web: healthy
✅ api: healthy
```

如果看到 `unhealthy` 状态，检查：
1. **验证健康检查命令是否可用**：
   ```bash
   docker exec <container_id> nc -z 127.0.0.1 80
   ```
   如果返回错误，说明端口未监听或 nc 命令不可用
2. **检查 localhost vs 127.0.0.1**：某些容器中 `localhost` 可能解析到 IPv6 (`::1`)，导致连接失败，建议直接使用 `127.0.0.1`
3. 容器日志是否有错误
4. `start_period` 是否足够长（服务启动可能需要更多时间）
5. 端口是否正确（web 检查 `80`，api 检查 `8000`）

---

## 🚀 部署流程

### 首次部署

1. 完成上述所有配置
2. 点击 **Deploy** 按钮
3. 等待构建完成（约 5-10 分钟）
4. 访问 `http://robotics.uwis.cn` 验证

### 后续更新

**方式一：自动部署**

在应用设置中启用 **Auto Deploy**：
- 每次 `git push` 到 `main` 分支
- Coolify 自动拉取代码并重新部署

**方式二：手动部署**

在 Coolify 应用页面点击 **Deploy** 按钮。

### 查看日志

- **构建日志**：在部署页面查看 `Build` 标签
- **运行日志**：在应用页面查看 `Logs` 标签，可分别查看 `web` 和 `api` 容器日志

---

## 🔧 常见问题

### Q1: 为什么必须选择 Docker Compose？

**A**: 项目包含 2 个独立容器（web + api），只有 Docker Compose 能同时构建和运行多个容器。

### Q2: 如何验证两个容器都在运行？

**A**: 在 Coolify 应用页面可以看到两个容器的状态：
```
✅ web (80)
✅ api (8000)
```

### Q3: 健康检查失败怎么办？

**A**: 检查步骤：

1. **验证 nc 命令是否存在**（排除工具缺失问题）：
   ```bash
   docker exec <container_id> which nc
   docker exec <container_id> nc -z localhost 80
   ```
   如果提示 "not found"，说明镜像中没有 `nc`（极少见）。

2. **查看容器健康状态详情**：
   ```bash
   docker inspect <container_id> | grep -A 10 Health
   ```
   可以看到具体的错误信息。

3. **查看容器日志**：`Logs` → 选择 `web` 或 `api`

4. **增加启动时间**：如果服务启动慢，将 `start_period` 改为 `60s` 或更长。

5. **临时禁用健康检查**（仅调试用）：如果问题持续，可以先注释掉 `healthcheck` 配置，让服务先运行起来，但要注意此时 Traefik 会立即路由流量，可能导致启动期间的请求失败。

### Q4: 数据会丢失吗？

**A**: 不会。SQLite 数据库存储在 `exam_data` 卷中，即使重新部署也会保留。

### Q5: 如何更新环境变量？

**A**: 
1. 在 Coolify 中修改环境变量
2. 点击 **Restart** 重启容器
3. 新的环境变量会自动注入

---

## 📚 参考资料

- [Coolify 官方文档](https://coolify.io/docs)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [健康检查配置说明](https://docs.docker.com/engine/reference/builder/#healthcheck)

---

## 📝 配置清单

部署前请确认：

- [ ] Git 仓库 URL 正确
- [ ] Branch 选择 `main`
- [ ] **Build Pack 选择 `Docker Compose`**（最重要！）
- [ ] 域名配置：`web` → `robotics.uwis.cn`
- [ ] 环境变量：`TEACHER_PASSWORD`, `JWT_SECRET`, `DOCS_DIR`, `DB_PATH`
- [ ] 健康检查已添加到 `docker-compose.yaml`
- [ ] 两个容器都显示 `healthy` 状态

---

**最后提醒**：如果部署后发现只有一个容器运行，说明选错了构建方式，请删除应用重新创建，确保选择 **Docker Compose**！
