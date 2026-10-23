#!/usr/bin/env python3
"""抓 DefiLlama 收入总榜，裁成看板要用的那一小块。

原始榜单 ~4.2MB / 2455 个协议，全塞进页面太重。
这里只保留：每个口径（24h / 7日 / 30日）的
  · 榜首前 10（天花板参照）
  · 两个目标协议的上下各 4 名（同侪对照）
  · 目标协议在该口径下的名次
裁完约 13KB，直接并进 dashboard-data.json。

用法：python3 work/leaderboard.py          # 只更新快照里的排行部分
      from leaderboard import fetch_board  # 供 build_monitor.py 调用
"""
import datetime
import gzip
import json
import os
import sys
import time
import urllib.request

from stonk_page import sf_daily_all, sf_revenue_usd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "dashboard-data.json")

API = ("https://api.llama.fi/overview/fees?dataType=dailyRevenue"
       "&excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
# 单协议接口：总榜偶发把某协议 24h 记成 0 时，用它兜底（见 patch_zero_targets）
SUMMARY = "https://api.llama.fi/summary/fees/{slug}?dataType=dailyRevenue"

# (看板内的 id, DefiLlama slug, 显示名)  —— Pons 主协议是 V2（V1 已停）
TARGETS = [("pons", "pons-v2", "Pons"), ("stonkfun", "stonkfun", "StonkFun")]
METRICS = [("total24h", "24h"), ("total7d", "7D"), ("total30d", "30D")]
NEAR = 4          # 上下各取几名
TOP_N = 10        # 榜首取几名


def get(url, tries=3):
    """带重试 + gzip。

    背景（2026-10-05 实测定性）：这个总榜接口原始包 4.2MB，偶发被中途掐断，
    报 IncompleteRead(4267266 bytes read)；而这里以前**没有重试**，
    一失败就静默退回上一份旧快照 —— 结果榜单连续两天没更新，
    页面上却只显示一个「排行数据时间」，看起来像数据源坏了。
    现在：最多试 3 次，每次都带 gzip（体积更小、更不容易被掐），
    仍然失败才由调用方标 stale，让页面把「这份榜单是旧的」明说出来。
    """
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "curl/8",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "Connection": "close",
            })
            r = urllib.request.urlopen(req, timeout=60)
            raw = r.read()
            if (r.headers.get("Content-Encoding") or "").lower() == "gzip":
                raw = gzip.decompress(raw)
            return json.loads(raw)
        except Exception as exc:
            last = exc
            if i < tries - 1:
                time.sleep(1.5 + i)
    raise last


def _row(p, rank, field, me=False):
    return {
        "r": rank,
        "n": (p.get("name") or "").strip(),
        "c": (p.get("category") or "").strip(),
        "v": round(float(p.get(field) or 0), 2),
        "me": me,
    }


def patch_zero_targets(protocols):
    """总榜偶发把某协议的 24h（或 7d/30d）记成 0 —— 单协议接口却是对的。

    实例（2026-10-14 09:08 北京）：总榜 stonkfun.total24h = 0 → 页面上
    StonkFun 显示「24 小时 #2388 $0、下滑 2381 位」，而它自己的单协议接口
    同一时刻是 $219,831。原因是上游按「领取时点」记账，当日行还没落库时
    24h 就是 0。这里对两个目标协议做兜底：
      ① 总榜值为 0 → 读单协议接口的 total24h/total7d/total30d；
      ② 单协议接口也是 0 → 退到它日线里**最后一个非零值**（至少同量级、不骗人）；
    补完的值直接写回 protocols，排序/名次跟着一起修正。
    """
    by_slug = {p.get("slug"): p for p in protocols}
    fixed = {}
    for tid, slug, _nm in TARGETS:
        p = by_slug.get(slug)
        if not p:
            continue
        need = [f for f, _label in METRICS if not (p.get(f) or 0)]
        if not need:
            continue
        try:
            s = get(SUMMARY.format(slug=slug)) or {}
        except Exception:
            s = {}
        for f in need:
            v = s.get(f) or 0
            src = "summary"
            if v <= 0:
                for _ts, val in reversed(s.get("totalDataChart") or []):
                    if val and val > 0:
                        v, src = val, "chart"
                        break
            if v > 0:
                p[f] = v
                fixed.setdefault(tid, {})[f] = {"v": round(v, 2), "src": src}
    return fixed


