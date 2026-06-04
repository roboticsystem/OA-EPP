"""
F-T-003-AI: AI 自动审查服务测试
"""

import sys
import os
import importlib.util

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Directly load ai_review_service module to avoid transitively importing
# services/__init__.py which pulls in database/github_service dependencies.
_service_path = os.path.join(
    os.path.dirname(__file__), '..', 'app', 'services', 'ai_review_service.py'
)
# Import backend/app/database.py as well to ensure backend.app is a package
_db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'database.py')
_db_pkg = os.path.dirname(_db_path)
if _db_pkg not in sys.path:
    sys.path.insert(0, _db_pkg)

spec = importlib.util.spec_from_file_location(
    "ai_review_service", _service_path,
    submodule_search_locations=[]
)
ai_review = importlib.util.module_from_spec(spec)
sys.modules["ai_review_service"] = ai_review
spec.loader.exec_module(ai_review)

_normalize = ai_review._normalize
_parse_iso_date = ai_review._parse_iso_date
_strip_leading_emoji = ai_review._strip_leading_emoji
analyze_name_match = ai_review.analyze_name_match
analyze_commit_patterns = ai_review.analyze_commit_patterns
analyze_branch_strategy = ai_review.analyze_branch_strategy
analyze_pr_quality = ai_review.analyze_pr_quality
analyze_code_activity = ai_review.analyze_code_activity
run_full_ai_review = ai_review.run_full_ai_review


# ---------------------------------------------------------------------------
# 工具函数测试
# ---------------------------------------------------------------------------

def test_normalize():
    assert _normalize("张三") == "张三"
    assert _normalize("Zhang San") == "zhangsan"
    assert _normalize("Hello, World!") == "helloworld"
    assert _normalize("") == ""
    assert _normalize(None) == ""


def test_parse_iso_date():
    dt = _parse_iso_date("2024-01-15T10:30:00Z")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15

    dt2 = _parse_iso_date("2024-01-15T10:30:00")
    assert dt2 is not None
    assert dt2.hour == 10

    dt3 = _parse_iso_date("2024-01-15")
    assert dt3 is not None
    assert dt3.day == 15

    assert _parse_iso_date(None) is None
    assert _parse_iso_date("") is None
    assert _parse_iso_date("invalid") is None


def test_strip_leading_emoji():
    assert _strip_leading_emoji("🔥 Fix bug") == "Fix bug"
    assert _strip_leading_emoji("✅ 添加功能") == "添加功能"
    assert _strip_leading_emoji("Normal text") == "Normal text"
    assert _strip_leading_emoji("🚀✨ Refactor") == "Refactor"


# ---------------------------------------------------------------------------
# 姓名匹配测试（已有）
# ---------------------------------------------------------------------------

def test_exact_match_cjk():
    github_user = {"login": "zhangsan", "name": "张三", "bio": ""}
    res = analyze_name_match("张三", github_user)
    assert res["match"] is True
    assert res["score"] == 1.0


def test_mismatch():
    github_user = {"login": "johndoe", "name": "John Doe", "bio": "software engineer"}
    res = analyze_name_match("王五", github_user)
    assert res["match"] is False


def test_bio_match_cjk():
    github_user = {"login": "lisi", "name": "Li Si", "bio": "数据科学家 | Python 开发"}
    res = analyze_name_match("李四 数据科学家", github_user)
    assert res["match"] is True


def test_substring_match():
    github_user = {"login": "abc", "name": "张三丰", "bio": ""}
    res = analyze_name_match("张三", github_user)
    assert res["match"] is True
    assert res["score"] >= 0.8


# ---------------------------------------------------------------------------
# 提交分析测试 (F-T-003-AI)
# ---------------------------------------------------------------------------

