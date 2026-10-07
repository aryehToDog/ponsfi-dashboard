#!/bin/bash
# 一次性授权：用 GitHub 设备码（device flow）给服务器换一个能触发 Actions 的 token。
#
# 用法：在服务器上跑  bash /home/ubuntu/ponspulse/device-login.sh
#   屏幕上会出现一个 8 位码（形如 WDJB-MJHT）——浏览器打开 https://github.com/login/device
#   输入这个码 → Continue → Authorize。成功后 token 写入 /home/ubuntu/ponspulse/.gh-token（600）。
#   设备码 15 分钟内有效；过期了就重新跑一遍。
#
# 用的是 GitHub CLI（gh）的公开 client id —— 等价于官方 `gh auth login` 的设备码流程，
# 同意页显示的应用名就是「GitHub CLI」。不想要了随时在 GitHub → Settings →
# Applications → Authorized OAuth Apps 里撤销。
set -u

BASE="${PONSPULSE_BASE:-/home/ubuntu/ponspulse}"
CLIENT_ID="178c6fc778ccc68e1d6a"   # GitHub CLI 公开 client id
SCOPE="repo workflow"              # workflow：允许触发 Actions；repo：访问仓库
OUT="$BASE/.gh-token"

resp="$(curl -s -m 20 -X POST https://github.com/login/device/code \
  -H 'Accept: application/json' \
  -d "client_id=$CLIENT_ID" -d "scope=$SCOPE")"

device_code="$(printf '%s' "$resp" | python3 -c 'import sys,json;print(json.load(sys.stdin)["device_code"])' 2>/dev/null || true)"
user_code="$(printf '%s' "$resp" | python3 -c 'import sys,json;print(json.load(sys.stdin)["user_code"])' 2>/dev/null || true)"
interval="$(printf '%s' "$resp" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("interval",5))' 2>/dev/null || echo 5)"

if [ -z "$device_code" ] || [ -z "$user_code" ]; then
  echo "拿设备码失败：$resp"
  exit 1
fi

echo "设备码：$user_code"
echo "浏览器打开：https://github.com/login/device  输入上面的码 → Continue → Authorize"
echo "（码 15 分钟内有效）"

while :; do
  sleep "$interval"
  tok="$(curl -s -m 20 -X POST https://github.com/login/oauth/access_token \
    -H 'Accept: application/json' \
    -d "client_id=$CLIENT_ID" -d "device_code=$device_code" \
    -d 'grant_type=urn:ietf:params:oauth:grant-type:device_code')"
  err="$(printf '%s' "$tok" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("error",""))' 2>/dev/null || echo parse_error)"
  case "$err" in
    "")
      printf '%s' "$tok" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])' > "$OUT"
      chmod 600 "$OUT"
      echo "✅ 拿到 token，已写入 $OUT"
      exit 0 ;;
    authorization_pending) : ;;
    slow_down) interval=$((interval + 5)); echo "（提示：放慢一点）" ;;
    expired_token) echo "⌛ 设备码过期，请重新运行本脚本"; exit 1 ;;
    access_denied) echo "🚫 授权被拒绝"; exit 1 ;;
    *) echo "异常：$tok"; exit 1 ;;
  esac
done
