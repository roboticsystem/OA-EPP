"""tests/reflex/conftest.py — pytest 公共 fixtures

所有 TDD 测试共享此文件中的 fixtures：
- mem_db: 每次测试使用独立 SQLite 内存数据库 Session
- REFLEX_DB_URL: 强制使用内存数据库，不依赖生产环境
"""
import os
import pytest
import sqlmodel

# 强制使用 SQLite 内存数据库
os.environ.setdefault("REFLEX_DB_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def mem_db():
    """每个测试函数独立的 SQLite in-memory 数据库 Session，测试后回滚。"""
    engine = sqlmodel.create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # 尝试初始化已导入模型的表结构（实现存在时生效）
    try:
        import oaepp.models  # noqa: F401
    except ImportError:
        pass
    sqlmodel.SQLModel.metadata.create_all(engine)
    with sqlmodel.Session(engine) as session:
        yield session
        session.rollback()
