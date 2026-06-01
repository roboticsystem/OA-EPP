"""F-D-009 Commitlint 规则配置 — Reflex State

对应 TDD 测试: tests/reflex/test_F_D_009_commitlint.py
"""

from oaepp.states.commitlint_engine import build_commitlintrc, generate_workflow_yml


class CommitlintState:
    rule_set: str = "conventional"
    is_enabled: bool = True
    recent_failures: list = []
    type_enum: list = ["feat", "fix", "refactor", "style", "test", "docs", "chore"]
    header_max_length: int = 100
    subject_min_length: int = 5
    MAX_FAILURES: int = 5

    def save_config(self) -> dict:
        """生成 .commitlintrc.json 和 commitlint.yml 配置文件内容"""
        rc = build_commitlintrc(
            type_enum=self.type_enum,
            header_max_length=self.header_max_length,
            subject_min_length=self.subject_min_length,
            is_enabled=self.is_enabled,
        )
        workflow = generate_workflow_yml()
        return {
            "commitlintrc": {
                "path": ".commitlintrc.json",
                "content": rc,
            },
            "workflow": {
                "path": ".github/workflows/commitlint.yml",
                "content": workflow,
            },
        }
