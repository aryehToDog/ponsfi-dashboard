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
     ponsfi.xyz 看板 · 版本 v1.5「跌档双曲轮换」 · 2026-10-02
     历史备份（每个都含同名 zip）：
       backups/ponsfi-v1-… / ponsfi-v1.1-… / ponsfi-v1.2-… / ponsfi-v1.3-… / ponsfi-v1.4-2026-10-02/
     本版备份：backups/ponsfi-v1.5-2026-10-02/  ＋  ponsfi-v1.5-2026-10-02.zip
     v1.5 改动：跌幅档从 1 首变 2 首，放完一首自动换下一首，来回轮换 ——
               《梦的翅膀受了伤》(audio/down-meng.mp3) → 《兄弟抱一下》(audio/down.mp3) → …
               · 进跌档先放《梦的翅膀受了伤》；涨档仍是《逍遥仙》(audio/up.mp3) 单曲循环
               · 曲目表在 rebuild_template.py 的 BGM_TRACKS；轮换游标 bgmRot
               · BGM 详情面板会显示「第 1/2 首」和当前曲名，方便确认在放哪首
     v1.4 新增：页脚浏览量统计（自建计数 /api/hits，见 deploy/counter/）
     v1.3 新增：收入排行板块（DefiLlama 全站榜单裁剪，见 work/leaderboard.py）
     回退方法：解压备份 zip → 用里面的 index.html 覆盖 deploy/index.html 重新上传。
     ========================================================================== -->
<meta name="dashboard-version" content="v1.5-2026-10-02">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v1.5 · 2026-10-02"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
