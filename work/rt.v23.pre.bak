#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 template.base.html 重新生成 template.html（作者名片 + 全新主题系统）。幂等，可反复运行。"""
import os, re, base64

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "template.base.html")
TPL  = os.path.join(HERE, "template.html")
AVATAR = os.path.join(HERE, "avatar_160.jpg")

X_URL = "https://x.com/arych_kun"
HANDLE_SHORT = "@arych_kun"
NAME = "阿拉斯加的狗💎"
HANDLE = "@arych_kun"

b64 = base64.b64encode(open(AVATAR, "rb").read()).decode()
AV = "data:image/jpeg;base64," + b64

# ============================================================
#  一、主题令牌
# ============================================================
DARK = """:root{
  color-scheme:dark;
  --bg:#0a0c11; --glow:rgba(139,124,255,.13);
  --panel:#11141c; --panel2:#161a24; --panel3:#1c2230;
  --line:#212736; --line2:#2c3446; --grid:#1a1f2b;
  --txt:#e9ecf3; --mut:#858ea1; --mut2:#606a7d;
  --up:#2ee6a8; --down:#ff5c72; --warn:#ffb020;
  --pons:#8b7cff; --stonk:#2ee6a8;
  --pons-dim:rgba(139,124,255,.55); --stonk-dim:rgba(46,230,168,.55);
  --accent:#8b7cff;
  --ok-bg:#0d2b22; --ok-line:#1c5443; --ok-txt:#7ff0c6;
  --wn-bg:#2b210d; --wn-line:#5c451a; --wn-txt:#ffd68a;
  --bd-bg:#2b0d13; --bd-line:#5c1a24; --bd-txt:#ff9aa8;
  --tip-bg:rgba(13,16,23,.94);
  --card-shadow:inset 0 1px 0 rgba(255,255,255,.04);
  --stick-shadow:0 18px 40px -30px rgba(0,0,0,.9);
  --author-glow:linear-gradient(115deg,rgba(139,124,255,.17),rgba(46,230,168,.09) 58%,transparent);
  --cta-bg:#fff; --cta-fg:#0a0c11;
  --cta-shadow:0 6px 20px rgba(0,0,0,.45);
}"""

LIGHT = """  color-scheme:light;
  --bg:#f5f7fb; --glow:rgba(98,73,232,.09);
  --panel:#ffffff; --panel2:#f7f9fd; --panel3:#eef2f9;
  --line:#e6eaf2; --line2:#d3dae7; --grid:#e9edf5;
  --txt:#0f1420; --mut:#5d6779; --mut2:#8a93a6;
  --up:#0d9b73; --down:#dc2f4e; --warn:#b97a00;
  --pons:#6249e8; --stonk:#0d9b73;
  --pons-dim:rgba(98,73,232,.45); --stonk-dim:rgba(13,155,115,.45);
  --accent:#6249e8;
  --ok-bg:#e9f8f2; --ok-line:#b9e6d5; --ok-txt:#0a7357;
  --wn-bg:#fdf4e4; --wn-line:#f0dcb4; --wn-txt:#8f5e00;
  --bd-bg:#fdeef1; --bd-line:#f6ccd5; --bd-txt:#b01e39;
  --tip-bg:rgba(255,255,255,.97);
  --card-shadow:0 1px 2px rgba(16,24,40,.04),0 10px 26px -18px rgba(16,24,40,.22);
  --stick-shadow:0 16px 34px -28px rgba(16,24,40,.55);
  --author-glow:linear-gradient(115deg,rgba(98,73,232,.10),rgba(13,155,115,.07) 58%,transparent);
  --cta-bg:#0f1420; --cta-fg:#ffffff;
  --cta-shadow:0 6px 18px rgba(16,24,40,.25);"""

TOKENS = DARK + "\n" + (
  "/* 浅色 · 手动切换 */\n:root[data-theme=\"light\"]{\n" + LIGHT + "\n}\n"
  "/* 浅色 · 跟随系统（未手动指定时生效） */\n@media (prefers-color-scheme:light){\n"
  ":root:not([data-theme=\"dark\"]):not([data-theme=\"light\"]){\n" + LIGHT + "\n}\n}\n"
)

