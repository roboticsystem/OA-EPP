# 学习时间线

## 功能概述

学习时间线按时间序展示任务发布 → 提交 → 批改 → 反馈全流程关键节点，帮助学生清晰掌握学习进度。

!!! info "需求来源"
    §5.5 F-S-041 学习时间线 — 优先级：低

## 验收标准

- [x] 时间线按时间序展示全部关键节点
- [x] 节点类型清晰区分（发布/提交/批改/反馈）
- [x] 支持按课程或时间段筛选

## 数据模型

`timeline_events` 表结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| student_id | TEXT | 学生学号 |
| event_type | TEXT | publish/submit/grade/feedback |
| title | TEXT | 事件标题 |
| description | TEXT | 事件描述 |
| course | TEXT | 所属课程 |
| related_id | TEXT | 关联 ID |
| event_time | TEXT | 事件发生时间 |
| created_at | TEXT | 记录创建时间 |

## API 端点

### GET /api/timeline

获取学生学习时间线事件。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| student_id | string | 是 | 学生学号 |
| course | string | 否 | 按课程筛选 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

## 原型页面

`prototype/timeline.html` — 垂直时间线布局，四种事件类型用不同颜色和图标区分。
