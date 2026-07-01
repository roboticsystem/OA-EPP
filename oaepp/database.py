"""
OA-EPP 公共数据库访问层 — oaepp/database.py

提供：
- 连接池管理（aiomysql，自动重连）
- 异步会话上下文（db() — 只读查询）
- 异步事务上下文（transaction() — 读写操作）
- 同步回退接口（db_sync / transaction_sync — 兼容非 async State）

配置优先级：环境变量 > 默认值
  DB_HOST      — MySQL 主机（默认 156.239.252.40）
  DB_PORT      — MySQL 端口（默认 13306）
  DB_USER      — 用户名（默认 student_dev）
  DB_PASSWORD  — 密码（默认 OaEpp@Dev2026）
  DB_NAME      — 数据库名（默认 oaepp_dev）
  DB_POOL_MIN  — 最小连接数（默认 2）
  DB_POOL_MAX  — 最大连接数（默认 10）

用法示例:

    from oaepp.database import db, transaction

    async def load_students():
        async with db() as cur:
            await cur.execute("SELECT * FROM students")
            return await cur.fetchall()

    async def create_student(name: str):
        async with transaction() as cur:
            await cur.execute(
                "INSERT INTO students (name) VALUES (%s)", (name,)
            )
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, Any

logger = logging.getLogger("oaepp.database")

# ── 配置 ──────────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "156.239.252.40"),
    "port": int(os.environ.get("DB_PORT", "13306")),
    "user": os.environ.get("DB_USER", "student_dev"),
    "password": os.environ.get("DB_PASSWORD", "OaEpp@Dev2026"),
    "db": os.environ.get("DB_NAME", "oaepp_dev"),
    "charset": "utf8mb4",
    "autocommit": True,  # db() 默认自动提交，transaction() 手动控制
    "minsize": int(os.environ.get("DB_POOL_MIN", "2")),
    "maxsize": int(os.environ.get("DB_POOL_MAX", "10")),
    "pool_recycle": 3600,  # 1 小时回收连接，避免 MySQL wait_timeout
}

# ── 异步连接池 ────────────────────────────────────────────────

_async_pool: Optional[Any] = None


async def _get_async_pool():
    """获取或初始化 aiomysql 异步连接池。"""
    global _async_pool
    if _async_pool is None:
        import aiomysql
        _async_pool = await aiomysql.create_pool(**DB_CONFIG)
        logger.info(
            "MySQL 异步连接池已创建: %s:%s/%s (pool=%s-%s)",
            DB_CONFIG["host"],
            DB_CONFIG["port"],
            DB_CONFIG["db"],
            DB_CONFIG["minsize"],
            DB_CONFIG["maxsize"],
        )
    return _async_pool


async def close_async_pool():
    """关闭异步连接池（应用退出时调用）。"""
    global _async_pool
    if _async_pool is not None:
        _async_pool.close()
        await _async_pool.wait_closed()
        _async_pool = None
        logger.info("MySQL 异步连接池已关闭")


@asynccontextmanager
async def db():
    """异步只读会话上下文 — 自动提交，不开启事务。

    用法:
        async with db() as cur:
            await cur.execute("SELECT * FROM students WHERE id=%s", (sid,))
            row = await cur.fetchone()
    """
    import aiomysql
    pool = await _get_async_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            try:
                yield cur
            finally:
                await cur.close()


@asynccontextmanager
async def transaction():
    """异步事务上下文 — 手动提交/回滚。

    用法:
        async with transaction() as cur:
            await cur.execute("INSERT INTO ...")
            await cur.execute("UPDATE ...")
            # 退出时自动 commit；异常时自动 rollback
    """
    import aiomysql
    pool = await _get_async_pool()
    async with pool.acquire() as conn:
        conn.autocommit(False)  # 关闭自动提交，手动控制事务
        async with conn.cursor(aiomysql.DictCursor) as cur:
            try:
                yield cur
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
            finally:
                await cur.close()


# ── 同步回退接口（pymysql）────────────────────────────────────

_sync_pool = None


def _get_sync_conn():
    """获取 pymysql 同步连接（带简单复用）。"""
    import pymysql
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["db"],
        charset=DB_CONFIG["charset"],
        autocommit=True,
    )
    return conn


@contextmanager
def db_sync():
    """同步只读会话上下文。

    用法:
        with db_sync() as cur:
            cur.execute("SELECT * FROM students WHERE id=%s", (sid,))
            row = cur.fetchone()
    """
    import pymysql
    conn = _get_sync_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            yield cur
    finally:
        conn.close()


@contextmanager
def transaction_sync():
    """同步事务上下文。

    用法:
        with transaction_sync() as cur:
            cur.execute("INSERT INTO ...")
            cur.execute("UPDATE ...")
    """
    import pymysql
    conn = _get_sync_conn()
    conn.autocommit(False)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
