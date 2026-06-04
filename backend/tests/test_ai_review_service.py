import sys
import os

# Ensure workspace root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.services.ai_review_service import analyze_name_match


def test_exact_match_cjk():
    github_user = {"login": "zhangsan", "name": "张三", "bio": ""}
    res = analyze_name_match("张三", github_user)
    assert res["match"] is True


def test_mismatch():
    github_user = {"login": "johndoe", "name": "John Doe", "bio": "software engineer"}
    res = analyze_name_match("王五", github_user)
    assert res["match"] is False


def test_bio_match_cjk():
    github_user = {"login": "lisi", "name": "Li Si", "bio": "数据科学家 | Python 开发"}
    res = analyze_name_match("李四 数据科学家", github_user)
    assert res["match"] is True
