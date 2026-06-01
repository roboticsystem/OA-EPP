import pymysql
import pymysql.cursors
import os
from contextlib import contextmanager
from urllib.parse import urlparse, unquote


def _parse_db_url(url: str) -> dict:
    """解析 DATABASE_URL 为 pymysql.connect 参数字典。格式: mysql+pymysql://user:pass@host:port/db"""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": parsed.username or "",
        "password": unquote(parsed.password) if parsed.password else "",
        "database": parsed.path.lstrip("/") or "",
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }


DB_CONFIG = _parse_db_url(os.environ["DATABASE_URL"])


class _ConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(self, sql, params_list):
        cursor = self.conn.cursor()
        cursor.executemany(sql, params_list)
        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_connection():
    return _ConnectionWrapper(pymysql.connect(**DB_CONFIG))


@contextmanager
def db():
    wrapper = get_connection()
    try:
        yield wrapper
        wrapper.commit()
    except Exception:
        wrapper.rollback()
        raise
    finally:
        wrapper.close()


def init_db():
    print("[init_db] 无 DDL 权限，跳过建表，假定表已存在")
