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
     ponsfi.xyz 看板 · 版本 v2.3「数据滞后讲明白」 · 2026-10-03
     【为什么会做这一版】
       用户截图问：STONK 的 10-02 / 10-03 怎么没数据，是不是 bug？
       实测 curl DefiLlama：stonkfun 最新只到 10-01（909,663），10-02、10-03 源站压根还没出；
       同一时刻 pons 已经出到 10-03（194,596）。也就是说 —— 看板没坏，是上游数据源滞后。
       （DefiLlama 对中小协议的日收入普遍滞后 1~2 天，两家不同步是常态。
         overview/fees 里 StonkFun 仍在榜、total24h 就是 10-01 那条，slug 没变、没掉榜。）
     【这一版改了什么】把「没数的那天」从一根光秃秃的「—」变成三处一眼就懂的提示：
       ① 表格单元格：源站还没出的那天，显示灰色小字「待更新」（英文 pending），
          鼠标悬停有解释：「DefiLlama 还没出这天的数字（不是看板坏了）…」→ 不再是莫名其妙的空白
       ② 表头徽章：PONS / STONK 后面挂橙色小胶囊「数据源最新 10-01」→ 一眼知道数据截止到哪天
       ③ 卡片 + 7 日均行：卡片名字后挂「数据滞后 N 天」；「近 7 日均」那行的日收入格里
          补一行小字「09-25 ~ 10-01」→ 明确告诉用户这个均值是用哪 7 天算出来的，
          避免"今天的数没进来，均值是不是也一起坏了"的误会
     【实现要点】stats() 里新增 lag / lastDate / winFrom / winTo 四个派生值：
       lag = rows.length - 1 - last（最后一个有数的那天距今天的自然天数）
       表头徽章用 lastDate 的 MM-DD；7 日均窗口用 winFrom ~ winTo 的 MM-DD
       文案全部走 i18n（pendingCell / pendingTip / srcLatest / lagBadge / lagTip，中英各一份）
     【注意】lagtag 用的是第 917 行 renderCards 的模板串 —— 这里是母版里的 JS 模板字符串，
       改动要落在 template.base.html，然后 python3 work/rebuild_template.py 重新注入。
       【以后遇到"某天没数"的排查顺序】先 curl 源站，别急着改代码：
       curl -s "https://api.llama.fi/summary/fees/stonkfun?dataType=dailyRevenue" | tail -c 400
       —— 源站没出 = 等；源站有、看板没有 = 才是真 bug。
     v2.2 新增：《无人之岛》配上官方歌词时间轴（audio/down-wuren.lrc，42 句）
       · 原始 lrc 前 16 秒是制作人员名单（词/曲/编曲/缩混/录音室…），显示出来很怪 → 已从文件里删掉，
         歌词从 [00:16]「黑色的背后是黎明」开始；顺便把解析器的过滤正则补全（缩混/配唱/录音室/混音室/企划/母带/宣发）
       · 时间轴核对：把 m4a 解码成 WAV 算了每秒能量包络 —— 副歌「如果云层是天空的一封信」正好踩在
         01:12 的能量大跳点（2037 → 11151），其它乐句也一一对上 → 不需要 lrcOffset
       · 别再把 fetch 放到 file:// 里测：file:// 下 fetch 会被拦，本地页面永远读不到 lrc（要起本地 http 服务器）
         ｜ 线上是同源 https，走的就是普通静态文件，和 up.lrc / down-v2.lrc 一模一样
     v2.1 新增：《无人之岛》进跌幅歌单（跌档现在三首轮换：梦的翅膀受了伤 → 兄弟抱一下 → 无人之岛）
       · 音频 audio/down-wuren.m4a（原始文件是 .aac 后缀，其实是 M4A/AAC 容器，实测浏览器能直接播：
         readyState=4、duration=285.3s、无 decode 错误；服务器 MIME 是 audio/x-m4a，Chrome/Safari/Firefox 都吃）
       · 这首没配 .lrc —— 没歌词时歌词块整块收起、共勉顶上，是 v1.7 就设计好的行为，不是 bug
       · 轮换逻辑是通用的（bgmRot + list.length），加歌只改 BGM_TRACKS 一处 + 补 i18n 歌名
       · 文案同步：BGM 面板「第 3 首（共 3 首）」自动算；bgmRule / bgmLegend 里的"两首"改成"三首"并补歌名
     v2.0.1 紧急修的两个问题（v2.0 只上线了十几分钟）：
       ① 共勉被挤成半宽、右边一大片空白、句子被迫折成两行 —— 根因是 QUOTE_JS 里的状态量
          用了 let：函数声明会提升而 let 不会，BGM_JS 结尾的初始化（lyricPaintIdle）比
          QUOTE_JS 先跑，回调进 qBoxShowSoon 时撞上「暂时性死区」（Cannot access 'QBoxT'
          before initialization），异常被外层 try/catch 静默吞掉，于是歌词块永远不收起、
          一半宽度被它占着。改成 var 后恢复正常（初始化也能正常收起来了）。
       ② 顺手做的设计调整：共勉正文 12.5px → 13px；点赞胶囊常驻粉色心形 + 淡粉底，
          靠右贴齐（不再吊在半空），和右边的「关注 / 打赏」连成一组。
     历史备份（每个都含同名 zip，都在 backups/ 下）：
       v1 / v1.1 / v1.2 / v1.3 / v1.4 / v1.5 / v1.6 / v1.7 / v1.8-2026-10-02 / v1.9-2026-10-03 /
       v2.0-2026-10-03 / v2.0.1-2026-10-03 / v2.1-2026-10-03 / v2.2-2026-10-03 /（本版）v2.3-2026-10-03
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
<meta name="dashboard-version" content="v2.3-2026-10-03">
"""
assert "<!DOCTYPE html>" in tpl
VER = "v2.3 · 2026-10-03"
out_html = tpl.replace("/*__VER__*/ 'v1.0'", repr(VER)).replace("/*__DATA__*/", data).replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)

out = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
open(out, "w", encoding="utf-8").write(out_html)
print("rendered", out, os.path.getsize(out))
