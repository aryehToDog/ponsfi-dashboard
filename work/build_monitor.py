#!/usr/bin/env python3
"""抓取 DefiLlama 数据并重新生成 Pons / StonkFun 监控面板。

用法: python3 work/build_monitor.py
输出: work/dashboard-data.json + outputs/pons-stonkfun-monitor.html
抓取失败会保留旧快照并以非 0 退出。
"""
import datetime
import json
import os
import runpy
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_HTML = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
OUT_JSON = os.path.join(HERE, "dashboard-data.json")
TEMPLATE = os.path.join(HERE, "template.html")

PAGES = ["pons", "stonkfun"]
DATATYPES = ["dailyRevenue", "dailyHoldersRevenue", "dailyFees"]
PRICE_KEYS = {
    "pons": "robinhood:0x39dBED3a2bd333467115dE45665cC57F813C4571",
    "stonkfun": "solana:6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx",
}

# CoinGecko id（用于成交额 / 换手率）
CG_IDS = {"pons": "pons", "stonkfun": "stonk-3"}


def get(url):
    last_error = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as exc:
            last_error = exc
    raise last_error


# ---- 上游「当天还没结算完」体检（v3.29.21） -----------------------------------
# 背景：2026-10-15 作者发现「每日明细」里 PONS 10-14 只有 $3.9K（-96%），怀疑坏了。
# 排查：DefiLlama 的 Pons 是父协议，下面是 Pons V1 / Pons V2 两个子模块；10-14 当天
#       V2 还没入库，totalDataChart 只有 V1 的零头（24K 费 / 3.9K 收入），父协议看着
#       就像「暴跌 96%」。半截数不能当整日数用，否则表格、均值、结论全被带歪。
# 做法：用 totalDataChartBreakdown（每天各子模块出了多少）做体检 ——
#       最近 2 天里，若某天缺了前 7 天中贡献 ≥20% 的子模块，就把这天标成「未结算完」
#       （seriesPending）。前端拿到这些日期后宁可写「待更新」，也不用半截数；
#       小时模式（ci_build.py）发现标记就地重取，上游补全后自动恢复。
def day_of(ts):
    return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")


def breakdown_by_day(j):
    """totalDataChartBreakdown → {YYYY-MM-DD: {child: value}}（多链时合并子模块口径）。"""
    out = {}
    for row in (j.get("totalDataChartBreakdown") or []):
        try:
            ts, mp = int(row[0]), (row[1] or {})
        except Exception:
            continue
        bag = out.setdefault(day_of(ts), {})
        for kids in mp.values():
            if not isinstance(kids, dict):
                continue
            for k, v in kids.items():
                try:
                    v = float(v)
                except Exception:
                    continue
                bag[k] = bag.get(k, 0.0) + v
    return out


def pending_days(j, recent=2, lookback=7, min_share=0.2):
    """还没结算完的天（见上）。返回 ['YYYY-MM-DD', ...]，正常情况是空列表。"""
    bd = breakdown_by_day(j)
    if len(bd) < 3:
        return []
    days = sorted(bd)
    out = []
    for d in days[-recent:]:
        kids = {k for k, v in bd[d].items() if v}
        if not kids:
            continue
        prev = [x for x in days if x < d][-lookback:]
        if not prev:
            continue
        total = {}
        for x in prev:
            for k, v in bd[x].items():
                total[k] = total.get(k, 0.0) + v
        allv = sum(total.values())
        missv = sum(v for k, v in total.items() if k not in kids)
        if allv > 0 and missv / allv >= min_share:
            out.append(d)
    return out


def series_of(j):
    return [[int(ts), round(float(v), 2)] for ts, v in (j.get("totalDataChart") or [])]


