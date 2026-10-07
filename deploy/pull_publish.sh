#!/bin/bash
# PonsPulse 站点发布器（服务器端）
#
# 作用：从 GitHub 的 snapshots 分支拉最新网页快照（由 GitHub Actions 每小时生成），
#       原子替换站点首页 —— 服务器自己「抓不了」的数（StonkFun 官网 / GeckoTerminal
#       被墙）由海外节点抓好后经仓库送到这里，因此本机、本服务器都无需再跑抓取脚本。
#
# 网络注意（2026-10-07 实测）：国内服务器连 github.com 偶发抽风（一次 90s 超时失败，
# 过几分钟又 2s 成功），所以这里：
#   ① git fetch 带重试 + 低速早断（GIT_HTTP_LOW_SPEED_*），最多 2 次；
#   ② 都失败时走兜底：api.github.com 的整包 tarball（实测 api 域名明显更稳）；
#   ③ flock 防重入：上一轮没跑完时，这一轮直接跳过。
#
# 部署：/home/ubuntu/ponspulse/pull_publish.sh（systemd 定时器 ponspulse-pull.timer 每 5 分钟触发）
# 日志：/home/ubuntu/ponspulse/pull.log
set -u

BASE="${PONSPULSE_BASE:-/home/ubuntu/ponspulse}"
REPO="$BASE/repo"
WEB="${PONSPULSE_WEB:-/var/www/pons-dashboard/index.html}"
LOG="$BASE/pull.log"

exec >>"$LOG" 2>&1
echo "[$(date '+%F %T')] 检查更新"

exec 9>"$BASE/pull.lock"
if ! flock -n 9; then
  echo "  已有一轮在跑，本轮跳过"
  exit 0
fi

cd "$REPO" || { echo "  仓库目录不存在：$REPO"; exit 0; }

publish() {  # publish <源文件> <新版本号> —— 文件太小就拒绝，正常则原子替换
  local src="$1" rev="$2"
  local sz
  sz="$(stat -c%s "$src" 2>/dev/null || echo 0)"
  if [ "$sz" -lt 100000 ]; then
    echo "  文件异常（${sz}B），不发布"
    return 1
  fi
  install -m 644 "$src" "$WEB.new" && mv -f "$WEB.new" "$WEB"
  echo "$rev" > "$BASE/last_rev"
  echo "  已发布 $rev（${sz}B）"
}

# ---- ① 优先 git fetch（带重试）----
export GIT_TERMINAL_PROMPT=0
export GIT_HTTP_LOW_SPEED_LIMIT=2000 GIT_HTTP_LOW_SPEED_TIME=15
FETCH_OK=0
for i in 1 2; do
  if timeout 45 git fetch -q --depth=1 origin snapshots 2>/tmp/ponspulse-fetch.err; then
    FETCH_OK=1; break
  fi
  echo "  git fetch 第 $i 次失败：$(tail -n 1 /tmp/ponspulse-fetch.err 2>/dev/null)"
  sleep $((i * 4))
done

if [ "$FETCH_OK" = "1" ]; then
  NEW="$(git rev-parse FETCH_HEAD)"
  OLD="$(cat "$BASE/last_rev" 2>/dev/null || true)"
  if [ "$NEW" = "$OLD" ]; then
    echo "  已是最新（$NEW）"
    exit 0
  fi
  if ! git checkout -q -f FETCH_HEAD -- outputs/pons-stonkfun-monitor.html 2>/dev/null; then
    echo "  快照里没有网页文件，跳过"
    exit 0
  fi
  publish "outputs/pons-stonkfun-monitor.html" "$NEW"
else
  # ---- ② 兜底：api.github.com 整包 tarball ----
  echo "  git 通道不通，改用 API 整包下载…"
  TMPD="$(mktemp -d)"
  if ! curl -sSL --max-time 120 -o "$TMPD/snap.tgz" \
       "https://api.github.com/repos/aryehToDog/ponsfi-dashboard/tarball/snapshots"; then
    rm -rf "$TMPD"; echo "  兜底下载失败，本轮跳过"; exit 0
  fi
  SZ0="$(stat -c%s "$TMPD/snap.tgz" 2>/dev/null || echo 0)"
  if [ "$SZ0" -lt 50000 ]; then
    rm -rf "$TMPD"; echo "  兜底包异常（${SZ0}B），跳过"; exit 0
  fi
  tar xzf "$TMPD/snap.tgz" -C "$TMPD" 2>/dev/null
  SRC="$(find "$TMPD" -path '*/outputs/pons-stonkfun-monitor.html' -print -quit)"
  if [ -z "$SRC" ]; then
    rm -rf "$TMPD"; echo "  兜底包里没有网页文件，跳过"; exit 0
  fi
  publish "$SRC" "tarball-$(date +%s)"
  rm -rf "$TMPD"
fi

# ---- ③ 定期整理对象库：快照是「孤儿提交 + 强推」，旧对象没人引用，
#      不定期清理每年会多占几个 GB（每 3 天一次，best-effort，失败不影响发布）----
SPOOL="$BASE/last_gc"
if [ ! -f "$SPOOL" ] || [ $(( $(date +%s) - $(stat -c %Y "$SPOOL" 2>/dev/null || echo 0) )) -gt 259200 ]; then
  git repack -adq 2>/dev/null || true
  git prune --expire=1.day.ago 2>/dev/null || true
  date +%s > "$SPOOL"
  echo "  已整理对象库（$(du -sh .git 2>/dev/null | cut -f1)）"
fi
