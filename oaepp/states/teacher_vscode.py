"""
F-T-002 VS Code扩展与Copilot提示词管理 — State模块

被测目标: oaepp.states.teacher_vscode.VSCodeConfigState
"""
import json
import os

try:
    import reflex as rx
except Exception:
    rx = None

_OAEPP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_OAEPP_DIR, ".oaepp_data")
_CONFIG_PATH = os.path.join(_DATA_DIR, "vscode_config.json")

_SAFE_PATHS = {
    ".github/copilot-instructions.md",
    ".github/instructions/commit-message.instructions.md",
}

EXTENSION_TYPES = ("required", "recommended", "banned")

PRESETS = {
    "python-dev": {
        "name": "Python标准",
        "recommendations": [
            "ms-python.python", "ms-python.vscode-pylance",
            "charliermarsh.ruff", "ms-python.debugpy"
        ],
        "unwantedRecommendations": ["ms-python.pylint"]
    },
    "copilot-suite": {
        "name": "Copilot全家桶",
        "recommendations": ["GitHub.copilot", "GitHub.copilot-chat"],
        "unwantedRecommendations": []
    },
    "reflex-dev": {
        "name": "Reflex开发",
        "recommendations": [
            "ms-python.python", "ms-python.vscode-pylance",
            "GitHub.copilot", "charliermarsh.ruff"
        ],
        "unwantedRecommendations": []
    }
}


def _load_config():
    if not os.path.exists(_CONFIG_PATH):
        return {"recommendations": [], "unwantedRecommendations": []}
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_config(config):
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _safe_path(rel_path):
    normalized = rel_path.replace("\\", "/")
    if normalized not in _SAFE_PATHS:
        raise ValueError("禁止写入路径: " + rel_path)
    full = os.path.normpath(os.path.join(_OAEPP_DIR, rel_path))
    if not full.startswith(os.path.normpath(_OAEPP_DIR)):
        raise ValueError("路径穿越检测")
    return full


VSCodeConfigState = None

