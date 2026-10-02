#!/usr/bin/env bash
# 在服务器上安装 / 升级浏览计数服务。用法：sudo bash install.sh
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"

install -d -o www-data -g www-data /opt/pons-counter /var/lib/pons-counter
install -m 0644 "$SRC/counter.py" /opt/pons-counter/counter.py
install -m 0644 "$SRC/pons-counter.service" /etc/systemd/system/pons-counter.service

systemctl daemon-reload
systemctl enable --now pons-counter >/dev/null
systemctl restart pons-counter
sleep 1
systemctl is-active pons-counter
curl -s --max-time 5 http://127.0.0.1:8788/stats || echo "(本地探测失败)"
echo
