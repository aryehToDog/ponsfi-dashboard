#!/bin/zsh
# 每天 09:00 由 LaunchAgent 调用：刷新 Pons / StonkFun 面板并做规则检查
cd "/Users/alasijiadegou/Documents/Codex/2026-09-28/https-x-com-ponsdotfamily-https-x" || exit 1
exec /usr/bin/python3 work/daily_check.py
