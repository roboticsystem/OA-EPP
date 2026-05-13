# 《机器人系统》在线课程网站

Welcome to the interactive course website for the "《机器人系统》" course.

This project is designed to provide a comprehensive learning platform that integrates multimedia courseware, interactive experiments, and project practice materials. It aims to facilitate a deep understanding of robotics systems by combining theoretical knowledge with practical applications.

---

## Project Overview

The "《机器人系统》" course website offers:

- **Multimedia Courseware:** Rich video lectures, slides, and reading materials to cover fundamental and advanced topics in robotics. These materials are curated by experts and updated regularly to reflect the latest advancements in the field.
- **Interactive Experiments:** Hands-on virtual labs and simulations that allow students to experiment with robotic algorithms and hardware concepts in a controlled environment. These experiments provide real-time feedback and encourage exploration and innovation.
- **Project Practice Materials:** Detailed project guidelines, datasets, and code repositories to support real-world robotics system development and research. Students can apply their knowledge by working on practical projects that simulate industry challenges.

---

## Innovative Learning Model

Our platform adopts a novel learning model that emphasizes:

- **Active Learning:** Encouraging students to engage actively with the content through interactive exercises, quizzes, and experiments. This approach helps reinforce concepts and improve retention.
- **Blended Theory and Practice:** Seamlessly integrating theoretical lessons with practical applications to reinforce understanding. Students can immediately apply what they learn in theory to hands-on activities.
- **Collaborative Projects:** Facilitating teamwork and knowledge sharing through project-based learning. Students can collaborate on projects, share insights, and develop communication skills essential for robotics engineering.

---

## Technical Highlights

- Responsive web design for accessibility across devices including desktops, tablets, and smartphones.
- Integration of multimedia content with interactive web technologies such as WebGL and real-time data visualization.
- Support for real-time experiment feedback and data visualization to enhance the learning experience.
- Modular architecture to easily extend course content and features, allowing for future scalability and customization.
- Secure user authentication and progress tracking to personalize the learning journey.

---

## Getting Started

To begin exploring the course materials, navigate through the sections provided on the website. Each module is designed to build upon the previous, ensuring a structured learning path. New users are encouraged to start with the introductory modules before progressing to advanced topics.

---

## Development & Deployment

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
├── docker-compose.yaml    # Coolify deployment configuration
├── nginx.conf             # nginx serving configuration
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
