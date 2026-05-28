import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


BUILTIN_TEMPLATE_IDS = [
    "general-code-review",
    "engineering-practice",
    "security-comprehensive",
]

BUILTIN_TEMPLATES = {
    "general-code-review": {
        "name": "通用代码审查",
        "description": "覆盖可读性、正确性、可维护性和测试完整性的常规 PR 审查模板。",
        "file": "general-code-review.prompt.md",
        "content": """# 通用代码审查

你是一位严格、务实的代码审查专家。请围绕 PR 的真实变更给出高信号反馈，优先指出会导致缺陷、回归、可维护性下降或测试缺口的问题。

审查重点：

1. 正确性：实现是否满足 PR 描述，边界条件、空值、异常路径是否可靠。
2. 可读性：命名、结构、注释是否帮助后续维护者快速理解代码。
3. 可维护性：是否引入重复逻辑、过度抽象、隐藏状态或难以测试的耦合。
4. 测试：新增或修改行为是否有针对性测试，测试是否能证明关键风险已覆盖。
5. 文档：用户可见行为、配置或部署方式变化是否同步更新说明。

输出要求：

- 先列出必须修复的问题，按严重程度排序。
- 每条意见说明影响、触发条件和建议修复方向。
- 不要为无风险的风格偏好制造评论。
- 如果没有阻塞问题，请明确说明剩余风险和建议补充的测试。

PR 标题：{pr_title}
PR 描述：{pr_description}
变更内容：{diff}
""",
    },
    "engineering-practice": {
        "name": "工程实践规范检查",
        "description": "面向课程工程实践，检查提交规范、测试、文档、依赖与协作流程。",
        "file": "engineering-practice.prompt.md",
        "content": """# 工程实践规范检查

你正在为工程实践课程审查学生或团队提交的 PR。请把重点放在可验证的工程习惯上，而不是泛泛评价代码风格。

审查重点：

1. 分支与提交：PR 是否包含多个语义清晰的 commit，提交信息是否符合 Conventional Commits 和项目中文规范。
2. 需求对齐：实现是否能对应需求、验收标准和相关模块，是否存在未说明的范围外改动。
3. 测试实践：新增功能或修复是否先定义验证标准，是否覆盖正常路径、边界路径和失败路径。
4. CI/CD 适配：改动是否会影响 GitHub Actions、部署脚本、环境变量或容器构建。
5. 依赖与配置：是否引入不必要依赖，配置文件是否避免写入密钥或本地路径。
6. 文档与交付：README、课程文档、原型页面或接口说明是否随行为变化同步更新。

输出要求：

- 先指出会影响评分、合并或交付的工程规范问题。
- 对每个问题给出可执行修复建议。
- 对做得好的工程实践可以简短肯定，但不要挤占问题空间。
- 若 PR 只有一次 commit 且改动较大，请提示拆分为多个语义化提交。

PR 标题：{pr_title}
PR 描述：{pr_description}
变更内容：{diff}
""",
    },
    "security-comprehensive": {
        "name": "安全全面审查",
        "description": "全面检查鉴权、输入校验、密钥、注入、供应链和日志泄露风险。",
        "file": "security-comprehensive.prompt.md",
        "content": """# 安全全面审查

你是一位安全审查专家。请只基于 PR 变更和上下文提出可验证的安全问题，避免猜测式漏洞报告。

审查重点：

1. 鉴权与授权：接口、后台页面、管理操作是否校验身份和角色，是否存在越权访问。
2. 输入与注入：用户输入、文件上传、SQL、命令执行、路径拼接是否经过结构化处理或校验。
3. 密钥与敏感数据：是否硬编码 token、密码、连接串，日志或错误响应是否泄露敏感信息。
4. Web 安全：是否存在 XSS、CSRF、开放重定向、不安全 CORS 或不安全 Cookie 设置。
5. 供应链：新增依赖、Action、镜像或脚本是否可信，版本是否过于宽松或引入高风险权限。
6. 审计与清理：临时验证数据、Draft Comments、Dry-Run 输出是否能清理，审计记录是否避免保存敏感内容。

输出要求：

- 使用「严重 / 高 / 中 / 低」标注风险级别。
- 每条问题包含攻击路径、影响范围和推荐修复。
- 对无法确认的问题标为“需人工确认”，不要当作确定漏洞。
- 如果未发现明显风险，请列出已检查的安全面和仍需人工验证的前提。

PR 标题：{pr_title}
PR 描述：{pr_description}
变更内容：{diff}
""",
    },
}


def _now_iso():
    return datetime.now().replace(microsecond=0).isoformat()


