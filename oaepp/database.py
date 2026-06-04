"""
MySQL 数据库连接模块 — 连接远程 oaepp_dev 数据库。
"""
import os
import pymysql
from contextlib import contextmanager

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "156.239.252.40"),
    "port": int(os.environ.get("MYSQL_PORT", "13306")),
    "user": os.environ.get("MYSQL_USER", "student_dev"),
    "password": os.environ.get("MYSQL_PASSWORD", "OaEpp@Dev2026"),
    "database": os.environ.get("MYSQL_DATABASE", "oaepp_dev"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
