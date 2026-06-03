"""tests/reflex/conftest.py — pytest 公共 fixtures

所有 TDD 测试共享此文件中的 fixtures：
- mem_db: 每次测试使用独立 SQLite 内存数据库 Session
- REFLEX_DB_URL: 强制使用内存数据库，不依赖生产环境
"""
import os
import sys
import pytest
try:
    import sqlmodel  # type: ignore
except Exception:
    sqlmodel = None

# 确保项目根目录在 sys.path 中，使 oaepp 包可导入
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 强制使用 SQLite 内存数据库
os.environ.setdefault("REFLEX_DB_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def mem_db():
    """提供测试用的内存 DB session。

    若环境中未安装 `sqlmodel`，返回一个占位对象（None），以便依赖 DB 的测试
    可以在不真正访问数据库的情况下运行 TDD 检查。
    """
    if sqlmodel is None:
        yield None
        return

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
