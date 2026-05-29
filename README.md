
# 《工程实践》在线网站

本项目为“《工程实践》”课程的在线学习与实践平台，聚焦工程能力训练与项目式学习。

这是一个支持在线课程学习、实验练习和项目交付的教学平台。

---

## 课程结构

网站内容分为四大工程实践模块，每个模块下设若干章节：

- **工程实践1**
- **工程实践2**
- **工程实践3**
- **工程实践4**

此外还包含：
- **附录**（开发环境、工具指南等）
- **书写规范**（贡献与协作说明）
- **参考资料**

导航结构详见 `mkdocs.yml`。

---

## 快速开始

1. 克隆本仓库，安装依赖：
  ```bash
  pip install -r requirements.txt
  ```
2. 本地预览：
  ```bash
  python3 deploy_local_or_coolify.py
  # 选择 [1] 本地预览
  ```
  访问 http://127.0.0.1:8008 查看。
3. 远程部署：
  ```bash
  python3 deploy_local_or_coolify.py
  # 选择 [2] 远程部署（Coolify）
  ```

---

## 技术亮点

- MkDocs + Material 主题，响应式设计
- 支持 svgbob/Kroki 图表渲染
- 评论系统（Utterances，基于 GitHub Issues）
- Docker 一键部署，预编译 svgbob_cli 加速构建

---

## 贡献与协作

采用分支协作与 PR 审核模式，详细规范见 docs/contributing.md。

---

## 联系方式

如有问题、建议或合作意向，请联系：robotics-course@example.com

### Prerequisites

Create a `.env` file in the project root (excluded from git) with the following keys:

```
COOLIFY_API_KEY=<your-coolify-api-key>
GITHUB_TOKEN=<your-github-personal-access-token>
```

Install local dependencies:

```bash
pip install -r requirements.txt
```

### Local Preview

Start a local development server with live reload:

```bash
python3 deploy_local_or_coolify.py
# Select [1] Local Preview
```

The site will be available at **http://127.0.0.1:8008**.  
Any changes to files under `docs/` are reflected in the browser immediately.

### Deploy to Server

Once satisfied with local testing, deploy to the production server (Coolify):

```bash
python3 deploy_local_or_coolify.py
# Select [2] Deploy to Coolify
```

This script will:
1. Verify that required source files exist
2. Locate the Coolify application
3. Trigger a forced rebuild and redeployment

The production site is served at **https://robotics.uwis.cn**.

### Docker Build Optimization

#### Precompiled svgbob_cli

To accelerate the Docker build process, this project uses a **precompiled svgbob_cli** binary instead of compiling from source on every build:

- **Build Time Improvement**: Reduced from 5-10 minutes to ~1.5 minutes (70-85% faster)
- **Binary Location**: `bin/svgbob_cli` (1.9MB ELF executable)
- **Runtime Dependency**: Requires `libgcc` library (configured in Dockerfile)

#### How to Update svgbob_cli

If you need to update to a newer version of svgbob_cli, you have two options:

**Option 1: Recompile (Recommended)**

```bash
# Build using the original compilation approach
docker build --target builder -t svgbob-builder .

# Extract the newly compiled binary
docker run --rm -v "$(pwd)/bin:/output" svgbob-builder \
  sh -c "cp /root/.cargo/bin/svgbob_cli /output/"

# Commit the update
git add bin/svgbob_cli
git commit -m "chore: update svgbob_cli to new version"
```

**Option 2: Use Original Compilation Approach**

In `Dockerfile`, comment out the precompiled approach and uncomment the original compilation lines (see comments in Dockerfile for details).

> **Note**: The compilation approach requires ~5-10 minutes build time and depends on crates.io network connectivity.

### Project Structure

```
├── docs/                  # Markdown source files
│   ├── index.md           # Home page
│   ├── intro.md           # Course introduction
│   ├── syllabus.md        # Syllabus
│   └── resources.md       # References & resources
├── mkdocs.yml             # MkDocs configuration
├── requirements.txt       # Pinned Python dependencies
├── Dockerfile             # Multi-stage build (MkDocs → nginx)
├── docker-compose.yaml    # Coolify deployment configuration (oaepp_web/oaepp_api)
├── nginx.conf             # nginx serving configuration (oaepp_web/oaepp_api)
├── deploy_local_or_coolify.py              # Unified management script (local preview & deploy)
├── .env                   # Secrets (not committed to git)
└── .gitignore
```

