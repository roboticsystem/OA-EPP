FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖 + ARM编译链 + QEMU + Renode + 嵌入式调试全量工具
RUN apt update && apt install -y \
    # ========== 原有核心工具 ==========
    gcc-arm-none-eabi \
    cmake \
    curl \
    iputils-ping \
    make \
    git \
    qemu-system-arm \
    qemu-utils \
    minicom \
    libncurses5-dev \
    wget \
    python3 \
    python3-pip \
    mono-complete \
    # ========== 补充：基础终端/文件工具（必加，日常调试高频） ==========
    vim \
    nano \
    tree \
    lsof \
    htop \
    duf \
    unzip \
    zip \
    tar \
    gzip \
    bzip2 \
    # ========== 补充：嵌入式调试核心工具（GD32/STM32必备） ==========
    openocd \
    gdb-multiarch \
    stlink-tools \
    socat \
    screen \
    picocom \
    # ========== 补充：总线/外设调试工具（I2C/CAN/串口，匹配你的风扇电源监控方案） ==========
    i2c-tools \
    can-utils \
    # ========== 补充：网络/系统调试工具（容器内网络、端口、进程排查） ==========
    net-tools \
    iproute2 \
    telnet \
    nmap \
    netcat-traditional \
    dnsutils \
    # ========== 补充：编译/依赖辅助工具（解决各类编译报错、库依赖） ==========
    build-essential \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    libudev-dev \
    && wget https://builds.renode.io/renode-latest.linux-portable.tar.gz -O renode.tar.gz \
    && tar -xzf renode.tar.gz -C /opt \
    && mv /opt/renode_* /opt/renode \
    && rm renode.tar.gz \
    && pip3 install -r /opt/renode/tests/requirements.txt --no-cache-dir \
    && rm -rf /var/lib/apt/lists/*

# 环境变量
ENV PATH=$PATH:/opt/renode
ENV RENODE_BIN=/opt/renode/renode
# 为gdb-multiarch设置别名，兼容arm-none-eabi-gdb调用
RUN ln -s /usr/bin/gdb-multiarch /usr/bin/arm-none-eabi-gdb

WORKDIR /workspace
