########################################
# STM32 编译环境 + PicSimLab 仿真器 + noVNC 浏览器访问
# 合并 exam1-1（STM32 工具链）和 picsimlab（GUI 仿真器 + VNC）
########################################
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    VNC_PORT=5901 \
    NOVNC_PORT=6080 \
    VNC_RESOLUTION=1280x800 \
    VNC_PW=picsimlab \
    TZ=Asia/Shanghai

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# ============================================================
# 第一层：STM32 编译工具链 + 嵌入式调试工具（来自 exam1-1）
# ============================================================
RUN apt-get update && apt-get install -y \
    # ARM 交叉编译链
    gcc-arm-none-eabi \
    cmake \
    make \
    build-essential \
    # QEMU 仿真
    qemu-system-arm \
    qemu-utils \
    # 嵌入式调试
    openocd \
    gdb-multiarch \
    stlink-tools \
    socat \
    screen \
    picocom \
    minicom \
    libncurses5-dev \
    # 总线调试
    i2c-tools \
    can-utils \
    # 编译依赖
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    libudev-dev \
    # 基础工具
    git \
    curl \
    wget \
    ca-certificates \
    python3 \
    python3-pip \
    vim \
    nano \
    tree \
    htop \
    unzip \
    zip \
    # 网络工具
    net-tools \
    iproute2 \
    iputils-ping \
    netcat-traditional \
    dnsutils \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 安装 Renode
RUN wget -q https://builds.renode.io/renode-latest.linux-portable.tar.gz -O /tmp/renode.tar.gz \
    && tar -xzf /tmp/renode.tar.gz -C /opt \
    && mv /opt/renode_* /opt/renode \
    && rm /tmp/renode.tar.gz \
    && pip3 install -r /opt/renode/tests/requirements.txt --no-cache-dir

ENV PATH=$PATH:/opt/renode
ENV RENODE_BIN=/opt/renode/renode
RUN ln -s /usr/bin/gdb-multiarch /usr/bin/arm-none-eabi-gdb

# ============================================================
# 第二层：PicSimLab 预编译包（来自 picsimlab）
# ============================================================
RUN wget -q "https://github.com/lcgamboa/picsimlab/releases/download/v0.9.2/PICSimLab_0.9.2_241005_Ubuntu_22.04.5_LTS_amd64.deb" \
        -O /tmp/picsimlab.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/picsimlab.deb \
    && rm -f /tmp/picsimlab.deb \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# 第三层：VNC + noVNC + 窗口管理器（来自 picsimlab）
# ============================================================
RUN apt-get update && apt-get install -y \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    openbox obconf dbus-x11 xterm \
    supervisor \
    fonts-wqy-zenhei \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -s /bin/bash picsimlab

# 工作目录
RUN mkdir -p /workspace /firmware \
    && chown picsimlab:picsimlab /firmware /workspace

# VNC 密码
RUN mkdir -p /home/picsimlab/.vnc \
    && echo "$VNC_PW" | vncpasswd -f > /home/picsimlab/.vnc/passwd \
    && chmod 600 /home/picsimlab/.vnc/passwd \
    && chown -R picsimlab:picsimlab /home/picsimlab/.vnc

# Openbox 配置 —— 自动最大化窗口 & 自启动 PicSimLab
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

WORKDIR /workspace

CMD ["/usr/local/bin/start-vnc.sh"]
