"""
F-T-002 VS Code扩展与Copilot提示词管理 — Reflex 页面
"""
import json
import os

try:
    import reflex as rx
except Exception:
    rx = None

vscode_config_page = None

if rx is not None:
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
            rec_id = self.rec_id
            self.rec_id = ""
            self.rec_name = ""
            self.load_extensions()
            self._set_status("已添加 " + rec_id, "success")

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
            ban_id = self.ban_id
            self.ban_id = ""
            self.ban_name = ""
            self.load_extensions()
            self._set_status("已禁止 " + ban_id, "success")

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

        def generate_extensions_json(self):
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
            self._set_status("已生成 .vscode/extensions.json", "success")

        def save_copilot_instructions(self, path, content):
            if not path or not content:
                return
            try:
                full = _safe_path(path)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass

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

    def _rec_item(item):
        return rx.hstack(
            rx.code(item["id"], size="1"),
            rx.text(item.get("name", ""), size="1", color="gray"),
            rx.icon_button(
                "x",
                on_click=lambda eid=item["id"]: VSCodeConfigState.remove_recommendation(eid),
                variant="ghost",
                color_scheme="red",
                size="1",
            ),
            justify="between",
            width="100%",
            padding="4px",
        )

    def _ban_item(item):
        return rx.hstack(
            rx.code(item["id"], size="1"),
            rx.text(item.get("name", ""), size="1", color="gray"),
            rx.icon_button(
                "x",
                on_click=lambda eid=item["id"]: VSCodeConfigState.remove_banned(eid),
                variant="ghost",
                color_scheme="red",
                size="1",
            ),
            justify="between",
            width="100%",
            padding="4px",
        )

    def _file_tab(f):
        return rx.button(
            f["name"],
            on_click=lambda p=f["path"]: VSCodeConfigState.set_current_file(p),
            variant="ghost",
            size="1",
        )

    def vscode_config_page():
        return rx.container(
            rx.vstack(
                rx.heading("VS Code & Copilot 配置管理", size="6"),
                rx.text("F-T-002 \u00b7 \u6559\u5e08\u7aef \u00b7 \u5f00\u53d1\u8fd0\u7ef4", color="gray", size="1"),

                rx.cond(
                    VSCodeConfigState.status_message != "",
                    rx.callout(
                        VSCodeConfigState.status_message,
                        icon=rx.cond(
                            VSCodeConfigState.status_type == "error", "triangle_alert",
                            rx.cond(VSCodeConfigState.status_type == "success", "circle_check", "info"),
                        ),
                        color_scheme=rx.cond(
                            VSCodeConfigState.status_type == "error", "red",
                            rx.cond(VSCodeConfigState.status_type == "success", "green", "blue"),
                        ),
                        width="100%",
                    ),
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("VS Code \u6269\u5c55\u7ba1\u7406", size="3"),
                        rx.hstack(
                            rx.vstack(
                                rx.heading("\u63a8\u8350\u5b89\u88c5", size="2", color="blue"),
                                rx.foreach(VSCodeConfigState.recommendations, _rec_item),
                                rx.hstack(
                                    rx.input(
                                        placeholder="\u6269\u5c55 ID",
                                        value=VSCodeConfigState.rec_id,
                                        on_change=VSCodeConfigState.set_rec_id,
                                        size="1",
                                    ),
                                    rx.input(
                                        placeholder="\u540d\u79f0",
                                        value=VSCodeConfigState.rec_name,
                                        on_change=VSCodeConfigState.set_rec_name,
                                        size="1",
                                    ),
                                    rx.button(
                                        "+ \u6dfb\u52a0",
                                        on_click=VSCodeConfigState.add_recommendation,
                                        color_scheme="blue",
                                        size="1",
                                    ),
                                    width="100%",
                                ),
                                width="50%",
                            ),
                            rx.vstack(
                                rx.heading("\u7981\u6b62\u5b89\u88c5", size="2", color="red"),
                                rx.foreach(VSCodeConfigState.banned, _ban_item),
                                rx.hstack(
                                    rx.input(
                                        placeholder="\u6269\u5c55 ID",
                                        value=VSCodeConfigState.ban_id,
                                        on_change=VSCodeConfigState.set_ban_id,
                                        size="1",
                                    ),
                                    rx.input(
                                        placeholder="\u540d\u79f0",
                                        value=VSCodeConfigState.ban_name,
                                        on_change=VSCodeConfigState.set_ban_name,
                                        size="1",
                                    ),
                                    rx.button(
                                        "+ \u6dfb\u52a0",
                                        on_click=VSCodeConfigState.add_banned,
                                        color_scheme="red",
                                        variant="outline",
                                        size="1",
                                    ),
                                    width="100%",
                                ),
                                width="50%",
                            ),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("\u9884\u8bbe\u6a21\u677f:", size="1", color="gray"),
                            rx.button(
                                "Python\u6807\u51c6",
                                on_click=lambda: VSCodeConfigState.apply_preset("python-dev"),
                                size="1",
                            ),
                            rx.button(
                                "Copilot\u5168\u5bb6\u6876",
                                on_click=lambda: VSCodeConfigState.apply_preset("copilot-suite"),
                                size="1",
                            ),
                            rx.button(
                                "Reflex\u5f00\u53d1",
                                on_click=lambda: VSCodeConfigState.apply_preset("reflex-dev"),
                                size="1",
                            ),
                            padding_top="8px",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("JSON \u9884\u89c8", size="3"),
                        rx.text(".vscode/extensions.json", size="1", color="gray"),
                        rx.code_block(
                            VSCodeConfigState.json_preview,
                            language="json",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.button(
                                "\u751f\u6210\u6587\u4ef6",
                                on_click=VSCodeConfigState.generate_extensions_json,
                                color_scheme="blue",
                                size="1",
                            ),
                            width="100%",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("Copilot \u6307\u4ee4\u6587\u4ef6\u7f16\u8f91", size="3"),
                        rx.hstack(
                            rx.foreach(VSCodeConfigState.instruction_files, _file_tab),
                            width="100%",
                        ),
                        rx.text_area(
                            value=VSCodeConfigState.editor_content,
                            on_change=VSCodeConfigState.set_editor_content,
                            placeholder="\u9009\u62e9\u6587\u4ef6\u540e\u5728\u6b64\u7f16\u8f91...",
                            width="100%",
                            min_height="260px",
                        ),
                        rx.hstack(
                            rx.button(
                                "\u91cd\u65b0\u52a0\u8f7d",
                                on_click=VSCodeConfigState.load_file_content,
                                size="1",
                            ),
                            rx.button(
                                "\u4fdd\u5b58\u6587\u4ef6",
                                on_click=VSCodeConfigState.save_file_content,
                                color_scheme="green",
                                size="1",
                            ),
                            width="100%",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.hstack(
                        rx.cond(
                            VSCodeConfigState.git_dirty,
                            rx.badge("\u6709\u53d8\u66f4", color_scheme="orange"),
                            rx.badge("\u5e72\u51c0", color_scheme="green"),
                        ),
                        rx.text("\u5206\u652f: " + VSCodeConfigState.git_branch, size="1", color="gray"),
                        rx.spacer(),
                        rx.button(
                            "\u5237\u65b0\u72b6\u6001",
                            on_click=VSCodeConfigState.check_git_status,
                            size="1",
                        ),
                        rx.button(
                            "\u63d0\u4ea4\u5230\u4ed3\u5e93",
                            on_click=VSCodeConfigState.commit_and_push,
                            color_scheme="blue",
                            size="1",
                        ),
                        width="100%",
                    ),
                    width="100%",
                ),

                on_mount=[
                    VSCodeConfigState.load_extensions(),
                    VSCodeConfigState.load_instruction_files(),
                    VSCodeConfigState.check_git_status(),
                ],
                spacing="4",
                width="100%",
            ),
            width="100%",
            min_height="100vh",
            max_width="900px",
            margin="0 auto",
            padding="20px",
        )

else:
    def vscode_config_page():
        return """<div style="padding:40px;text-align:center;">
            <h2>Reflex not installed</h2>
            <p>Please install Reflex to use this feature.</p>
        </div>"""
