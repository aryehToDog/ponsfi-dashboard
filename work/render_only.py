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
     ponsfi.xyz 看板 · 版本 v1.4「浏览量统计」 · 2026-10-02
     历史备份（每个都含同名 zip）：
       backups/ponsfi-v1-2026-10-02/  ponsfi-v1.1-… / ponsfi-v1.2-… / ponsfi-v1.3-2026-10-02/
     本版备份：backups/ponsfi-v1.4-2026-10-02/  ＋  ponsfi-v1.4-2026-10-02.zip
     v1.4 新增：页脚浏览量统计（自建计数，不接任何第三方统计）——
               「👁 总浏览 / 今日 / 今日访客」跟着版本号排在页脚最下面一行。
               · 后端 deploy/counter/counter.py：纯标准库小服务，systemd 常驻，
                 nginx 把 /api/hits 反代到 127.0.0.1:8788（见 /etc/nginx/conf.d/pons-dashboard.conf）
               · 每次打开页面计 1 次浏览；同一天同一 IP 只计 1 个访客（存的是加盐哈希，不存原始 IP）
               · 爬虫 / 探针（bot、spider、curl、wget、监控…）不计入
               · 数据留在 /var/lib/pons-counter/counts.json，保留最近 400 天
               · 只读统计：https://ponsfi.xyz/api/stats
               · 本地 file:// 打开不计数；计数服务挂了页面也不会报错，只是不显示这块
     v1.3 新增：收入排行板块（DefiLlama 全站榜单裁剪，见 work/leaderboard.py）
     回退方法：解压备份 zip → 用里面的 index.html 覆盖 deploy/index.html 重新上传。
     ========================================================================== -->
<meta name="dashboard-version" content="v1.4-2026-10-02">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v1.4 · 2026-10-02"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
