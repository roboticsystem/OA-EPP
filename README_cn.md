# 机器人系统

欢迎访问《机器人系统》课程的交互式课程网站。

本项目旨在提供一个综合性的学习平台，集成了多媒体课件、交互式实验和项目实践资料。通过理论知识与实践应用的结合，帮助学生深入理解机器人系统。


## 功能特色

《机器人系统》课程网站提供：

- **多媒体课件：** 丰富的视频讲座、幻灯片和阅读材料，涵盖机器人学的基础和高级主题。这些材料由专家精心策划，并定期更新以反映该领域的最新进展。
- **交互式实验：** 通过虚拟实验室和仿真，学生可以在受控环境中实践机器人算法和硬件概念。这些实验提供实时反馈，鼓励探索和创新。
- **项目实践资料：** 详细的项目指南、数据集和代码库，支持真实的机器人系统开发与研究。学生可以通过实际项目应用所学知识，模拟行业挑战。

---

## 创新学习模式

本平台采用新型学习模式，强调：

- **主动学习：** 通过交互式练习、测验和实验，鼓励学生积极参与内容。这种方法有助于强化概念并提高记忆效果。
- **理论与实践结合：** 无缝整合理论课程与实践应用，强化理解。学生可以将理论知识立即应用于动手活动中。
- **协作项目：** 通过项目驱动学习，促进团队合作与知识共享。学生可以在项目中协作，分享见解，培养机器人工程所需的沟通技能。

---

## 技术亮点

- 响应式网页设计，支持包括桌面、平板和智能手机在内的多设备访问。
- 多媒体内容与交互式网页技术（如WebGL和实时数据可视化）的集成。
- 支持实时实验反馈和数据可视化，提升学习体验。
- 模块化架构，便于扩展课程内容和功能，实现未来的可扩展性和定制化。
- 安全的用户认证和进度跟踪，个性化学习旅程。

---

## 快速开始

请浏览网站提供的各个模块，课程内容循序渐进，确保结构化学习路径。建议新用户从入门模块开始，然后逐步学习高级主题。

---

## 开发与部署

### 前置准备

在项目根目录创建 `.env` 文件（已加入 .gitignore，不会提交到 git）：

```
COOLIFY_API_KEY=<你的 Coolify API Key>
GITHUB_TOKEN=<你的 GitHub 个人访问令牌>
```

安装本地依赖：

```bash
pip install -r requirements.txt
```

### 本地预览

启动支持热重载的本地开发服务器：

```bash
python3 deploy_local_or_coolify.py
# 选择 [1] 本地预览
```

浏览器访问 **http://127.0.0.1:8008** 即可预览。  
修改 `docs/` 目录下的任意文件后，浏览器会自动刷新。

### 部署到服务器

本地测试满意后，执行以下命令部署到线上服务器（Coolify）：

```bash
python3 deploy_local_or_coolify.py
# 选择 [2] 远程部署（Coolify）
```

该脚本会自动完成以下步骤：
1. 检查必要的源文件是否存在
2. 定位 Coolify 应用
3. 触发强制重建与重新部署

线上站点地址：**https://robotics.uwis.cn**

### Docker 构建优化

#### 预编译 svgbob_cli

为了加速 Docker 构建过程，本项目使用**预编译的 svgbob_cli** 而不是每次构建时重新编译：

- **构建时间优化**：从 5-10 分钟减少到约 1.5 分钟（提速 70-85%）
- **预编译文件位置**：`bin/svgbob_cli`（1.9MB ELF 可执行文件）
- **依赖要求**：运行时需要 `libgcc` 库（已在 Dockerfile 中配置）

#### 如何更新 svgbob_cli

如果需要更新到新版本的 svgbob_cli，有两种方式：

**方式一：重新编译（推荐）**

```bash
# 使用原始编译方案构建
docker build --target builder -t svgbob-builder .

# 提取新编译的二进制文件
docker run --rm -v "$(pwd)/bin:/output" svgbob-builder \
  sh -c "cp /root/.cargo/bin/svgbob_cli /output/"

# 提交更新
git add bin/svgbob_cli
git commit -m "chore: 更新 svgbob_cli 到新版本"
```

**方式二：使用原始编译方案**

在 `Dockerfile` 中，注释掉预编译方案，取消注释原始编译方案（详见 Dockerfile 中的说明）。

> **注意**：编译方案需要约 5-10 分钟构建时间，且依赖 crates.io 网络连接。

### 项目结构

```
├── docs/                  # Markdown 源文件
│   ├── index.md           # 首页
│   ├── intro.md           # 课程介绍
│   ├── syllabus.md        # 教学大纲
│   └── resources.md       # 参考资料
├── mkdocs.yml             # MkDocs 配置
├── requirements.txt       # Python 依赖（锁定主版本）
├── Dockerfile             # 多阶段构建（MkDocs → nginx）
├── docker-compose.yaml    # Coolify 部署配置
├── nginx.conf             # nginx 服务配置
├── deploy_local_or_coolify.py              # 统一管理脚本（本地预览 & 远程部署）
├── .env                   # 密钥文件（不提交到 git）
└── .gitignore
```

