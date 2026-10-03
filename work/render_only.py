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
     ponsfi.xyz 看板 · 版本 v2.0「共勉搬进作者名片」 · 2026-10-03
     历史备份（每个都含同名 zip）：
       backups/ponsfi-v1-… / v1.1-… / v1.2-… / v1.3-… / v1.4-… / v1.5-… / v1.6-… / v1.7-… / v1.8-2026-10-02/ / v1.9-2026-10-03/
     本版备份：backups/ponsfi-v2.0-2026-10-03/  ＋  ponsfi-v2.0-2026-10-03.zip
     v2.0 改动（这一版只动「共勉 / 点赞」的位置和默认口径，数据与规则逻辑没碰）：
       ① 「共勉」从独立板块搬进作者名片中间那块空白 —— 每次刷新随机显示一句，不轮播，
          换页也不重复上一句（localStorage 记着上一条）。名片不再空一块。
       ② 共勉和歌词互斥，同一个位置同一时间只站一个人：
            放歌 → 共勉立刻收起，歌词顶上（歌词里那一行高亮 + 底部进度条）
            暂停 → 歌词停在原地不动，共勉不抢回来
            关掉音乐 / 这首没有歌词（试听片段、纯音乐）→ 歌词收起，共勉自动回来
          切歌会先清歌词再挂新词，所以「共勉回来」延后 350ms，中间不闪。
       ③ 点赞按钮跟着搬进名片：心形胶囊 + 数字，只加不减、可以一直连点，六句话共用一个数。
          点下去：心形变实心 + 数字蹦一下 + 冒「+1」+ 一把撒花粒子；服务器没接住时数字不掉，
          6 秒后自动再试一次（不会出现"点了又缩回去"）。
       ④ 默认口径改成"先看最近的"：收入排行默认「24 小时」，趋势图默认「日收入」。
          （P/S 卡片仍是 7 日 / 30 日两档，属于估值口径，跟这两个默认值不冲突）
     v1.9 新增：指标说明下方多了一块「共勉」——
       · 六句话每 8 秒轮换一句（只淡换文字，卡片和按钮都不动；鼠标移上去暂停）
       · 右侧一个固定的点赞按钮：不随句子变化消失，只加不减、可以一直连点
         点下去：心形短暂变实心 + 数字蹦一下 + 冒出「+1」+ 一把撒花粒子（canvas，零依赖）
       · 六个句子共用同一个累计数（服务端 /api/likes 计数，不是本地假数）
         ｜ 计数服务：deploy/counter/counter.py（新增 /likes；?d=N 只认正数，单次≤20）
         ｜ 连点先在本地累加，攒成一批再发（5 连点 = d=1 + d=4 两个请求）
         ｜ nginx：/etc/nginx/conf.d/pons-dashboard.conf 里的 location = /api/likes
         ｜ 文案：template.base.html 的 i18n（secQuote / quotes / qLike / qThanks…），中英各一份
     v1.8 改动（只动 BGM 面板的文案与排版，逻辑一行没变）：
       ① 右上角徽章「涨档 / 跌档 / 横盘」→ 大白话「涨了 / 跌了 / 不涨不跌」
       ② 大号百分比旁边加小标题「两家平均涨跌」，一眼知道这数是什么
       ③ 图例改成三行大白话（谁说了算 / 涨跌放什么歌 / 什么时候才换歌），
          删掉「综合情绪 = 按市值加权（7 日涨跌 × 0.65 + 24h 涨跌 × 0.35）」这种黑话
       ④ 逐币明细：「近 7 天 / 近 24 小时」小字放不下时自动换行右对齐，手机不溢出
       ⑤ 面板底部说明同样去掉公式，只留「第几首 / 真歌还是占位 / 最短播放时长」
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
<meta name="dashboard-version" content="v2.0-2026-10-03">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v2.0 · 2026-10-03"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
