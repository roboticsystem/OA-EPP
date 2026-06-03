import os
import pymysql
from contextlib import contextmanager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 判断是否在 Docker 容器环境中运行
def is_docker_env():
    """检测是否在 Docker 容器中运行
    通过检查常见的 Docker 环境特征来判断
    """
    # 方式1：检查 /.dockerenv 文件
    if os.path.exists("/.dockerenv"):
        return True
    # 方式2：检查 /proc/1/cgroup 文件中是否包含 docker
    try:
        with open("/proc/1/cgroup", "r") as f:
            if "docker" in f.read():
                return True
    except:
        pass
    # 方式3：检查环境变量
    if os.environ.get("DOCKER_CONTAINER", "") == "true":
        return True
    return False

# 根据环境自动选择数据库连接配置
if is_docker_env():
    # Docker 生产环境：使用容器网络内部主机名
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "oaepp-mysql")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
else:
    # 本地开发环境：使用公网可访问地址
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "156.239.252.40")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 13306))

MYSQL_USER = os.environ.get("MYSQL_USER", "student_dev")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "OaEpp@Dev2026")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "oaepp_dev")


def get_connection():
    """获取 MySQL 数据库连接"""
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


@contextmanager
def db():
    """数据库连接上下文管理器"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库（不创建表，只检查连接"""
    with db() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [list(t.values())[0] for t in cursor.fetchall()]
        print(f"当前数据库表: {tables}")