CSS_BODY = """*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--txt);
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro SC","PingFang SC","Segoe UI",Roboto,sans-serif;
  font-size:12.5px;line-height:1.55;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  font-variant-numeric:tabular-nums;transition:background .25s ease,color .25s ease}
body::before{content:"";position:fixed;left:0;right:0;top:0;height:360px;pointer-events:none;z-index:0;
  background:radial-gradient(780px 360px at 50% -110px,var(--glow),transparent 72%)}
.wrap{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:18px 20px 64px}
.mono{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace}

/* ---------- 页头 ---------- */
header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}
h1{font-size:15.5px;margin:0;font-weight:600;letter-spacing:-.1px}
h1 span{color:var(--mut);font-weight:400;font-size:11.5px;margin-left:9px;letter-spacing:0}
.hdr-right{display:flex;align-items:center;gap:8px}
.badge{font-size:11px;padding:4px 11px;border-radius:20px;border:1px solid var(--line2);
  color:var(--mut);white-space:nowrap;background:var(--panel)}
.badge.live{color:var(--ok-txt);border-color:var(--ok-line);background:var(--ok-bg)}
.badge.off{color:var(--wn-txt);border-color:var(--wn-line);background:var(--wn-bg)}
button{background:var(--panel2);color:var(--txt);border:1px solid var(--line2);border-radius:9px;
  padding:6px 12px;font-size:12px;cursor:pointer;font-family:inherit;font-variant-numeric:inherit;
  transition:background .15s,border-color .15s,transform .08s}
button:hover{background:var(--panel3)}
button:active{transform:translateY(1px)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ---------- 栅格与卡片 ---------- */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 16px;
  box-shadow:var(--card-shadow)}
.card,.rule,.gitem,.chartbox,.cmp-head .col{transition:background .25s ease,border-color .25s ease}

.proj-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:13px}
.proj-name{display:flex;align-items:center;gap:9px;font-size:15px;font-weight:600;letter-spacing:-.1px}
.dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto;box-shadow:0 0 10px currentColor}
.tick{font-size:11px;color:var(--mut);background:var(--panel2);border:1px solid var(--line2);
  padding:2px 7px;border-radius:6px}
.price{text-align:right}
.price .p{font-size:20px;font-weight:600;letter-spacing:-.5px}
.price .m{font-size:11px;color:var(--mut)}
.pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:6px;margin-top:4px;font-weight:600}
.pill.up{background:var(--ok-bg);color:var(--up)}
.pill.down{background:var(--bd-bg);color:var(--down)}

/* ---------- 指标格 ---------- */
.kv{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:11px;overflow:hidden;margin-bottom:12px}
.kv>div{background:var(--panel2);padding:9px 11px}
.kv .k{font-size:10.5px;color:var(--mut);margin-bottom:4px;letter-spacing:.2px}
.kv .v{font-size:14px;font-weight:600;letter-spacing:-.2px}
.kv .v small{font-size:10.5px;color:var(--mut);font-weight:400;letter-spacing:0}
.kv .qi{display:inline-block;width:11px;height:11px;line-height:11px;text-align:center;border-radius:50%;
  background:var(--panel3);border:1px solid var(--line2);color:var(--mut);font-size:8.5px;
  cursor:help;vertical-align:1px;font-weight:700}

/* ---------- 状态条 ---------- */
.status{border-radius:11px;padding:9px 12px;font-size:12px;display:flex;align-items:center;gap:9px;border:1px solid}
.status.good{background:var(--ok-bg);border-color:var(--ok-line);color:var(--ok-txt)}
.status.warn{background:var(--wn-bg);border-color:var(--wn-line);color:var(--wn-txt)}
.status.bad{background:var(--bd-bg);border-color:var(--bd-line);color:var(--bd-txt)}
.status .lbl{font-weight:600}

/* ---------- 段落标题（右侧引一条细线） ---------- */
.sec-title{display:flex;align-items:center;gap:11px;font-size:11.5px;color:var(--mut);
  margin:26px 0 12px;letter-spacing:.6px;font-weight:600;text-transform:uppercase}
.sec-title::after{content:"";flex:1;height:1px;background:var(--line)}

/* ---------- 标签页 ---------- */
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.tab{padding:6px 14px;border-radius:9px;border:1px solid var(--line);background:var(--panel);
  color:var(--mut);cursor:pointer;font-size:12px;font-weight:600;transition:.16s}
.tab:hover{color:var(--txt);border-color:var(--line2)}
.tab.on{background:var(--accent);color:#fff;border-color:transparent;font-weight:800;
  box-shadow:0 8px 22px -12px var(--accent),0 0 0 3px color-mix(in srgb,var(--accent) 20%,transparent)}
.tab.on::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;
  background:#fff;margin-right:7px;vertical-align:1px}

/* ---------- 图表 ---------- */
.chartbox{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:14px 14px 8px;box-shadow:var(--card-shadow)}
.legend{display:flex;gap:16px;margin-bottom:6px;font-size:11.5px;color:var(--mut);flex-wrap:wrap}
.legend i{display:inline-block;width:11px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle}
svg{display:block;width:100%;height:auto;overflow:visible}
.tip{position:absolute;pointer-events:none;background:var(--tip-bg);border:1px solid var(--line2);
  border-radius:9px;padding:7px 10px;font-size:11.5px;display:none;z-index:9;
  -webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);min-width:150px;
  box-shadow:0 10px 30px -12px rgba(0,0,0,.5)}
.tip .d{color:var(--mut);margin-bottom:4px;font-size:10.5px}
.tip .r{display:flex;justify-content:space-between;gap:14px}

/* ---------- 表格（日度明细）---------- */
#tbl{width:100%;min-width:720px;border-collapse:separate;border-spacing:0;font-size:13.5px}
#tbl th,#tbl td{text-align:right;padding:9px 14px;border-bottom:1px solid var(--line);
  font-variant-numeric:tabular-nums;white-space:nowrap}
#tbl th{color:var(--mut);font-weight:600;font-size:11.5px;letter-spacing:.4px;user-select:none;
  position:sticky;background:var(--panel);z-index:2}
#tbl thead tr.grp th{top:0;font-size:13px;font-weight:700;letter-spacing:.5px;padding-top:11px;padding-bottom:8px}
#tbl thead tr.sub th{top:37px;font-size:11px;letter-spacing:.3px;color:var(--mut2);
  padding-top:6px;padding-bottom:6px;border-bottom:1px solid var(--line2);background:var(--panel)}
#tbl th:first-child,#tbl td:first-child{text-align:left}
#tbl td.c-date{color:var(--mut);font-weight:600;font-size:12.5px;letter-spacing:.2px}
#tbl td{color:var(--txt);position:relative}
/* 项目分组：底色 + 左侧色条，一眼区分 PONS / STONK */
#tbl th.g-pons,#tbl td.g-pons{background-color:color-mix(in srgb,var(--pons) 6%,transparent)}
#tbl th.g-stonk,#tbl td.g-stonk{background-color:color-mix(in srgb,var(--stonk) 7%,transparent)}
#tbl tbody tr:nth-child(even) td.g-pons{background-color:color-mix(in srgb,var(--pons) 11%,transparent)}
#tbl tbody tr:nth-child(even) td.g-stonk{background-color:color-mix(in srgb,var(--stonk) 12%,transparent)}
/* 表头必须不透明，否则数据行会从表头下面透出来 */
#tbl thead th.c-date{background:var(--panel)}
#tbl thead th.g-pons{background:linear-gradient(color-mix(in srgb,var(--pons) 10%,transparent),color-mix(in srgb,var(--pons) 10%,transparent)),var(--panel)}
#tbl thead th.g-stonk{background:linear-gradient(color-mix(in srgb,var(--stonk) 11%,transparent),color-mix(in srgb,var(--stonk) 11%,transparent)),var(--panel)}
#tbl thead tr.grp th.g-pons{color:var(--pons);box-shadow:inset 0 -2px 0 var(--pons-dim)}
#tbl thead tr.grp th.g-stonk{color:var(--stonk);box-shadow:inset 0 -2px 0 var(--stonk-dim)}
#tbl tbody tr:hover td{background-image:linear-gradient(color-mix(in srgb,var(--txt) 7%,transparent),color-mix(in srgb,var(--txt) 7%,transparent))}
/* 组间分隔线 */
#tbl th:nth-child(4),#tbl td:nth-child(4){border-right:2px solid var(--line2)}
#tbl th:nth-child(5),#tbl td:nth-child(5){border-left:0}
/* 数值配色 */
#tbl td.v-rev{font-weight:700;font-size:14px}
#tbl td.g-pons.v-rev{color:var(--pons)}
#tbl td.g-stonk.v-rev{color:var(--stonk)}
#tbl td.g-pons.v-bb{color:color-mix(in srgb,var(--pons) 55%,var(--txt))}
#tbl td.g-stonk.v-bb{color:color-mix(in srgb,var(--stonk) 55%,var(--txt))}
#tbl td.v-px{color:var(--mut)}
/* 单元格内的迷你条形：从左侧起，长度＝占当期最大值 */
#tbl td .bar{position:absolute;left:0;top:0;bottom:0;width:var(--w,0%);pointer-events:none;
  border-right:1px solid color-mix(in srgb,currentColor 30%,transparent)}
#tbl td.g-pons .bar{background:linear-gradient(90deg,color-mix(in srgb,var(--pons) 24%,transparent),color-mix(in srgb,var(--pons) 6%,transparent))}
#tbl td.g-stonk .bar{background:linear-gradient(90deg,color-mix(in srgb,var(--stonk) 22%,transparent),color-mix(in srgb,var(--stonk) 5%,transparent))}
#tbl td .v{position:relative;z-index:1}
/* 环比小标 */
#tbl .dlt{position:relative;z-index:1;margin-left:7px;font-size:11px;font-weight:700;letter-spacing:.2px}
#tbl .dlt.up{color:var(--up)} #tbl .dlt.dn{color:var(--down)} #tbl .dlt.flat{color:var(--mut2);font-weight:600}
/* 置顶汇总行：近 7 日均 */
#tbl tbody tr.sum td{border-top:1px solid var(--line2);border-bottom:1px solid var(--line2);font-weight:700}
#tbl tbody tr.sum td.c-date{color:var(--txt);font-weight:700}
#tbl tbody tr.sum td.v-rev,#tbl tbody tr.sum td.v-bb{font-size:14px}

/* ---------- 规则引擎 ---------- */
.rules{display:flex;flex-direction:column;gap:16px}
.rule-legend{display:flex;gap:20px;flex-wrap:wrap;font-size:11.5px;color:var(--mut);margin:0 0 12px;line-height:1.6}
.rule-legend .lg{display:flex;align-items:center;gap:7px}
.tag{font-size:10.5px;font-weight:700;padding:2px 9px;border-radius:6px;white-space:nowrap;flex:0 0 auto;letter-spacing:.5px}
.tag.ok{background:var(--ok-bg);color:var(--ok-txt);border:1px solid var(--ok-line)}
.tag.warn{background:var(--wn-bg);color:var(--wn-txt);border:1px solid var(--wn-line)}
.tag.bad{background:var(--bd-bg);color:var(--bd-txt);border:1px solid var(--bd-line);
  font-weight:800;box-shadow:0 0 0 3px rgba(255,92,114,.14)}
.cmp-head{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:6px}
.cmp-head .col{display:flex;align-items:center;gap:8px;background:var(--panel2);border:1px solid var(--line);
  border-radius:11px;padding:8px 13px;font-size:13px;font-weight:600}
.cmp-head .col .cnt{margin-left:auto;font-size:11px;font-weight:400;color:var(--mut)}
.cmp-row{display:flex;flex-direction:column;gap:7px}
.cmp-label{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:0 2px}
.cmp-label b{font-size:12px;font-weight:600;color:var(--txt)}
.cmp-label .hint{font-size:11px;color:var(--mut2)}
.cmp-label .verdict{margin-left:auto;font-size:11px;padding:2px 10px;border-radius:6px;
  background:var(--panel2);border:1px solid var(--line2);color:var(--mut)}
.cmp-label .verdict.win{color:var(--ok-txt);border-color:var(--ok-line)}
.cmp-pair{display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:stretch}
.cmp-pair>.rule{display:flex;flex-direction:column}
.cmp-pair>.rule .act{margin-top:auto}
.rule{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--line2);
  border-radius:12px;padding:11px 13px;box-shadow:var(--card-shadow)}
.rule.ok{border-left-color:var(--up)}
.rule.warn{border-left-color:var(--warn)}
/* 危险/已触发：整张卡片变红 + 呼吸高亮，第一眼就能看到 */
@keyframes badpulse{
  0%,100%{box-shadow:var(--card-shadow),0 0 0 1px var(--bd-line)}
  50%{box-shadow:var(--card-shadow),0 0 0 1px var(--bd-line),0 0 0 5px color-mix(in srgb,var(--down) 13%,transparent)}}
.rule.bad{border-left-color:var(--down);border-left-width:4px;border-color:var(--bd-line);
  background:color-mix(in srgb,var(--bd-bg) 42%,var(--panel));animation:badpulse 2.6s ease-in-out infinite}
.rule.bad .badflag{display:inline-flex;align-items:center;gap:5px;margin-bottom:7px;padding:3px 9px;
  font-size:10.5px;font-weight:800;letter-spacing:.4px;border-radius:6px;
  color:var(--bd-txt);background:var(--bd-bg);border:1px solid var(--bd-line)}
.rule.bad .s{color:var(--txt);font-weight:600}
@media (prefers-reduced-motion:reduce){.rule.bad{animation:none}}
/* 顶部异常横幅：把所有「已触发」的项一次列清楚 */
.alertbar{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:0 0 12px;padding:10px 13px;
  border-radius:12px;font-size:12.5px;line-height:1.7;font-weight:600;
  background:color-mix(in srgb,var(--bd-bg) 78%,var(--panel));border:1px solid var(--bd-line);color:var(--bd-txt)}
.alertbar .ah{margin-left:auto;font-weight:500;color:var(--mut)}
.rule.sum{border-left-color:var(--line2)}
.rule .rtop{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px}
.rule .pname{font-size:11.5px;font-weight:600;display:none}
.rule .s{color:var(--mut);font-size:11.5px;line-height:1.6}
.rule .act{margin-top:8px;font-size:11.5px;padding:6px 10px;border-radius:8px;
  background:var(--panel2);border:1px solid var(--line);color:var(--mut)}
.rule .act.ok{color:var(--ok-txt);border-color:var(--ok-line)}
.rule .act.warn{color:var(--wn-txt);border-color:var(--wn-line)}
.rule .act.bad{color:var(--bd-txt);border-color:var(--bd-line);background:var(--bd-bg);font-weight:700}
.rule.sum .act{color:var(--txt);border-color:var(--line2)}

/* ---------- 指标说明 ---------- */
.guide{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.gitem{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 17px;
  box-shadow:var(--card-shadow)}
.gitem h3{margin:0 0 5px;font-size:13px;font-weight:600;letter-spacing:-.1px}
.gitem .f{font-size:10.5px;color:var(--mut2);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  margin-bottom:10px;word-break:break-all}
.gitem .lead{font-size:12px;color:var(--mut);line-height:1.8;margin:0 0 11px}
.gitem .ex{background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:10px 12px;
  font-size:11.5px;line-height:2;margin-bottom:11px;word-break:break-word}
.gitem .ex b{color:var(--txt)}
.gitem .ex .cap{color:var(--mut2);font-size:10.5px;letter-spacing:.3px;margin-bottom:4px}
.gitem ul{margin:0;padding-left:0;list-style:none;font-size:11.5px;line-height:1.95;color:var(--mut)}
.gitem ul li{display:flex;gap:9px}
.gitem ul li .band{flex:0 0 auto;min-width:66px;font-family:ui-monospace,monospace;color:var(--txt)}
.gitem .note{margin-top:10px;font-size:11px;color:var(--mut2);line-height:1.8;
  border-top:1px dashed var(--line2);padding-top:9px}
.gitem .g-ok{color:var(--up)} .gitem .g-warn{color:var(--warn)} .gitem .g-bad{color:var(--down)}

/* ---------- 页脚 ---------- */
.foot{color:var(--mut2);font-size:11px;margin-top:28px;line-height:1.85;max-width:1080px}
.foot a{color:var(--accent);text-decoration:none;font-weight:600;border-bottom:1px solid var(--pons-dim)}
.foot a:hover{border-bottom-color:var(--accent)}
.foot .foot-author{display:inline-flex;align-items:center;gap:8px;margin-top:10px;padding:7px 12px;
  border:1px solid var(--line2);border-radius:999px;background:var(--panel);vertical-align:middle}
.foot .foot-author img{width:22px;height:22px;border-radius:50%;object-fit:cover}
.dash-ver{display:inline-flex;align-items:center;gap:7px;margin-top:7px;
  font-size:10.5px;letter-spacing:.5px;color:var(--mut2);font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
  border:1px solid var(--line);border-radius:999px;padding:3px 11px;background:var(--panel)}
.dash-ver::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--up);opacity:.75;
  box-shadow:0 0 0 3px color-mix(in srgb,var(--up) 14%,transparent)}
/* 页脚底行：版本号 + 浏览量（一行排开，窄屏自动换行） */
.foot-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:7px}
.foot-meta .dash-ver{margin-top:0}
.pv{display:inline-flex;align-items:center;gap:6px;font-size:10.5px;letter-spacing:.4px;
  color:var(--mut);border:1px solid var(--line);border-radius:999px;padding:3px 11px;background:var(--panel);
  font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace}
.pv b{font-weight:800;color:var(--txt);letter-spacing:0}
.pv .pv-ic{font-size:12px;line-height:1;opacity:.85}
.pv .pv-k{color:var(--mut2)}
.pv i{font-style:normal;color:var(--line2);margin:0 1px}
.warnline{stroke-dasharray:4 4}

/* ---------- 作者名片 ---------- */
.author{position:relative;z-index:60;display:flex;align-items:center;gap:14px;flex-wrap:wrap;
  background:var(--author-glow),var(--panel);
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  border:1px solid var(--line2);border-radius:16px;padding:12px 15px;margin-bottom:16px;
  overflow:hidden;box-shadow:var(--card-shadow),var(--stick-shadow)}
.topbar{position:fixed;top:0;left:0;right:0;height:60px;z-index:110;pointer-events:none;opacity:0;
  display:flex;align-items:center;
  background:color-mix(in srgb,var(--bg) 74%,transparent);
  -webkit-backdrop-filter:blur(16px) saturate(150%);backdrop-filter:blur(16px) saturate(150%);
  border-bottom:1px solid var(--line)}
.topbar .tb-t{padding-left:152px;font-size:12.5px;font-weight:600;color:var(--mut);letter-spacing:.2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:0;transition:opacity .4s ease}
.topbar.on .tb-t{opacity:1}
.author-mini{position:fixed;top:0;left:0;z-index:120;display:flex;align-items:center;gap:0;
  padding:4px;border-radius:999px;text-decoration:none;
  opacity:0;pointer-events:none;transform-origin:top left;backface-visibility:hidden;
  will-change:transform,opacity}
.author-mini.settled{pointer-events:auto}
.author-mini .mini-bg{position:absolute;inset:0;border-radius:inherit;z-index:-1;opacity:0;
  background:var(--author-glow),var(--panel);border:1px solid var(--line2);
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  box-shadow:0 12px 32px -14px rgba(0,0,0,.6);transition:opacity .3s ease}
.author-mini.settled .mini-bg{opacity:1}
.author-mini img{width:40px;height:40px;border-radius:50%;object-fit:cover;display:block;flex:0 0 auto;
  border:2px solid var(--pons-dim);box-shadow:0 6px 18px -8px rgba(0,0,0,.6)}
.author-mini .mini-tip{max-width:0;margin-left:0;overflow:hidden;white-space:nowrap;
  font-size:12px;font-weight:600;color:var(--mut);letter-spacing:.2px;
  transition:max-width .35s cubic-bezier(.22,1,.36,1),margin-left .35s cubic-bezier(.22,1,.36,1)}
.author-mini.settled:hover .mini-tip{max-width:150px;margin-left:9px}
.author-me{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;min-width:0}
.author-av{width:54px;height:54px;border-radius:50%;object-fit:cover;flex:0 0 auto;background:var(--panel2);
  border:2px solid var(--pons-dim);box-shadow:0 6px 18px -8px rgba(0,0,0,.6)}
.author-name{font-size:15.5px;font-weight:600;display:flex;align-items:center;gap:5px;line-height:1.25;letter-spacing:-.1px}
.author-name .vfy{width:15px;height:15px;flex:0 0 auto}
.author-handle{font-size:11.5px;color:var(--mut);margin-top:2px}
.author-bio{font-size:11.5px;color:var(--mut2);margin-top:3px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;max-width:min(44vw,430px)}
.author-cta{margin-left:auto;display:inline-flex;align-items:center;gap:7px;
  background:var(--cta-bg);color:var(--cta-fg);font-weight:700;font-size:13px;text-decoration:none;
  padding:10px 17px;border-radius:999px;white-space:nowrap;transition:.16s;box-shadow:var(--cta-shadow)}
.author-cta:hover{transform:translateY(-1px)}
.author-cta svg{width:14px;height:14px;fill:var(--cta-fg);flex:0 0 auto}

/* ---------- 作者名片 · 横幅歌词（跟着右下角行情 BGM 走） ---------- */
.lyric{flex:1 1 180px;min-width:0;display:flex;justify-content:center;align-items:center;
  opacity:0;transition:opacity .6s ease;pointer-events:none}
.lyric.hidden{display:none}   /* 没歌词可显示时整块收掉，不留空话 */
.lyric.on{opacity:1}
.ly-in{width:100%;max-width:620px;display:flex;flex-direction:column;gap:6px}
.ly-window{position:relative;height:54px;overflow:hidden;
  -webkit-mask-image:linear-gradient(180deg,transparent 0,#000 27%,#000 73%,transparent 100%);
  mask-image:linear-gradient(180deg,transparent 0,#000 27%,#000 73%,transparent 100%)}
.lyric.note .ly-window{-webkit-mask-image:none;mask-image:none}
.ly-track{will-change:transform;transition:transform .6s cubic-bezier(.22,1,.36,1)}
.ly-line{height:18px;line-height:18px;font-size:12.5px;font-weight:500;color:var(--mut2);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:center;letter-spacing:.2px;
  opacity:.55;transition:color .4s ease,opacity .4s ease}
.ly-line.past{opacity:.3}
.ly-line.on{color:var(--txt);font-weight:700;opacity:1;
  text-shadow:0 0 16px color-mix(in srgb,var(--pons) 55%,transparent)}
.ly-note{font-style:normal;margin-right:6px;color:var(--pons);opacity:.95}
.lyric.note .ly-line.on{color:var(--mut);font-weight:500;opacity:.85;text-shadow:none}
.lyric.note .ly-note{animation:lyPulse 2.4s ease-in-out infinite}
@keyframes lyPulse{0%,100%{opacity:.4}50%{opacity:1}}
.ly-bar{height:2px;border-radius:2px;background:var(--line);overflow:hidden;
  opacity:0;transition:opacity .4s ease}
.lyric.on .ly-bar{opacity:1}
.lyric.note .ly-bar{opacity:0}
.ly-bar i{display:block;height:100%;width:0;border-radius:2px;
  background:linear-gradient(90deg,var(--pons),var(--stonk));transition:width .3s linear}
@media(max-width:900px){.lyric{flex:1 1 100%}.ly-in{max-width:none}}

/* ---------- 刷新反馈 + 手机端点击 ---------- */
@keyframes pxflash{
  0%{transform:scale(1)}
  30%{transform:scale(1.075);color:var(--up)}
  100%{transform:scale(1)}
}
.price .p.flash{animation:pxflash 1.4s cubic-bezier(.22,1,.36,1)}
header button{transition:opacity .2s ease,transform .15s ease}
header button.busy{opacity:.55}
header button:disabled{cursor:default}
a.author-cta,a.author-me,a.author-mini,.foot a,header button,.tab{touch-action:manipulation;
  -webkit-tap-highlight-color:transparent}
.author-cta{position:relative;z-index:3}
.author-me{position:relative;z-index:3}
@media(hover:none){
  .author-cta:hover{transform:none}
  .tab:hover{color:inherit}
}

/* ---------- 响应式 ---------- */
@media(max-width:900px){
  .grid2,.guide,.cmp-head,.cmp-pair{grid-template-columns:1fr}
  .rule .pname{display:inline}
}
@media(max-width:680px){
  body{font-size:12.5px}
  .wrap{padding:14px 14px 52px}
  .kv{grid-template-columns:repeat(2,1fr)}
  .kv .v{font-size:13.5px}
  .price .p{font-size:18px}
  .author{padding:11px 12px;gap:10px;top:6px}
  .author-av{width:46px;height:46px}
  .author-name{font-size:14.5px}
  .author-bio{display:none}
  .author-acts{margin-left:0;width:100%}
  .author-acts>*{flex:1 1 0;justify-content:center;padding:10px 14px}
  .sec-title{margin:22px 0 10px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}

/* ============================================================
   排版系统 v2 —— 统一字体 / 字号 / 字重（解决「字体不一致、有的太小」）
   所有组件统一走 --fs-* 一套字号，数字统一用 tabular-nums 对齐
   ============================================================ */
:root{
  --font-ui:-apple-system,BlinkMacSystemFont,"SF Pro SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei","Segoe UI",Roboto,sans-serif;
  --font-num:ui-monospace,SFMono-Regular,"SF Mono",Menlo,"Roboto Mono",monospace;
  --fs-11:11.5px; --fs-12:12.5px; --fs-13:13.5px; --fs-14:15px; --fs-16:16.5px; --fs-20:21px;
}
body{font-family:var(--font-ui);font-size:var(--fs-13);line-height:1.62;
  font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}
h1{font-size:var(--fs-16);font-weight:700;letter-spacing:-.15px}
h1 span{font-size:var(--fs-11);font-weight:500}
.badge,.tbtn,header button{font-size:var(--fs-12)}
.proj-name{font-size:var(--fs-16);font-weight:700}
.tick{font-size:var(--fs-11)}
.price .p{font-size:var(--fs-20);font-weight:700}
.price .m,.pill{font-size:var(--fs-11)}
.kv .k{font-size:var(--fs-11);font-weight:500;letter-spacing:.15px}
.kv .v{font-size:var(--fs-14);font-weight:700}
.kv .v small{font-size:var(--fs-11);font-weight:500}
.status{font-size:var(--fs-12)}
.status .lbl{font-weight:700}
.sec-title{font-size:var(--fs-12);letter-spacing:.9px}
.tab,.legend,.rule-legend{font-size:var(--fs-12)}
.tag{font-size:var(--fs-11);letter-spacing:.4px}
.cmp-head .col{font-size:var(--fs-13)}
.cmp-head .col .cnt{font-size:var(--fs-11)}
.cmp-label b{font-size:var(--fs-13);font-weight:700}
.cmp-label .hint,.cmp-label .verdict{font-size:var(--fs-11)}
.rule .pname{font-size:var(--fs-12)}
.rule .s{font-size:var(--fs-12);line-height:1.7;color:var(--mut)}
.rule .act{font-size:var(--fs-12);line-height:1.65}
#tbl{font-size:var(--fs-13)}
#tbl td.c-date{font-size:var(--fs-12)}
#tbl th{font-size:var(--fs-11)}
.gitem h3{font-size:var(--fs-14);font-weight:700}
.gitem .f{font-size:var(--fs-11)}
.gitem .lead{font-size:var(--fs-12);line-height:1.85}
.gitem .ex{font-size:var(--fs-12);line-height:1.95}
.gitem ul{font-size:var(--fs-12)}
.gitem .note{font-size:var(--fs-11)}
.foot,.foot .foot-author{font-size:var(--fs-11);line-height:1.9}

/* 关键信息高亮（加底色 + 加粗，让重点一眼看见） */
.hl{font-weight:700;color:var(--txt);
  background:linear-gradient(transparent 58%,color-mix(in srgb,var(--accent) 32%,transparent) 0);
  padding:0 2px;border-radius:3px}
.hl-up{color:var(--up);font-weight:700}
.hl-dn{color:var(--down);font-weight:700}
.hl-warn{color:var(--warn);font-weight:700}
/* 关键数字高亮：颜色自动跟着这张卡的等级走（危险=红 / 警戒=黄 / 正常=绿） */
.hi{font-weight:800;font-family:var(--font-num);letter-spacing:-.2px}
.hi-dn{font-weight:800;color:var(--down)}
.hi-up{font-weight:800;color:var(--up)}
.hi-wn{font-weight:800;color:var(--warn)}
.rule .s .hi{font-size:13px}
.rule.ok   .s .hi{color:var(--ok-txt)}
.rule.warn .s .hi{color:var(--wn-txt)}
.rule.bad  .s .hi{color:var(--bd-txt)}
.gitem .f .hi{color:var(--accent)}
.gitem .lead .hi,.gitem .note .hi,.gitem .ex .hi{color:var(--txt)}
/* 指标说明：颜色图例 */
.glegend{display:flex;gap:16px;flex-wrap:wrap;margin:-2px 0 12px;font-size:var(--fs-11);color:var(--mut)}
.glegend span{display:inline-flex;align-items:center;gap:6px}
.glegend i{width:24px;height:8px;border-radius:3px;display:inline-block}
.glegend .sw-hl{background:linear-gradient(transparent 46%,color-mix(in srgb,var(--accent) 40%,transparent) 0);
  height:14px}
.glegend .sw-num{background:var(--panel2);border:1px solid var(--line2);height:14px}
.gitem b,.gitem .ex b,.rule b,.summary b{font-weight:700;color:var(--txt)}
.gitem .ex b{color:var(--txt)}

/* ---------- 一句话结论卡（放在信号区最上面） ---------- */
.summary{background:var(--panel);border:1px solid var(--line2);border-left:3px solid var(--accent);
  border-radius:14px;padding:14px 16px;margin-bottom:14px;
  box-shadow:var(--card-shadow),0 18px 40px -34px rgba(0,0,0,.9)}
.summary .sum-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.summary .sum-badge{font-size:var(--fs-11);font-weight:700;letter-spacing:.5px;
  color:var(--cta-fg);background:var(--cta-bg);padding:3px 10px;border-radius:6px}
.summary .sum-line{font-size:var(--fs-20);font-weight:700;letter-spacing:-.3px;line-height:1.4}
.summary .sum-line .pnm{font-size:var(--fs-13);color:var(--mut);font-weight:700}
.summary .sum-line b{font-weight:800}
.summary .sum-line b.ok{color:var(--ok-txt)}
.summary .sum-line b.warn{color:var(--wn-txt)}
.summary .sum-line b.bad{color:var(--bd-txt)}
.sum-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.sum-proj{background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:11px 13px}
.sum-proj.ok{border-color:var(--ok-line);background:color-mix(in srgb,var(--ok-bg) 70%,var(--panel))}
.sum-proj.warn{border-color:var(--wn-line);background:color-mix(in srgb,var(--wn-bg) 70%,var(--panel))}
.sum-proj.bad{border-color:var(--bd-line);background:color-mix(in srgb,var(--bd-bg) 70%,var(--panel));
  box-shadow:0 0 0 3px color-mix(in srgb,var(--down) 12%,transparent)}
.sum-proj .sp-top{display:flex;align-items:center;gap:8px;font-weight:700;font-size:var(--fs-13);margin-bottom:6px}
.sum-proj .sp-act{font-size:var(--fs-12);line-height:1.7}
.sum-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.chip{font-size:var(--fs-11);padding:2px 8px;border-radius:6px;background:var(--panel);
  border:1px solid var(--line2);color:var(--mut);white-space:nowrap}
.chip b{color:var(--txt);font-family:var(--font-num);font-weight:700}
.chip b.hi{color:var(--txt)}
.chip b.hi-dn{color:var(--down)}
.chip b.hi-up{color:var(--up)}
.chip b.hi-wn{color:var(--warn)}
.sum-foot{margin-top:10px;font-size:var(--fs-12);color:var(--mut);
  border-top:1px dashed var(--line2);padding-top:9px;line-height:1.7}
.sum-foot b{color:var(--txt)}

/* ---------- 深层分析（每条信号下面的一块数据推理） ---------- */
.rule .deep{margin-top:9px;padding:9px 11px;border-radius:9px;
  background:color-mix(in srgb,var(--accent) 8%,transparent);border:1px solid var(--line);
  font-size:var(--fs-11);line-height:1.8;color:var(--mut)}
.rule .deep .dh{display:block;font-size:10.5px;font-weight:700;letter-spacing:.7px;
  color:var(--accent);margin-bottom:3px}
.rule .deep .dl{display:block;margin-top:4px}
.rule .deep b{color:var(--txt)}

/* ---------- 打赏（钱包地址） ---------- */
.author-acts{display:flex;align-items:center;gap:9px;margin-left:auto;flex-wrap:wrap}
.author-tip{display:inline-flex;align-items:center;gap:7px;font-size:var(--fs-12);
  font-weight:700;padding:10px 16px;border-radius:999px;white-space:nowrap;transition:.16s;
  border:1px solid color-mix(in srgb,var(--warn) 45%,var(--line2));
  background:color-mix(in srgb,var(--wn-bg) 58%,var(--panel));color:var(--wn-txt)}
.author-tip:hover{transform:translateY(-1px);
  border-color:color-mix(in srgb,var(--warn) 78%,var(--line2))}
/* 下滑后停在左上角的打赏按钮（跟着小头像一起出现，方便随时打赏） */
.tip-mini{position:fixed;top:12.5px;left:64px;z-index:119;display:inline-flex;align-items:center;gap:6px;
  padding:8px 13px;border-radius:999px;cursor:pointer;font-size:var(--fs-12);font-weight:700;
  font-family:inherit;color:var(--wn-txt);white-space:nowrap;
  border:1px solid color-mix(in srgb,var(--warn) 45%,var(--line2));
  background:color-mix(in srgb,var(--wn-bg) 62%,var(--panel));
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  box-shadow:0 12px 32px -16px rgba(0,0,0,.6);
  opacity:0;pointer-events:none;transform:translateX(-8px) scale(.94);transform-origin:left center;
  transition:opacity .28s ease,transform .34s cubic-bezier(.22,1,.36,1)}
.tip-mini.settled{opacity:1;pointer-events:auto;transform:none}
.tip-mini:hover{transform:translateY(-1px)}
.tip-mini .tm-ic{font-size:13px;line-height:1}
@media(hover:none){.tip-mini:hover{transform:none}}
.tip-btn{display:inline-flex;align-items:center;gap:6px;font-weight:700;
  border-color:color-mix(in srgb,var(--warn) 55%,var(--line2));
  background:color-mix(in srgb,var(--wn-bg) 70%,var(--panel));color:var(--wn-txt)}
.tip-modal{position:fixed;inset:0;z-index:400;display:none;align-items:center;justify-content:center;
  padding:18px;background:rgba(6,8,12,.6);-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px)}
.tip-modal.on{display:flex}
.tip-card{width:min(560px,100%);max-height:88vh;overflow:auto;background:var(--panel);
  border:1px solid var(--line2);border-radius:16px;padding:20px;
  box-shadow:0 30px 80px -30px rgba(0,0,0,.75)}
.tip-card h3{margin:0 0 6px;font-size:var(--fs-16)}
.tip-card .tsub{margin:0 0 14px;font-size:var(--fs-12);color:var(--mut);line-height:1.75}
.tip-card .tnote{font-size:var(--fs-11);color:var(--mut2);line-height:1.75;margin-top:10px}
.addr{display:flex;align-items:center;gap:9px;background:var(--panel2);border:1px solid var(--line);
  border-radius:11px;padding:10px 12px;margin-top:8px}
.addr .chain{font-size:var(--fs-11);font-weight:700;color:var(--mut);flex:0 0 auto;min-width:58px}
.addr code{flex:1;font-family:var(--font-num);font-size:var(--fs-11);word-break:break-all;color:var(--txt)}
.addr button{flex:0 0 auto;font-size:var(--fs-11);padding:6px 12px;font-weight:700}
.tip-close{position:absolute;top:12px;right:14px}
.tip-thanks{margin-top:14px;padding:10px 12px;border-radius:10px;font-size:var(--fs-12);line-height:1.75;
  background:var(--ok-bg);border:1px solid var(--ok-line);color:var(--ok-txt)}
.toast{position:fixed;left:50%;bottom:34px;z-index:500;transform:translateX(-50%) translateY(14px);
  opacity:0;transition:opacity .26s ease,transform .26s ease;pointer-events:none;
  background:var(--cta-bg);color:var(--cta-fg);font-size:var(--fs-12);font-weight:700;
  padding:10px 18px;border-radius:999px;box-shadow:0 18px 40px -18px rgba(0,0,0,.75);max-width:88vw;text-align:center}
.toast.on{opacity:1;transform:translateX(-50%) translateY(0)}
.foot .foot-tip{display:inline-flex;align-items:center;gap:7px;margin-top:10px;margin-left:8px;vertical-align:middle;
  padding:6px 11px;border:1px solid var(--line2);border-radius:999px;background:var(--panel);
  color:var(--mut);font-size:var(--fs-11);cursor:pointer}
.foot .foot-tip:hover{color:var(--txt);border-color:var(--line2)}
@media(max-width:900px){.sum-grid{grid-template-columns:1fr}}
@media(max-width:680px){
  body{font-size:var(--fs-13)}
  .kv .v{font-size:var(--fs-14)}
  .price .p{font-size:var(--fs-16)}
  .summary .sum-line{font-size:var(--fs-14)}
  .author-tip{margin-left:0;width:100%;justify-content:center;padding:10px 14px}
  .tip-mini{top:11px;left:58px;padding:7px 11px}
  .topbar .tb-t{padding-left:140px}
}

/* ============================================================
   收入排行 —— 「我们现在坐在第几排」
   一张卡 = 一个项目：名次 + 对数刻度轴 + 三个口径 + 环比 + 还差多远
   ============================================================ */
.rank-sub{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:var(--fs-11);
  color:var(--mut);line-height:1.7;margin:-2px 0 11px}
.rank-sub .rank-force{font-size:var(--fs-11);font-weight:700;padding:4px 11px;color:var(--accent);
  border-color:color-mix(in srgb,var(--accent) 40%,var(--line2));
  background:color-mix(in srgb,var(--accent) 10%,var(--panel))}
.rank-sub .rank-force:hover{border-color:var(--accent)}
.rank-updated{font-size:var(--fs-11);color:var(--mut2);margin-left:auto}
.rank-warn{color:var(--wn-txt);font-weight:600}

/* ---- 一句话总结：近一个月名次怎么动 ---- */
.rank-insight{display:flex;align-items:center;gap:10px 16px;flex-wrap:wrap;margin:0 0 13px;padding:9px 13px;
  border-radius:11px;font-size:var(--fs-12);line-height:1.7;color:var(--txt);border:1px solid var(--line);
  background:linear-gradient(90deg,color-mix(in srgb,var(--accent) 13%,transparent),transparent 58%),var(--panel)}
.rank-insight .ri-t{font-size:var(--fs-11);font-weight:700;letter-spacing:.4px;color:var(--mut)}
.rank-insight .ri-p{display:inline-flex;align-items:center;gap:7px;white-space:nowrap}
.rank-insight .ri-p b{font-weight:800;letter-spacing:.2px}
.rank-insight .ri-p i{font-style:normal;font-family:var(--font-num);color:var(--mut)}
.rank-insight .ri-p em{font-style:normal;font-weight:700;font-size:var(--fs-11);padding:1px 7px;
  border-radius:5px;background:var(--panel2);border:1px solid var(--line2)}
.rank-insight .rd-up{color:var(--up)} .rank-insight .rd-down{color:var(--down)}
.rank-insight .rd-flat{color:var(--mut)}

/* ---- 名次卡 ---- */
.rank-card{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:14px 16px 14px 19px;box-shadow:var(--card-shadow);overflow:hidden}
.rank-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;
  background:var(--rank-c,var(--accent))}
.rc-pons{--rank-c:var(--pons)} .rc-stonk{--rank-c:var(--stonk)}
.rank-card-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
.rank-pct{font-size:var(--fs-11);font-weight:700;color:var(--mut);background:var(--panel2);
  border:1px solid var(--line2);border-radius:999px;padding:2px 10px;white-space:nowrap}
.rank-big{font-family:var(--font-num);font-size:36px;font-weight:800;letter-spacing:-1.6px;line-height:1.02;
  color:color-mix(in srgb,var(--rank-c,var(--accent)) 72%,var(--txt))}
.rank-big small{display:block;font-family:var(--font-ui);font-size:var(--fs-11);font-weight:500;
  letter-spacing:0;color:var(--mut);margin-top:4px}

/* ---- 对数刻度轴：#1 在最左，#总数 在最右 ---- */
.rank-scale{padding:0 9px;margin:13px 0 12px}
.rs-track{position:relative;height:5px;border-radius:999px;background:var(--panel3);
  border:1px solid var(--line);box-shadow:inset 0 1px 2px rgba(0,0,0,.16)}
.rs-track i{position:absolute;top:-4.5px;bottom:-4.5px;width:3px;margin-left:-1.5px;border-radius:2px;
  background:var(--rank-c,var(--accent));
  box-shadow:0 0 0 3px color-mix(in srgb,var(--rank-c,var(--accent)) 20%,transparent)}
.rs-ticks{position:relative;height:15px;margin-top:5px}
.rs-ticks span{position:absolute;top:0;transform:translateX(-50%);font-size:10px;color:var(--mut2);
  font-family:var(--font-num);letter-spacing:-.2px}
.rs-ticks span:first-child{transform:none}
.rs-ticks span.rt-end{transform:translateX(-100%)}

/* ---- 三个口径一栏 ---- */
.rank-kv{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.rank-kv span{display:inline-flex;align-items:center;gap:5px;white-space:nowrap;
  font-size:var(--fs-11);color:var(--mut);background:var(--panel2);border:1px solid var(--line);
  border-radius:8px;padding:4px 9px;font-variant-numeric:tabular-nums}
.rank-kv span b{color:var(--mut2);font-weight:600}
.rank-kv span i{font-style:normal;font-family:var(--font-num);font-weight:700;color:var(--txt)}
.rank-kv span em{font-style:normal;font-family:var(--font-num);color:var(--mut)}

/* ---- 环比 + 还差多远 ---- */
.rank-delta{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-size:var(--fs-12);font-weight:700;
  padding-top:10px;border-top:1px dashed var(--line)}
.rank-delta .rd-up{color:var(--up)} .rank-delta .rd-down{color:var(--down)}
.rank-delta .rd-flat{color:var(--mut)}
.rank-delta .rd-why{font-size:var(--fs-11);font-weight:500;color:var(--mut2)}
.rank-gap{margin-top:9px;font-size:var(--fs-12);line-height:1.7;color:var(--txt);border-radius:9px;
  padding:8px 11px;background:color-mix(in srgb,var(--accent) 9%,transparent);
  border:1px solid color-mix(in srgb,var(--accent) 26%,var(--line))}
.rank-gap .rd-why{color:var(--mut2);font-size:var(--fs-11)}
.rank-gap b{color:color-mix(in srgb,var(--accent) 66%,var(--txt))}

/* ---- 榜首 10 名 + 上下邻居 ---- */
.rank-block{margin-top:16px}
.rank-h{display:flex;align-items:center;gap:10px;margin:0 0 9px}
.rank-h .rh-t{font-size:var(--fs-12);font-weight:700;letter-spacing:.3px;color:var(--mut)}
.rank-h::after{content:"";flex:1;height:1px;background:var(--line)}
.rank-list{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;
  box-shadow:var(--card-shadow)}
.rank-row{display:grid;grid-template-columns:46px minmax(0,1fr) minmax(0,168px) 96px;align-items:center;
  gap:10px;padding:9px 14px;border-bottom:1px solid var(--line);font-size:var(--fs-12);
  transition:background .15s ease}
.rank-row:last-child{border-bottom:0}
.rank-row:hover{background:var(--panel2)}
.rank-row .rr-rank{font-family:var(--font-num);font-size:var(--fs-11);font-weight:700;color:var(--mut2)}
.rank-row .rr-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}
.rank-row .rr-cat{font-size:var(--fs-11);color:var(--mut2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank-row .rr-val{font-family:var(--font-num);font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.rank-row.me{background:color-mix(in srgb,var(--accent) 12%,transparent);box-shadow:inset 3px 0 0 var(--accent)}
.rank-row.me .rr-name{font-weight:800;color:var(--txt)}
.rank-row.me .rr-rank,.rank-row.me .rr-val{color:var(--accent)}
.rank-row .rr-me{font-style:normal;font-size:10px;font-weight:800;letter-spacing:.4px;color:var(--accent);
  background:color-mix(in srgb,var(--accent) 16%,transparent);
  border:1px solid color-mix(in srgb,var(--accent) 40%,var(--line));border-radius:5px;
  padding:1px 6px;margin-left:7px;vertical-align:1px;white-space:nowrap}
.rank-near{margin-top:14px;align-items:start}
@media(max-width:680px){
  .rank-card{padding:13px 13px 13px 16px}
  .rank-big{font-size:30px}
  .rank-row{grid-template-columns:38px minmax(0,1fr) 84px;gap:8px;padding:8px 11px}
  .rank-row .rr-cat{display:none}
  .rs-ticks .rt-1000{display:none}
  .rank-updated{margin-left:0;flex-basis:100%}
}
"""

