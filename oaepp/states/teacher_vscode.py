import json
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "backend", "app", "data")
_CONFIG_PATH = os.path.join(_DATA_DIR, "vscode_config.json")
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_SAFE_PATHS = {
    ".github/copilot-instructions.md",
    ".github/instructions/commit-message.instructions.md",
}

EXTENSION_TYPES = ("required", "recommended", "banned")


class VSCodeConfigState:
    EXTENSION_TYPES = EXTENSION_TYPES

    extensions: list = []
    copilot_instructions: str = ""

    @staticmethod
    def _load_config():
        if not os.path.exists(_CONFIG_PATH):
            return {"recommendations": [], "unwantedRecommendations": []}
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save_config(config):
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    @classmethod
    def generate_extensions_json(cls):
        config = cls._load_config()
        output = {
            "recommendations": [entry["id"] for entry in config.get("recommendations", [])],
            "unwantedRecommendations": [entry["id"] for entry in config.get("unwantedRecommendations", [])],
        }
        vscode_dir = os.path.join(_REPO_ROOT, ".vscode")
        os.makedirs(vscode_dir, exist_ok=True)
        output_path = os.path.join(vscode_dir, "extensions.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        return output

    @classmethod
    def save_copilot_instructions(cls, path=None, content=None):
        if path is None or content is None:
            return
        normalized = path.replace("\\", "/")
        if normalized not in _SAFE_PATHS:
            raise ValueError(f"禁止访问路径: {path}")
        full_path = os.path.normpath(os.path.join(_REPO_ROOT, path))
        if not full_path.startswith(os.path.normpath(_REPO_ROOT)):
            raise ValueError("路径遍历攻击")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
