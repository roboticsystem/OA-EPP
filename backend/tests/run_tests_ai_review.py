"""
F-T-003-AI: AI 自动审查服务测试运行器
"""
import sys
import os
import importlib.util

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import test module directly without triggering services/__init__.py chain
_test_path = os.path.join(os.path.dirname(__file__), 'test_ai_review_service.py')
spec = importlib.util.spec_from_file_location(
    "test_ai_review_service", _test_path
)
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)


def run():
    """运行所有 AI 审查服务测试。"""
    results = {"passed": 0, "failed": 0, "errors": []}

    test_funcs = [
        # 工具函数
        ("_normalize", tests.test_normalize),
        ("_parse_iso_date", tests.test_parse_iso_date),
        ("_strip_leading_emoji", tests.test_strip_leading_emoji),
        # 姓名匹配
        ("test_exact_match_cjk", tests.test_exact_match_cjk),
        ("test_mismatch", tests.test_mismatch),
        ("test_bio_match_cjk", tests.test_bio_match_cjk),
        ("test_substring_match", tests.test_substring_match),
        # 提交分析 (F-T-003-AI)
        ("test_empty_commits", tests.test_empty_commits),
        ("test_good_commit_messages", tests.test_good_commit_messages),
        ("test_poor_commit_messages", tests.test_poor_commit_messages),
        ("test_commit_consistency", tests.test_commit_consistency),
        ("test_weekend_commit_detection", tests.test_weekend_commit_detection),
        # 分支策略分析 (F-T-003-AI)
        ("test_single_branch", tests.test_single_branch),
        ("test_feature_branch_strategy", tests.test_feature_branch_strategy),
        ("test_bad_branch_names", tests.test_bad_branch_names),
        ("test_empty_branches", tests.test_empty_branches),
        # PR 质量分析 (F-T-003-AI)
        ("test_empty_prs", tests.test_empty_prs),
        ("test_good_prs", tests.test_good_prs),
        ("test_poor_prs", tests.test_poor_prs),
        # 代码活跃度分析 (F-T-003-AI)
        ("test_inactive_repo", tests.test_inactive_repo),
        ("test_high_activity", tests.test_high_activity),
        ("test_hour_distribution", tests.test_hour_distribution),
        # 综合 AI 审查 (F-T-003-AI)
        ("test_full_review_empty_repo", tests.test_full_review_empty_repo),
        ("test_full_review_basic_repo", tests.test_full_review_basic_repo),
        ("test_full_review_scores_bounded", tests.test_full_review_scores_bounded),
        ("test_full_review_grade_mapping", tests.test_full_review_grade_mapping),
    ]

    for name, fn in test_funcs:
        try:
            fn()
            results["passed"] += 1
            print(f"  PASS {name}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append((name, str(e)))
            print(f"  FAIL {name}: {e}")

    print()
    print(f"{'='*50}")
    print(f"Results: {results['passed']} passed, {results['failed']} failed")

    if results["errors"]:
        print("\nFailed tests:")
        for name, error in results["errors"]:
            print(f"  - {name}: {error}")

    print(f"{'='*50}")
    return results


if __name__ == '__main__':
    run()
