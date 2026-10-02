#!/usr/bin/env python3
# 只用现有快照重新渲染面板（不联网）
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
data = open(os.path.join(HERE, "dashboard-data.json"), encoding="utf-8").read()
assert "/*__DATA__*/" in tpl
assert "/*__VER__*/" in tpl

# ---- 版本标识：写进产出的 HTML，方便以后一眼确认"线上跑的是哪一版" ----
BANNER = """<!-- ==========================================================================
     ponsfi.xyz 看板 · 版本 v1.2「自动行情 BGM」 · 2026-10-02
     上一版备份：backups/ponsfi-v1-2026-10-02/  ＋  ponsfi-v1-2026-10-02.zip
     本版备份：  backups/ponsfi-v1.1-2026-10-02/  ＋  ponsfi-v1.1-2026-10-02.zip
     v1.2 新增：行情 BGM 改为自动播放 —— 加载即尝试出声（老访客全自动），
               被浏览器拦下时等用户第一次点/划/滚立刻淡入；按钮改为「静音/取消静音」，
               访客手动静音过就永不再自动响；首次响起弹一次小提示告知可静音。
     v1.1 新增：右下角「行情BGM」——涨 →《逍遥仙》· 跌 →《兄弟抱一下》
               评分 = 按市值加权（7 日涨跌 × 0.65 + 24h 涨跌 × 0.35）
               ≥ +3% 涨档 · ≤ −3% 跌档 · ±1.5% 滞回防抖 · 横盘不切歌
               同一首至少播 90 秒 · 1.2 秒交叉淡入淡出 · 开着时每 5 分钟自动刷新
               真歌放服务器 /var/www/pons-dashboard/audio/up.mp3 与 down.mp3；
               没有文件时自动播放内置原创占位旋律（Web Audio 合成）
     回退方法：解压备份 zip → 用里面的 index.html 覆盖 deploy/index.html 重新上传。
     ========================================================================== -->
<meta name="dashboard-version" content="v1.2-2026-10-02">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v1.2 · 2026-10-02"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