# ============================================================
#  二、作者名片 HTML
# ============================================================
VFY = '<svg class="vfy" viewBox="0 0 24 24" aria-label="认证账号"><path fill="#1d9bf0" d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z"/></svg>'
XLOGO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'

AUTHOR_HTML = (
'  <!-- ===== 作者名片（改文案改这里）===== -->\n'
'  <div class="author">\n'
'    <a class="author-me" href="' + X_URL + '" data-xlink target="_blank" rel="noopener">\n'
'      <img class="author-av" alt="' + NAME + '" src="' + AV + '">\n'
'      <div class="author-info">\n'
'        <div class="author-name">' + NAME + VFY + '</div>\n'
'        <div class="author-handle">' + HANDLE + '</div>\n'
'      </div>\n'
'    </a>\n'
'    <!-- 共勉：每次刷新随机一句；一放歌就让位给歌词 -->\n'
'    <div class="qbox" id="qbox">\n'
'      <div class="qtext" id="qText"></div>\n'
'      <button class="q-like" id="qLike" type="button" onclick="qLike()" title="">\n'
'        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>\n'
'        <b id="qN">0</b>\n'
'        <span class="q-plus" id="qPlus">+1</span>\n'
'      </button>\n'
'    </div>\n'
'    <div class="lyric" id="lyric">\n'
'      <div class="ly-in">\n'
'        <div class="ly-window"><div class="ly-track" id="lyTrack"></div></div>\n'
'        <div class="ly-bar"><i id="lyBarI"></i></div>\n'
'      </div>\n'
'    </div>\n'
'    <div class="author-acts">\n'
'      <a class="author-cta" href="' + X_URL + '" data-xlink target="_blank" rel="noopener">\n'
'        ' + XLOGO + '\n'
'        关注 ' + HANDLE_SHORT + '\n'
'      </a>\n'
'      <button class="author-tip" onclick="openTip()" title="支持作者：请我喝杯咖啡">☕ <span data-tip="btn">打赏</span></button>\n'
'    </div>\n'
'  </div>\n'
'  <!-- 下滑后出现的顶部渐隐条 + 左上角小头像 -->\n'
'  <div class="topbar" id="topbar"><span class="tb-t">Pons · StonkFun 收入与回购监控面板</span></div>\n'
'  <a class="author-mini" href="' + X_URL + '" data-xlink target="_blank" rel="noopener" title="' + NAME + ' ' + HANDLE_SHORT + '">\n'
'    <span class="mini-bg"></span>\n'
'    <img src="' + AV + '" alt="' + NAME + '">\n'
'    <span class="mini-tip">' + HANDLE_SHORT + '</span>\n'
'  </a>\n'
'  <button class="tip-mini" id="tipMini" onclick="openTip()" title="支持作者：请我喝杯咖啡">\n'
'    <span class="tm-ic">☕</span><span data-tip="btn">打赏</span>\n'
'  </button>\n\n')