---

## 评论系统

课程网站每个页面底部集成了基于 [Utterances](https://utteranc.es/) 的评论功能，评论以 GitHub Issue 形式存储在 `uwislab/robotics-systems-course` 仓库中。

- **工作原理：** 每个页面通过 URL 路径名（pathname）映射到一个 GitHub Issue，用户评论直接写入对应 Issue。
- **使用要求：** 需要 GitHub 账号才能发表评论。
- **主题样式：** 使用 `github-light` 主题，与课程网站风格一致。
- **SPA 支持：** 支持 Material for MkDocs 即时导航模式，页面切换时评论区自动重新加载。

如需在新部署中启用评论，需在仓库安装 [utterances GitHub App](https://github.com/apps/utterances)。

---

## 图表渲染（svgbob）

本项目使用 **` ```bob `** 围栏代码块标记 svgbob 图表，MkDocs 构建时由 `markdown-svgbob` 扩展自动渲染为内联 SVG。

### 在 VS Code 中实时预览

编辑 svgbob 图表时，若需在 VS Code 中实时预览渲染效果，可安装以下任一插件：

- **Markdown Preview Enhanced**（ID: `shd101wyy.markdown-preview-enhanced`）
- **Markdown Live Preview**（支持 Kroki 渲染）

安装后，**临时**将代码块标记修改为 Kroki 格式以启用实时预览：

```diff
- ```bob
+ ```svgbob {kroki=true}
```

调试完成后，**务必改回** ` ```bob ` 再提交：

```diff
- ```svgbob {kroki=true}
+ ```bob
```

> **注意：** MkDocs 构建仅识别 ` ```bob ` 标记。若提交时使用 ` ```svgbob ` 或 ` ```svgbob {kroki=true} `，图表将显示为普通代码块而非渲染图形。

## 图表渲染（Kroki）

除 svgbob 外，本项目还通过 `mkdocs-kroki-plugin` 支持 [Kroki](https://kroki.io/) 渲染多种图表类型（PlantUML、Mermaid、BlockDiag、D2、Graphviz 等）。

### 使用方法

使用 `kroki-` 前缀 + 图表类型作为代码块标记：

````markdown
```kroki-plantuml
@startuml
Alice -> Bob: Hello
Bob --> Alice: Hi!
@enduml
```

```kroki-mermaid
graph LR
    A[开始] --> B[结束]
```

```kroki-d2
x -> y: hello
```
````

### 支持的图表类型

[Kroki](https://kroki.io/#support) 支持的所有图表类型均可使用，包括：PlantUML、Mermaid、BlockDiag、GraphViz/DOT、D2、BPMN、Excalidraw、Ditaa、ERD、Nomnoml、Pikchr、Structurizr、WaveDrom、WireViz 等。

### 配置说明

插件在 `mkdocs.yml` 中的配置：
- `fence_prefix: kroki-` —— 图表使用 ` ```kroki-<类型> ` 语法
- `enable_mermaid: false` —— Mermaid 由现有 JS 渲染器处理；仅当需要 Kroki 渲染时才用 `kroki-mermaid`

---

## 贡献与反馈

我们欢迎社区贡献以改进课程内容和平台功能。请参阅网站上的贡献指南。如需反馈或支持，请联系课程负责人。

### 合作编写工作流

本课程采用**分支协作编写**模式。每位参与者在自己的分支上工作，完成后提交 Pull Request（PR），经老师审核后合并到主分支。

```
1. 创建分支    git checkout -b docs/chapter3-你的名字
2. 编写与预览   编辑 docs/ 下的文件，然后运行：mkdocs serve
3. 提交与推送   git add . && git commit && git push origin HEAD
4. 发起 PR       在 GitHub 上创建 Pull Request，目标分支选 main
5. 老师审核     老师查看改动、点评、提修改意见
6. 修改完善     根据反馈修改后再次 push
7. 合并发布     老师确认无误后合并 → 自动部署成书籍网页
```

**分支预览**：当 PR 被创建时，[Coolify](https://coolify.io/) 会自动为该分支构建预览站点。老师无需拉取分支到本地，可直接在浏览器中查看学生分支的渲染网页效果，确认无误后再合并。

> 详细的分支命名、提交信息、PR 规范请参见[教材书写规范](docs/contributing.md)。

---

## 语言切换

本README默认使用英文。  
您可以切换到英文版本： [README.md](README.md)

---

## 联系方式

如有任何问题、建议或需要支持，请联系课程负责人，邮箱：robotics-course@example.com。