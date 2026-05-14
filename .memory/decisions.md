# Decisions

Architectural commitments made in this project.


- [student-gitflow-issue-branching] 第10章第16节采用课程版Gitflow：学生按Issue创建feature分支并PR到develop，main只保留稳定发布。

- [teacher-gitflow-execution-policy] 教师端Gitflow规范：计划发布走develop->release->main；线上受影响故障走main->hotfix->main并强制回合并develop。

- [chapter13-er-sql-draft] 第10章第13节需同时给出数据库E-R草图与MySQL建库SQL草稿，作为需求评审与迁移实现前的教学基线。
