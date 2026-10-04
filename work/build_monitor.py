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
    for slug in PAGES:
        for dt in DATATYPES:
            try:
                j = get(f"https://api.llama.fi/summary/fees/{slug}?dataType={dt}")
                bundle["series"][f"{slug}.{dt}"] = [
                    [int(ts), round(float(v), 2)] for ts, v in (j.get("totalDataChart") or [])
                ]
            except Exception as exc:
                errors.append(f"{slug}.{dt}: {exc}")
        try:
            m = get(f"https://api.llama.fi/protocol/{slug}")
            bundle["meta"][slug] = {"name": m.get("name"), "mcap": m.get("mcap"), "symbol": m.get("symbol")}
        except Exception as exc:
            errors.append(f"meta.{slug}: {exc}")
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
                bundle["leaderboard"] = old["leaderboard"]
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
