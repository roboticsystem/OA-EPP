#!/bin/bash
set -e

# 确保 VNC 密码文件存在
if [ ! -f /home/picsimlab/.vnc/passwd ]; then
    mkdir -p /home/picsimlab/.vnc
    echo "${VNC_PW:-picsimlab}" | vncpasswd -f > /home/picsimlab/.vnc/passwd
    chmod 600 /home/picsimlab/.vnc/passwd
    chown -R picsimlab:picsimlab /home/picsimlab/.vnc
fi

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
