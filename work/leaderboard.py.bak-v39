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
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "dashboard-data.json")

API = ("https://api.llama.fi/overview/fees?dataType=dailyRevenue"
       "&excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")

# (看板内的 id, DefiLlama slug, 显示名)  —— Pons 主协议是 V2（V1 已停）
TARGETS = [("pons", "pons-v2", "Pons"), ("stonkfun", "stonkfun", "StonkFun")]
METRICS = [("total24h", "24h"), ("total7d", "7D"), ("total30d", "30D")]
NEAR = 4          # 上下各取几名
TOP_N = 10        # 榜首取几名


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def _row(p, rank, field, me=False):
    return {
        "r": rank,
        "n": (p.get("name") or "").strip(),
        "c": (p.get("category") or "").strip(),
        "v": round(float(p.get(field) or 0), 2),
        "me": me,
    }


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
    b = build_board(j.get("protocols") or [])
    b["updated"] = (j.get("updated") or
                    datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    b["source"] = "defillama.com/revenue"
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
    print(f"  体积 {len(json.dumps(board, ensure_ascii=False))} 字节")
    return 0


if __name__ == "__main__":
    sys.exit(main())