---

## Comment System

Each page of the course website includes a comment section powered by [Utterances](https://utteranc.es/), a lightweight comment widget built on GitHub Issues.

- **How it works:** Comments are stored as GitHub Issues in the `uwislab/robotics-systems-course` repository, with each page mapped to an issue via its URL pathname.
- **Requirements:** Users need a GitHub account to post comments.
- **Theme:** Uses the `github-light` theme for a clean reading experience.
- **SPA support:** Comments reload automatically when navigating between pages (Material for MkDocs instant navigation).

To enable comments on a new deployment, install the [utterances GitHub App](https://github.com/apps/utterances) on the repository.

---

## Diagram Rendering (svgbob)

This project uses **` ```bob `** fenced code blocks to render ASCII diagrams via the `markdown-svgbob` extension. When the site is built with MkDocs, these blocks are automatically converted to inline SVG.

### Preview in VS Code

To preview svgbob diagrams in real-time while editing in VS Code, install one of the following extensions:

- **Markdown Preview Enhanced** (ID: `shd101wyy.markdown-preview-enhanced`)
- **Markdown Live Preview** with Kroki support

Then **temporarily** change the fence tag to enable Kroki-based rendering:

```diff
- ```bob
+ ```svgbob {kroki=true}
```

After finishing your diagram edits, **revert** the tag back to ` ```bob ` before committing:

```diff
- ```svgbob {kroki=true}
+ ```bob
```

> **Note:** The MkDocs build only recognizes ` ```bob `. Committing ` ```svgbob ` or ` ```svgbob {kroki=true} ` will result in the diagram being rendered as a plain code block on the published site.

## Diagram Rendering (Kroki)

In addition to svgbob, this project supports [Kroki](https://kroki.io/) for rendering a wide variety of diagram types (PlantUML, Mermaid, BlockDiag, D2, Graphviz, etc.) via the `mkdocs-kroki-plugin`.

### Usage

Use fenced code blocks with the `kroki-` prefix followed by the diagram type:

````markdown
```kroki-plantuml
@startuml
Alice -> Bob: Hello
Bob --> Alice: Hi!
@enduml
```

```kroki-mermaid
graph LR
    A[Start] --> B[End]
```

```kroki-d2
x -> y: hello
```
````

### Supported Diagram Types

All diagram types supported by [Kroki](https://kroki.io/#support) can be used, including: PlantUML, Mermaid, BlockDiag, GraphViz/DOT, D2, BPMN, Excalidraw, Ditaa, ERD, Nomnoml, Pikchr, Structurizr, WaveDrom, WireViz, and more.

### Configuration

The plugin is configured in `mkdocs.yml` with:
- `fence_prefix: kroki-` — diagrams use ` ```kroki-<type> ` syntax
- `enable_mermaid: false` — Mermaid is handled by the existing JS-based renderer; use `kroki-mermaid` only when you explicitly want Kroki rendering

---

## Contribution and Feedback

We welcome contributions from the community to improve the course content and platform features. Please refer to the contribution guidelines on the website. For feedback or support, contact the course coordinator.

### Collaborative Writing Workflow

This course uses a **branch-based collaborative writing** model. Each contributor works on their own branch, then submits a Pull Request (PR) for review before merging into the main branch.

```
1. Create branch    git checkout -b docs/chapter3-your-name
2. Write & preview   Edit docs/, then run: mkdocs serve
3. Commit & push     git add . && git commit && git push origin HEAD
4. Open PR           Create a Pull Request to main on GitHub
5. Review            Instructor reviews changes, leaves comments
6. Revise            Address feedback, push additional commits
7. Merge             Instructor approves and merges → auto-deploy
```

**Preview Deployments:** When a PR is opened, [Coolify](https://coolify.io/) automatically builds a preview site for that branch. The instructor can view the rendered result directly in the browser before merging — no need to check out the branch locally.

> For detailed branch naming, commit message, and PR conventions, see the [Contributing Guide](docs/contributing.md).

---

## Language Switch

This README is in English by default.  
You can switch to the Chinese version here: [README_cn.md](README_cn.md)

---

## Contact

For any questions, suggestions, or support, please contact the course coordinator at robotics-course@example.com.
