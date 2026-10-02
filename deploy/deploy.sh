#!/usr/bin/env bash
# ============================================================
#  Pons / StonkFun 监控看板 —— 一键部署脚本
#  用法：把整个 deploy 文件夹上传到服务器，然后运行
#        bash 一键部署.sh
#  支持：Ubuntu / Debian / CentOS / AliyunLinux / Rocky
# ============================================================
set -e

PORT=80                                    # 主端口（网址不用带端口号）
WEB_DIR=/var/www/pons-dashboard            # 网站文件放这里
CONF_NAME=pons-dashboard.conf

BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'
say()  { echo -e "${BLUE}▶${NC} $1"; }
ok()   { echo -e "${GREEN}✔${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
die()  { echo -e "${RED}✗${NC} $1"; exit 1; }

# ---------- 0. 必须是 root ----------
if [ "$(id -u)" -ne 0 ]; then
  die "请用 root 运行。先执行：sudo -i   然后再跑 bash 一键部署.sh"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/index.html" ] || die "没找到 index.html，请确认你是在 deploy 文件夹里运行的"

# ---------- 1. 安装 nginx ----------
if command -v nginx >/dev/null 2>&1; then
  ok "nginx 已安装，跳过安装"
else
  say "正在安装 nginx（大约 30 秒）..."
  if   command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq && apt-get install -y -qq nginx
  elif command -v dnf >/dev/null 2>&1; then
        dnf install -y -q nginx
  elif command -v yum >/dev/null 2>&1; then
        yum install -y -q nginx
  else
        die "认不出这个系统，请手动安装 nginx 后再运行"
  fi
  ok "nginx 安装完成"
fi

# ---------- 2. 放网页文件 ----------
say "复制看板文件到 $WEB_DIR ..."
mkdir -p "$WEB_DIR"
cp -f "$SCRIPT_DIR/index.html" "$WEB_DIR/index.html"
chmod 644 "$WEB_DIR/index.html"
ok "看板已就位（大小 $(du -h "$WEB_DIR/index.html" | cut -f1)）"

# ---------- 2.5 干掉 nginx 自带默认站点（否则抢 80 端口）----------
for f in /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf; do
  if [ -e "$f" ]; then
    rm -f "$f" && ok "已移除自带默认站点：$f"
  fi
done

# ---------- 3. 写 nginx 配置 ----------
say "写 nginx 配置（端口 $PORT）..."
CONF_DIR=/etc/nginx/conf.d
[ -d "$CONF_DIR" ] || CONF_DIR=/etc/nginx/nginx.conf.d
mkdir -p "$CONF_DIR"

cat > "$CONF_DIR/$CONF_NAME" <<NGINX_EOF
server {
    listen $PORT default_server;
    listen [::]:$PORT default_server;
    listen 8080;
    listen [::]:8080;
    server_name _;

    root $WEB_DIR;
    index index.html;

    # 中文不乱码
    charset utf-8;

    # 看板是个静态单页，关掉缓存保证数据新鲜
    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # 不暴露服务器版本号
    server_tokens off;

    gzip on;
    gzip_types text/html text/css application/javascript;

    access_log /var/log/nginx/pons-dashboard.access.log;
    error_log  /var/log/nginx/pons-dashboard.error.log;
}
NGINX_EOF
ok "配置已写入 $CONF_DIR/$CONF_NAME"

# ---------- 4. 检查配置并重启 ----------
say "检查配置..."
nginx -t >/dev/null 2>&1 || { nginx -t; die "nginx 配置有误，请看上面的报错"; }
ok "配置检查通过"

# ---------- 5. 放行防火墙 ----------
say "放行防火墙端口 $PORT ..."
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow "$PORT"/tcp >/dev/null 2>&1
  ufw allow 8080/tcp >/dev/null 2>&1 && ok "ufw 已放行 $PORT 和 8080"
elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port="$PORT"/tcp >/dev/null 2>&1
  firewall-cmd --permanent --add-port=8080/tcp >/dev/null 2>&1
  firewall-cmd --reload >/dev/null 2>&1 && ok "firewalld 已放行 $PORT 和 8080"
else
  warn "没检测到开启的防火墙，跳过（如果你的服务器有防火墙请手动放行 $PORT）"
fi

# ---------- 6. 启动 / 重载 ----------
say "启动 nginx ..."
if command -v systemctl >/dev/null 2>&1; then
  systemctl enable nginx >/dev/null 2>&1 || true
  systemctl restart nginx
  systemctl is-active --quiet nginx && ok "nginx 正在运行" || die "nginx 启动失败，执行 journalctl -u nginx -n 50 看原因"
else
  nginx -s reload 2>/dev/null || nginx
  ok "nginx 已重载"
fi

# ---------- 7. 自检 ----------
say "本机自检 ..."
if command -v curl >/dev/null 2>&1; then
  if curl -fsS "http://127.0.0.1:$PORT/" -o /dev/null; then
    ok "网站在本机可以正常打开"
  else
    warn "本机访问失败，请检查 nginx 日志"
  fi
fi

# ---------- 8. 打印访问地址 ----------
PUBIP=$(curl -fsS --max-time 5 https://api.ipify.org 2>/dev/null \
     || curl -fsS --max-time 5 https://ifconfig.me 2>/dev/null \
     || curl -fsS --max-time 5 https://ipinfo.io/ip 2>/dev/null \
     || echo "")

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
if [ -n "$PUBIP" ]; then
  echo -e "  别人打开这个网址就能看："
  echo -e "  ${YELLOW}http://$PUBIP${NC}          ← 首选，直接发这个"
  echo -e "  ${YELLOW}http://$PUBIP:8080${NC}   ← 上面打不开就用这个"
else
  echo -e "  访问地址：${YELLOW}http://你的服务器公网IP${NC}  （或 :8080）"
fi
echo ""
echo -e "  ${YELLOW}还打不开的话，去云服务商控制台【安全组 / 防火墙】放行 $PORT 端口${NC}"
echo -e "  （阿里云/腾讯云/华为云都必须在安全组里放行，这是最常见的坑）"
echo ""
echo -e "  更新看板：把新的 index.html 传上来，再跑一次本脚本即可"
echo -e "  改端口：编辑本脚本第 10 行 PORT=80 改成别的数字，重跑"
echo -e "  看日志：tail -f /var/log/nginx/pons-dashboard.error.log"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
