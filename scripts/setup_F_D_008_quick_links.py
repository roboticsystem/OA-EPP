#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F_D_008 GitHub 快捷链接 -- 数据库初始化 & 验证脚本
===========================================================================
作用：
  1. 创建 gh_quick_links 表（如权限允许）
  2. 预填 7 类标准快捷链接默认数据
  3. 查询并打印当前全部记录，方便验证

使用（VSCode 中右键 -> Run Python File，或终端执行）：
  python scripts/setup_F_D_008_quick_links.py

数据库连接：
  主机：156.239.252.40:13306 | 库：oaepp_dev | 用户：student_dev
===========================================================================
"""
from __future__ import annotations

import os
import sys

# Fix Windows GBK console encoding for CJK + special chars
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 默认仓库 URI（可通过环境变量 GITHUB_REPO_URL 覆盖） ────────────
GITHUB_REPO_URL = os.environ.get(
    "GITHUB_REPO_URL",
    "https://github.com/uwislab/robotics-systems-course",
).rstrip("/")

# ── 数据库连接 ────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "156.239.252.40"),
    "port":     int(os.environ.get("DB_PORT", "13306")),
    "user":     os.environ.get("DB_USER", "student_dev"),
    "password": os.environ.get("DB_PASSWORD", "OaEpp@Dev2026"),
    "database": os.environ.get("DB_NAME", "oaepp_dev"),
    "charset":  "utf8mb4",
}

# ── 7 类默认链接 ──────────────────────────────────────────────────
DEFAULT_LINKS = [
    ("repo",               "[仓库主页]",            "",                          "folder-git-2",      1),
    ("pulls",              "Pull Requests",        "/pulls",                    "git-pull-request",  2),
    ("issues",             "Issues",                "/issues",                   "alert-circle",      3),
    ("actions",            "Actions / CI",          "/actions",                  "play",              4),
    ("branches",           "[分支管理]",            "/branches",                 "git-branch",        5),
    ("secrets",            "Settings * Secrets",    "/settings/secrets/actions", "key",               6),
    ("branch_protection",  "Settings * [分支保护]", "/settings/branches",        "shield-check",      7),
]


def main() -> None:
    import pymysql

    conn = pymysql.connect(**DB_CONFIG, autocommit=True)
    table_ready = False  # will be set True once table exists + we can write

    print("[OK] 已连接 MySQL  oaepp_dev")
    print()

    try:
        with conn.cursor() as cur:
            # ── 1. 建表（仅管理员有权限） ───────────────────────────
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS gh_quick_links (
                        id          VARCHAR(64)  PRIMARY KEY   COMMENT '链接类型标识',
                        label       VARCHAR(128) NOT NULL DEFAULT '' COMMENT '自定义标签名',
                        url         VARCHAR(512) NOT NULL DEFAULT '' COMMENT '完整跳转URL',
                        icon        VARCHAR(64)  NOT NULL DEFAULT 'link-2' COMMENT 'Lucide图标',
                        visible     TINYINT(1)   NOT NULL DEFAULT 1    COMMENT '是否可见',
                        sort_order  INT          NOT NULL DEFAULT 99   COMMENT '显示排序',
                        INDEX idx_visible     (visible),
                        INDEX idx_sort_order  (sort_order)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    COMMENT='GitHub快捷链接配置'
                """)
                print("[TABLE] gh_quick_links 已创建")
                table_ready = True
            except pymysql.err.OperationalError as e:
                if "CREATE command denied" in str(e):
                    print("[SKIP] 无 CREATE 权限 (student_dev), 跳过建表 (表应由管理员预先创建)")
                else:
                    raise
            except pymysql.err.ProgrammingError as e:
                # 表已存在
                if "already exists" in str(e).lower():
                    print("[TABLE] gh_quick_links 已存在")
                    table_ready = True
                else:
                    raise

            # 如果建表被跳过，快速验证表是否已存在
            if not table_ready:
                try:
                    cur.execute("SELECT 1 FROM gh_quick_links LIMIT 0")
                    table_ready = True
                    print("[TABLE] gh_quick_links 表已存在 (管理员已创建)")
                except pymysql.err.ProgrammingError:
                    table_ready = False

            # ── 2. 预填默认数据 ────────────────────────────────────
            if table_ready:
                inserted = 0
                base_url = GITHUB_REPO_URL
                for lid, label, suffix, icon, sort_order in DEFAULT_LINKS:
                    full_url = f"{base_url}{suffix}"
                    try:
                        cur.execute(
                            "INSERT INTO gh_quick_links (id, label, url, icon, visible, sort_order) "
                            "VALUES (%s, %s, %s, %s, 1, %s) "
                            "ON DUPLICATE KEY UPDATE "
                            "  url = VALUES(url), "
                            "  icon = VALUES(icon)",
                            (lid, label, full_url, icon, sort_order),
                        )
                        if cur.rowcount == 1:
                            inserted += 1
                    except pymysql.err.OperationalError as e:
                        if "command denied" in str(e).lower():
                            print("[SKIP] 无 INSERT 权限, 跳过种子数据")
                            break
                        raise

                if inserted > 0:
                    print(f"[SEED] 已插入 {inserted} 条默认链接")
                else:
                    print("[INFO] 所有链接已存在, 跳过插入")
            else:
                print("[SKIP] 表不存在且无建表权限")
                print("  --> 请管理员执行: scripts/migration_F_D_008_gh_quick_links.sql")

            # ── 3. 查询当前全部数据 ──────────────────────────────────
            if table_ready:
                try:
                    cur.execute(
                        "SELECT id, label, url, visible, sort_order "
                        "FROM gh_quick_links ORDER BY sort_order"
                    )
                    rows = cur.fetchall()
                except pymysql.err.OperationalError:
                    print("[SKIP] 无 SELECT 权限, 无法展示数据")
                    rows = []

                print()
                print("=" * 90)
                print(f"{'ID':<22} {'Label':<22} {'Vis':<5} {'Sort':<5} URL")
                print("-" * 90)
                for row in rows:
                    vid = row[0]
                    label = row[1]
                    url = row[2]
                    visible = "Y" if row[3] else "N"
                    sort = row[4]
                    print(f"{vid:<22} {label:<22} {visible:<5} {sort:<5} {url}")
                print("=" * 90)
                print(f"  Total: {len(rows)} rows")
                print()

            print(f"  Repo URL: {GITHUB_REPO_URL}")
            print("[DONE] F_D_008 快捷链接数据库初始化完成!")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
