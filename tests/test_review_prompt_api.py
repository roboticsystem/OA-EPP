import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from backend.app.auth_utils import create_token
from backend.app.routers import teacher


class ReviewPromptApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["REVIEW_PROMPTS_DIR"] = str(Path(self.tmp.name) / ".github" / "review-prompts")
        app = FastAPI()
        app.include_router(teacher.router)
        self.client = TestClient(app)
        self.headers = {"Authorization": f"Bearer {create_token({'role': 'teacher'})}"}

    def tearDown(self):
        os.environ.pop("REVIEW_PROMPTS_DIR", None)
        self.tmp.cleanup()

    def test_lists_templates_and_returns_content(self):
        response = self.client.get("/api/teacher/review-prompts", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["templates"]), 3)
        self.assertEqual(body["default_template"], "general-code-review")

        detail = self.client.get(
            "/api/teacher/review-prompts/security-comprehensive",
            headers=self.headers,
        )
        self.assertEqual(detail.status_code, 200)
        self.assertIn("{diff}", detail.json()["content"])

    def test_creates_copies_renames_and_deletes_custom_templates(self):
        created = self.client.post(
            "/api/teacher/review-prompts",
            headers=self.headers,
            json={
                "name": "专项审查",
                "description": "课程专项审查模板",
                "content": "# 专项审查\n\n请检查 {diff}",
            },
        ).json()

        copied = self.client.post(
            f"/api/teacher/review-prompts/{created['id']}/copy",
            headers=self.headers,
            json={"name": "专项审查副本"},
        ).json()
        self.assertFalse(copied["built_in"])

        renamed = self.client.patch(
            f"/api/teacher/review-prompts/{copied['id']}/rename",
            headers=self.headers,
            json={"name": "专项审查终版"},
        ).json()
        self.assertEqual(renamed["name"], "专项审查终版")

        deleted = self.client.delete(
            f"/api/teacher/review-prompts/{renamed['id']}",
            headers=self.headers,
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["ok"])

    def test_dry_run_and_clear_are_platform_only(self):
        dry_run = self.client.post(
            "/api/teacher/review-prompts/dry-run",
            headers=self.headers,
            json={
                "template_id": "general-code-review",
                "pr_title": "新增成绩导出",
                "pr_description": "导出 Excel",
                "diff": "+return StreamingResponse(buf)",
            },
        )

        self.assertEqual(dry_run.status_code, 200)
        self.assertEqual(dry_run.json()["github_submission"], "not_submitted")
        self.assertIn("prompt_version", dry_run.json())

        cleared = self.client.delete("/api/teacher/review-prompts/dry-run", headers=self.headers)
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(cleared.json()["status"], "cleared")


if __name__ == "__main__":
    unittest.main()