def make_commits(count, days_spread=7, msg_quality="good"):
    """Helper: generate fake commit data."""
    from datetime import datetime, timedelta
    commits = []
    base = datetime(2024, 1, 1, 10, 0, 0)

    messages = {
        "good": [
            "feat: add user authentication module",
            "fix: resolve race condition in database query",
            "refactor: extract common validation logic",
            "docs: update API documentation for v2 endpoints",
            "test: add unit tests for export service",
            "chore: update dependencies to latest versions",
            "feat: implement batch export with progress tracking",
            "fix: handle edge case when file is empty",
            "perf: optimize database index for scores query",
            "style: format code according to PEP 8",
        ],
        "poor": [
            "update",
            "fix",
            ".",
            "aaa",
            "tmp",
            "WIP",
            "update code",
            "fix bug",
            "changes",
            "test",
        ],
    }

    msgs = messages.get(msg_quality, messages["good"])
    for i in range(count):
        date = base + timedelta(days=(i * days_spread // max(count, 1)), hours=i % 12)
        commits.append({
            "sha": f"abc{i:04d}",
            "message": msgs[i % len(msgs)],
            "author_name": "Test Student",
            "author_email": "test@test.com",
            "date": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "additions": 10 + i * 5,
            "deletions": i * 2,
        })
    return commits


def test_empty_commits():
    result = analyze_commit_patterns([])
    assert result["total_commits"] == 0
    assert result["message_quality_score"] == 0
    assert result["consistency_score"] == 0
    assert len(result["suggestions"]) > 0


def test_good_commit_messages():
    commits = make_commits(15, msg_quality="good")
    result = analyze_commit_patterns(commits)
    assert result["total_commits"] == 15
    assert result["message_quality_score"] >= 60
    assert result["message_quality"]["good"] > result["message_quality"]["poor"]


def test_poor_commit_messages():
    commits = make_commits(10, msg_quality="poor")
    result = analyze_commit_patterns(commits)
    assert result["total_commits"] == 10
    assert result["message_quality_score"] < 60
    assert result["message_quality"]["poor"] > 0


def test_commit_consistency():
    commits = make_commits(30, days_spread=14)
    result = analyze_commit_patterns(commits)
    assert result["coding_days"] > 0
    assert result["active_period_days"] > 0
    assert isinstance(result["avg_per_week"], (int, float))
    assert isinstance(result["max_per_day"], int)


def test_weekend_commit_detection():
    """Weekend-only commits should give high weekend_pct."""
    from datetime import datetime, timedelta
    commits = []
    # Jan 6, 2024 is Saturday; generate commits only on Saturdays and Sundays
    weekend_dates = []
    base = datetime(2024, 1, 6)  # Saturday
    for i in range(12):  # 12 commits spread over ~3 weeks
        # Add only weekend days (Sat/Sun)
        d = base + timedelta(weeks=i // 2, days=i % 2)  # Sat, Sun, Sat, Sun...
        if d.weekday() >= 5:
            weekend_dates.append(d)

    for i, date in enumerate(weekend_dates):
        commits.append({
            "sha": f"w{i:04d}",
            "message": f"feat: weekend work #{i}",
            "author_name": "Student",
            "author_email": "s@test.com",
            "date": date.strftime("%Y-%m-%dT10:00:00Z"),
            "additions": 5,
            "deletions": 0,
        })
    result = analyze_commit_patterns(commits)
    assert result["weekend_commit_pct"] > 90


# ---------------------------------------------------------------------------
# 分支策略分析测试 (F-T-003-AI)
# ---------------------------------------------------------------------------

def test_single_branch():
    branches = [{"name": "main", "protected": True}]
    result = analyze_branch_strategy(branches, [])
    assert result["total_branches"] == 1
    assert result["strategy_type"] == "single_branch"
    assert result["has_default_branch"] is True


def test_feature_branch_strategy():
    branches = [
        {"name": "main", "protected": True},
        {"name": "develop", "protected": False},
        {"name": "feature/login", "protected": False},
        {"name": "feature/dashboard", "protected": False},
        {"name": "fix/bug-123", "protected": False},
    ]
    result = analyze_branch_strategy(branches, [])
    assert result["total_branches"] == 5
    assert result["strategy_type"] == "gitflow_like"
    assert result["strategy_score"] >= 60


def test_bad_branch_names():
    branches = [
        {"name": "main", "protected": False},
        {"name": "test1", "protected": False},
        {"name": "tmp", "protected": False},
        {"name": "aaa", "protected": False},
    ]
    result = analyze_branch_strategy(branches, [])
    assert len(result["naming_issues"]) > 0
    assert result["naming_score"] < 80


def test_empty_branches():
    result = analyze_branch_strategy([], [])
    assert result["total_branches"] == 0
    assert result["strategy_type"] == "no_branches"


# ---------------------------------------------------------------------------
# PR 质量分析测试 (F-T-003-AI)
# ---------------------------------------------------------------------------

def make_prs(count, merged_ratio=0.7):
    prs = []
    for i in range(count):
        merged_at = f"2024-01-{15+i:02d}T10:00:00Z" if i < count * merged_ratio else None
        state = "closed" if merged_at else ("open" if i % 3 == 0 else "closed")
        prs.append({
            "number": i + 1,
            "title": f"feat: implement feature module {i+1} with comprehensive tests" if i % 2 == 0 else f"fix: bug {i+1}",
            "state": state,
            "user_login": "student",
            "created_at": f"2024-01-{10+i:02d}T10:00:00Z",
            "merged_at": merged_at,
            "additions": 50 + i * 20,
            "deletions": 10 + i * 5,
            "review_comments": 2 if i % 3 == 0 else 0,
            "url": f"https://github.com/user/repo/pull/{i+1}",
        })
    return prs


def test_empty_prs():
    result = analyze_pr_quality([])
    assert result["total_prs"] == 0
    assert result["overall_pr_score"] == 0


def test_good_prs():
    prs = make_prs(10, merged_ratio=0.9)
    result = analyze_pr_quality(prs)
    assert result["total_prs"] == 10
    assert result["merge_rate"] >= 50
    assert result["description_quality_score"] >= 0


def test_poor_prs():
    prs = [
        {
            "number": 1, "title": "fix", "state": "open",
            "user_login": "student", "created_at": "2024-01-01T10:00:00Z",
            "merged_at": None, "additions": 500, "deletions": 300,
            "review_comments": 0, "url": "https://github.com/test/pr/1",
        },
        {
            "number": 2, "title": "update", "state": "closed",
            "user_login": "student", "created_at": "2024-01-02T10:00:00Z",
            "merged_at": None, "additions": 1000, "deletions": 800,
            "review_comments": 0, "url": "https://github.com/test/pr/2",
        },
    ]
    result = analyze_pr_quality(prs)
    assert result["description_quality_score"] < 50
    assert result["merge_rate"] == 0.0


# ---------------------------------------------------------------------------
# 代码活跃度分析测试 (F-T-003-AI)
# ---------------------------------------------------------------------------

def test_inactive_repo():
    result = analyze_code_activity([], [], [])
    assert result["activity_level"] == "inactive"
    assert result["activity_score"] == 0
    assert result["total_actions"] == 0


def test_high_activity():
    commits = make_commits(40, msg_quality="good")
    branches = [{"name": "main"}, {"name": "develop"}, {"name": "feature/a"}, {"name": "feature/b"}]
    prs = make_prs(10)
    result = analyze_code_activity(commits, branches, prs)
    assert result["activity_level"] in ("high", "very_high")
    assert result["total_actions"] == 40 + 10 + 4
    assert result["activity_score"] >= 50


def test_hour_distribution():
    from datetime import datetime
    commits = []
    for h in range(24):
        commits.append({
            "sha": f"h{h:02d}",
            "message": f"commit at hour {h}",
            "author_name": "Student",
            "author_email": "s@test.com",
            "date": f"2024-01-15T{h:02d}:00:00Z",
            "additions": 5,
            "deletions": 0,
        })
    result = analyze_code_activity(commits, [], [])
    dist = result["active_hours_distribution"]
    total = sum(dist.values())
    assert total == 24


# ---------------------------------------------------------------------------
# 综合 AI 审查测试 (F-T-003-AI)
# ---------------------------------------------------------------------------

def test_full_review_empty_repo():
    github_data = {
        "commits": [],
        "branches": [],
        "pull_requests": [],
        "languages": {},
        "total_lines": 0,
    }
    result = run_full_ai_review(github_data, "测试学生", "20240001")
    assert result["overall_score"] < 30
    assert result["student_id"] == "20240001"
    assert result["student_name"] == "测试学生"
    assert "dimensions" in result
    assert "summary" in result
    assert "suggestions" in result


def test_full_review_basic_repo():
    commits = make_commits(20, msg_quality="good")
    branches = [
        {"name": "main", "protected": True},
        {"name": "feature/login", "protected": False},
        {"name": "feature/dashboard", "protected": False},
    ]
    prs = make_prs(5, merged_ratio=0.8)
    github_data = {
        "commits": commits,
        "branches": branches,
        "pull_requests": prs,
        "languages": {"Python": 5000, "JavaScript": 2000, "HTML": 1000},
        "total_lines": 8000,
    }
    result = run_full_ai_review(github_data, "张三", "20240002")

    assert "overall_score" in result
    assert result["overall_score"] >= 0
    assert result["overall_score"] <= 100
    assert result["grade"] in ("A", "B", "C", "D", "F")
    assert len(result["suggestions"]) > 0
    assert len(result["highlights"]) > 0
    assert len(result["risks"]) > 0

    # 验证维度存在
    dims = result["dimensions"]
    assert "commit_patterns" in dims
    assert "branch_strategy" in dims
    assert "pr_quality" in dims
    assert "code_activity" in dims
    assert "code_scale" in dims

    # 验证权重和为 1
    weights = result["weights"]
    weight_sum = sum(weights.values())
    assert abs(weight_sum - 1.0) < 0.01


def test_full_review_scores_bounded():
    """所有维度分数应在 0-100 范围内。"""
    github_data = {
        "commits": make_commits(25, msg_quality="poor"),
        "branches": [
            {"name": "main", "protected": False},
            {"name": "tmp", "protected": False},
        ],
        "pull_requests": make_prs(3, merged_ratio=0.3),
        "languages": {"Python": 500},
        "total_lines": 500,
    }
    result = run_full_ai_review(github_data, "test", "id")
    scores = result["scores"]
    for key, score in scores.items():
        assert 0 <= score <= 100, f"{key} score {score} out of bounds"


def test_full_review_grade_mapping():
    """验证评分与等级映射正确。"""
    github_data = {
        "commits": make_commits(0),
        "branches": [],
        "pull_requests": [],
        "languages": {},
        "total_lines": 0,
    }
    result = run_full_ai_review(github_data, "test", "id")
    assert result["grade"] == "F"
    assert result["grade_desc"] == "待改进"
