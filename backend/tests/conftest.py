import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "exam.db"
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("TEACHER_PASSWORD", "test-teacher-password")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")

    for module_name in ("app.database", "app.sync_exams", "app.main"):
        sys.modules.pop(module_name, None)

    database = importlib.import_module("app.database")
    database.init_db()

    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client
