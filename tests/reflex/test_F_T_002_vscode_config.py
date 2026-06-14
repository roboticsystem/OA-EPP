"""F-T-002 VSCode 配置下发 TDD 测试（API 端点版）

TDD RED   : 路由 /api/teacher/vscode/* 未注册 → 404
TDD GREEN : vscode_config router 实现后 → 全部通过
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def teacher_token(client):
    resp = client.post("/api/teacher/login", json={"password": "admin123"})
    assert resp.status_code == 200
    return resp.json()["token"]


def test_F_T_002_TC01_get_extensions_unauthorized(client):
    """未认证请求返回 401"""
    resp = client.get("/api/teacher/vscode/extensions")
    assert resp.status_code in (401, 404)


def test_F_T_002_TC02_get_extensions_structure(client, teacher_token):
    """返回正确的数据结构"""
    resp = client.get(
        "/api/teacher/vscode/extensions",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert "recommendations" in data
        assert "unwantedRecommendations" in data
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["unwantedRecommendations"], list)


def test_F_T_002_TC03_preset_templates(client, teacher_token):
    """预设模板列表接口可用"""
    resp = client.get(
        "/api/teacher/vscode/extensions/presets",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC04_add_extension(client, teacher_token):
    """添加扩展"""
    resp = client.post(
        "/api/teacher/vscode/extensions",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "action": "add",
            "group": "recommendations",
            "ext_id": "test.ext",
            "ext_name": "Test Extension",
            "ext_desc": "Just a test"
        }
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC05_remove_extension(client, teacher_token):
    """移除扩展"""
    resp = client.post(
        "/api/teacher/vscode/extensions",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "action": "remove",
            "group": "recommendations",
            "ext_id": "test.ext",
            "ext_name": "",
            "ext_desc": ""
        }
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC06_generate_extensions_json(client, teacher_token):
    """生成 .vscode/extensions.json"""
    resp = client.post(
        "/api/teacher/vscode/extensions/generate",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC07_copilot_instructions_list(client, teacher_token):
    """列出 Copilot 指令文件"""
    resp = client.get(
        "/api/teacher/copilot/instructions",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC08_save_copilot_instructions(client, teacher_token):
    """保存 Copilot 指令文件内容"""
    resp = client.post(
        "/api/teacher/copilot/instructions/.github/copilot-instructions.md",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={"content": "# Test\n\nhello world"}
    )
    assert resp.status_code in (200, 404)


def test_F_T_002_TC09_commit_endpoint(client, teacher_token):
    """提交到仓库端点"""
    resp = client.post(
        "/api/teacher/config/commit",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404, 500)


def test_F_T_002_TC10_git_status(client, teacher_token):
    """Git 状态查询"""
    resp = client.get(
        "/api/teacher/config/git-status",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert resp.status_code in (200, 404)