FOOT_ZH = ('<br><br><span class="foot-author"><img src="' + AV + '" alt="' + NAME + '">'
        '本看板作者 <a href="' + X_URL + '" data-xlink target="_blank" rel="noopener">' + NAME + ' ' + HANDLE_SHORT + '</a>'
        ' &nbsp;·&nbsp; 想看更多项目拆解与实盘记录，欢迎关注</span>'
        '<span class="foot-tip" onclick="openTip()">☕ 请我喝杯咖啡 · 打赏地址</span>')
FOOT_EN = ('<br><br><span class="foot-author"><img src="' + AV + '" alt="' + NAME + '">'
        'Dashboard by <a href="' + X_URL + '" data-xlink target="_blank" rel="noopener">' + NAME + ' ' + HANDLE_SHORT + '</a>'
        ' &nbsp;·&nbsp; Follow for more deep dives and live trades</span>'
        '<span class="foot-tip" onclick="openTip()">☕ Buy me a coffee · tip addresses</span>')

# ============================================================
#  二·五、打赏（钱包地址 / 复制 / 感谢）
# ============================================================
WALLET_EVM = "0xa7f6cc31b6b5454b0eb705e5b56ebfc320e7b5b9"
WALLET_SOL = "EEchRHEuNiMZrHaEVgW1UxtGZwHx4S4JEhW12uGuuQKq"

TIP_BTN = ('      <button class="tip-btn" onclick="openTip()" '
           'title="支持作者：请我喝杯咖啡">☕ <span data-tip="btn">打赏</span></button>\n')

TIP_MODAL = (
'  <!-- ===== 打赏弹窗（改地址改这里）===== -->\n'
'  <div class="tip-modal" id="tipModal" onclick="if(event.target===this)closeTip()">\n'
'    <div class="tip-card">\n'
'      <h3 data-tip="title">☕ 请我喝杯咖啡</h3>\n'
'      <p class="tsub" data-tip="sub">这个面板是我自己一行行写、每天手动核对数据做出来的。如果它帮你少亏了一笔、或者多赚了一笔，欢迎请我喝杯咖啡——不影响任何功能，纯属心意。</p>\n'
'      <div class="addr"><span class="chain">EVM</span><code id="addrEvm">' + WALLET_EVM + '</code>'
'<button onclick="copyAddr(\'addrEvm\',\'EVM\')" data-tip="copy">复制</button></div>\n'
'      <div class="addr"><span class="chain">Solana</span><code id="addrSol">' + WALLET_SOL + '</code>'
'<button onclick="copyAddr(\'addrSol\',\'Solana\')" data-tip="copy">复制</button></div>\n'
'      <div class="tip-thanks" data-tip="thanks">谢谢你的咖啡 ☕ 每一笔打赏我都会记着——它会变成下一次更深的拆解和更快的更新。</div>\n'
'      <div class="tnote" data-tip="note">温馨提示：只认这两个地址，任何让你点链接、输助记词、转「授权」的都是骗子。打赏纯自愿，不构成任何投资建议或收益承诺。</div>\n'
'    </div>\n'
'  </div>\n'
'  <div class="toast" id="toast"></div>\n\n')

