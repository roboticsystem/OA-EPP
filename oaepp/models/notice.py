"""OA-EPP 通知模块 — 数据库模型

提供 notifications 表的数据库连接和模型定义。
复用项目根目录 .env 中的数据库配置。
"""
import os
import pymysql
from pathlib import Path
from urllib.parse import urlparse, unquote


def _load_env():
    """加载 .env 文件"""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key not in os.environ:
                        os.environ[key] = value


_load_env()


def _parse_db_config():
    """解析数据库连接配置"""
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    if DATABASE_URL:
        try:
            parsed = urlparse(DATABASE_URL)
            return {
                "host": parsed.hostname or "127.0.0.1",
                "port": parsed.port or 3306,
                "user": parsed.username or "root",
                "password": unquote(parsed.password) if parsed.password else "",
                "database": parsed.path.lstrip("/") or "oaepp_dev",
                "charset": "utf8mb4",
            }
        except Exception:
            pass
    return {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "oaepp_dev"),
        "charset": "utf8mb4",
    }


def get_db_connection():
    """获取数据库连接"""
    cfg = _parse_db_config()
    conn = pymysql.connect(**cfg, autocommit=False)
    return conn
