#!/bin/bash
# ============================================================
#  双击本文件 → 输入服务器 IP → 全自动部署到你的服务器
#  （在你的 Mac 上运行，不需要自己登录服务器）
# ============================================================
cd "$(dirname "$0")" || exit 1

BOLD=$'\033[1m'; BLUE=$'\033[1;34m'; GREEN=$'\033[1;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[1;31m'; NC=$'\033[0m'

clear
echo ""
echo "${BOLD}========================================================${NC}"
echo "${BOLD}   把看板部署到你的服务器（全自动）${NC}"
echo "${BOLD}========================================================${NC}"
echo ""
echo "  接下来会问你 2 个信息，都在你买服务器的网站后台能看到："
echo ""
echo "   1) 公网 IP   —— 形如 ${YELLOW}123.45.67.89${NC}"
echo "   2) 登录密码  —— 买服务器时你设置的那串密码"
echo ""
echo "${YELLOW}  提示：密码输入时屏幕上不会显示，这是正常的，盲打后按回车${NC}"
echo ""

read -r -p "  请输入服务器公网 IP: " SERVER_IP
if [ -z "$SERVER_IP" ]; then
  echo "${RED}✗${NC} 没输入 IP，退出。"
  read -r -p "按回车关闭…" _; exit 1
fi

read -r -p "  登录用户名（直接回车＝root）: " SERVER_USER
SERVER_USER="${SERVER_USER:-root}"

echo ""
echo "${BOLD}--------------------------------------------------------${NC}"
echo "  目标服务器：${BOLD}$SERVER_USER@$SERVER_IP${NC}"
echo "${BOLD}--------------------------------------------------------${NC}"
echo ""
read -r -p "  确认无误？按回车开始部署（输 n 取消）: " OK
case "$OK" in
  [nN]*) echo "已取消。"; read -r -p "按回车关闭…" _; exit 0 ;;
esac

echo ""
echo "${BLUE}▶${NC} 第 1 步：检查服务器能不能连上…"
if ! ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -o BatchMode=no \
      "$SERVER_USER@$SERVER_IP" "echo connected" >/dev/null 2>&1; then
  echo ""
  echo "${RED}✗${NC} 连不上服务器。常见原因："
  echo "   · IP 输错了"
  echo "   · 密码输错了"
  echo "   · 服务器还没启动完成（刚买的需要等 1~2 分钟）"
  echo ""
  read -r -p "按回车关闭…" _
  exit 1
fi
echo "${GREEN}✔${NC} 连接成功"

echo ""
echo "${BLUE}▶${NC} 第 2 步：上传看板文件…"
scp -o StrictHostKeyChecking=accept-new -q -r \
    index.html deploy.sh nginx.conf "$SERVER_USER@$SERVER_IP:/root/" 2>/dev/null \
  && echo "${GREEN}✔${NC} 上传完成" \
  || { echo "${RED}✗${NC} 上传失败"; read -r -p "按回车关闭…" _; exit 1; }

echo ""
echo "${BLUE}▶${NC} 第 3 步：在服务器上自动安装配置（约 1 分钟）…"
echo ""
ssh -o StrictHostKeyChecking=accept-new -t \
    "$SERVER_USER@$SERVER_IP" \
    "mkdir -p /root/deploy && mv -f /root/index.html /root/deploy.sh /root/nginx.conf /root/deploy/ 2>/dev/null; cd /root/deploy && chmod +x deploy.sh && bash deploy.sh"

echo ""
echo "${BOLD}========================================================${NC}"
echo "${GREEN}  部署流程结束！${NC}"
echo "  浏览器打开上面打印的网址即可，发给他人的也是这个网址。"
echo "${BOLD}========================================================${NC}"
echo ""
read -r -p "按回车关闭窗口…" _
