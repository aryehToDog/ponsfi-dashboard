#!/bin/bash
# PonsPulse 兜底触发器（服务器端，2026-10-07 加）
#
# 背景：本仓库的 GitHub 自带 schedule（ponspulse.yml 的 cron）迁移当天连续多个窗口
#   一次都没触发（探针 7 个窗口 0 次），而 push 触发一切正常。为避免「没人 push 数据
#   就停更」，服务器每 10 分钟检查一次 snapshots 快照的新鲜度：超过 STALE_MIN 分钟
#   没更新，就用 workflow_dispatch 主动踢一脚云端构建（云端跑完照常压回 snapshots，
#   服务器上的 ponspulse-pull.timer 再把它发布上线）。
#   GitHub 自带 schedule 一旦恢复，本脚本会自动「静默」——快照够新就不触发，不会重复跑。
#
# 依赖：curl + python3 标准库；token 存在 $BASE/.gh-token（600 权限，见 device-login.sh）。
# 部署：systemd 定时器 ponspulse-dispatch.timer
# 日志：/home/ubuntu/ponspulse/dispatch.log
set -u

BASE="${PONSPULSE_BASE:-/home/ubuntu/ponspulse}"
TOKEN_FILE="$BASE/.gh-token"
STATE="$BASE/last_dispatch"
LOG="$BASE/dispatch.log"
STALE_MIN="${STALE_MIN:-75}"          # 快照超过这么久没更新 → 踢一脚（GitHub 定时正常时一小时一轮）
COOLDOWN_MIN="${COOLDOWN_MIN:-25}"    # 两次主动触发的最小间隔，防失败时连环踢
REPO="aryehToDog/ponsfi-dashboard"
WF="ponspulse.yml"

exec >>"$LOG" 2>&1
log() { echo "[$(date '+%F %T')] $*"; }

if [ ! -s "$TOKEN_FILE" ]; then
  log "没有 token（$TOKEN_FILE），跳过 —— 需要跑一次 deploy/device-login.sh 授权"
  exit 0
fi
chmod 600 "$TOKEN_FILE" 2>/dev/null || true
TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"

# ---- ① snapshots 分支最新快照有多旧 ----
AGE="$(curl -s -m 25 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/commits?sha=snapshots&per_page=1" \
  | python3 -c '
import sys, json, time, calendar
try:
    d = json.load(sys.stdin)
    t = d[0]["commit"]["committer"]["date"]
    epoch = calendar.timegm(time.strptime(t, "%Y-%m-%dT%H:%M:%SZ"))
    print(int((time.time() - epoch) // 60))
except Exception:
    print(-1)
')"

if [ -z "$AGE" ] || [ "$AGE" = "-1" ]; then
  log "拿不到快照时间（API 异常或 token 失效），本轮跳过"
  exit 0
fi

if [ "$AGE" -lt "$STALE_MIN" ]; then
  log "快照 ${AGE} 分钟前刚更新，不用管"
  exit 0
fi

# ---- ② 冷却检查 ----
NOW="$(date +%s)"
LAST="$(cat "$STATE" 2>/dev/null || echo 0)"
case "$LAST" in (''|*[!0-9]*) LAST=0 ;; esac
if [ $(( NOW - LAST )) -lt $(( COOLDOWN_MIN * 60 )) ]; then
  log "快照已 ${AGE} 分钟没更新，但距上次主动触发不到 ${COOLDOWN_MIN} 分钟，继续等"
  exit 0
fi

# ---- ③ 触发 workflow_dispatch ----
CODE="$(curl -s -m 25 -o /tmp/ponspulse-dispatch.out -w '%{http_code}' \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$REPO/actions/workflows/$WF/dispatches" \
  -d '{"ref":"main","inputs":{"mode":"auto"}}')"

echo "$NOW" > "$STATE"
case "$CODE" in
  204) log "快照已 ${AGE} 分钟没更新 → 已触发云端构建（HTTP 204）" ;;
  401|403) log "触发失败（HTTP $CODE）：token 可能失效/权限不足，需要重新跑 deploy/device-login.sh 授权"
           log "  详情：$(head -c 300 /tmp/ponspulse-dispatch.out 2>/dev/null)" ;;
  *)   log "触发失败（HTTP $CODE）：$(head -c 300 /tmp/ponspulse-dispatch.out 2>/dev/null)" ;;
esac
