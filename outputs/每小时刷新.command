#!/bin/zsh
# 每小时第 5 分钟由 LaunchAgent 调用（经 Terminal 中转，绕开 macOS 对 ~/Documents 的权限限制）
cd "/Users/alasijiadegou/Documents/Codex/2026-09-28/https-x-com-ponsdotfamily-https-x" || exit 1
exec /usr/bin/python3 work/hourly_check.py
