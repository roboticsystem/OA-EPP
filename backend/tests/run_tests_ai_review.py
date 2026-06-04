import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.tests import test_ai_review_service as tests


def run():
    tests.test_exact_match_cjk()
    tests.test_mismatch()
    tests.test_bio_match_cjk()
    print('All tests passed')


if __name__ == '__main__':
    run()