TIP_JS = """
/* ---------- 打赏弹窗 + 复制地址 + 感谢提示 ---------- */
function openTip(){
  var m=document.getElementById('tipModal'); if(!m) return;
  m.classList.add('on'); document.body.style.overflow='hidden';
}
function closeTip(){
  var m=document.getElementById('tipModal'); if(!m) return;
  m.classList.remove('on'); document.body.style.overflow='';
}
document.addEventListener('keydown',function(e){ if(e.key==='Escape') closeTip(); });
function toast(msg){
  var el=document.getElementById('toast'); if(!el) return;
  el.textContent=msg; el.classList.add('on');
  clearTimeout(el._tm);
  el._tm=setTimeout(function(){ el.classList.remove('on'); },2600);
}
function copyAddr(id,label){
  var node=document.getElementById(id); if(!node) return;
  var text=(node.textContent||'').trim();
  var done=function(){
    toast((LANG==='zh'?('已复制 '+label+' 地址 · 谢谢你的咖啡 ☕'):(label+' address copied · thank you ☕')));
  };
  var fallback=function(){
    try{
      var ta=document.createElement('textarea');
      ta.value=text; ta.setAttribute('readonly',''); ta.style.position='fixed'; ta.style.top='-1000px';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
      done();
    }catch(e){ toast(LANG==='zh'?'复制失败，请长按地址手动复制':'Copy failed — long-press to copy'); }
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(done).catch(fallback);
  } else { fallback(); }
}
function renderTip(){
  var zh = (LANG==='zh');
  var map={btn:zh?'打赏':'Tip',
    title:zh?'☕ 请我喝杯咖啡':'☕ Buy me a coffee',
    sub:zh?'这个面板是我自己一行行写、每天手动核对数据做出来的。如果它帮你少亏了一笔、或者多赚了一笔，欢迎请我喝杯咖啡——不影响任何功能，纯属心意。'
           :'I built this dashboard myself and check the data by hand every day. If it saved you a bad trade, a coffee is welcome — purely optional, nothing is gated.',
    copy:zh?'复制':'Copy',
    thanks:zh?'谢谢你的咖啡 ☕ 每一笔打赏我都会记着——它会变成下一次更深的拆解和更快的更新。'
             :'Thank you ☕ Every tip goes straight back into deeper research and faster updates.',
    note:zh?'温馨提示：只认这两个地址，任何让你点链接、输助记词、转「授权」的都是骗子。打赏纯自愿，不构成任何投资建议或收益承诺。'
           :'Note: these are the only two addresses. Anyone asking you to click a link, enter a seed phrase or sign an approval is a scammer. Tips are voluntary and never buy returns.'};
  document.querySelectorAll('[data-tip]').forEach(function(el){
    var k=el.getAttribute('data-tip'); if(map[k]) el.textContent=map[k];
  });
}
"""

# ============================================================
#  三、防闪屏 + 主题按钮 + 切换脚本
# ============================================================
HEAD_INIT = ('<meta name="viewport" content="width=device-width, initial-scale=1">\n'
  '<script>/* 主题：先于渲染应用，避免闪屏 */\n'
  '(function(){try{var t=localStorage.getItem("pons-theme")||"auto";\n'
  'if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}catch(e){}})();\n'
  '</script>')

THEME_BTN = ('      <button class="tbtn" id="tbtn" onclick="cycleTheme()" '
             'title="切换主题：跟随系统 / 浅色 / 深色">◐ 系统</button>\n')
LANG_BTN = ('      <button class="tbtn" id="lbtn" onclick="cycleLang()" '
            'title="中文 / English">EN</button>\n')

THEME_JS = """
/* ---------- 主题切换 ---------- */
const THEMES=[{k:'auto',ic:'◐',zh:'系统',en:'Auto'},{k:'light',ic:'☀',zh:'浅色',en:'Light'},{k:'dark',ic:'☾',zh:'深色',en:'Dark'}];
function curTheme(){try{return localStorage.getItem('pons-theme')||'auto'}catch(e){return 'auto'}}
function applyTheme(t){
  const th=THEMES.find(x=>x.k===t)||THEMES[0];
  if(th.k==='auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme',th.k);
  try{localStorage.setItem('pons-theme',th.k);}catch(e){}
  const b=document.getElementById('tbtn');
  if(b){ b.textContent=th.ic+' '+(LANG==='zh'?th.zh:th.en);
         b.title=(LANG==='zh'?'切换主题：跟随系统 / 浅色 / 深色':'Theme: system / light / dark'); }
}
function cycleTheme(){
  const i=THEMES.findIndex(x=>x.k===curTheme());
  applyTheme(THEMES[(i+1)%THEMES.length].k);
}
applyTheme(curTheme());

/* ---------- 顶部作者名片 → 左上角小头像：共享元素式过渡 ----------
   大头像不动，下滑时小头像从大头像的「原位」出发，边缩小边飞向左上角，
   回到顶部再原路飞回。全程跟随滚动位置，不用定时器，所以没有一跳一跳的感觉。 */
(function(){
  var mini=document.querySelector('.author-mini');
  var tmini=document.getElementById('tipMini');
  var big=document.querySelector('.author-av');
  var card=document.querySelector('.author');
  var bar=document.getElementById('topbar');
  if(!mini||!big||!card) return;
  var IMG=40, PAD=4, CX=12, CY=10;      /* 终点：左上角，尺寸与内边距跟 CSS 保持一致 */
  var reduce=false;
  try{ reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){}
  var ticking=false, sx=null, sy=0, s0=1;
  function frame(){
    ticking=false;
    var rc=card.getBoundingClientRect(), rb=big.getBoundingClientRect();
    var p=(8-rc.top)/(rc.height-8);            /* 0＝停在顶部　1＝名片已完全离开视口 */
    p=p<0?0:(p>1?1:p);
    if(p<=0.001||sx===null){ sx=rb.left; sy=rb.top; s0=rb.width/IMG; }  /* 起点＝顶部时的原位 */
    var e=reduce?(p>0.5?1:0):p*p*(3-2*p);      /* smoothstep：起步轻、中段快、落位稳 */
    var s=s0+(1-s0)*e;
    var tx=sx+(CX-sx)*e-PAD*s;
    var ty=sy+(CY-sy)*e-PAD*s;
    mini.style.transform='translate3d('+tx.toFixed(2)+'px,'+ty.toFixed(2)+'px,0) scale('+s.toFixed(4)+')';
    mini.style.opacity=Math.min(1,p/0.10).toFixed(3);
    big.style.opacity=(1-Math.min(1,p/0.28)).toFixed(3);
    var st=e>0.995;
    if(bar){ bar.style.opacity=Math.max(0,Math.min(1,(p-0.18)/0.30)).toFixed(3);
             bar.classList.toggle('on',st); }
    mini.classList.toggle('settled',st);
    if(tmini) tmini.classList.toggle('settled',st);
  }
  function req(){ if(!ticking){ ticking=true; requestAnimationFrame(frame); } }
  window.addEventListener('scroll',req,{passive:true});
  window.addEventListener('resize',req);
  window.addEventListener('load',req);
  req();
})();
"""

# ---- 行情 BGM：样式 / 结构 / 逻辑 ----
BGM_CSS = r'''
/* ---------- 行情 BGM：涨听《逍遥仙》· 跌听《兄弟抱一下》 ---------- */
.bgm{position:fixed;right:16px;bottom:16px;z-index:130;display:flex;flex-direction:column;align-items:flex-end;
  gap:8px;width:min(356px,calc(100vw - 32px));pointer-events:none}
.bgm>*{pointer-events:auto}
.bgm-card{display:flex;align-items:center;gap:9px;padding:8px 14px 8px 11px;border-radius:999px;
  background:color-mix(in srgb,var(--panel) 86%,transparent);
  -webkit-backdrop-filter:blur(16px) saturate(150%);backdrop-filter:blur(16px) saturate(150%);
  border:1px solid var(--line2);color:var(--txt);cursor:pointer;font-family:inherit;text-align:left;
  box-shadow:0 14px 34px -20px rgba(0,0,0,.9);
  transition:border-color .28s ease,box-shadow .28s ease,transform .12s ease}
.bgm-card:hover{transform:translateY(-1px)}
.bgm.up .bgm-card{border-color:color-mix(in srgb,var(--up) 52%,var(--line2));
  box-shadow:0 14px 36px -20px color-mix(in srgb,var(--up) 65%,transparent)}
.bgm.down .bgm-card{border-color:color-mix(in srgb,var(--down) 52%,var(--line2));
  box-shadow:0 14px 36px -20px color-mix(in srgb,var(--down) 65%,transparent)}
.bgm-eq{display:inline-flex;align-items:flex-end;gap:2.5px;height:14px;width:15px;flex:0 0 15px}
.bgm-eq i{width:3px;height:4px;border-radius:2px;background:var(--mut2);transform-origin:bottom;
  transition:background .28s ease}
.bgm.up .bgm-eq i{background:var(--up)} .bgm.down .bgm-eq i{background:var(--down)}
.bgm.live .bgm-eq i{animation:bgmEq 1.05s ease-in-out infinite}
.bgm-eq i:nth-child(2){animation-delay:.16s} .bgm-eq i:nth-child(3){animation-delay:.32s}
@keyframes bgmEq{0%,100%{height:4px}50%{height:14px}}
@media (prefers-reduced-motion:reduce){.bgm.live .bgm-eq i{animation:none;height:8px}}
.bgm-txt{display:flex;flex-direction:column;line-height:1.3}
.bgm-t{font-size:var(--fs-12);font-weight:700;letter-spacing:-.1px;white-space:nowrap}
.bgm-cv{display:none;align-items:center;justify-content:center;width:19px;height:19px;flex:0 0 19px;
  border-radius:50%;color:var(--mut);font-size:10px;line-height:1;background:var(--panel2);
  border:1px solid var(--line);transition:transform .28s ease,color .2s ease,background .2s ease}
.bgm.on .bgm-cv{display:inline-flex}
.bgm.det .bgm-cv{transform:rotate(180deg)}
.bgm-cv:hover{color:var(--txt);background:var(--panel3)}
.bgm-s{font-size:10.5px;color:var(--mut);font-variant-numeric:tabular-nums;white-space:nowrap}
.bgm-det{display:none;width:100%;background:color-mix(in srgb,var(--panel) 92%,transparent);
  -webkit-backdrop-filter:blur(18px) saturate(150%);backdrop-filter:blur(18px) saturate(150%);
  border:1px solid var(--line);border-radius:14px;padding:12px 14px;
  box-shadow:0 20px 44px -26px rgba(0,0,0,.95)}
.bgm.det .bgm-det{display:block;animation:bgmIn .34s cubic-bezier(.32,.72,0,1)}
@keyframes bgmIn{from{opacity:0;transform:translateY(9px) scale(.985)}to{opacity:1;transform:none}}
.bgm-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.bgm-head b{font-size:var(--fs-16);font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.4px}
.bgm-head b.u{color:var(--up)} .bgm-head b.d{color:var(--down)}
.bgm-labw{display:inline-flex;align-items:baseline;gap:7px;min-width:0}
.bgm-hl{font-size:11px;color:var(--mut2);letter-spacing:.2px;white-space:nowrap}
.bgm-tag{font-size:10.5px;font-weight:700;letter-spacing:.6px;padding:2px 9px;border-radius:999px;
  border:1px solid var(--line2);color:var(--mut);white-space:nowrap}
.bgm-tag.up{color:var(--up);border-color:color-mix(in srgb,var(--up) 48%,var(--line2));
  background:color-mix(in srgb,var(--up) 12%,transparent)}
.bgm-tag.down{color:var(--down);border-color:color-mix(in srgb,var(--down) 48%,var(--line2));
  background:color-mix(in srgb,var(--down) 12%,transparent)}
.bgm-legend{font-size:10.5px;color:var(--mut2);line-height:1.62;margin:5px 0 8px;white-space:pre-line}
.bgm-prow{display:flex;align-items:center;gap:9px;font-size:var(--fs-11);padding:5px 0;
  border-top:1px dashed var(--line);flex-wrap:wrap}
.bgm-pn{display:inline-flex;align-items:center;gap:6px;font-weight:700;min-width:70px}
.bgm-pn i{width:6px;height:6px;border-radius:50%;display:inline-block}
.bgm-pv{font-weight:700;font-variant-numeric:tabular-nums;min-width:56px}
.bgm-pv.u{color:var(--up)} .bgm-pv.d{color:var(--down)}
.bgm-pd{color:var(--mut2);font-size:10.5px;margin-left:auto;flex:0 0 auto;font-variant-numeric:tabular-nums}
.bgm-src{font-size:10.5px;color:var(--mut2);line-height:1.62;margin-top:9px;
  border-top:1px dashed var(--line);padding-top:8px}
@media(max-width:640px){.bgm{right:12px;bottom:12px;width:min(330px,calc(100vw - 24px))}}
'''

BGM_HTML = (
    '  <!-- ===== 行情BGM：涨 →《逍遥仙》· 跌 →《梦的翅膀受了伤》/《兄弟抱一下》轮换（音源、阈值改这里）===== -->'
    '  <div class="bgm" id="bgm">'
    '    <div class="bgm-det" id="bgmDet">'
    '      <div class="bgm-head" id="bgmScore"></div>'
    '      <div class="bgm-legend" id="bgmLegend"></div>'
    '      <div class="bgm-parts" id="bgmParts"></div>'
    '      <div class="bgm-src" id="bgmSrc"></div>'
    '    </div>'
    '    <button class="bgm-card" id="bgmCard" type="button" onclick="bgmToggle()" onmouseenter="bgmDetShow()">'
    '      <span class="bgm-eq" id="bgmEq"><i></i><i></i><i></i></span>'
    '      <span class="bgm-txt"><span class="bgm-t" id="bgmT">行情BGM</span><span class="bgm-s" id="bgmS">点一下开启</span></span>'
    '      <span class="bgm-cv" id="bgmCv" onclick="event.stopPropagation();bgmDetToggle()">\u25b4</span>'
    '    </button>'
    '  </div>'
)

