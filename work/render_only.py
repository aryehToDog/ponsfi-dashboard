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
     ponsfi.xyz 看板 · 版本 v1.7「歌词校对 + 收起逻辑」 · 2026-10-03
     历史备份（每个都含同名 zip）：
       backups/ponsfi-v1-… / v1.1-… / v1.2-… / v1.3-… / v1.4-… / v1.5-… / v1.6-2026-10-02/
     本版备份：backups/ponsfi-v1.7-2026-10-03/  ＋  ponsfi-v1.7-2026-10-03.zip
     v1.7 修复：
       ① 歌词校对 —— 线上原来用的 down.lrc 来自网易云「兄弟抱一下 2021 版」，跟本站这首
          mp3（庞龙《美好》专辑版，ID3 可查）完全是两版编曲：2021 版 2:40 就唱完、还多一段
          原版没有的段落。改用 audio/down-v2.lrc（与专辑版逐句对齐，已用音频能量包络核对
          副歌/主歌切点）。曲目表里可加 lrcOffset（秒）微调：正数＝歌词提前。
       ② 没有歌词可显示时（待命 / 加载中 / 纯音乐 / 试听片段）整块收起，不再显示无意义的
          提示文字，作者名片自动变回紧凑布局（手机上省一行高度）
       ③ 展开的 BGM 详情面板：点屏幕其它地方 / 滑动 / 滚轮 → 立刻收起（PC 与手机同一套行为）
          · 注意 scroll/wheel 的事件目标是 window 不是 Node，判断要用 ev.target.nodeType 兜住
     v1.6 新增：作者名片中间空白处跟着 BGM 滚动显示当前歌词（当前行高亮 + 进度条）
     v1.5 新增：跌幅档双曲轮换（《梦的翅膀受了伤》→《兄弟抱一下》→ …）
     v1.4 新增：页脚浏览量统计（自建计数 /api/hits，见 deploy/counter/）
     v1.3 新增：收入排行板块（DefiLlama 全站榜单裁剪，见 work/leaderboard.py）
     回退方法：解压备份 zip → 用里面的 index.html 覆盖 deploy/index.html 重新上传。
     注意：回退 index.html 不影响歌词文件；服务器上 down-v2.lrc 与 down.lrc 都在。
     ========================================================================== -->
<meta name="dashboard-version" content="v1.7-2026-10-03">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v1.7 · 2026-10-03"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
