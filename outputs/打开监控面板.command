#!/bin/bash
# 双击本文件打开 Pons / StonkFun 监控面板（不依赖常驻服务）
DIR="$(cd "$(dirname "$0")" && pwd)"
HTML="$DIR/pons-stonkfun-monitor.html"
PORT=8777

if [ ! -f "$HTML" ]; then
  echo "找不到面板文件：$HTML"
  read -r -p "按回车关闭…" _
  exit 1
fi

# 有 python3 就顺手起一个本地服务（页面里的“实时数据”刷新更稳），失败就直接用文件打开
if command -v python3 >/dev/null 2>&1; then
  lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
  ( cd "$DIR/.." && python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & )
  sleep 1
  if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/outputs/pons-stonkfun-monitor.html"; then
    echo "面板已启动：http://127.0.0.1:$PORT/outputs/pons-stonkfun-monitor.html"
    open "http://127.0.0.1:$PORT/outputs/pons-stonkfun-monitor.html"
    echo "关闭本终端窗口即停止服务；也可以随时直接双击 pons-stonkfun-monitor.html。"
    wait
    exit 0
  fi
fi

echo "本地服务未启动，直接用浏览器打开文件：$HTML"
open "$HTML"
sleep 1
exit 0