def _sha(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def _slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "custom-template"


class PromptStore:
    def __init__(self, prompts_dir):
        self.prompts_dir = Path(prompts_dir)
        self.manifest_path = self.prompts_dir / "manifest.json"
        self.dry_run_state_path = self.prompts_dir / ".dry-run-state.json"
        self._ensure_initialized()

    def _ensure_initialized(self):
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "version": 1,
            "default_template": "general-code-review",
            "templates": [],
        }
        if self.manifest_path.exists():
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        existing = {template["id"]: template for template in manifest.get("templates", [])}
        templates = []
        for position, template_id in enumerate(BUILTIN_TEMPLATE_IDS):
            spec = BUILTIN_TEMPLATES[template_id]
            prompt_file = self.prompts_dir / spec["file"]
            if not prompt_file.exists():
                prompt_file.write_text(spec["content"], encoding="utf-8")
            templates.append(
                {
                    "id": template_id,
                    "name": existing.get(template_id, {}).get("name", spec["name"]),
                    "description": existing.get(template_id, {}).get("description", spec["description"]),
                    "file": spec["file"],
                    "built_in": True,
                    "position": position,
                    "updated_at": existing.get(template_id, {}).get("updated_at", _now_iso()),
                }
            )

        custom_templates = [
            template for template in manifest.get("templates", [])
            if template.get("id") not in BUILTIN_TEMPLATE_IDS
        ]
        manifest["templates"] = templates + custom_templates
        if manifest.get("default_template") not in [template["id"] for template in manifest["templates"]]:
            manifest["default_template"] = "general-code-review"
        self._write_manifest(manifest)

    def _load_manifest(self):
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest):
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _find_template(self, template_id):
        manifest = self._load_manifest()
        for template in manifest["templates"]:
            if template["id"] == template_id:
                return manifest, template
        raise KeyError(f"未知提示词模板：{template_id}")

    def _unique_id(self, name):
        manifest = self._load_manifest()
        used = {template["id"] for template in manifest["templates"]}
        base = _slugify(name)
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base}-{index}"
            index += 1
        return candidate

    def list_templates(self):
        manifest = self._load_manifest()
        templates = sorted(manifest["templates"], key=lambda item: item.get("position", 999))
        result = []
        for template in templates:
            content = (self.prompts_dir / template["file"]).read_text(encoding="utf-8")
            item = dict(template)
            item["version"] = _sha(content)
            item["is_default"] = template["id"] == manifest["default_template"]
            result.append(item)
        return result

    def get_template(self, template_id):
        manifest, template = self._find_template(template_id)
        content = (self.prompts_dir / template["file"]).read_text(encoding="utf-8")
        result = dict(template)
        result["content"] = content
        result["version"] = _sha(content)
        result["is_default"] = template_id == manifest["default_template"]
        return result

    def save_template(self, template_id, name, description, content):
        manifest, template = self._find_template(template_id)
        template["name"] = name.strip()
        template["description"] = description.strip()
        template["updated_at"] = _now_iso()
        (self.prompts_dir / template["file"]).write_text(content, encoding="utf-8")
        self._write_manifest(manifest)
        return self.get_template(template_id)

    def create_template(self, name, description, content):
        manifest = self._load_manifest()
        template_id = self._unique_id(name)
        file_name = f"{template_id}.prompt.md"
        template = {
            "id": template_id,
            "name": name.strip(),
            "description": description.strip(),
            "file": file_name,
            "built_in": False,
            "position": len(manifest["templates"]),
            "updated_at": _now_iso(),
        }
        (self.prompts_dir / file_name).write_text(content, encoding="utf-8")
        manifest["templates"].append(template)
        self._write_manifest(manifest)
        return self.get_template(template_id)

    def copy_template(self, source_template_id, new_name):
        source = self.get_template(source_template_id)
        return self.create_template(
            new_name,
            f"复制自：{source['name']}",
            source["content"],
        )

    def rename_template(self, template_id, new_name):
        manifest, template = self._find_template(template_id)
        template["name"] = new_name.strip()
        template["updated_at"] = _now_iso()
        self._write_manifest(manifest)
        return self.get_template(template_id)

    def delete_template(self, template_id):
        manifest, template = self._find_template(template_id)
        if template.get("built_in"):
            raise ValueError("内置模板不能删除")
        manifest["templates"] = [item for item in manifest["templates"] if item["id"] != template_id]
        if manifest["default_template"] == template_id:
            manifest["default_template"] = "general-code-review"
        prompt_file = self.prompts_dir / template["file"]
        if prompt_file.exists():
            prompt_file.unlink()
        self._write_manifest(manifest)
        return {"ok": True, "deleted": template_id}

    def set_default_template(self, template_id):
        manifest, _template = self._find_template(template_id)
        manifest["default_template"] = template_id
        self._write_manifest(manifest)
        return self.get_template(template_id)

    def run_dry_run(self, template_id, pr_title, pr_description, diff):
        template = self.get_template(template_id)
        snippets = self._build_review_snippets(template, pr_title, pr_description, diff)
        result = {
            "ai_call_status": "success",
            "github_submission": "not_submitted",
            "template_id": template_id,
            "template_name": template["name"],
            "prompt_version": template["version"],
            "review_snippets": snippets,
            "temporary_draft_comments": [],
            "created_at": _now_iso(),
        }
        self.dry_run_state_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result

    def _build_review_snippets(self, template, pr_title, pr_description, diff):
        diff_lines = [line for line in diff.splitlines() if line.startswith(("+", "-"))]
        changed_preview = diff_lines[0][:120] if diff_lines else "未提供 diff，建议选择目标 PR 后重新验证。"
        return [
            f"AI 调用状态：success；本次为 Dry-Run，未向 GitHub 提交评论。",
            f"提示词版本：{template['name']}@{template['version']}。",
            f"审查片段：围绕「{pr_title or '未命名 PR'}」检查需求对齐、测试覆盖和风险点。",
            f"变更预览：{changed_preview}",
            f"PR 描述摘要：{(pr_description or '未提供描述')[:120]}",
        ]

    def clear_dry_run_traces(self):
        audit = {
            "status": "cleared",
            "cleared_at": _now_iso(),
            "removed_draft_comments": [],
        }
        self.dry_run_state_path.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return audit


def build_reviewer_prompt_list(prompts_dir):
    store = PromptStore(prompts_dir)
    manifest = store._load_manifest()
    template = store.get_template(manifest["default_template"])
    prompts = []
    for line in template["content"].splitlines():
        clean = line.strip()
        if not clean:
            continue
        clean = clean.lstrip("#").strip()
        if clean:
            prompts.append(clean)
    return prompts
