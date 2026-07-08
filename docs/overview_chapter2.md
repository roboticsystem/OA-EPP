# 工程实践1-5 学习重点

## 工程实践1（编码训练）

| 模块 | 内容 |
|------|------|
| **C 程序设计编程** | 受监管的 C 语言编程训练，掌握基础语法、指针、内存管理、文件操作 |
| **无 AI 辅助 Python 编程** | 受监管的不使用 AI 工具的 Python 编程，夯实基本编程能力 |
| **AI 辅助编程入门** | 最简单的 AI 编程体验，学习如何利用 AI 工具辅助编码 |
| **Git 版本控制** | Git 基本操作：clone、commit、push、pull、branch、merge |
| **Gitee 平台使用** | 基于 Gitee 的代码托管、仓库管理、团队协作 |
| **Git PR 开发流程** | Pull Request 工作流：fork、feature branch、code review、merge |

## 工程实践2（软件技术）——智能体应用开发实践

| 模块 | 内容 |
|------|------|
| **AI 快速原型** | 基于 AI 驱动的快速原型开发，利用生成式 AI 快速构建应用雏形 |
| **代码-原型一致性** | 实现代码与快速原型的一一对应，确保设计与实现同步 |
| **前后端一致框架** | 使用 Reflex 框架或 Java 前后端一致框架（如 Spring Boot + Thymeleaf）开发全栈应用 |
| **数据库一致性** | 保持数据库在各个小组的一致，使用迁移脚本和共享 Schema |
| **容器化 CI/CD** | 基于容器（Docker）的持续集成与持续部署流水线 |
| **PlantUML 绘图** | 使用 PlantUML 绘制 UML 图：用例图、类图、时序图、活动图 |
| **Markdown 文档** | 使用 Markdown 书写技术文档、接口说明、项目报告 |

## 工程实践3（软件测试）——知识切面质量保障与安全实践

| 模块 | 内容 |
|------|------|
| **TDD 开发** | 基于 Superpowers 的测试驱动开发（TDD），先写测试再写实现，红-绿-重构循环 |
| **GUI 自动化测试** | 图形用户界面的自动化测试，包括页面元素定位、交互模拟、断言验证 |

## 工程实践4（大数据处理）——向量数据库管理及服务实践

| 模块 | 内容 |
|------|------|
| **RAG 数据库应用** | 基于 Python 的检索增强生成（RAG）数据库应用开发，结合向量数据库实现语义搜索 |
| **数据分析与统计学习** | 最基本的数据分析与统计学习方法，使用 Pandas、NumPy、Matplotlib 等工具 |
| **LLM 构建与微调** | 大语言模型的构建与微调实践，理解 Transformer 架构、Fine-tuning 流程 |

## 工程实践5（软件产品研发）——智能软件架构项目实践

| 模块 | 内容 |
|------|------|
| **AI 驱动全流程** | 基于 AI 的、基于 Gitee 的软件产品全流程开发，从需求到交付的端到端实践 |
| **模型训练** | 训练 YOLO 等目标检测模型，掌握数据集准备、模型训练、评估与部署 |
| **数据样本处理** | 数据采集、清洗、标注、增强全流程处理 |
| **AI 大规模代码 TDD** | AI 辅助大规模代码的测试驱动开发，平衡 AI 生成代码与测试覆盖 |
| **软件持续维护** | 软件的持续维护策略：版本发布、Bug 修复、性能优化、技术债务管理 |
| **Git Flow 开发流程** | 采用 Git Flow 分支模型：feature、develop、release、hotfix、master 分支管理 |

## 附录：Web 应用框架简单对比（Gradio / Streamlit / Reflex / FastAPI + React/Vue）

在为 AI 模型或智能体应用构建 Demo 界面时，常用的四个框架对比如下：

| 对比维度 | Gradio | Streamlit | Reflex | FastAPI + React/Vue | Vaadin (Java) | Spring Boot + Vue |
|---------|--------|-----------|--------|---------------------|---------------|-------------------|
| **定位** | 机器学习模型 Demo / 快速原型 | 数据应用 / 交互式分析报告 | 纯 Python 全栈 Web 应用 | 现代 SPA + 高性能 API | 企业级 Java 全栈框架 | Java 后端 + Vue 前端分离架构 |
| **上手难度** | ⭐ 最简单，装饰器写法 | ⭐ 简单，命令式 API | ⭐⭐ 中等，需理解 Reflex 状态模型 | ⭐⭐⭐ 较复杂，需前后端分离知识 | ⭐⭐⭐ 较复杂，需 Java 基础 | ⭐⭐⭐ 较复杂，需 Java + Vue 双栈 |
| **UI 定制化** | 有限，依赖内置组件 | 中等，支持 HTML/CSS 嵌入 | 高，完全自定义组件 | 极高，完全自由 | 高，基于 Web 组件 | 高，Vue 组件化 + Spring 生态 |
| **实时 / WebSocket** | 支持，但有限 | 支持（需额外配置） | 原生支持 | 原生支持 | 原生支持 | 原生支持（WebSocket 配置） |
| **部署** | Hugging Face Spaces / 容器 | 容器 / Streamlit Cloud | 容器 / VPS | 容器 / 云平台 | 容器 / JAR 部署 | 容器 / JAR + 前端构建 |
| **状态管理** | 简单装饰器 + 变量 | Session/Client 状态 | Reflex 状态系统（原子化） | React: Redux/Recoil/Zustand; Vue: Pinia/Vuex | Vaadin 状态管理 / Spring Session | Vuex/Pinia + Spring Session |
| **Python 优先** | ✅ 完全 Python | ✅ 完全 Python | ✅ 完全 Python | ❌ 需要 JS/TS | ❌ Java | ❌ Java + JS/TS |
| **适合场景** | 模型演示、API 可视化 | 数据报告、交互分析 | 完整业务 Web 应用 | 企业级 / 高定制需求 | 企业级 Java 系统 / 后端主导项目 | 前后端分离 / 中大型项目 |
| **社区生态** | 庞大（ML 社区） | 庞大（数据社区） | 较小（发展中） | 极大 | 成熟（Java 企业级） | 成熟（Java + Vue 生态） |
| **许可证** | Apache 2.0 | Apache 2.0 | MIT | MIT / Apache 2.0 | Apache 2.0 | MIT / Apache 2.0 |

### 快速选型建议

| 需求 | 推荐 |
|------|------|
| 快速为模型 API 做一个演示界面 | **Gradio** |
| 构建含图表/数据可视化的分析报告 | **Streamlit** |
| 想用纯 Python 构建完整 Web 应用 | **Reflex** |
| 需要高度定制 UI + 高并发 API | **FastAPI + React/Vue** |
| 团队有前端能力，想做正式产品 | **FastAPI + React/Vue** |
| 个人/学术演示，追求最快速度 | **Gradio** |
| 已有 Java 后端团队，想快速构建企业级 UI | **Vaadin** |
| 前后端完全分离，Vue 前端 + Java 后端 | **Spring Boot + Vue** |

> **注**：如果学术工具需要**多用户并发**、**自定义工作流**或**复杂前端交互**，推荐 **FastAPI + React**；如果只是**单模型 Demo** 或**快速原型验证**，**Gradio** 是最高效的选择。