def patch_stonk_official_revenue(protocols, days=None):
    """用官网完整日线总收入覆盖 STONK 排行指标（含 $STONK quote revenue）。

    24h 使用最近一个完整 UTC 日，7D/30D 分别汇总最近 7/30 个完整日；
    这些窗口与看板其余协议的收入排行保持日线口径，避免浏览器/快照各算一套。
    """
    if days is None:
        try:
            days = sf_daily_all() or []
        except Exception as exc:
            print("warn: stonk official leaderboard data: %s" % exc, file=sys.stderr)
            days = []
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for row in days:
        if not isinstance(row, dict):
            continue
        day = (row.get("date") or "")[:10]
        if day and day < today:
            rows.append((day, sf_revenue_usd(row)))
    rows.sort(key=lambda x: x[0])
    by_slug = {p.get("slug"): p for p in protocols}
    target = by_slug.get("stonkfun")
    if not target:
        return {}
    aligned = {}
    for field, n in (("total24h", 1), ("total7d", 7), ("total30d", 30)):
        window = rows[-n:]
        if len(window) < n:
            continue
        value = round(sum(v for _day, v in window), 2)
        target[field] = value
        aligned[field] = {
            "v": value, "from": window[0][0], "to": window[-1][0],
            "source": "stonkfun.xyz official total revenue",
        }
    return aligned


def build_board(protocols):
    """把原始协议数组裁成看板要用的结构。前端刷新排行时用的是同一套逻辑。"""
    total = len(protocols)
    board, ranks = {}, {}
    for field, _label in METRICS:
        arr = sorted(protocols, key=lambda p: -(p.get(field) or 0))
        index = {p.get("slug"): i + 1 for i, p in enumerate(arr)}
        board[field] = {"top": [], "near": {}}
        top_slugs = {slug for _tid, slug, _nm in TARGETS}
        for i, p in enumerate(arr[:TOP_N]):
            board[field]["top"].append(_row(p, i + 1, field, p.get("slug") in top_slugs))
        for tid, slug, _nm in TARGETS:
            r = index.get(slug)
            if not r:
                board[field]["near"][tid] = []
                continue
            i = r - 1
            if r <= TOP_N:
                # 已经站在榜首榜里 → 只列身后的追兵，免得和上面的 Top10 重复
                lo, hi = i, min(total, i + NEAR * 2 + 1)
            else:
                lo, hi = max(0, i - NEAR), min(total, i + NEAR + 1)
            board[field]["near"][tid] = [
                _row(arr[j], j + 1, field, (j + 1) == r) for j in range(lo, hi)
            ]
        ranks[field] = {}
    for tid, slug, _nm in TARGETS:
        for field, _label in METRICS:
            arr = sorted(protocols, key=lambda p: -(p.get(field) or 0))
            idx = {p.get("slug"): i + 1 for i, p in enumerate(arr)}.get(slug)
            board[field].setdefault("rank", {})[tid] = idx
    return {"total": total, "board": board}


def fetch_board():
    j = get(API)
    protocols = j.get("protocols") or []
    fixed = patch_zero_targets(protocols)
    stonk_official = patch_stonk_official_revenue(protocols)
    b = build_board(protocols)
    if fixed:
        b["fixed"] = fixed
    if stonk_official:
        b["stonkOfficial"] = stonk_official
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # updated   = 上游自己给的时间（没有就用我们的抓取时间）
    # fetchedAt = 我们这次真正抓到的时刻，页面据此判断"这份榜单是不是旧的"
    b["updated"] = j.get("updated") or now
    b["fetchedAt"] = now
    b["stale"] = False
    b["source"] = "defillama.com/revenue + stonkfun.xyz/revenue"
    return b


def main():
    board = fetch_board()
    with open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    data["leaderboard"] = board
    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    n = board["total"]
    print(f"ok  协议总数 {n}")
    for tid, slug, nm in TARGETS:
        r24 = board["board"]["total24h"]["rank"].get(tid)
        r7 = board["board"]["total7d"]["rank"].get(tid)
        r30 = board["board"]["total30d"]["rank"].get(tid)
        print(f"  {nm:9s} 24h #{r24}  7日 #{r7}  30日 #{r30}")
    for tid, fields in (board.get("fixed") or {}).items():
        for f, info in fields.items():
            print(f"  [兜底] {tid}.{f} 总榜为 0，已用单协议接口补：{info['v']}（{info['src']}）")
    print(f"  体积 {len(json.dumps(board, ensure_ascii=False))} 字节")
    return 0


if __name__ == "__main__":
    sys.exit(main())
