# Decisions

Architectural commitments made in this project.


- [student-gitflow-issue-branching] 第10章第16节采用课程版Gitflow：学生按Issue创建feature分支并PR到develop，main只保留稳定发布。

- [teacher-gitflow-execution-policy] 教师端Gitflow规范：计划发布走develop->release->main；线上受影响故障走main->hotfix->main并强制回合并develop。

- [chapter13-er-sql-draft] 第10章第13节需同时给出数据库E-R草图与MySQL建库SQL草稿，作为需求评审与迁移实现前的教学基线。

- [merge-conflict-version-line] 合并main分支时，优先采用远程分支较新版本信息（如文档版本号、日期、分支名），其余内容以本地为准，确保所有本地补充内容不丢失。

- [prototype-tool-selection-and-reason] 原型设计章节明确要求全班统一原型，推荐 Lovable（免费、1:1 映射 Reflex）、Stitch（免费、视觉一致）、v0（付费、体验最佳），并强调快速原型是风格一致与高效开发的保障。此内容已补充进 19.5 节。
