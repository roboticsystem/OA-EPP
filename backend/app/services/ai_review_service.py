"""
AI 自动审查服务 (F-T-003-AI)

对学生的 GitHub 仓库数据进行多维度自动化审查，包括：
- 提交行为分析（频率、消息质量、一致性）
- 分支策略分析
- PR 质量分析
- 代码活跃度模式分析
- 综合评分与 AI 评语生成

所有指标均基于 GitHub API 拉取的原始数据通过启发式规则计算得出，
无需依赖外部 AI API（可选集成）。
"""

import re
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _normalize(s: Optional[str]) -> str:
    """去除标点符号、转为小写，用于模糊匹配。"""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^0-9a-z一-鿿]+", "", s)
    return s


def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析 ISO 8601 格式日期字符串。"""
    if not date_str:
        return None
    date_str = str(date_str).replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _strip_leading_emoji(s: str) -> str:
    """移除字符串开头的 emoji 及修饰符（Variation Selector + ZWJ 序列等），保留后续文本。"""
    # 覆盖常见 emoji 范围：表情符号、交通与地图、装饰符号、补充符号与象形文字
    pattern = re.compile(
        r"^[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\U00002600-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF"
        r"️‍\U0001F1E0-\U0001F1FF\U0001F900-\U0001F9FF"
        r"\U0001FA00-\U0001FA6F\U0001F300-\U0001F5FF"
        r"\U00002300-\U000023FF\U00002B50\U00002714\U00002763\U00002764"
        r"\U0001F500-\U0001F53F]+"
    )
    return pattern.sub("", s).strip()


# ---------------------------------------------------------------------------
# 姓名匹配（已有功能，保留增强）
# ---------------------------------------------------------------------------

def analyze_name_match(expected_name: str, github_user: Dict[str, str]) -> Dict[str, object]:
    """Basic heuristic to compare student expected name with GitHub profile name.
    Returns dict: {match: bool, score: float, github_name: str, reason: str}
    """
    github_name = (github_user.get("name") or "").strip()
    github_bio = (github_user.get("bio") or "").strip()

    norm_expected = _normalize(expected_name)
    norm_github = _normalize(github_name)
    norm_bio = _normalize(github_bio)

    # exact match
    if norm_expected and norm_expected == norm_github:
        return {"match": True, "score": 1.0, "github_name": github_name, "reason": "完全匹配"}

    # substring match
    if norm_expected and norm_expected in norm_github:
        return {"match": True, "score": 0.85, "github_name": github_name, "reason": "姓名为 GitHub 名称的子串"}

    if norm_github and norm_github in norm_expected:
        return {"match": True, "score": 0.8, "github_name": github_name, "reason": "GitHub 名称为姓名的子串"}

    # bio contains name tokens
    if norm_expected and norm_expected in norm_bio:
        return {"match": True, "score": 0.7, "github_name": github_name, "reason": "姓名出现在 GitHub bio 中"}

    # token overlap heuristic
    def tokens(s: str):
        if not s:
            return set()
        if re.search(r"[一-鿿]", s):
            return set(list(s))
        return set(re.findall(r"[a-z0-9]+", s))

    t_expected = tokens(norm_expected)
    t_github = tokens(norm_github) | tokens(norm_bio)
    if t_expected and t_github:
        overlap = t_expected & t_github
        ratio = len(overlap) / max(len(t_expected), 1)
        if ratio >= 0.5:
            return {"match": True, "score": round(0.6 + 0.4 * ratio, 2),
                    "github_name": github_name, "reason": f"部分匹配，重合率 {ratio:.2f}"}

    return {"match": False, "score": 0.0, "github_name": github_name, "reason": "未能在 GitHub 资料中找到明显匹配"}


# ---------------------------------------------------------------------------
# 提交行为分析
# ---------------------------------------------------------------------------

def analyze_commit_patterns(commits: List[Dict[str, Any]]) -> Dict[str, object]:
    """分析提交模式：频率、消息质量、规律性。

    Args:
        commits: GitHub commits 列表，每项含 sha, message, author_name, author_email, date, additions, deletions

    Returns:
        {
            total_commits, avg_per_week, max_per_day,
            message_quality_score (0-100),
            message_quality: {good, needs_improvement, poor},
            consistency_score (0-100),
            coding_days, active_period_days,
            weekend_commit_pct, late_night_commit_pct,
            avg_message_length,
            suggestions: [...]
        }
    """
    total = len(commits)
    if total == 0:
        return {
            "total_commits": 0,
            "avg_per_week": 0,
            "max_per_day": 0,
            "message_quality_score": 0,
            "message_quality": {"good": 0, "needs_improvement": 0, "poor": 0},
            "consistency_score": 0,
            "coding_days": 0,
            "active_period_days": 0,
            "weekend_commit_pct": 0,
            "late_night_commit_pct": 0,
            "avg_message_length": 0,
            "suggestions": ["暂无提交记录，建议开始提交代码到仓库"],
        }

    # 按日期分组统计
    date_map: Dict[str, int] = defaultdict(int)
    dates_list: List[datetime] = []
    msg_lengths: List[int] = []

    weekend_count = 0
    late_night_count = 0  # 22:00-06:00

    for c in commits:
        dt = _parse_iso_date(c.get("date"))
        if dt:
            date_key = dt.strftime("%Y-%m-%d")
            date_map[date_key] += 1
            dates_list.append(dt)
            # weekend
            if dt.weekday() >= 5:  # Saturday=5, Sunday=6
                weekend_count += 1
            # late night
            if dt.hour >= 22 or dt.hour < 6:
                late_night_count += 1

        msg = (c.get("message") or "").strip()
        msg_lengths.append(len(msg))

    # 频率计算
    coding_days = len(date_map)
    if dates_list:
        min_date = min(dates_list)
        max_date = max(dates_list)
        active_days = (max_date - min_date).days + 1
        active_weeks = max(active_days / 7.0, 0.14)  # 至少 1 天
        avg_per_week = round(total / active_weeks, 1)
        max_per_day = max(date_map.values())
    else:
        active_days = 0
        avg_per_week = 0
        max_per_day = 0

    # 消息质量评估
    good_count = 0
    needs_improvement_count = 0
    poor_count = 0
    quality_suggestions: List[str] = []

    good_keywords = [
        "fix", "add", "update", "remove", "refactor", "merge", "implement",
        "修复", "添加", "更新", "删除", "重构", "实现", "合并",
        "feat", "chore", "docs", "test", "style", "perf", "ci",
    ]

    for c in commits:
        msg = (c.get("message") or "").strip()
        msg_lower = msg.lower()
        length = len(msg)

        # 评分逻辑
        score = 0
        if length >= 10:
            score += 1
        if length >= 30:
            score += 1
        if length >= 80:
            score += 1
        if any(kw in msg_lower for kw in good_keywords):
            score += 1
        if not msg.startswith(".") and not msg.startswith("Update") and not msg == "update":
            score += 1
        # 是否包含描述性内容（非纯标点/emoji）
        cleaned = _strip_leading_emoji(msg)
        if len(cleaned) >= 5:
            score += 1

        if score >= 4:
            good_count += 1
        elif score >= 2:
            needs_improvement_count += 1
        else:
            poor_count += 1

    if total > 0:
        message_quality_score = round(
            (good_count * 100 + needs_improvement_count * 50) / total, 0
        )
    else:
        message_quality_score = 0

    if poor_count > total * 0.3:
        quality_suggestions.append("超过30%的提交信息质量较低，建议使用更详细的提交信息描述变更内容")
    if total > 0 and sum(msg_lengths) / total < 20:
        quality_suggestions.append("提交信息平均长度较短，建议增加描述性内容")

    # 一致性评分
    if coding_days >= 10:
        commits_per_day = [date_map[d] for d in sorted(date_map)]
        if len(commits_per_day) >= 2:
            avg_per_day = total / coding_days if coding_days else 0
            variance = sum((c - avg_per_day) ** 2 for c in commits_per_day) / len(commits_per_day)
            std_dev = variance ** 0.5
            # 变异系数
            cv = std_dev / max(avg_per_day, 0.01)
            consistency_score = round(max(0, min(100, 100 - cv * 50)), 0)
        else:
            consistency_score = 50
    else:
        consistency_score = min(coding_days * 10, 50)

    consistency_suggestions: List[str] = []
    if consistency_score < 40:
        consistency_suggestions.append("提交频率波动较大，建议保持规律的提交习惯，避免集中在截止日前大量提交")
    if coding_days > 0 and max_per_day > coding_days * 0.5 and max_per_day > 5:
        consistency_suggestions.append(f"单日最高提交 {max_per_day} 次，存在突击提交现象")

    # 周末/深夜占比
    weekend_pct = round(weekend_count / total * 100, 1) if total > 0 else 0
    late_night_pct = round(late_night_count / total * 100, 1) if total > 0 else 0

    time_suggestions: List[str] = []
    if weekend_pct > 50:
        time_suggestions.append(f"周末提交占比 {weekend_pct}%，可能存在工作量安排不均的问题")
    if late_night_pct > 30:
        time_suggestions.append(f"深夜提交（22:00-06:00）占比 {late_night_pct}%，建议调整作息，在正常工作时间提交代码")

    # 汇总建议
    all_suggestions = quality_suggestions + consistency_suggestions + time_suggestions
    if not all_suggestions and total > 0:
        all_suggestions.append("提交习惯良好，保持当前节奏")

    return {
        "total_commits": total,
        "avg_per_week": avg_per_week,
        "max_per_day": max_per_day,
        "message_quality_score": message_quality_score,
        "message_quality": {
            "good": good_count,
            "needs_improvement": needs_improvement_count,
            "poor": poor_count,
        },
        "consistency_score": consistency_score,
        "coding_days": coding_days,
        "active_period_days": active_days,
        "weekend_commit_pct": weekend_pct,
        "late_night_commit_pct": late_night_pct,
        "avg_message_length": round(sum(msg_lengths) / total, 0) if total > 0 else 0,
        "suggestions": all_suggestions,
    }


# ---------------------------------------------------------------------------
# 分支策略分析
# ---------------------------------------------------------------------------

def analyze_branch_strategy(branches: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> Dict[str, object]:
    """分析分支使用策略：命名规范、保护分支、分支数量合理性。

    Args:
        branches: GitHub branches 列表
        commits: GitHub commits 列表

    Returns:
        {
            total_branches, protected_branches,
            naming_score (0-100),
            strategy_score (0-100),
            strategy_type: "single_branch" | "basic" | "feature_branch" | "gitflow_like",
            has_default_branch,
            naming_issues: [...],
            suggestions: [...]
        }
    """
    total = len(branches)
    if total == 0:
        return {
            "total_branches": 0,
            "protected_branches": 0,
            "naming_score": 0,
            "strategy_score": 0,
            "strategy_type": "no_branches",
            "has_default_branch": False,
            "naming_issues": [],
            "suggestions": ["仓库没有分支记录，请确认仓库状态"],
        }

    protected_count = sum(1 for b in branches if b.get("protected"))

    # 命名规范检查
    good_naming_patterns = [
        r"^(main|master|develop|dev)$",
        r"^(feature|feat)[/-].+",
        r"^(bugfix|fix|hotfix)[/-].+",
        r"^(release|rel)[/-].+",
        r"^(chore|docs|test|refactor)[/-].+",
        r"^[a-z0-9]+([-_][a-z0-9]+)*$",
    ]

    bad_naming_patterns = [
        r"^test\d*$",
        r"^tmp",
        r"^temp",
        r"^aaa",
        r"^111",
        r"^xxx",
        r"^untitled",
        r"^new-branch",
        r"^my-branch",
    ]

    naming_issues: List[str] = []
    good_name_count = 0

    default_branches = {"main", "master"}
    has_default = False

    for b in branches:
        name = b.get("name", "")
        if name in default_branches:
            has_default = True
            good_name_count += 1
            continue

        is_good = any(re.match(p, name) for p in good_naming_patterns)
        is_bad = any(re.match(p, name) for p in bad_naming_patterns)

        if is_bad:
            naming_issues.append(f"分支 '{name}' 命名不规范，无实际含义")
        elif is_good:
            good_name_count += 1
        else:
            naming_issues.append(f"分支 '{name}' 命名建议改进，推荐使用 feature/xxx 或 fix/xxx 格式")

    naming_score = round(good_name_count / total * 100, 0) if total > 0 else 0

    # 策略类型判断
    has_feature_branches = any(
        "feature" in (b.get("name") or "").lower() or "feat/" in (b.get("name") or "").lower()
        for b in branches
    )
    has_develop = any(
        re.match(r"^(develop|dev)$", b.get("name", "")) for b in branches
    )

    if total == 1:
        strategy_type = "single_branch"
        strategy_desc = "仅使用单一分支"
    elif has_default and has_develop and has_feature_branches:
        strategy_type = "gitflow_like"
        strategy_desc = "类 GitFlow 工作流"
    elif has_feature_branches:
        strategy_type = "feature_branch"
        strategy_desc = "Feature Branch 工作流"
    elif total <= 3:
        strategy_type = "basic"
        strategy_desc = "基础分支策略（主分支 + 少量功能分支）"
    else:
        strategy_type = "custom"
        strategy_desc = "自定义分支策略"

    # 综合策略评分
    strategy_score = naming_score
    if has_default:
        strategy_score = min(100, strategy_score + 10)
    if protected_count > 0:
        strategy_score = min(100, strategy_score + 10)
    if total >= 3 and strategy_type in ("feature_branch", "gitflow_like"):
        strategy_score = min(100, strategy_score + 10)

    suggestions: List[str] = []
    if not has_default:
        suggestions.append("仓库缺少默认分支（main/master），建议创建")
    if naming_issues:
        suggestions.append(f"发现 {len(naming_issues)} 个命名问题")
    if total == 1 and len(commits) > 20:
        suggestions.append("提交数量较多但仅使用单一分支，建议使用功能分支隔离开发")
    if not suggestions and total > 0:
        suggestions.append("分支管理策略良好")

    return {
        "total_branches": total,
        "protected_branches": protected_count,
        "naming_score": naming_score,
        "strategy_score": strategy_score,
        "strategy_type": strategy_type,
        "strategy_desc": strategy_desc,
        "has_default_branch": has_default,
        "naming_issues": naming_issues[:5],
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# PR 质量分析
# ---------------------------------------------------------------------------

def analyze_pr_quality(pull_requests: List[Dict[str, Any]]) -> Dict[str, object]:
    """分析 PR 质量：描述完整度、评审参与度、合并效率。

    Args:
        pull_requests: GitHub PR 列表

    Returns:
        {
            total_prs, open_prs, merged_prs, closed_prs,
            merge_rate, avg_description_length,
            description_quality_score (0-100),
            review_engagement_score (0-100),
            overall_pr_score (0-100),
            suggestions: [...]
        }
    """
    total = len(pull_requests)
    if total == 0:
        return {
            "total_prs": 0,
            "open_prs": 0,
            "merged_prs": 0,
            "closed_prs": 0,
            "merge_rate": 0.0,
            "avg_description_length": 0,
            "description_quality_score": 0,
            "review_engagement_score": 0,
            "overall_pr_score": 0,
            "suggestions": ["暂无 PR 记录，建议开始使用 PR 进行代码审查"],
        }

    merged = sum(1 for pr in pull_requests if pr.get("merged_at"))
    open_prs = sum(1 for pr in pull_requests if pr.get("state") == "open")
    closed_not_merged = sum(1 for pr in pull_requests if pr.get("state") == "closed" and not pr.get("merged_at"))
    merge_rate = round(merged / total * 100, 1) if total > 0 else 0.0

    # 描述长度分析
    desc_lengths: List[int] = []
    good_desc = 0
    for pr in pull_requests:
        title = (pr.get("title") or "").strip()
        desc_lengths.append(len(title))
        if len(title) >= 20:
            good_desc += 1

    avg_desc_len = round(sum(desc_lengths) / total, 0)
    desc_score = round(good_desc / total * 100, 0) if total > 0 else 0

    # 评审参与度（基于 review_comments 数量）
    total_reviews = sum(pr.get("review_comments", 0) for pr in pull_requests)
    avg_reviews = round(total_reviews / total, 1) if total > 0 else 0

    # 规模分析
    total_additions = sum(pr.get("additions", 0) for pr in pull_requests)
    total_deletions = sum(pr.get("deletions", 0) for pr in pull_requests)
    avg_size = round((total_additions + total_deletions) / total, 0) if total > 0 else 0

    review_score = min(100, round(avg_reviews * 20 + 20, 0))

    # 综合评分
    overall = round(desc_score * 0.4 + merge_rate * 0.3 + review_score * 0.3, 0)

    suggestions: List[str] = []
    if desc_score < 50:
        suggestions.append("PR 标题普遍偏短，建议使用更详细的标题描述变更内容")
    if merge_rate < 50 and total > 3:
        suggestions.append(f"PR 合并率仅 {merge_rate}%，建议及时处理或关闭不需要的 PR")
    if avg_size > 500:
        suggestions.append(f"PR 平均变更量 {avg_size} 行，建议拆分为更小的 PR 便于审查")
    if avg_reviews < 0.5 and total > 3:
        suggestions.append("PR 评审参与度较低，建议增加代码审查环节")
    if not suggestions:
        suggestions.append("PR 管理良好")

    return {
        "total_prs": total,
        "open_prs": open_prs,
        "merged_prs": merged,
        "closed_prs": closed_not_merged,
        "merge_rate": merge_rate,
        "avg_description_length": avg_desc_len,
        "description_quality_score": desc_score,
        "review_engagement_score": review_score,
        "avg_review_comments": avg_reviews,
        "avg_pr_size": avg_size,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "overall_pr_score": overall,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# 代码活跃度分析
# ---------------------------------------------------------------------------

def analyze_code_activity(
    commits: List[Dict[str, Any]],
    branches: List[Dict[str, Any]],
    pull_requests: List[Dict[str, Any]]
) -> Dict[str, object]:
    """分析代码活跃度模式：贡献频率、活跃时段、项目周期。

    Returns:
        {
            activity_score (0-100),
            activity_level: "inactive" | "low" | "moderate" | "high" | "very_high",
            total_actions,  # commits + PRs + branch_creations
            active_hours_distribution: {morning, afternoon, evening, night},
            peak_day_of_week,
            project_duration_days,
            suggestions: [...]
        }
    """
    total_commits = len(commits)
    total_prs = len(pull_requests)
    total_branches = len(branches)
    total_actions = total_commits + total_prs + total_branches

    if total_actions == 0:
        return {
            "activity_score": 0,
            "activity_level": "inactive",
            "total_actions": 0,
            "active_hours_distribution": {"morning": 0, "afternoon": 0, "evening": 0, "night": 0},
            "peak_day_of_week": "unknown",
            "project_duration_days": 0,
            "suggestions": ["仓库暂无活动记录，建议开始提交代码"],
        }

    # 时段分布
    hour_buckets = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
    day_of_week_counter = Counter()

    all_dates: List[datetime] = []
    for c in commits:
        dt = _parse_iso_date(c.get("date"))
        if dt:
            all_dates.append(dt)
            day_of_week_counter[dt.strftime("%A")] += 1
            h = dt.hour
            if 6 <= h < 12:
                hour_buckets["morning"] += 1
            elif 12 <= h < 18:
                hour_buckets["afternoon"] += 1
            elif 18 <= h < 22:
                hour_buckets["evening"] += 1
            else:
                hour_buckets["night"] += 1

    for pr in pull_requests:
        dt = _parse_iso_date(pr.get("created_at"))
        if dt:
            all_dates.append(dt)
            day_of_week_counter[dt.strftime("%A")] += 1

    # 活跃度评级
    if total_actions < 5:
        activity_level = "low"
        activity_score = max(10, total_actions * 5)
    elif total_actions < 20:
        activity_level = "moderate"
        activity_score = 40
    elif total_actions < 50:
        activity_level = "high"
        activity_score = 70
    else:
        activity_level = "very_high"
        activity_score = min(100, 70 + (total_actions - 50) // 5)

    # 项目周期
    project_duration = 0
    if len(all_dates) >= 2:
        project_duration = (max(all_dates) - min(all_dates)).days

    # 峰值
    peak_day = day_of_week_counter.most_common(1)[0][0] if day_of_week_counter else "unknown"
    # 翻译星期
    day_cn = {"Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
              "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"}
    peak_day_cn = day_cn.get(peak_day, peak_day)

    suggestions: List[str] = []
    if activity_level in ("inactive", "low"):
        suggestions.append("仓库活跃度较低，建议增加提交频率和参与度")
    if project_duration > 30 and total_commits < 10:
        suggestions.append(f"项目已持续 {project_duration} 天但提交量偏少，建议增加开发投入")
    if hour_buckets["night"] > sum(hour_buckets.values()) * 0.5:
        suggestions.append("深夜提交占比过高，建议调整作息")
    if not suggestions:
        suggestions.append("代码活跃度良好")

    return {
        "activity_score": activity_score,
        "activity_level": activity_level,
        "total_actions": total_actions,
        "active_hours_distribution": hour_buckets,
        "peak_day_of_week": peak_day_cn,
        "project_duration_days": project_duration,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# 综合 AI 审查
# ---------------------------------------------------------------------------

def run_full_ai_review(
    github_data: Dict[str, Any],
    student_name: str = "",
    student_id: str = "",
) -> Dict[str, object]:
    """对学生的 GitHub 仓库执行完整的 AI 自动审查。

    Args:
        github_data: GitHubService.get_full_data() 的返回结果
        student_name: 学生姓名
        student_id: 学生学号

    Returns:
        AIReviewResult 字典，包含各维度分析结果和综合评分
    """
    commits: List[Dict] = github_data.get("commits", [])
    branches: List[Dict] = github_data.get("branches", [])
    pull_requests: List[Dict] = github_data.get("pull_requests", [])
    languages: Dict[str, int] = github_data.get("languages", {})
    total_lines: int = github_data.get("total_lines", 0)

    # 各维度分析
    commit_analysis = analyze_commit_patterns(commits)
    branch_analysis = analyze_branch_strategy(branches, commits)
    pr_analysis = analyze_pr_quality(pull_requests)
    activity_analysis = analyze_code_activity(commits, branches, pull_requests)

    # 代码规模评估
    lang_count = len(languages)
    if total_lines > 10000:
        scale_level = "large"
        scale_score = 90
    elif total_lines > 3000:
        scale_level = "medium"
        scale_score = 70
    elif total_lines > 500:
        scale_level = "small"
        scale_score = 50
    else:
        scale_level = "tiny"
        scale_score = 20

    # ---- 综合评分计算 ----
    scores = {
        "commit_quality": commit_analysis.get("message_quality_score", 0),
        "commit_consistency": commit_analysis.get("consistency_score", 0),
        "branch_strategy": branch_analysis.get("strategy_score", 0),
        "pr_quality": pr_analysis.get("overall_pr_score", 0),
        "activity": activity_analysis.get("activity_score", 0),
        "code_scale": scale_score,
    }

    # 权重分配
    weights = {
        "commit_quality": 0.25,
        "commit_consistency": 0.15,
        "branch_strategy": 0.15,
        "pr_quality": 0.20,
        "activity": 0.15,
        "code_scale": 0.10,
    }

    overall_score = round(
        sum(scores[k] * weights[k] for k in weights),
        0
    )

    # 评级
    if overall_score >= 85:
        grade = "A"
        grade_desc = "优秀"
    elif overall_score >= 70:
        grade = "B"
        grade_desc = "良好"
    elif overall_score >= 55:
        grade = "C"
        grade_desc = "中等"
    elif overall_score >= 40:
        grade = "D"
        grade_desc = "及格"
    else:
        grade = "F"
        grade_desc = "待改进"

    # 汇总建议
    all_suggestions: List[str] = []
    for analysis, label in [
        (commit_analysis, "提交"),
        (branch_analysis, "分支"),
        (pr_analysis, "PR"),
        (activity_analysis, "活跃度"),
    ]:
        for s in analysis.get("suggestions", []):
            all_suggestions.append(f"[{label}] {s}")

    # 生成 AI 自动评语摘要
    summary = _generate_review_summary(
        overall_score=overall_score,
        grade=grade,
        grade_desc=grade_desc,
        commit_analysis=commit_analysis,
        branch_analysis=branch_analysis,
        pr_analysis=pr_analysis,
        activity_analysis=activity_analysis,
        total_lines=total_lines,
        lang_count=lang_count,
        student_name=student_name,
    )

    # 亮点和风险点
    highlights = _identify_highlights(commit_analysis, branch_analysis, pr_analysis, activity_analysis)
    risks = _identify_risks(commit_analysis, branch_analysis, pr_analysis, activity_analysis)

    return {
        "student_name": student_name,
        "student_id": student_id,
        "overall_score": overall_score,
        "grade": grade,
        "grade_desc": grade_desc,
        "dimensions": {
            "commit_patterns": commit_analysis,
            "branch_strategy": branch_analysis,
            "pr_quality": pr_analysis,
            "code_activity": activity_analysis,
            "code_scale": {
                "total_lines": total_lines,
                "language_count": lang_count,
                "languages": languages,
                "scale_level": scale_level,
                "scale_score": scale_score,
            },
        },
        "scores": scores,
        "weights": weights,
        "summary": summary,
        "highlights": highlights,
        "risks": risks,
        "suggestions": all_suggestions[:10],
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _generate_review_summary(
    overall_score: float,
    grade: str,
    grade_desc: str,
    commit_analysis: dict,
    branch_analysis: dict,
    pr_analysis: dict,
    activity_analysis: dict,
    total_lines: int,
    lang_count: int,
    student_name: str,
) -> str:
    """生成 AI 审查摘要文字。"""
    name = student_name or "同学"

    parts = [
        f"综合评分 {overall_score} 分（{grade_desc}），"
        f"仓库代码总量约 {total_lines:,} 行，使用 {lang_count} 种编程语言。"
    ]

    # 提交方面
    commit_score = commit_analysis.get("message_quality_score", 0)
    total_commits = commit_analysis.get("total_commits", 0)
    if commit_score >= 70:
        parts.append(f"提交信息质量较好（{total_commits} 次提交），commit message 描述清晰。")
    elif total_commits > 0:
        parts.append(f"已提交 {total_commits} 次，但提交信息质量有待提升。")

    # 分支方面
    strategy_type = branch_analysis.get("strategy_desc", "")
    total_branches = branch_analysis.get("total_branches", 0)
    if total_branches >= 2:
        parts.append(f"分支管理采用'{strategy_type}'（{total_branches} 个分支）。")
    elif total_branches == 1:
        parts.append("仅使用单一分支进行开发，建议引入功能分支管理。")

    # PR 方面
    pr_merge_rate = pr_analysis.get("merge_rate", 0)
    total_prs = pr_analysis.get("total_prs", 0)
    if total_prs > 0:
        parts.append(f"共创建 {total_prs} 个 PR，合并率 {pr_merge_rate}%。")

    # 活跃度
    activity_level = activity_analysis.get("activity_level", "")
    level_cn = {"inactive": "不活跃", "low": "较低", "moderate": "中等", "high": "较高", "very_high": "非常高"}
    parts.append(f"整体开发活跃度{level_cn.get(activity_level, activity_level)}。")

    return "".join(parts)


def _identify_highlights(
    commit_analysis: dict,
    branch_analysis: dict,
    pr_analysis: dict,
    activity_analysis: dict,
) -> List[str]:
    """识别代码仓库的亮点。"""
    highlights: List[str] = []

    if commit_analysis.get("message_quality_score", 0) >= 80:
        highlights.append("✅ 提交信息质量优秀，commit message 规范清晰")
    if commit_analysis.get("consistency_score", 0) >= 70:
        highlights.append("✅ 提交频率稳定，开发节奏良好")
    if branch_analysis.get("strategy_score", 0) >= 70:
        highlights.append(f"✅ 分支策略合理（{branch_analysis.get('strategy_desc', '')}）")
    if pr_analysis.get("merge_rate", 0) >= 80:
        highlights.append("✅ PR 合并率高，代码审查流程运作良好")
    if activity_analysis.get("activity_score", 0) >= 70:
        highlights.append("✅ 开发活跃度高，持续投入")
    if commit_analysis.get("weekend_commit_pct", 100) < 30 and commit_analysis.get("total_commits", 0) > 10:
        highlights.append("✅ 工作时间提交为主，作息规律")
    if branch_analysis.get("protected_branches", 0) > 0:
        highlights.append("✅ 使用分支保护，重视代码质量")

    if not highlights:
        highlights.append("📝 暂无特别亮点，持续改进中")

    return highlights


def _identify_risks(
    commit_analysis: dict,
    branch_analysis: dict,
    pr_analysis: dict,
    activity_analysis: dict,
) -> List[str]:
    """识别代码仓库的风险点。"""
    risks: List[str] = []

    if commit_analysis.get("message_quality_score", 100) < 40:
        risks.append("⚠️ 提交信息质量较低，不利于代码追溯和团队协作")
    if commit_analysis.get("consistency_score", 100) < 30 and commit_analysis.get("total_commits", 0) > 5:
        risks.append("⚠️ 提交频率波动大，可能存在突击提交（deadline rush）")
    if commit_analysis.get("late_night_commit_pct", 0) > 50:
        risks.append("⚠️ 深夜提交占比过高，可能影响代码质量和身体健康")
    if branch_analysis.get("total_branches", 0) == 1 and commit_analysis.get("total_commits", 0) > 20:
        risks.append("⚠️ 大量提交在单一分支进行，缺少分支隔离，风险较高")
    if pr_analysis.get("merge_rate", 100) < 30 and pr_analysis.get("total_prs", 0) > 5:
        risks.append("⚠️ PR 合并率过低，可能存在大量被废弃的工作")
    if activity_analysis.get("activity_level", "") in ("inactive", "low"):
        risks.append("⚠️ 仓库活跃度较低，开发进度可能滞后")
    if commit_analysis.get("avg_message_length", 0) < 15 and commit_analysis.get("total_commits", 0) > 10:
        risks.append("⚠️ 提交信息平均长度过短，建议补充有意义的描述")

    if not risks:
        risks.append("✅ 未发现明显风险点")

    return risks


# ---------------------------------------------------------------------------
# 可选：AI API 集成（当配置了 AI_API_KEY 时启用）
# ---------------------------------------------------------------------------

def _get_ai_api_config() -> Optional[Dict[str, str]]:
    """获取可选的 AI API 配置。"""
    api_key = os.environ.get("AI_API_KEY", "")
    api_base = os.environ.get("AI_API_BASE", "https://api.openai.com/v1")
    api_model = os.environ.get("AI_MODEL", "gpt-4o-mini")

    if not api_key:
        return None
    return {"key": api_key, "base": api_base, "model": api_model}


async def ai_generate_review_comment(
    review_data: Dict[str, Any],
    custom_prompt: Optional[str] = None,
) -> Optional[str]:
    """（可选）调用外部 AI API 生成更智能的审查评语。

    需要设置环境变量：
    - AI_API_KEY: API 密钥
    - AI_API_BASE: API 基础 URL（默认 OpenAI）
    - AI_MODEL: 模型名称（默认 gpt-4o-mini）

    Args:
        review_data: run_full_ai_review 的返回结果
        custom_prompt: 自定义提示词

    Returns:
        AI 生成的评语文本，或 None（未配置 API）
    """
    config = _get_ai_api_config()
    if not config:
        return None

    import httpx

    dimensions = review_data.get("dimensions", {})
    prompt = custom_prompt or (
        f"你是一位代码审查专家。请根据以下学生代码仓库的自动化分析结果，"
        f"用中文撰写一段 150-300 字的评语，包括：总体评价、优点、需要改进的地方、具体建议。\n\n"
        f"学生：{review_data.get('student_name', '未知')}\n"
        f"综合评分：{review_data.get('overall_score', 0)} 分（{review_data.get('grade_desc', '')}）\n"
        f"提交分析：{json.dumps(dimensions.get('commit_patterns', {}), ensure_ascii=False)}\n"
        f"分支分析：{json.dumps(dimensions.get('branch_strategy', {}), ensure_ascii=False)}\n"
        f"PR 分析：{json.dumps(dimensions.get('pr_quality', {}), ensure_ascii=False)}\n"
        f"活跃度分析：{json.dumps(dimensions.get('code_activity', {}), ensure_ascii=False)}\n"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{config['base']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": "你是一位专业的代码审查专家，擅长对学生的代码仓库进行评价和给出建设性建议。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            return None
    except Exception:
        return None
