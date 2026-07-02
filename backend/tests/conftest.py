import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_modules(tmp_path, monkeypatch):
    db_path = tmp_path / "exam.db"
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("TEACHER_PASSWORD", "test-teacher-password")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")

    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    database = importlib.import_module("app.database")
    database.init_db()
    main = importlib.import_module("app.main")

    return {"database": database, "main": main}


@pytest.fixture()
def db_conn(app_modules):
    with app_modules["database"].db() as conn:
        yield conn


@pytest.fixture()
def client(app_modules):
    with TestClient(app_modules["main"].app) as test_client:
        yield test_client
