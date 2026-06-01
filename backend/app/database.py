import os
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

# MySQL 数据库连接配置
DB_HOST = os.environ.get("DB_HOST", "156.239.252.40")
DB_PORT = int(os.environ.get("DB_PORT", "13306"))
DB_NAME = os.environ.get("DB_NAME", "oaepp_dev")
DB_USER = os.environ.get("DB_USER", "student_dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "OaEpp@Dev2026")


class ResultCursor:
    """包装 MySQL cursor，让 execute() 方法返回结果集"""
    
    def __init__(self, cursor):
        self._cursor = cursor
    
    def execute(self, query, params=None):
        """执行 SQL 查询并返回游标对象"""
        try:
            while self._cursor.fetchone():
                pass
        except:
            pass
        if params is None:
            self._cursor.execute(query)
        else:
            self._cursor.execute(query, params)
        return self
    
    def fetchone(self):
        """获取单行结果"""
        return self._cursor.fetchone()
    
    def fetchall(self):
        """获取所有结果"""
        return self._cursor.fetchall()
    
    def close(self):
        """关闭 cursor"""
        self._cursor.close()


@contextmanager
def db():
    """数据库连接上下文管理器"""
    conn = None
    cursor = None
    wrapper = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SET NAMES utf8mb4")
        cursor.fetchall()  # 清除 SET 命令的结果
        wrapper = ResultCursor(cursor)
        yield wrapper
    except Error as e:
        print(f"数据库连接错误: {e}")
        raise
    finally:
        if wrapper:
            try:
                wrapper.close()
            except:
                pass
        elif cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


def init_db():
    """初始化数据库（MySQL版本）"""
    print("[database] 正在连接 MySQL 数据库...")
    try:
        with db() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("[database] MySQL 数据库连接成功！")
    except Exception as e:
        print(f"[database] 数据库初始化失败: {e}")
        raise