# ---- 共勉：作者名片里的一句 + 点赞（有歌词时让位给歌词） ----
QUOTE_CSS = r'''
/* ---------- 共勉：名片中间那一句（BGM 一开口，这里就让位给歌词） ---------- */
.qbox{flex:1 1 180px;min-width:0;display:flex;align-items:center;gap:12px;
  opacity:0;transition:opacity .5s ease}
.qbox.hidden{display:none}         /* 有歌词时整块收掉，不留半透明残影 */
.qbox.on{opacity:1}
.qtext{position:relative;flex:1 1 auto;min-width:0;padding-left:13px;
  font-size:13px;font-weight:500;line-height:1.6;color:var(--txt);letter-spacing:.15px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.qtext::before{content:"";position:absolute;left:0;top:3px;bottom:3px;width:2px;border-radius:2px;
  background:linear-gradient(180deg,var(--pons),var(--stonk));opacity:.8}
@media(max-width:900px){.qbox{flex:1 1 100%}}

/* 点赞：只加不减、可连点；心形和数字都在一个胶囊里 */
:root{--like:#ff6b8a}
:root[data-theme="light"]{--like:#e0325a}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]):not([data-theme="light"]){--like:#e0325a}}
.q-like{position:relative;flex:0 0 auto;margin-left:auto;display:inline-flex;align-items:center;gap:7px;
  padding:7px 14px;border-radius:999px;cursor:pointer;
  border:1px solid color-mix(in srgb,var(--like) 22%,var(--line2));
  background:color-mix(in srgb,var(--like) 7%,var(--panel2));
  color:var(--txt);font-size:12.5px;font-weight:800;letter-spacing:-.2px;
  font-family:inherit;font-variant-numeric:tabular-nums;
  transition:border-color .22s ease,color .22s ease,background .22s ease,transform .12s ease}
.q-like:hover{border-color:var(--like);color:var(--like)}
.q-like:active{transform:scale(.97)}
.q-like svg{width:14px;height:14px;display:block;overflow:visible;color:var(--like)}
.q-like svg path{fill:none;stroke:currentColor;stroke-width:1.7;stroke-linejoin:round;transition:fill .22s ease}
.q-like b{display:inline-block;min-width:13px;text-align:center}
.q-like.hit{border-color:color-mix(in srgb,var(--like) 55%,var(--line2));color:var(--like);
  background:color-mix(in srgb,var(--like) 13%,transparent)}
.q-like.hit svg path{fill:var(--like)}
/* 撒花：点一次赞在按钮上方炸开一小把彩纸（canvas 贴在按钮上，纯装饰） */
.q-confetti{position:fixed;pointer-events:none;z-index:150;display:none}
/* 点下去时飘一个 +1 上去 */
.q-plus{position:absolute;left:50%;top:-3px;transform:translateX(-50%);font-size:11px;font-weight:800;
  color:var(--like);opacity:0;pointer-events:none;letter-spacing:-.2px}
.q-like.plus .q-plus{animation:qPlus .95s cubic-bezier(.32,.72,0,1)}
@keyframes qPlus{0%{opacity:0;transform:translateX(-50%) translateY(3px) scale(.85)}
  22%{opacity:1;transform:translateX(-50%) translateY(-5px) scale(1.08)}
  100%{opacity:0;transform:translateX(-50%) translateY(-26px) scale(1)}}
@keyframes qPop{0%{transform:scale(1)}32%{transform:scale(1.42)}62%{transform:scale(.9)}100%{transform:scale(1)}}
.q-like.pop svg,.q-like.pop b{animation:qPop .46s cubic-bezier(.32,.72,0,1)}
@media (prefers-reduced-motion:reduce){
  .q-like.pop svg,.q-like.pop b{animation:none}
  .q-like.plus .q-plus{animation:none}
}
'''

QUOTE_JS = r'''
/* ==================== 共勉 + 点赞（就在作者名片中间） ====================
   规则（和歌词互斥，开关都挂在 lyricShow / lyricHide 上）：
     · 没在放歌 / 放不出歌词（占位旋律、纯音乐、试听片段）→ 显示一句共勉 + 点赞按钮
     · 歌词一出现 → 立刻收起共勉，让位给歌词；暂停时歌词停在那不动，共勉也不抢回来
     · 用户关掉音乐（lyricClear）→ 歌词收起，共勉回来
     · 切歌瞬间会先清歌词再挂新词，所以「显示共勉」延迟 350ms，避免中间闪一下
   每次只显示一句，不轮播；刷新页面随机换一句（不和上次重复，记在 localStorage）。
   点赞只加不减、可以连点：连点先在本地累加，攒成一批发给服务器，点完还有一把撒花。
   文案在 template.base.html 的 i18n（quotes / qLike / qLikeTip），中英各一份。
   ================================================== */
/* 注意：这几个必须是 var —— 函数声明会提升，let 不会。
   BGM_JS 里的初始化（lyricPaintIdle）比这段代码先执行，会回调 qBoxShowSoon，
   用 let 的话那时还在暂时性死区（TDZ），整个初始化会被 try/catch 静默吞掉，
   症状就是：歌词块永远不收起、共勉被挤成半宽。 */
var QN = null;                       /* 服务器上的赞数 */
var QPend = 0, QFlush = false, QHitT = null, QBoxT = null, QRetryT = false;
var QI = 0;

function qList(){ var a = t('quotes'); return (a && a.length) ? a : []; }
function qBoxEl(){ return document.getElementById('qbox'); }

/* 每次刷新随机挑一句：尽量不和上次那句重复 */
function qPick(){
  var list = qList(); if(!list.length) return 0;
  var last = -1;
  try{ last = parseInt(localStorage.getItem('pons-q-last'), 10); }catch(e){}
  var pool = [];
  for(var i = 0; i < list.length; i++){ if(i !== last) pool.push(i); }
  if(!pool.length) pool = [0];
  var pick = pool[(Math.random()*pool.length)|0];
  try{ localStorage.setItem('pons-q-last', String(pick)); }catch(e){}
  return pick;
}

function qRedraw(){ qPaint(); }          /* 切语言：同一句换成另一种语言，赞数不动 */
function qPaint(){
  var list = qList();
  var el = document.getElementById('qText');
  if(el) el.textContent = list[QI] || '';
  var n = document.getElementById('qN');
  if(n) n.textContent = fmtN((QN===null? 0 : QN) + QPend, 0);
  var btn = document.getElementById('qLike');
  if(btn){ btn.title = t('qLikeTip'); btn.setAttribute('aria-label', t('qLikeTip')); }
}

/* ---- 与歌词互斥：名片中间那块地方，同一时间只站一个人 ---- */
function qBoxHideNow(){
  if(QBoxT){ clearTimeout(QBoxT); QBoxT = null; }
  var r = qBoxEl(); if(!r) return;
  r.classList.remove('on');
  setTimeout(function(){ if(!r.classList.contains('on')) r.classList.add('hidden'); }, 420);
}
function qBoxShowNow(){
  var r = qBoxEl(); if(!r) return;
  r.classList.remove('hidden');
  requestAnimationFrame(function(){ r.classList.add('on'); });
  qPaint();
}
function qBoxShowSoon(){            /* 切歌瞬间会先清歌词 → 稍等一下再接回来 */
  if(QBoxT) clearTimeout(QBoxT);
  QBoxT = setTimeout(function(){ QBoxT = null; qBoxShowNow(); }, 350);
}

/* ---- 点赞：只加不减，连点攒批发 ---- */
function qLikeApply(n){ if(typeof n === 'number'){ QN = n; qPaint(); } }

var qCv = null, qCtx = null, qParts = [], qRAF = 0;
function qConfetti(btn){
  try{
    if(window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches) return;
    if(!btn) return;
    var r = btn.getBoundingClientRect();
    var W = 320, H = 260, dpr = Math.min(2, window.devicePixelRatio || 1);
    if(!qCv){
      qCv = document.createElement('canvas');
      qCv.className = 'q-confetti';
      document.body.appendChild(qCv);
    }
    qCv.width = Math.round(W*dpr); qCv.height = Math.round(H*dpr);
    qCv.style.width = W + 'px'; qCv.style.height = H + 'px';
    qCv.style.left = Math.round(r.left + r.width/2 - W/2) + 'px';
    qCv.style.top  = Math.round(r.top + r.height/2 - H/2 - 14) + 'px';
    qCv.style.display = 'block';
    qCtx = qCv.getContext('2d');
    qCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    qCtx.clearRect(0, 0, W, H);
    var COLORS = ['#ff6b8a','#8b7cff','#2ee6a8','#ffb020','#ff9aa8','#7ff0c6','#ffffff'];
    var cx = W/2, cy = H*0.66;
    for(var i = 0; i < 34; i++){
      var ang = (-90 + (Math.random()*160 - 80)) * Math.PI/180;   /* 往上开的扇形 */
      var sp  = 2.3 + Math.random()*4.4;
      qParts.push({
        x: cx + (Math.random()*22 - 11), y: cy + (Math.random()*12 - 6),
        vx: Math.cos(ang)*sp - 0.35, vy: Math.sin(ang)*sp - 1.6,   /* 略微往左偏：按钮偏右，别被屏幕边裁掉 */
        g: 0.12 + Math.random()*0.055,
        w: 3.2 + Math.random()*3.8, h: 5 + Math.random()*5.4,
        rot: Math.random()*Math.PI, vr: (Math.random() - 0.5)*0.36,
        c: COLORS[(Math.random()*COLORS.length)|0],
        life: 1, dec: 0.011 + Math.random()*0.009,
        round: Math.random() < 0.3
      });
    }
    if(!qRAF) qRAF = requestAnimationFrame(qTick);
  }catch(e){}
}
function qTick(){
  qRAF = 0;
  if(!qCtx || !qCv) return;
  qCtx.clearRect(0, 0, qCv.width, qCv.height);
  var alive = 0;
  for(var i = 0; i < qParts.length; i++){
    var p = qParts[i];
    p.vy += p.g; p.vx *= 0.994; p.x += p.vx; p.y += p.vy;
    p.rot += p.vr; p.life -= p.dec;
    if(p.life <= 0) continue;
    alive++;
    qCtx.save();
    qCtx.globalAlpha = Math.min(1, p.life*1.25);
    qCtx.translate(p.x, p.y);
    qCtx.rotate(p.rot);
    qCtx.fillStyle = p.c;
    if(p.round){ qCtx.beginPath(); qCtx.arc(0, 0, p.w/2, 0, Math.PI*2); qCtx.fill(); }
    else qCtx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
    qCtx.restore();
  }
  qParts = qParts.filter(function(p){ return p.life > 0; });
  if(alive > 0) qRAF = requestAnimationFrame(qTick);
  else { qParts = []; qCtx.clearRect(0, 0, qCv.width, qCv.height); qCv.style.display = 'none'; }
}

function qFlush(){
  if(QFlush || QPend <= 0) return;
  var n = Math.min(QPend, 20);
  QFlush = true;
  fetch('/api/likes?d=' + n + '&t=' + Date.now(), {cache:'no-store'})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      QPend = Math.max(0, QPend - n);                 /* 这一批已经落到服务器上 */
      if(d && typeof d.likes === 'number') QN = d.likes;
      qPaint();
    })
    .catch(function(){
      /* 服务器没接住（离线 / 接口挂了）：数字先不掉，过 6 秒再试一次，
         免得用户看到自己点的赞又缩回去 */
      QRetryT = true;
    })
    .then(function(){
      QFlush = false;
      if(QPend > 0){
        if(QRetryT){ QRetryT = false; setTimeout(qFlush, 6000); }
        else qFlush();
      }
    });
}

function qLike(){
  QPend++;                                            /* 乐观 +1：立刻上屏，连点也不卡 */
  var btn = document.getElementById('qLike');
  if(btn){
    btn.classList.remove('pop','plus','hit');
    void btn.offsetWidth;
    btn.classList.add('pop','plus','hit');
    qConfetti(btn);
    if(QHitT) clearTimeout(QHitT);
    QHitT = setTimeout(function(){ QHitT = null; btn.classList.remove('hit'); }, 900);
  }
  qPaint();
  qFlush();
}

function qLoadLikes(){
  if(location.protocol !== 'http:' && location.protocol !== 'https:') return;
  fetch('/api/likes?t=' + Date.now(), {cache:'no-store'})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){ if(d && typeof d.likes === 'number') qLikeApply(d.likes); })
    .catch(function(){});
}

function qInit(){
  QI = qPick();
  qBoxShowNow();
  qLoadLikes();
}
'''

