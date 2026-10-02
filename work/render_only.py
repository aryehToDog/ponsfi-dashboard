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
     ponsfi.xyz 看板 · 版本 v1.6「横幅歌词」 · 2026-10-02
     历史备份（每个都含同名 zip）：
       backups/ponsfi-v1-… / v1.1-… / v1.2-… / v1.3-… / v1.4-… / v1.5-2026-10-02/
     本版备份：backups/ponsfi-v1.6-2026-10-02/  ＋  ponsfi-v1.6-2026-10-02.zip
     v1.6 新增：作者名片中间空白处滚动显示「正在播放」的歌词（跟着右下角行情 BGM 走）——
               · 歌词文件与音频同目录：audio/up.lrc、audio/down-meng.lrc、audio/down.lrc
               · 当前行居中高亮、上下行渐隐，下面一条细进度条；窄屏自动铺满一整行
               · 曲目表 BGM_TRACKS 每首多了 lrc 字段，引擎在 rebuild_template.py 的 BGM_JS
               · 音源比歌词时间轴短（如《梦的翅膀受了伤》现在是 19 秒试听片段）会自动降级为
                 文字提示，不会出现「歌词永远是第一句」；换成完整版音频后自动恢复同步
     v1.5 新增：跌幅档双曲轮换（《梦的翅膀受了伤》→《兄弟抱一下》→ …）
     v1.4 新增：页脚浏览量统计（自建计数 /api/hits，见 deploy/counter/）
     v1.3 新增：收入排行板块（DefiLlama 全站榜单裁剪，见 work/leaderboard.py）
     回退方法：解压备份 zip → 用里面的 index.html 覆盖 deploy/index.html 重新上传。
     ========================================================================== -->
<meta name="dashboard-version" content="v1.6-2026-10-02">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v1.6 · 2026-10-02"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
