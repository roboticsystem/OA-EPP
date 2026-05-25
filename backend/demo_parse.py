from app.github_issues import parse_markdown_for_features
import json
md = '''# 需求文档

### F-T-011 需求文档一键转GitHub Issues

该功能应在文档封存后自动解析并创建 Issue。

### F-S-002 学生端改进：考试提醒

增加考试开始前提醒功能。

### F-D-005 运维：CI 自动发布脚本

为部署添加一键构建与发布脚本。
'''
items = parse_markdown_for_features(md)
print(json.dumps(items, ensure_ascii=False, indent=2))