BGM_JS = r'''
/* ==================== 行情 BGM ====================
   涨 →《逍遥仙》　跌 →《梦的翅膀受了伤》→《兄弟抱一下》→ 两首来回轮着放
   （以币价为主：涨了开心，跌了难受；跌幅这一档两首换着听，不腻）
   面板上的「两家平均涨跌」：单个币 = 近 7 天涨跌 × 0.65 + 近 24 小时涨跌 × 0.35
        两家再按市值加权（谁盘子大谁影响大，避免小盘插针带节奏）
   分档：≥ +3% 涨档 · ≤ −3% 跌档；回到 ±1.5% 以内才退出该档（滞回，防抖）
   横盘不上不下时：不切歌，继续放当前这首
   同一首至少播 90 秒才允许切；切换用 1.2 秒交叉淡入淡出
   浏览器禁止自动播放 → 默认关闭，点一下按钮＝用户授权，之后才会出声
   音源：优先 audio/up.mp3、audio/down.mp3（你自己上传的真歌）；
        文件不存在时自动回落到内置占位旋律（Web Audio 合成的原创乐句，不含任何版权素材）
   ================================================== */
/* 每个档位一组曲目：跌幅档两首轮换，第一首《梦的翅膀受了伤》，第二首《兄弟抱一下》 */
const BGM_TRACKS = {
  up:   [{ src:'audio/up.mp3',        lrc:'audio/up.lrc',        name:'bgmUpName'   }],
  down: [{ src:'audio/down-meng.mp3', lrc:'audio/down-meng.lrc', name:'bgmDownName2' },
         /* down-v2 = 跟《美好》专辑版 mp3 对齐的时间轴（旧的 down.lrc 是网易云「2021 版」，两版编曲不同、对不上） */
         { src:'audio/down.mp3',      lrc:'audio/down-v2.lrc',   name:'bgmDownName', lrcOffset:0 },
         /* 无人之岛：m4a（AAC）+ 官方时间轴 lrc；时间轴已用音频能量包络核对过
            （副歌「如果云层是天空的一封信」正好落在 01:12 的能量大跳点上），不需要 lrcOffset */
         { src:'audio/down-wuren.m4a', lrc:'audio/down-wuren.lrc', name:'bgmDownName3' }]
};
/* 歌词与音频同目录同名（.lrc）。新增歌曲：mp3 + lrc 一起放进 audio/，这里补一条。 */
const BGM_TH = 3.0, BGM_EXIT = 1.5, BGM_MIN_MS = 90000, BGM_FADE_MS = 1200;

let bgmOn=true, bgmBand=null, bgmCur=null, bgmCurIdx=0, bgmSince=0, bgmMoodCache=null;
const bgmEls={}, bgmMissing={};
const bgmRot={ up:0, down:0 };      /* 每档下一首该放第几首（轮换游标） */
/* 默认自动开；用户手动关过（静音）就再也不自动响 */
try{ if(localStorage.getItem('pons-bgm-muted')==='1') bgmOn=false; }catch(e){}
var bgmStartedOnce=false, bgmListenersOn=false, bgmSkipToggle=false;

function bgmBandTxt(b){ return b==='up'? t('bgmBandUp') : b==='down'? t('bgmBandDown') : t('bgmBandFlat'); }
function bgmTrack(band, idx){ var l=BGM_TRACKS[band]||[]; return l[idx]||l[0]||null; }
function bgmName(band, idx){
  if(band===null||band===undefined) return t('bgmName');
  var tr=bgmTrack(band, idx||0);
  return tr? t(tr.name) : (band==='up'? t('bgmUpName') : t('bgmDownName'));
}
function bgmTrackNo(band, idx){
  var n=(BGM_TRACKS[band]||[]).length;
  return n>1? t('bgmTrackNo')((idx||0)+1, n) : '';
}
function bgmPct(v){ return (v===null||v===undefined||!isFinite(v))? '—' : (v>=0?'+':'')+v.toFixed(1)+'%'; }

/* ---- 自动播放闸门 ----
   浏览器禁止「零交互出声」。策略：
     ① 加载时直接 play()：老访客 / 已互动过的域会被放行 → 完全自动，用户什么都看不到
     ② 被拦下（NotAllowedError）→ 挂一组一次性监听，用户第一次点/划/滚就把音乐淡入
     ③ 用户手动静音过 → 之后永不再自动响 */
const BGM_GESTURES = ['pointerdown','touchstart','touchend','mousedown','keydown','click','wheel','scroll'];
function bgmArmGesture(){
  if(bgmListenersOn) return;
  bgmListenersOn = true;
  BGM_GESTURES.forEach(function(ev){
    window.addEventListener(ev, bgmFirstGesture, {capture:true, passive:true});
  });
}
function bgmDisarmGesture(){
  if(!bgmListenersOn) return;
  bgmListenersOn = false;
  BGM_GESTURES.forEach(function(ev){
    window.removeEventListener(ev, bgmFirstGesture, {capture:true});
  });
}
function bgmFirstGesture(){
  if(bgmOffState()){ bgmDisarmGesture(); return; }
  if(bgmCur){ bgmDisarmGesture(); return; }
  bgmSkipToggle = true;
  setTimeout(function(){ bgmSkipToggle = false; }, 0);
  bgmKickstart();                      /* 必须同步调用，iOS 只认手势里的 play() */
}
function bgmOffState(){ return !bgmOn; }
function bgmKickstart(){
  if(!bgmOn || bgmCur) return;
  try{ if(bgmActx && bgmActx.state==='suspended') bgmActx.resume(); }catch(e){}
  Object.keys(BGM_TRACKS).forEach(function(b){
    BGM_TRACKS[b].forEach(function(_tr,i){ try{ bgmEl(b,i).load(); }catch(e){} });
  });
  bgmBand = null; bgmSince = 0;
  bgmSync();
  if(bgmOn && !bgmCur && bgmMoodCache) bgmSwitch(bgmMoodCache.score>=0? 'up' : 'down');
  bgmPaint();
}
function bgmOnPlayed(){
  bgmDisarmGesture();
  bgmKeepFresh();
  if(!bgmStartedOnce){ bgmStartedOnce = true; if(typeof toast==='function') toast(t('bgmTip')); }
}

function bgmEl(band, idx){
  var key = band + idx;
  if(bgmEls[key]) return bgmEls[key];
  var tr = bgmTrack(band, idx);
  var a = new Audio();
  a.loop = ((BGM_TRACKS[band]||[]).length < 2);   /* 只有一首就单曲循环；两首就放完换下一首 */
  a.preload = 'none'; a.volume = 0;
  a.src = tr.src;
  a.addEventListener('error', function(){
    bgmMissing[key] = true;
    if(bgmOn && bgmCur===band && bgmCurIdx===idx && bgmSynthOn!==band) bgmSynthStart(band);
    bgmPaint();
  });
  a.addEventListener('ended', function(){
    if(bgmOn && bgmCur===band && bgmCurIdx===idx) bgmNext();   /* 这首放完 → 同档下一首 */
  });
  a.addEventListener('timeupdate', function(){                 /* 歌词跟播放进度走 */
    if(bgmCur===band && bgmCurIdx===idx) lyricSeek(a.currentTime, a.duration);
  });
  bgmEls[key] = a; return a;
}

function bgmFade(a, to, ms, cb){
  if(!a) return;
  var token = (a.__fade = (a.__fade||0) + 1);
  var from = a.volume, t0 = Date.now();
  (function step(){
    if(a.__fade !== token) return;
    var k = Math.min(1, (Date.now()-t0)/ms);
    a.volume = Math.max(0, Math.min(1, from + (to-from)*k));
    if(k<1) requestAnimationFrame(step);
    else { if(to<=0.001){ try{ a.pause(); }catch(e){} } if(cb) cb(); }
  })();
}

/* ---- 内置占位旋律（原创，Web Audio 合成；不是任何现有歌曲）---- */
var bgmActx=null, bgmMaster=null, bgmLoopTimer=null, bgmSynthOn=null;
const BGM_SYNTH = {
  up:   { base:261.63, step:0.22, wave:'triangle', gain:0.085,
          seq:[0,4,7,12,7,16,12,7, 5,9,12,19,12,9,5,9, 0,4,7,12,16,19,16,12, 9,5,9,12,7,4,0,4] },
  down: { base:220.00, step:0.44, wave:'sine', gain:0.095,
          seq:[0,-2,-5,-2,-9,-5,-2,-5, 0,-2,-5,-2,-7,-5,-3,-5] }
};
function bgmSynthStart(key){
  if(bgmSynthOn===key) return;
  try{
    if(!bgmActx) bgmActx = new (window.AudioContext||window.webkitAudioContext)();
    if(bgmActx.state==='suspended') bgmActx.resume();
  }catch(e){ return; }
  bgmSynthStop(0);
  var m = bgmActx.createGain(); m.gain.value = 0; m.connect(bgmActx.destination);
  bgmMaster = m; bgmSynthOn = key;
  try{ m.gain.linearRampToValueAtTime(1, bgmActx.currentTime + 1.2); }catch(e){}
  bgmSynthLoop();
}
function bgmSynthLoop(){
  if(!bgmSynthOn || !bgmActx || !bgmMaster) return;
  var key = bgmSynthOn, c = BGM_SYNTH[key], ctx = bgmActx, tm = ctx.currentTime + 0.06;
  c.seq.forEach(function(n){
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = c.wave;
    o.frequency.value = c.base * Math.pow(2, n/12);
    g.gain.setValueAtTime(0.0001, tm);
    g.gain.linearRampToValueAtTime(c.gain, tm + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0006, tm + c.step*1.55);
    o.connect(g); g.connect(bgmMaster);
    o.start(tm); o.stop(tm + c.step*1.7);
    tm += c.step;
  });
  bgmLoopTimer = setTimeout(bgmSynthLoop, Math.max(400, c.seq.length*c.step*1000 - 260));
}
function bgmSynthStop(ms){
  if(bgmLoopTimer){ clearTimeout(bgmLoopTimer); bgmLoopTimer = null; }
  var m = bgmMaster; bgmMaster = null; bgmSynthOn = null;
  if(m && bgmActx){
    var fade = (ms===undefined)? 1200 : ms;
    try{
      var now = bgmActx.currentTime;
      m.gain.cancelScheduledValues(now);
      m.gain.setValueAtTime(m.gain.value, now);
      if(fade>0) m.gain.linearRampToValueAtTime(0, now + fade/1000);
      else m.gain.value = 0;
    }catch(e){}
    setTimeout(function(){ try{ m.disconnect(); }catch(e){} }, fade + 160);
  }
}

function bgmStopAll(){
  Object.keys(bgmEls).forEach(function(k){ bgmFade(bgmEls[k], 0, BGM_FADE_MS); });
  bgmSynthStop();
  bgmCur = null;
  lyricPaintIdle();
}

function bgmPlay(band, idx){
  var tr = bgmTrack(band, idx);
  if(!tr) return;
  var key = band + idx;
  Object.keys(bgmEls).forEach(function(k){ if(k!==key) bgmFade(bgmEls[k], 0, BGM_FADE_MS); });
  bgmSynthStop();
  bgmCur = band; bgmCurIdx = idx; bgmSince = Date.now();
  if(bgmMissing[key]){ lyricClear(); bgmSynthStart(band); bgmPaint(); return; }
  var a = bgmEl(band, idx);
  a.volume = 0;
  var pr = null;
  try{ pr = a.play(); }catch(e){}
  function go(){ a.volume = 0; bgmFade(a, 1, BGM_FADE_MS); bgmOnPlayed(); lyricOnTrack(band, idx); bgmPaint(); }
  function fail(err){
    var n = err && err.name;
    if(n === 'NotAllowedError' || n === 'AbortError'){    /* 被自动播放策略拦下：等第一次交互 */
      bgmCur = null; lyricPaintIdle(); bgmArmGesture(); bgmPaint(); return;
    }
    bgmMissing[key] = true; bgmSynthStart(band); bgmArmGesture(); bgmPaint();
  }
  if(pr && pr.then) pr.then(go).catch(fail); else go();
  bgmPaint();
}

/* 切到某一档：同一档正在放就不打断；进档时取轮换游标那首，取完游标后移 */
function bgmSwitch(band){
  if(bgmCur === band) return;
  var list = BGM_TRACKS[band] || [];
  if(!list.length) return;
  var idx = (bgmRot[band]||0) % list.length;
  bgmRot[band] = (idx + 1) % list.length;
  bgmPlay(band, idx);
}

/* 一首放完 → 同档下一首（跌幅档两首来回轮） */
function bgmNext(){
  if(!bgmCur) return;
  var list = BGM_TRACKS[bgmCur] || [];
  if(list.length < 2) return;
  var idx = (bgmRot[bgmCur]||0) % list.length;
  bgmRot[bgmCur] = (idx + 1) % list.length;
  bgmPlay(bgmCur, idx);
}

function bgmMood(){
  var rows = build(), sw = 0, sm = 0, parts = [];
  PROJECTS.forEach(function(p){
    var s = stats(rows, p);
    var m7  = (s.priceChg7!==null && isFinite(s.priceChg7))? s.priceChg7*100 : null;
    var m24 = (typeof s.volChange === 'number' && isFinite(s.volChange))? s.volChange : null;
    if(m7===null && m24===null) return;
    var mood = (m7!==null && m24!==null)? (m7*0.65 + m24*0.35) : (m7!==null? m7 : m24);
    var mc = (s.mcap && isFinite(s.mcap) && s.mcap>0)? s.mcap : 1;
    sw += mc; sm += mc*mood;
    parts.push({ p:p, m7:m7, m24:m24, mood:mood });
  });
  if(!sw || !parts.length) return null;
  return { score: sm/sw, parts: parts };
}

function bgmBandOf(score, prev){
  if(score >=  BGM_TH) return 'up';
  if(score <= -BGM_TH) return 'down';
  if(prev==='up'   && score >  BGM_EXIT) return 'up';
  if(prev==='down' && score < -BGM_EXIT) return 'down';
  return 'flat';
}

function bgmSync(){
  var m = bgmMood();
  bgmMoodCache = m;
  bgmBand = m? bgmBandOf(m.score, bgmBand) : null;
  if(bgmOn && m){
    var want = (bgmBand==='up')? 'up' : (bgmBand==='down'? 'down' : null);
    if(!want && !bgmCur) want = (m.score>=0? 'up' : 'down');
    var ready = (Date.now() - bgmSince) >= BGM_MIN_MS;
    if(want && want!==bgmCur && (ready || !bgmCur)) bgmSwitch(want);
  }
  bgmPaint();
}

function bgmPaint(){
  var root = document.getElementById('bgm'); if(!root) return;
  var m = bgmMoodCache, playing = bgmOn && bgmCur;
  root.classList.toggle('on', bgmOn);
  root.classList.toggle('live', !!playing);
  if(!bgmOn) root.classList.remove('det');
  root.classList.toggle('up', !!playing && bgmCur==='up');
  root.classList.toggle('down', !!playing && bgmCur==='down');
  var tEl = document.getElementById('bgmT'), sEl = document.getElementById('bgmS');
  if(tEl) tEl.textContent = bgmCur? bgmName(bgmCur, bgmCurIdx) : t('bgmName');
  if(sEl){
    if(!bgmOn) sEl.textContent = t('bgmOff');
    else if(!m) sEl.textContent = t('bgmNoData');
    else if(!bgmCur) sEl.textContent = t('bgmWait');
    else sEl.textContent = (m.score>=0?'+':'') + m.score.toFixed(1) + '% · ' + bgmBandTxt(bgmBand);
  }
  var card = document.getElementById('bgmCard');
  if(card) card.title = t('bgmName') + '　' + t('bgmRule');
  var leg = document.getElementById('bgmLegend'); if(leg) leg.textContent = t('bgmLegend');
  var sc = document.getElementById('bgmScore');
  if(sc){
    sc.innerHTML = m
      ? '<span class="bgm-labw"><span class="bgm-hl">'+t('bgmLab')+'</span>'
          + '<b class="'+(m.score>=0?'u':'d')+'">'+(m.score>=0?'+':'')+m.score.toFixed(2)+'%</b></span>'
        + '<span class="bgm-tag '+(bgmBand||'flat')+'">'+bgmBandTxt(bgmBand)+'</span>'
      : '<b>—</b><span class="bgm-tag">'+t('bgmNoData')+'</span>';
  }
  var pp = document.getElementById('bgmParts');
  if(pp){
    pp.innerHTML = !m? '' : m.parts.map(function(x){
      return '<div class="bgm-prow">'
        + '<span class="bgm-pn"><i style="background:'+x.p.color+'"></i>'+x.p.ticker+'</span>'
        + '<span class="bgm-pv '+(x.mood>=0?'u':'d')+'">'+bgmPct(x.mood)+'</span>'
        + '<span class="bgm-pd">'+t('bgmSev7')+' '+bgmPct(x.m7)+'　·　'+t('bgmSev24')+' '+bgmPct(x.m24)+'</span>'
        + '</div>';
    }).join('');
  }
  var src = document.getElementById('bgmSrc');
  if(src){
    var no = bgmCur? bgmTrackNo(bgmCur, bgmCurIdx) : '';
    if(bgmOn && bgmCur && bgmMissing[bgmCur+bgmCurIdx]) src.textContent = t('bgmPlaceholder');
    else if(bgmOn && bgmCur) src.textContent = (no? no+' · ' : '') + t('bgmReal') + ' · ' + t('bgmMin');
    else src.textContent = t('bgmRule');
  }
}

/* 详情面板：开启/换歌时自动展开，15 秒后收起；鼠标移上去或点小箭头再看 */
var bgmDetTimer = null;
function bgmDetShow(){
  var r = document.getElementById('bgm'); if(!r || !bgmOn) return;
  r.classList.add('det');
  if(bgmDetTimer) clearTimeout(bgmDetTimer);
  bgmDetTimer = setTimeout(function(){ bgmDetHide(); }, 15000);
}
function bgmDetHide(){
  if(bgmDetTimer){ clearTimeout(bgmDetTimer); bgmDetTimer = null; }
  var r = document.getElementById('bgm'); if(r) r.classList.remove('det');
}
function bgmDetToggle(){
  var r = document.getElementById('bgm'); if(!r || !bgmOn) return;
  if(r.classList.contains('det')) bgmDetHide(); else bgmDetShow();
}

function bgmToggle(){
  if(bgmSkipToggle){ bgmSkipToggle = false; bgmDetShow(); return; }   /* 刚被第一次交互自动点亮，这次点击不算静音 */
  bgmOn = !bgmOn;
  try{ localStorage.setItem('pons-bgm-muted', bgmOn?'0':'1'); }catch(e){}
  if(bgmOn){
    bgmCur = null;
    bgmKickstart();
    bgmKeepFresh();
  }else{
    bgmStopAll();
  }
  bgmPaint();
  if(bgmOn) bgmDetShow(); else bgmDetHide();
}

/* 开着 BGM 时，每 5 分钟顺手刷一次数据，让曲子跟着最新价格走 */
var bgmRefreshTimer = null;
function bgmKeepFresh(){
  if(bgmRefreshTimer) return;
  bgmRefreshTimer = setInterval(function(){ if(bgmOn) loadLive(); }, 300000);
}

/* ==================== 横幅歌词（跟着 BGM 走） ====================
   歌词文件与音频同目录（LRC）：audio/up.lrc · audio/down-meng.lrc · audio/down-v2.lrc
   当前行居中高亮、上下行渐隐，下面一条细进度条；窄屏铺满一整行
   · 只有「真的有歌词」时才显示；待命 / 加载中 / 纯音乐 / 试听片段 → 整块收起，不留空话
   · 音源明显短于歌词时间轴（试听片段）→ 自动收起，不硬套
   · 每条曲目可加 lrcOffset（秒）：正数＝歌词提前，负数＝歌词延后；用来微调个别版本
   ================================================================ */
const LY_LH = 18, LY_CACHE = {};
let lyLines = [], lyNodes = null, lyIdx = -1, lyTok = 0, lyReady = false, lyFit = false, lyHideTimer = null;

function lyTrackEl(){ return document.getElementById('lyTrack'); }
function lyRootEl(){ return document.getElementById('lyric'); }
function lyBarEl(){ return document.getElementById('lyBarI'); }

/* 当前曲目的时间轴微调（秒） */
function lyricOff(){
  var tr = (bgmCur!==null && bgmCur!==undefined)? bgmTrack(bgmCur, bgmCurIdx) : null;
  return (tr && isFinite(tr.lrcOffset))? Number(tr.lrcOffset) : 0;
}

/* LRC → [{t:秒, s:文本}]，过滤元数据行与空行 */
function lyricParse(raw){
  var out = [], re = /\[(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)\]/g;
  raw.split(/\r?\n/).forEach(function(line){
    var m, stamps = [], end = 0;
    re.lastIndex = 0;
    while((m = re.exec(line))){
      stamps.push(parseInt(m[1],10)*60 + parseFloat(String(m[2]).replace(':', '.')));
      end = re.lastIndex;
    }
    if(!stamps.length) return;
    var txt = line.slice(end).trim();
    if(!txt) return;
    if(/^(作词|作曲|编曲|制作人|配唱|出品人|出品|发行|混音室|混音|录音室|录音|和声编写|和声|缩混|母带|监制|统筹|企划|宣发|吉他|贝斯|鼓|键盘|弦乐|词|曲|OP|SP)\s*[:：]/.test(txt)) return;
    stamps.forEach(function(sec){ out.push({ t:sec, s:txt }); });
  });
  out.sort(function(a,b){ return a.t - b.t; });
  return out;
}

function lyricShow(){
  if(typeof qBoxHideNow === 'function') qBoxHideNow();   /* 歌词来了，共勉让位 */
  var r = lyRootEl(); if(!r) return;
  if(lyHideTimer){ clearTimeout(lyHideTimer); lyHideTimer = null; }
  r.classList.remove('hidden');
  requestAnimationFrame(function(){ r.classList.add('on'); });
}
function lyricHide(){
  if(typeof qBoxShowSoon === 'function') qBoxShowSoon(); /* 歌词走了，共勉延迟接回来 */
  var r = lyRootEl(); if(!r) return;
  r.classList.remove('on');
  if(lyHideTimer) clearTimeout(lyHideTimer);
  lyHideTimer = setTimeout(function(){                 /* 先淡出，再从排版里收掉 */
    lyHideTimer = null;
    if(!r.classList.contains('on')) r.classList.add('hidden');
  }, 620);
}
/* 没有歌词可显示时的唯一出口：清空 + 整块收起 */
function lyricClear(){
  lyReady = false; lyIdx = -1; lyLines = []; lyNodes = null; lyFit = false;
  var tr = lyTrackEl();
  if(tr){ tr.innerHTML = ''; tr.style.transform = 'translateY(0px)'; }
  var bi = lyBarEl(); if(bi) bi.style.width = '0%';
  lyricHide();
}
function lyricPaintIdle(){ lyricClear(); }

function lyricIdxAt(time){
  var i = -1;
  for(var k = 0; k < lyLines.length; k++){ if(time + 0.15 >= lyLines[k].t) i = k; else break; }
  return i;
}
function lyricShift(){
  var tr = lyTrackEl(); if(!tr) return;
  var di = lyIdx < 0 ? 0 : lyIdx;
  var c = ((tr.parentNode.clientHeight || 54) - LY_LH)/2;
  tr.style.transform = 'translateY(' + (c - di*LY_LH) + 'px)';
}
function lyricSetIdx(i){
  lyIdx = i;
  if(!lyNodes) return;
  for(var k = 0; k < lyNodes.length; k++){
    lyNodes[k].className = 'ly-line' + (k === i ? ' on' : (k < i ? ' past' : ''));
  }
  lyricShift();
}
function lyricMount(lines){
  var tr = lyTrackEl(); if(!tr) return;
  lyLines = lines; lyIdx = -1; lyReady = true; lyFit = false;
  tr.innerHTML = lines.map(function(l){ return '<div class="ly-line">' + esc(l.s) + '</div>'; }).join('');
  lyNodes = tr.children;
  /* 歌词是异步来的：到位时可能已经唱到中段了，第一下直接归位、不要从第一行滚过去 */
  var el = (bgmCur!==null && bgmCur!==undefined)? bgmEls[bgmCur + bgmCurIdx] : null;
  var now = ((el && isFinite(el.currentTime))? el.currentTime : 0) + lyricOff();
  tr.style.transition = 'none';
  lyricSetIdx(lyricIdxAt(now));
  requestAnimationFrame(function(){ requestAnimationFrame(function(){ tr.style.transition = ''; }); });
  lyricShow();
}
function lyricOnTrack(band, idx){
  var tr = bgmTrack(band, idx), url = tr && tr.lrc;
  if(!url){ lyricClear(); return; }
  var key = band + idx, tok = ++lyTok, hit = LY_CACHE[key];
  if(hit){ if(hit.length) lyricMount(hit); else lyricClear(); return; }
  lyricClear();                                        /* 取词之前先收起，等真有词再出现 */
  fetch(url, {cache:'force-cache'}).then(function(r){
    return r.ok ? r.text() : Promise.reject(new Error('lrc ' + r.status));
  }).then(function(txt){
    var lines = lyricParse(txt);
    LY_CACHE[key] = lines;
    if(tok !== lyTok || bgmCur !== band) return;       /* 已经切歌 / 已经停播 → 丢弃这次结果 */
    if(lines.length) lyricMount(lines); else lyricClear();
  }).catch(function(){
    if(tok !== lyTok || bgmCur !== band) return;
    LY_CACHE[key] = [];
    lyricClear();
  });
}
function lyricSeek(time, dur){
  if(!lyReady || !lyLines.length) return;
  var off = lyricOff(), lt = time + off;
  if(dur && isFinite(dur) && dur > 0 && !lyFit){
    lyFit = true;
    if(dur + 3 < lyLines[lyLines.length-1].t - off){   /* 试听片段：时间轴对不上，别硬套 */
      lyricClear(); return;
    }
  }
  var i = lyricIdxAt(lt);
  if(i !== lyIdx) lyricSetIdx(i);
  var bi = lyBarEl();
  if(bi) bi.style.width = (dur && isFinite(dur) && dur > 0 ? Math.min(100, Math.max(0, lt)/dur*100) : 0) + '%';
}
try{ lyricPaintIdle(); }catch(e){}

/* 展开的详情面板：点到别处 / 滑动页面 → 立刻收起（PC 与手机同一套行为）
   手机上面板里的按钮小，用户大概率会直接点屏幕其它地方来关，这里兜住这个直觉 */
(function(){
  function bgmAway(ev){
    var r = document.getElementById('bgm');
    if(!r || !r.classList.contains('det')) return;
    /* 注意：scroll/wheel 的事件目标是 window（不是 Node），直接 contains 会抛异常 */
    if(ev && ev.target && ev.target.nodeType && r.contains(ev.target)) return;   /* 点播放器自己不算 */
    bgmDetHide();
  }
  ['pointerdown','mousedown','touchstart','touchmove','wheel'].forEach(function(ev){
    window.addEventListener(ev, bgmAway, {capture:true, passive:true});
  });
  window.addEventListener('scroll', bgmAway, {passive:true});
})();

/* 每次渲染完（手动刷新 / 自动刷新 / 切语言）重算情绪并决定要不要换歌 */
(function(){
  var _renderAll = renderAll;
  renderAll = function(){
    _renderAll.apply(null, arguments);
    try{ bgmSync(); }catch(e){ console.error('bgm:', e); }
  };
})();
'''

