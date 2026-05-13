# ── Stage 1: 构建 MkDocs ──────────────────────────────────────────────────────
FROM python:3.12-alpine AS builder
WORKDIR /build

# ━━━ 方案选择：预编译 vs 实时编译 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 
# 【当前方案】使用预编译的 svgbob_cli（推荐）
# 优点：构建时间从 5-10 分钟减少到 1.5 分钟，节省 70-85% 时间
# 缺点：需要维护预编译二进制文件（bin/svgbob_cli）
#
# 【原始方案】每次构建时编译 svgbob_cli（已废弃，保留供参考）
# 如需重新编译新版本的 svgbob_cli，取消下面注释并注释掉当前方案：
#
# RUN apk add --no-cache cargo rust \
#     && cargo install svgbob_cli --locked \
#     && ln -sf /root/.cargo/bin/svgbob_cli /root/.cargo/bin/svgbob
#
# 注意：编译需要约 5-10 分钟，且依赖 crates.io 网络连接
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 使用预编译的 svgbob_cli
RUN apk add --no-cache libgcc  # svgbob_cli 运行时依赖
COPY bin/svgbob_cli /usr/local/bin/svgbob_cli
RUN chmod +x /usr/local/bin/svgbob_cli \
	&& ln -sf /usr/local/bin/svgbob_cli /usr/local/bin/svgbob
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdocs build

# ── Stage 2: Nginx 提供静态文件 ───────────────────────────────────────────────
FROM nginx:alpine
COPY --from=builder /build/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