if rx is not None:

    class VSCodeConfigState(rx.State):
        extensions: list = []
        copilot_instructions: str = ""

        recommendations: list = []
        banned: list = []
        json_preview: str = "{}"

        instruction_files: list = []
        current_file: str = ""
        editor_content: str = ""

        rec_id: str = ""
        rec_name: str = ""
        ban_id: str = ""
        ban_name: str = ""

        git_dirty: bool = False
        git_branch: str = ""
        git_changed_files: list = []

        status_message: str = ""
        status_type: str = "info"

        EXTENSION_TYPES = EXTENSION_TYPES

        def _set_status(self, msg, msg_type="info"):
            self.status_message = msg
            self.status_type = msg_type

        def set_rec_id(self, value):
            self.rec_id = value

        def set_rec_name(self, value):
            self.rec_name = value

        def set_ban_id(self, value):
            self.ban_id = value

        def set_ban_name(self, value):
            self.ban_name = value

        def set_current_file(self, path):
            self.current_file = path
            self.load_file_content()

        def set_editor_content(self, content):
            self.editor_content = content

        # ─── 扩展管理 ───

        def load_extensions(self):
            config = _load_config()
            self.recommendations = config.get("recommendations", [])
            self.banned = config.get("unwantedRecommendations", [])
            self.extensions = self.recommendations + self.banned
            self._update_preview()

        def _update_preview(self):
            output = {
                "recommendations": [e["id"] for e in self.recommendations],
                "unwantedRecommendations": [e["id"] for e in self.banned],
            }
            self.json_preview = json.dumps(output, ensure_ascii=False, indent=2)

        def add_recommendation(self):
            if not self.rec_id:
                return
            config = _load_config()
            existing = any(e["id"] == self.rec_id for e in config.get("recommendations", []))
            if not existing:
                config.setdefault("recommendations", []).append({
                    "id": self.rec_id, "name": self.rec_name or self.rec_id, "description": ""
                })
                _save_config(config)
            self.rec_id = ""
            self.rec_name = ""
            self.load_extensions()
            self._set_status("已添加 " + self.rec_id, "success")

        def remove_recommendation(self, ext_id: str):
            config = _load_config()
            config["recommendations"] = [
                e for e in config.get("recommendations", []) if e["id"] != ext_id
            ]
            _save_config(config)
            self.load_extensions()
            self._set_status("已移除 " + ext_id, "success")

        def add_banned(self):
            if not self.ban_id:
                return
            config = _load_config()
            existing = any(e["id"] == self.ban_id for e in config.get("unwantedRecommendations", []))
            if not existing:
                config.setdefault("unwantedRecommendations", []).append({
                    "id": self.ban_id, "name": self.ban_name or self.ban_id, "description": ""
                })
                _save_config(config)
            self.ban_id = ""
            self.ban_name = ""
            self.load_extensions()
            self._set_status("已禁止 " + self.ban_id, "success")

        def remove_banned(self, ext_id: str):
            config = _load_config()
            config["unwantedRecommendations"] = [
                e for e in config.get("unwantedRecommendations", []) if e["id"] != ext_id
            ]
            _save_config(config)
            self.load_extensions()
            self._set_status("已解除禁止 " + ext_id, "success")

        def apply_preset(self, preset_id: str):
            preset = PRESETS.get(preset_id)
            if not preset:
                return
            config = {
                "recommendations": [
                    {"id": eid, "name": eid, "description": ""}
                    for eid in preset["recommendations"]
                ],
                "unwantedRecommendations": [
                    {"id": eid, "name": eid, "description": ""}
                    for eid in preset["unwantedRecommendations"]
                ]
            }
            _save_config(config)
            self.load_extensions()
            self._set_status("已应用模板: " + preset["name"], "success")

        @classmethod
        def generate_extensions_json(cls):
            config = _load_config()
            output = {
                "recommendations": [e["id"] for e in config.get("recommendations", [])],
                "unwantedRecommendations": [e["id"] for e in config.get("unwantedRecommendations", [])],
            }
            vscode_dir = os.path.join(_OAEPP_DIR, ".vscode")
            os.makedirs(vscode_dir, exist_ok=True)
            output_path = os.path.join(vscode_dir, "extensions.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            return output

        @classmethod
        def save_copilot_instructions(cls, path=None, content=None):
            if not path or not content:
                return
            try:
                full = _safe_path(path)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass

        # ─── Copilot 指令 (UI用实例方法) ───

        def load_instruction_files(self):
            files = []
            for rel in _SAFE_PATHS:
                full = os.path.join(_OAEPP_DIR, rel)
                name = os.path.basename(rel)
                size = 0
                if os.path.isfile(full):
                    size = os.path.getsize(full)
                files.append({"path": rel, "name": name, "size": size})
            self.instruction_files = files
            if files and not self.current_file:
                self.current_file = files[0]["path"]
                self.load_file_content()

        def load_file_content(self):
            try:
                full = _safe_path(self.current_file)
                if os.path.isfile(full):
                    with open(full, "r", encoding="utf-8") as f:
                        self.editor_content = f.read()
                        self.copilot_instructions = self.editor_content
                else:
                    self.editor_content = ""
            except Exception:
                self.editor_content = ""

        def save_file_content(self):
            if not self.current_file or not self.editor_content:
                return
            self.save_copilot_instructions(self.current_file, self.editor_content)
            self.copilot_instructions = self.editor_content
            self._set_status("已保存 " + self.current_file, "success")
            self.check_git_status()

        # ─── Git 操作 ───

        def check_git_status(self):
            import subprocess
            try:
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=_OAEPP_DIR, capture_output=True, text=True
                )
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=_OAEPP_DIR, capture_output=True, text=True
                )
                changed = [line.strip() for line in status_result.stdout.splitlines() if line.strip()]
                self.git_dirty = len(changed) > 0
                self.git_changed_files = changed
                self.git_branch = branch_result.stdout.strip()
            except Exception:
                self.git_dirty = False
                self.git_changed_files = []
                self.git_branch = "unknown"

        def commit_and_push(self):
            import subprocess
            from datetime import datetime
            try:
                target_files = [
                    ".vscode/extensions.json",
                    ".github/copilot-instructions.md",
                    ".github/instructions/",
                ]
                add_args = ["git", "add"]
                for f in target_files:
                    full_path = os.path.join(_OAEPP_DIR, f)
                    if os.path.exists(full_path):
                        add_args.append(f)
                subprocess.run(add_args, cwd=_OAEPP_DIR, check=True, capture_output=True)

                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                result = subprocess.run(
                    ["git", "commit", "-m", "chore: update VSCode & Copilot config (" + date_str + ")"],
                    cwd=_OAEPP_DIR, capture_output=True, text=True
                )

                sha = None
                if result.returncode == 0 and "nothing to commit" not in result.stdout:
                    sha_result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=_OAEPP_DIR, capture_output=True, text=True
                    )
                    sha = sha_result.stdout.strip()[:7]

                try:
                    subprocess.run(["git", "push"], cwd=_OAEPP_DIR, capture_output=True)
                except Exception:
                    pass

                self.git_dirty = False
                self.git_changed_files = []
                if sha:
                    self._set_status("提交成功: " + sha, "success")
                else:
                    self._set_status("无变更需要提交", "info")
            except subprocess.CalledProcessError as e:
                self._set_status("Git 操作失败: " + str(e.stderr), "error")