# ============================================================
#  四、生成
# ============================================================
src = open(BASE, encoding="utf-8").read()

assert "</style>" in src and '<div class="wrap">\n' in src
assert "const FOOT_AUTHOR = /*__FOOT_AUTHOR__*/ {zh:'', en:''};" in src
assert "const BUNDLE = /*__DATA__*/;" in src

# 1) 换掉整段样式
st = src.index("<style>"); en = src.index("</style>") + len("</style>")
src = src[:st] + "<style>\n" + TOKENS + CSS_BODY + BGM_CSS + QUOTE_CSS + "</style>" + src[en:]

# 2) 防闪屏脚本
old_meta = '<meta name="viewport" content="width=device-width, initial-scale=1">'
assert old_meta in src
src = src.replace(old_meta, HEAD_INIT, 1)

# 3) 作者名片
src = src.replace('<div class="wrap">\n', '<div class="wrap">\n' + AUTHOR_HTML + TIP_MODAL, 1)

# 4b) 行情 BGM 悬浮播放器（固定在右下角，不占正文）
anchor_bgm = '  <div class="foot" id="foot"></div>\n</div>'
assert anchor_bgm in src, "找不到页脚锚点"
src = src.replace(anchor_bgm, '  <div class="foot" id="foot"></div>\n' + BGM_HTML + '</div>', 1)

# 4) 主题按钮
old_btn = '      <span class="badge" id="src">加载中…</span>\n'
assert old_btn in src
# 打赏按钮已移到作者名片里（跟在「关注」按钮旁边），不再放顶部工具条
src = src.replace(old_btn, old_btn + THEME_BTN + LANG_BTN, 1)

# 5) 页脚作者链接（中英双语，由前端按语言取用）
FOOT_OBJ = "const FOOT_AUTHOR = {zh:'" + FOOT_ZH + "', en:'" + FOOT_EN + "'};"
assert "const FOOT_AUTHOR = /*__FOOT_AUTHOR__*/ {zh:'', en:''};" in src
src = src.replace("const FOOT_AUTHOR = /*__FOOT_AUTHOR__*/ {zh:'', en:''};", FOOT_OBJ, 1)

# 6) 主题脚本（放到最后初始化之前）
anchor = "renderStatic();\nrenderAll();\nloadViews();\nloadLive();"
assert anchor in src
src = src.replace(anchor, THEME_JS + TIP_JS + BGM_JS + QUOTE_JS + "\nrenderTip();\nrenderStatic();\nrenderAll();\nloadViews();\nloadLive();\nqInit();", 1)

# 7) 把 JS 里写死的颜色换成主题变量
js_fix = [
    ("color:'#8b7cff'", "color:'var(--pons)', colorDim:'var(--pons-dim)'"),
    ("color:'#2ee6a8', supply", "color:'var(--stonk)', colorDim:'var(--stonk-dim)', supply"),
    ("thresholds=[{v:100,label:'基准 100',color:'#4b5468'}]",
     "thresholds=[{v:100,label:'基准 100',color:'var(--mut2)'}]"),
]
for a, b in js_fix:
    assert a in src, "找不到待替换片段: " + a
    src = src.replace(a, b)

open(TPL, "w", encoding="utf-8").write(src)
print("OK template.html 已重建：", len(src), "字符")
