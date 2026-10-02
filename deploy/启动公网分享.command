#!/bin/bash
# ============================================================
#  双击这个文件 → 自动把看板发布到公网，并显示网址
#  按 Control + C 或关掉这个窗口 = 停止分享
# ============================================================
cd "$(dirname "$0")" || exit 1

BOLD=$'\033[1m'; BLUE=$'\033[1;34m'; GREEN=$'\033[1;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'

echo ""
echo "${BOLD}========================================================${NC}"
echo "${BOLD}   Pons / StonkFun 看板 · 公网分享${NC}"
echo "${BOLD}========================================================${NC}"
echo ""
echo "${BLUE}▶${NC} 第 1 步：清理旧进程…"
pkill -f "http.server 8777" 2>/dev/null
pkill -f "localhost.run" 2>/dev/null
sleep 1

echo "${BLUE}▶${NC} 第 2 步：启动本地服务…"
nohup python3 -m http.server 8777 --bind 127.0.0.1 >/tmp/pons-server.log 2>&1 &
sleep 2
if curl -s -o /dev/null --max-time 5 http://127.0.0.1:8777/ ; then
  echo "${GREEN}✔${NC} 本地服务正常"
else
  echo "${YELLOW}!${NC} 本地服务可能有问题，但还是继续试"
fi

echo "${BLUE}▶${NC} 第 3 步：开启公网隧道（约 10 秒）…"
echo ""
echo "${YELLOW}   ↓↓↓ 下面这一行 https:// 开头的，就是要发出去的网址 ↓↓↓${NC}"
echo ""

# 启动隧道，边输出边把网址抄到桌面文件
ssh -o StrictHostKeyChecking=accept-new \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -T -R 80:localhost:8777 nokey@localhost.run 2>&1 | while IFS= read -r line; do
  echo "$line"
  url=$(echo "$line" | grep -oE 'https://[a-z0-9]+\.lhr\.life' | head -1)
  if [ -n "$url" ]; then
    echo "$url" > "$HOME/Desktop/看板网址.txt"
    printf '%s\n' "$url" | pbcopy 2>/dev/null
    echo ""
    echo "${GREEN}========================================================${NC}"
    echo "${GREEN}  ✔ 网址已生成，并已复制到剪贴板！${NC}"
    echo ""
    echo "  ${BOLD}$url${NC}"
    echo ""
    echo "  直接粘贴发给别人就能打开。${NC}"
    echo "  同时也存到了你桌面的「看板网址.txt」。${NC}"
    echo "${GREEN}========================================================${NC}"
    echo ""
  fi
done

echo ""
echo "${YELLOW}隧道已断开。想重新开启，再双击一次本文件即可。${NC}"
read -r -p "按回车键关闭窗口…" _
