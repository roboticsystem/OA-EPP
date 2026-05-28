import json
import tempfile
import unittest
from pathlib import Path

from backend.app.review_prompts import (
    BUILTIN_TEMPLATE_IDS,
    PromptStore,
    build_reviewer_prompt_list,
)


class ReviewPromptStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prompts_dir = Path(self.tmp.name) / ".github" / "review-prompts"
        self.store = PromptStore(self.prompts_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_initializes_three_builtin_templates_on_disk(self):
        templates = self.store.list_templates()

        self.assertEqual([t["id"] for t in templates], BUILTIN_TEMPLATE_IDS)
        for template in templates:
            prompt_file = self.prompts_dir / template["file"]
            self.assertTrue(prompt_file.exists())
            self.assertGreater(len(prompt_file.read_text(encoding="utf-8")), 200)

        manifest = json.loads((self.prompts_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["default_template"], "general-code-review")

    def test_custom_template_copy_rename_delete_lifecycle(self):
        copied = self.store.copy_template("engineering-practice", "课程项目专项审查")

        renamed = self.store.rename_template(copied["id"], "课程项目最终审查")
        self.assertEqual(renamed["name"], "课程项目最终审查")
        self.assertFalse(renamed["built_in"])
        self.assertTrue((self.prompts_dir / renamed["file"]).exists())

        self.store.delete_template(renamed["id"])

        self.assertNotIn(renamed["id"], [t["id"] for t in self.store.list_templates()])
        self.assertFalse((self.prompts_dir / renamed["file"]).exists())

    def test_dry_run_caches_review_preview_and_clear_removes_trace_content(self):
        result = self.store.run_dry_run(
            template_id="security-comprehensive",
            pr_title="修复登录权限校验",
            pr_description="补充教师端接口鉴权",
            diff="diff --git a/backend/app/routers/teacher.py b/backend/app/routers/teacher.py\n+_require_teacher(token)",
        )

        self.assertEqual(result["ai_call_status"], "success")
        self.assertEqual(result["github_submission"], "not_submitted")
        self.assertEqual(result["template_id"], "security-comprehensive")
        self.assertTrue(result["prompt_version"])
        self.assertGreaterEqual(len(result["review_snippets"]), 3)

        cleared = self.store.clear_dry_run_traces()

        self.assertEqual(cleared["status"], "cleared")
        self.assertEqual(cleared["removed_draft_comments"], [])
        state = json.loads((self.prompts_dir / ".dry-run-state.json").read_text(encoding="utf-8"))
        self.assertNotIn("review_snippets", state)
        self.assertNotIn("diff", state)


class PrAgentConfigBuilderTest(unittest.TestCase):
    def test_builds_reviewer_prompt_list_from_default_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PromptStore(Path(tmp) / ".github" / "review-prompts")
            store.set_default_template("engineering-practice")

            prompts = build_reviewer_prompt_list(store.prompts_dir)

            self.assertGreaterEqual(len(prompts), 4)
            self.assertIn("工程实践规范检查", prompts[0])
            self.assertTrue(any("测试" in prompt for prompt in prompts))


if __name__ == "__main__":
    unittest.main()
