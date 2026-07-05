########################################
# PicSimLab + noVNC (browser-based GUI)
# 使用预编译 .deb 包安装 PicSimLab
########################################
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    VNC_PORT=5901 \
    NOVNC_PORT=6080 \
    VNC_RESOLUTION=1280x800 \
    VNC_PW=picsimlab \
    TZ=Asia/Shanghai

# 设置时区（避免交互式配置）
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 先安装基础工具和 wget
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 下载并安装 PicSimLab 预编译 .deb（Ubuntu 22.04 版）—— 它会拉入大量 GUI 依赖
RUN wget -q "https://github.com/lcgamboa/picsimlab/releases/download/v0.9.2/PICSimLab_0.9.2_241005_Ubuntu_22.04.5_LTS_amd64.deb" \
        -O /tmp/picsimlab.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/picsimlab.deb \
    && rm -f /tmp/picsimlab.deb \
    && rm -rf /var/lib/apt/lists/*

# 在 PicSimLab 依赖安装后，再安装 VNC + noVNC + 窗口管理器
RUN apt-get update && apt-get install -y \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    openbox obconf dbus-x11 xterm \
    supervisor \
    procps net-tools \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -s /bin/bash picsimlab

# 固件挂载目录
RUN mkdir -p /firmware && chown picsimlab:picsimlab /firmware

# 安装 netcat（供 rcontrol 远程控制使用）
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# VNC 密码
RUN mkdir -p /home/picsimlab/.vnc \
    && echo "$VNC_PW" | vncpasswd -f > /home/picsimlab/.vnc/passwd \
    && chmod 600 /home/picsimlab/.vnc/passwd \
    && chown -R picsimlab:picsimlab /home/picsimlab/.vnc

# Openbox 自启动 —— 启动时自动打开 PicSimLab
RUN mkdir -p /home/picsimlab/.config/openbox \
    && printf '<?xml version="1.0" encoding="UTF-8"?>\n<openbox_config xmlns="http://openbox.org/3.4/rc">\n  <applications>\n    <application class="*"><maximized>yes</maximized></application>\n  </applications>\n</openbox_config>\n' \
       > /home/picsimlab/.config/openbox/rc.xml \
    && echo 'picsimlab &' > /home/picsimlab/.config/openbox/autostart \
    && chown -R picsimlab:picsimlab /home/picsimlab/.config

# supervisord 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 启动脚本
COPY start-vnc.sh /usr/local/bin/start-vnc.sh
RUN chmod +x /usr/local/bin/start-vnc.sh

EXPOSE ${NOVNC_PORT} 5000

CMD ["/usr/local/bin/start-vnc.sh"]
