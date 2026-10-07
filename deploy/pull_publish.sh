#!/bin/bash
# PonsPulse 站点发布器（服务器端）
#
# 作用：从 GitHub 的 snapshots 分支拉最新网页快照（由 GitHub Actions 每小时生成），
#       原子替换站点首页 —— 服务器自己「抓不了」的数（StonkFun 官网 / GeckoTerminal
#       被墙）由海外节点抓好后经仓库送到这里，因此本机、本服务器都无需再跑抓取脚本。
#
# 部署：/home/ubuntu/ponspulse/pull_publish.sh（由系统服务 ponspulse-pull.timer 每 5 分钟触发）
# 日志：/home/ubuntu/ponspulse/pull.log
set -u

BASE="${PONSPULSE_BASE:-/home/ubuntu/ponspulse}"
REPO="$BASE/repo"
WEB="${PONSPULSE_WEB:-/var/www/pons-dashboard/index.html}"
LOG="$BASE/pull.log"

exec >>"$LOG" 2>&1
echo "[$(date '+%F %T')] 检查更新"

cd "$REPO" || { echo "  仓库目录不存在：$REPO"; exit 0; }

if ! git fetch -q --depth=1 origin snapshots 2>/dev/null; then
  echo "  抓取失败（网络？），本轮跳过"
  exit 0
fi
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
SRC="outputs/pons-stonkfun-monitor.html"
SZ="$(stat -c%s "$SRC" 2>/dev/null || echo 0)"
if [ "$SZ" -lt 100000 ]; then
  echo "  文件异常（${SZ}B），不发布"
  exit 0
fi
install -m 644 "$SRC" "$WEB.new" && mv -f "$WEB.new" "$WEB"
echo "$NEW" > "$BASE/last_rev"
echo "  已发布 $NEW（${SZ}B）"

# 定期整理对象库：快照是「孤儿提交 + 强推」，旧的 HTML/JSON 对象没人再引用，
# 不定期清理的话每年会多占几个 GB（每 3 天一次，best-effort，失败不影响发布）。
SPOOL="$BASE/last_gc"
if [ ! -f "$SPOOL" ] || [ $(( $(date +%s) - $(stat -c %Y "$SPOOL" 2>/dev/null || echo 0) )) -gt 259200 ]; then
  git repack -adq 2>/dev/null || true
  git prune --expire=1.day.ago 2>/dev/null || true
  date +%s > "$SPOOL"
  echo "  已整理对象库（$(du -sh .git 2>/dev/null | cut -f1)）"
fi
