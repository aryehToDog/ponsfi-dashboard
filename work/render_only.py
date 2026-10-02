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
     ponsfi.xyz 看板 · 版本 v1.3「收入排行」 · 2026-10-02
     历史备份（每个都含同名 zip）：
       backups/ponsfi-v1-2026-10-02/  backups/ponsfi-v1.1-2026-10-02/  backups/ponsfi-v1.2-2026-10-02/
     本版备份：backups/ponsfi-v1.3-2026-10-02/  ＋  ponsfi-v1.3-2026-10-02.zip
     v1.3 新增：新增「收入排行 · 在整个行业里的位置」板块 ——
               数据来自 DefiLlama 全站收入榜（2,455 个协议），两个项目各一张名次卡：
               24h / 7日 / 30日 三个口径的名次、百分位、对数刻度轴（#1 → #总数）、
               环比（30 日口径 → 现在）、以及「再涨 $X/天就能超过上一名」；
               另附榜首 Top10（天花板在哪）与自身上下/身后的邻居，并用一句话总结近一个月的名次变化。
               榜单快照走 dashboard-data.json 的 leaderboard 字段（约 7KB），
               页面每 6 小时自动刷新一次，也可点「↻ 更新排行」手动拉。
     回退方法：解压备份 zip → 用里面的 index.html 覆盖 deploy/index.html 重新上传。
     ========================================================================== -->
<meta name="dashboard-version" content="v1.3-2026-10-02">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v1.3 · 2026-10-02"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
