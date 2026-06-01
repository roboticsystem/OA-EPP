"""
mysql_db.py — MySQL 数据库连接模块（仅用于 commitlint_configs 表）

环境变量：
  MYSQL_HOST / MYSQL_PORT / MYSQL_DB / MYSQL_USER / MYSQL_PASSWORD
  COMMITLINT_COURSE_ID  (默认 1，对应 courses 表)
  COMMITLINT_UPDATED_BY (默认 1，对应 teachers 表)
"""

import os
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

MYSQL_HOST = os.environ.get("MYSQL_HOST", "156.239.252.40")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "13306"))
MYSQL_DB   = os.environ.get("MYSQL_DB", "oaepp_dev")
MYSQL_USER = os.environ.get("MYSQL_USER", "student_dev")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "OaEpp@Dev2026")

COMMITLINT_COURSE_ID  = int(os.environ.get("COMMITLINT_COURSE_ID", "1"))
COMMITLINT_UPDATED_BY = int(os.environ.get("COMMITLINT_UPDATED_BY", "1"))


@contextmanager
def mysql_db():
    """MySQL 连接上下文管理器，自动提交/回滚。"""
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DB,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        cursorclass=DictCursor,
        charset="utf8mb4",
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
