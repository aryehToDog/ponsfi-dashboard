#!/bin/bash
# 把看板发布到 Cloudflare Pages —— 固定网址 https://ponsfi.pages.dev （免备案、永久不变）
# 用法:
#   第一次:  npx wrangler login     (浏览器点一下「允许」即可授权)
#   发布:    ./work/deploy_pages.sh
set -e
cd "$(dirname "$0")/.."
export NPM_CONFIG_CACHE="$PWD/work/.npmcache"
mkdir -p deploy/pages
cp outputs/pons-stonkfun-monitor.html deploy/pages/index.html
echo "== 准备发布 $(wc -c < deploy/pages/index.html) 字节 =="
npx --yes wrangler@3 pages project create ponsfi --production-branch=main >/dev/null 2>&1 || true
npx --yes wrangler@3 pages deploy deploy/pages --project-name=ponsfi --branch=main --commit-dirty=true
