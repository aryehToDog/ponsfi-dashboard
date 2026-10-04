#!/bin/zsh
# ponsfi.xyz 看板 · 每小时自动刷新（常驻守护）
#
# 为什么长这样：macOS 隐私保护不允许 launchd 直接拉起的进程读 ~/Documents，
# 所以借 Terminal 跑（Terminal 有权限）。与其每小时开一个新窗口，不如在这里
# 常驻一个循环 —— 桌面只多这一个窗口，不会堆积。
# 开关：关掉这个窗口即停止；LaunchAgent com.ponspulse.hourly 每 30 分钟检查一次，
#       发现不在跑就自动重新打开。
cd "/Users/alasijiadegou/Documents/Codex/2026-09-28/https-x-com-ponsdotfamily-https-x" || exit 1
LOG="work/hourly-daemon.log"
PIDFILE="/tmp/ponsfi-hourly.pid"
# 去重：已经有一个守护在跑就别再开第二个（看门狗 / 手动双击都可能重复触发）
# 存活判断用 ps，不用 kill -0 —— kill 在某些受限环境下会被拒绝（误判成"没在跑"）
if [ -f "$PIDFILE" ]; then
  OLD=$(cat "$PIDFILE" 2>/dev/null)
  if [ -n "$OLD" ] && [ "$OLD" != "$$" ] && ps -p "$OLD" -o pid= >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已有守护在跑（pid $OLD），本窗口退出" >> "$LOG"
    exit 0
  fi
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 守护启动（pid $$）" >> "$LOG"
echo $$ > "$PIDFILE"
while true; do
  echo $$ > "$PIDFILE"
  MIN=$((10#$(date +%M)))
  SEC=$((10#$(date +%S)))
  if [ "$MIN" -lt 5 ]; then
    WAIT=$(( (5 - MIN) * 60 - SEC ))
  else
    WAIT=$(( (65 - MIN) * 60 - SEC ))
  fi
  [ "$WAIT" -lt 5 ] && WAIT=5
  sleep "$WAIT"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始刷新" >> "$LOG"
  /usr/bin/python3 work/hourly_check.py >> "$LOG" 2>&1
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 本轮结束" >> "$LOG"
done
