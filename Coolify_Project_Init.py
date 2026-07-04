#!/usr/bin/env python3
"""
Coolify_Project_Init.py — 一键在 Coolify 上创建“工程实践在线网站”项目
"""
import os
import sys
from pathlib import Path

def main():
    # 优先加载 .env 文件中的环境变量
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    COOLIFY_BASE = "https://coolify.uwis.cn/api/v1"
    COOLIFY_API_KEY = os.environ.get("COOLIFY_API_KEY", "")
    PROJECT_NAME = "工程实践1-4在线网站"
    DESCRIPTION = "工程实践1-4在线网站自动创建"

    if not COOLIFY_API_KEY:
        print("❌ 缺少 COOLIFY_API_KEY，请在 .env 文件中配置")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {COOLIFY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 查询项目是否已存在
    resp = requests.get(f"{COOLIFY_BASE}/projects", headers=headers, verify=False)
    resp.raise_for_status()
    project = next((p for p in resp.json() if p["name"] == PROJECT_NAME), None)
    if project:
        print(f"✅ 已有项目: {PROJECT_NAME}  uuid={project['uuid']}")
    else:
        resp = requests.post(f"{COOLIFY_BASE}/projects", headers=headers, json={"name": PROJECT_NAME, "description": DESCRIPTION}, verify=False)
        resp.raise_for_status()
        project_uuid = resp.json()["uuid"]
        print(f"✅ 已创建项目: {PROJECT_NAME}  uuid={project_uuid}")

if __name__ == "__main__":
    main()