def fetch_bundle():
    bundle = {
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "series": {},
        "meta": {},
        "priceSeries": {},
        "price": {},
        "market": {},
    }
    errors = []
    pending = {}
    for slug in PAGES:
        for dt in DATATYPES:
            try:
                j = get(f"https://api.llama.fi/summary/fees/{slug}?dataType={dt}")
                key = f"{slug}.{dt}"
                bundle["series"][key] = series_of(j)
                pd = pending_days(j)
                if pd:
                    pending[key] = pd
                    print("warn: %s 最近 %s 还没结算完（缺子模块）→ 前端先不给半截数" %
                          (key, ",".join(pd)), file=sys.stderr)
            except Exception as exc:
                errors.append(f"{slug}.{dt}: {exc}")
        try:
            m = get(f"https://api.llama.fi/protocol/{slug}")
            bundle["meta"][slug] = {"name": m.get("name"), "mcap": m.get("mcap"), "symbol": m.get("symbol")}
        except Exception as exc:
            errors.append(f"meta.{slug}: {exc}")
    bundle["seriesPending"] = pending
    try:
        j = get("https://coins.llama.fi/chart/" + ",".join(PRICE_KEYS.values()) + "?span=90&period=1d")
        coins = j.get("coins", {})
        for name, key in PRICE_KEYS.items():
            prices = (coins.get(key) or {}).get("prices") or []
            bundle["priceSeries"][name] = [
                [int(x["timestamp"]), round(float(x["price"]), 8)] for x in prices
            ]
    except Exception as exc:
        errors.append(f"priceSeries: {exc}")
    try:
        url = ("https://api.coingecko.com/api/v3/simple/price?ids=" + ",".join(CG_IDS.values())
               + "&vs_currencies=usd&include_24hr_vol=true&include_market_cap=true&include_24hr_change=true")
        cg = get(url)
        for name, cid in CG_IDS.items():
            x = cg.get(cid) or {}
            bundle["market"][name] = {
                "vol24h": round(x.get("usd_24h_vol") or 0, 2),
                "mcap": round(x.get("usd_market_cap") or 0, 2),
                "price": x.get("usd"),
                "change24h": round(x.get("usd_24h_change") or 0, 2),
            }
    except Exception as exc:
        errors.append(f"market: {exc}")
    try:
        p = get("https://coins.llama.fi/prices/current/" + ",".join(PRICE_KEYS.values()))
        for name, key in PRICE_KEYS.items():
            bundle["price"][name] = p["coins"][key]["price"]
    except Exception as exc:
        errors.append(f"price: {exc}")
    # 全站收入排行榜（裁过的小快照，见 leaderboard.py）
    try:
        from leaderboard import fetch_board
        bundle["leaderboard"] = fetch_board()
    except Exception as exc:
        errors.append(f"leaderboard: {exc}")
    if not bundle.get("leaderboard"):
        try:
            old = json.load(open(OUT_JSON, encoding="utf-8"))
            if old.get("leaderboard"):
                # 退回旧榜时必须打标记：页面要能说出"这份榜单是旧的、抓取失败了"，
                # 而不是让用户看到一个不明所以的时间戳（2026-10-05 修的坑）
                lb = dict(old["leaderboard"])
                lb["stale"] = True
                lb["staleReason"] = "fetch-failed"
                bundle["leaderboard"] = lb
        except Exception:
            pass
    # 回购 / 销毁：链上真实烧毁量 + 全行业回购强度（见 buyback.py）
    try:
        from buyback import fetch_burn
        old_burn = (json.load(open(OUT_JSON, encoding="utf-8")) or {}).get("burn")
    except Exception:
        fetch_burn = None
        old_burn = None
    if fetch_burn:
        try:
            bundle["burn"] = fetch_burn(old_burn)
        except Exception as exc:
            errors.append(f"buyback: {exc}")
    if not bundle.get("burn") and old_burn:
        bundle["burn"] = old_burn
    # 小时级监控（最近 72 小时：交易量 / 收入推算 / 链上销毁，见 hourly.py）
    try:
        runpy.run_path(os.path.join(HERE, "hourly.py"), run_name="__main__")
        bundle["hourly"] = json.load(open(os.path.join(HERE, "hourly.json"), encoding="utf-8"))
    except Exception as exc:
        errors.append(f"hourly: {exc}")
        try:
            bundle["hourly"] = json.load(open(os.path.join(HERE, "hourly.json"), encoding="utf-8"))
        except Exception:
            pass
    return bundle, errors


def write_panel(bundle):
    """渲染这一步统一交给 render_only.py —— 它会注入版本标签与备份说明，别再自己拼一份。"""
    subprocess.run([sys.executable, os.path.join(HERE, "render_only.py")], check=True)


def main():
    bundle, errors = fetch_bundle()
    for err in errors:
        print("warn:", err, file=sys.stderr)
    if not bundle["series"]:
        print("抓取全部失败，保留旧面板不动", file=sys.stderr)
        return 1
    if not bundle["market"]:
        try:
            old = json.load(open(OUT_JSON, encoding="utf-8"))
            bundle["market"] = old.get("market") or {}
        except Exception:
            pass
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, ensure_ascii=False)
    write_panel(bundle)
    print("ok", bundle["generated"], {k: len(v) for k, v in bundle["series"].items()},
          "price", bundle["price"], "errors", len(errors))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
