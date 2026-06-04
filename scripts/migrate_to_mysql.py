#!/usr/bin/env python3
"""将第10章文档中所有 PostgreSQL 引用替换为 MySQL"""

DOC_PATH = '/root/OA-EPP/docs/第10章_软件产品介绍.md'

with open(DOC_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─── 容器规划表 ──────────────────────────────────────────────────────────────
content = content.replace(
    '| `oaepp-postgres` | `postgres:16-alpine` | 仅内网（5432） | 统一开发数据库，存储全部业务数据 |',
    '| `oaepp-mysql` | `mysql:8.0` | 仅内网（3306） | 统一开发数据库，存储全部业务数据 |',
    1
)
content = content.replace(
    '| `oaepp-pgadmin` | `dpage/pgadmin4` | 5050（管理员专用，按需启动） | 教师 DDL 操作与数据库可视化管理 |',
    '| `oaepp-phpmyadmin` | `phpmyadmin:latest` | 5050（管理员专用，按需启动） | 教师 DDL 操作与数据库可视化管理 |',
    1
)
content = content.replace(
    '| `oaepp-postgres-preview-{pr}` | 隔离的测试数据库，预填 fixture 数据 |',
    '| `oaepp-mysql-preview-{pr}` | 隔离的测试数据库，预填 fixture 数据 |',
    1
)

# ─── docker-compose.yml 生产环境 ──────────────────────────────────────────────
old_compose_prod = '''```yaml
version: "3.9"

services:
  oaepp-app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://oaepp:${POSTGRES_PASSWORD}@oaepp-postgres:5432/oaepp_dev
      REDIS_URL: redis://oaepp-redis:6379
      SECRET_KEY: ${SECRET_KEY}
      REFLEX_ENV: prod
    depends_on:
      oaepp-postgres:
        condition: service_healthy
      oaepp-redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      # Coolify / Traefik 自动 HTTPS
      - "traefik.enable=true"
      - "traefik.http.routers.oaepp.rule=Host(`oaepp.yourdomain.com`)"
      - "traefik.http.routers.oaepp.tls.certresolver=letsencrypt"

  oaepp-postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: oaepp
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: oaepp_dev
    volumes:
      - oaepp_postgres_data:/var/lib/postgresql/data
      # 初始化学生角色（无 DDL 权限）
      - ./scripts/init-student-role.sql:/docker-entrypoint-initdb.d/01-student-role.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U oaepp -d oaepp_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  oaepp-redis:
    image: redis:7-alpine
    volumes:
      - oaepp_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  oaepp-pgadmin:
    image: dpage/pgadmin4:latest
    profiles: ["admin"]   # 仅需要时启动：docker compose --profile admin up
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    ports:
      - "5050:80"
    depends_on:
      - oaepp-postgres

volumes:
  oaepp_postgres_data:
  oaepp_redis_data:
```'''

new_compose_prod = '''```yaml
version: "3.9"

services:
  oaepp-app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: mysql+pymysql://oaepp:${MYSQL_ROOT_PASSWORD}@oaepp-mysql:3306/oaepp_dev
      REDIS_URL: redis://oaepp-redis:6379
      SECRET_KEY: ${SECRET_KEY}
      REFLEX_ENV: prod
    depends_on:
      oaepp-mysql:
        condition: service_healthy
      oaepp-redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      # Coolify / Traefik 自动 HTTPS
      - "traefik.enable=true"
      - "traefik.http.routers.oaepp.rule=Host(`oaepp.yourdomain.com`)"
      - "traefik.http.routers.oaepp.tls.certresolver=letsencrypt"

  oaepp-mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_USER: oaepp
      MYSQL_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: oaepp_dev
    volumes:
      - oaepp_mysql_data:/var/lib/mysql
      # 初始化学生账号（仅 DML 权限）
      - ./scripts/init-student-role.sql:/docker-entrypoint-initdb.d/01-student-role.sql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  oaepp-redis:
    image: redis:7-alpine
    volumes:
      - oaepp_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  oaepp-phpmyadmin:
    image: phpmyadmin:latest
    profiles: ["admin"]   # 仅需要时启动：docker compose --profile admin up
    environment:
      PMA_HOST: oaepp-mysql
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    ports:
      - "5050:80"
    depends_on:
      - oaepp-mysql

volumes:
  oaepp_mysql_data:
  oaepp_redis_data:
```'''

content = content.replace(old_compose_prod, new_compose_prod, 1)

# ─── init-student-role.sql（PostgreSQL 语法 → MySQL 语法） ───────────────────
old_sql = '''```sql
-- 创建学生专用角色（无 DDL 权限）
CREATE ROLE student_role WITH LOGIN PASSWORD 'changeme';
GRANT CONNECT ON DATABASE oaepp_dev TO student_role;
GRANT USAGE ON SCHEMA public TO student_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO student_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO student_role;
-- 注意：无 CREATE / ALTER / DROP 权限
```'''
python3 deploy_local_or_coolify.pynew_sql = '''```sql
-- 创建学生专用账号（仅 DML 权限，无 DDL 权限）
CREATE USER IF NOT EXISTS 'student_role'@'%' IDENTIFIED BY 'changeme';
GRANT SELECT, INSERT, UPDATE, DELETE ON oaepp_dev.* TO 'student_role'@'%';
FLUSH PRIVILEGES;
-- 注意：未授予 CREATE / ALTER / DROP 权限
```'''
content = content.replace(old_sql, new_sql, 1)

# ─── GitHub Actions preview 中的 DATABASE_URL ────────────────────────────────
content = content.replace(
    '"DATABASE_URL": "postgresql://oaepp:preview@oaepp-postgres-preview-${{ github.event.number }}:5432/oaepp_preview",',
    '"DATABASE_URL": "mysql+pymysql://oaepp:preview@oaepp-mysql-preview-${{ github.event.number }}:3306/oaepp_preview",',
    1
)

# ─── Coolify 配置要点 ─────────────────────────────────────────────────────────
content = content.replace(
    '在 Coolify 控制台配置 `POSTGRES_PASSWORD`、`SECRET_KEY` 等，不写入 `.env` 文件',
    '在 Coolify 控制台配置 `MYSQL_ROOT_PASSWORD`、`SECRET_KEY` 等，不写入 `.env` 文件',
    1
)
content = content.replace(
    '`oaepp_postgres_data` 挂载至 Coolify 持久卷，防止重部署丢失数据',
    '`oaepp_mysql_data` 挂载至 Coolify 持久卷，防止重部署丢失数据',
    1
)

# ─── 资源估算表 ───────────────────────────────────────────────────────────────
content = content.replace(
    '| PostgreSQL（轻量配置） | ~128 MB | 1,280 MB |',
    '| MySQL（轻量配置） | ~256 MB | 2,560 MB |',
    1
)

# ─── 大班并发策略：共享预览数据库 + DB 隔离 ─────────────────────────────────
old_preview_db = '''不为每个 PR 创建独立数据库容器，所有 PR 预览环境共用一个「预览专用 PostgreSQL」，通过 **schema 隔离**区分不同 PR 数据：

```yaml
# docker-compose.preview.yml（所有 PR 预览共享）
services:
  oaepp-postgres-preview:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: preview
      POSTGRES_PASSWORD: ${PREVIEW_DB_PASSWORD}
      POSTGRES_DB: oaepp_preview
    volumes:
      - oaepp_preview_db_data:/var/lib/postgresql/data

  oaepp-preview-${PR_NUMBER}:
    build: .
    environment:
      DATABASE_URL: postgresql://preview:${PREVIEW_DB_PASSWORD}@oaepp-postgres-preview:5432/oaepp_preview
      DB_SCHEMA: pr_${PR_NUMBER}   # 每个 PR 使用独立 schema
    mem_limit: 512m      # 内存上限
    cpus: "0.5"          # CPU 上限
```

**效果**：将每个 PR 的容器数从 2 个降至 1 个，数据库资源节省 50%。'''

new_preview_db = '''不为每个 PR 创建独立数据库容器，所有 PR 预览环境共用一个「预览专用 MySQL」，通过**独立数据库名**区分不同 PR 数据：

```yaml
# docker-compose.preview.yml（所有 PR 预览共享）
services:
  oaepp-mysql-preview:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${PREVIEW_DB_PASSWORD}
    volumes:
      - oaepp_preview_db_data:/var/lib/mysql

  oaepp-preview-${PR_NUMBER}:
    build: .
    environment:
      DATABASE_URL: mysql+pymysql://root:${PREVIEW_DB_PASSWORD}@oaepp-mysql-preview:3306/oaepp_pr_${PR_NUMBER}
      DB_NAME: oaepp_pr_${PR_NUMBER}   # 每个 PR 使用独立数据库
    mem_limit: 512m      # 内存上限
    cpus: "0.5"          # CPU 上限
```

**效果**：将每个 PR 的容器数从 2 个降至 1 个，数据库资源节省 50%。'''

content = content.replace(old_preview_db, new_preview_db, 1)

# ─── 大班并发优化汇总表 ───────────────────────────────────────────────────────
content = content.replace(
    '| 预览数据库模式 | 共享 PostgreSQL + schema 隔离 | 节省数据库容器 |',
    '| 预览数据库模式 | 共享 MySQL + 独立数据库隔离 | 节省数据库容器 |',
    1
)

# ─── 架构示意图 ───────────────────────────────────────────────────────────────
content = content.replace(
    '│ PostgreSQL（:5432）      │',
    '│ MySQL（:3306）           │',
    1
)

# ─── Section 16.3.5 .env 配置示例 ────────────────────────────────────────────
content = content.replace(
    '# 服务器：156.239.252.40，端口：5432\n# 账号密码由教师课堂发放，以实际发放为准\nDATABASE_URL=postgresql://oaepp_dev:<教师发放密码>@156.239.252.40:5432/oaepp_dev',
    '# 服务器：156.239.252.40，端口：3306\n# 账号密码由教师课堂发放，以实际发放为准\nDATABASE_URL=mysql+pymysql://oaepp_dev:<教师发放密码>@156.239.252.40:3306/oaepp_dev',
    1
)

# ─── 学生数据库账号说明（schema → 数据库） ──────────────────────────────────
content = content.replace(
    '> **注意**：每位学生使用相同数据库账号连接同一 PostgreSQL，通过独立 schema（`student_学号`）隔离数据。教师在开学初统一创建各学生 schema 并授权。',
    '> **注意**：每位学生使用相同数据库账号连接同一 MySQL 服务器，通过独立数据库（`student_学号`）隔离数据。教师在开学初统一创建各学生数据库并授权，MySQL 中每个"数据库"即等同于 PostgreSQL 的"schema"。',
    1
)

# ─── 常见问题表中的端口 ───────────────────────────────────────────────────────
content = content.replace(
    '确认 `.env` 中 `DATABASE_URL` 正确，课程服务器防火墙已开放 5432 端口',
    '确认 `.env` 中 `DATABASE_URL` 正确，课程服务器防火墙已开放 3306 端口',
    1
)

with open(DOC_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ MySQL 迁移完成")

# 验证
checks_removed = ['PostgreSQL', 'postgresql', 'oaepp-postgres', 'postgres:16-alpine',
                  'POSTGRES_USER', 'pg_isready', 'pgadmin', 'oaepp_postgres_data']
checks_added = ['MySQL', 'mysql+pymysql', 'oaepp-mysql', 'mysql:8.0',
                'MYSQL_ROOT_PASSWORD', 'mysqladmin', 'phpmyadmin', 'oaepp_mysql_data']

print("\n已移除:")
for c in checks_removed:
    count = content.count(c)
    status = "✓ 已清除" if count == 0 else f"⚠️  仍有 {count} 处"
    print(f"  {status}: {c}")

print("\n已引入:")
for c in checks_added:
    count = content.count(c)
    status = f"✓ {count} 处" if count > 0 else "✗ 未找到"
    print(f"  {status}: {c}")
