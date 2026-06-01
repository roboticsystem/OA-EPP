"""commitlint_engine — 共享核心逻辑

被以下模块共用：
  - oaepp.states.devops_commitlint (Reflex State)
  - app.routers.commitlint (FastAPI 路由)
"""

import json


def build_commitlintrc(
    type_enum: list,
    header_max_length: int,
    subject_min_length: int,
    is_enabled: bool = True,
) -> str:
    """生成 .commitlintrc.json 内容。enabled 时规则级别 2（error），disabled 时 0（关闭）。"""
    level = 2 if is_enabled else 0
    rules = {
        "type-enum": [level, "always", sorted(set(type_enum))],
        "subject-min-length": [level, "always", subject_min_length],
        "header-max-length": [level, "always", header_max_length],
    }
    rc = {
        "extends": ["@commitlint/config-conventional"],
        "rules": rules,
    }
    return json.dumps(rc, indent=2, ensure_ascii=False)


def generate_workflow_yml() -> str:
    """生成 .github/workflows/commitlint.yml 内容。"""
    return (
        "name: Commit Message 检查\n\n"
        "on: [pull_request]\n\n"
        "jobs:\n"
        "  commitlint:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "        with:\n"
        "          fetch-depth: 0\n"
        "      - uses: wagoid/commitlint-github-action@v5\n"
        "        with:\n"
        "          configFile: .commitlintrc.json\n"
    )
