#!/usr/bin/env python3
"""回购 / 销毁数据：链上真实烧毁量 + DefiLlama 回购强度 + 同行对照。

数据源（全部公开、无需 key）：
  1. PONS 死地址余额   → Robinhood Chain RPC  eth_call balanceOf(0x…dEaD) / totalSupply
  2. STONK 累计销毁    → Solana RPC getTokenSupply（初始 10 亿 − 当前供应）
  3. 回购强度 / 同行    → DefiLlama overview（dataType=dailyHoldersRevenue）的
                          total24h / total30d / totalAllTime

用法：python3 work/buyback.py            # 单独更新快照并打印
      from buyback import fetch_burn     # 供 build_monitor.py 调用
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "dashboard-data.json")

RH_RPC = "https://rpc.mainnet.chain.robinhood.com"
SOL_RPCS = ["https://api.mainnet-beta.solana.com", "https://solana-rpc.publicnode.com"]
OVERVIEW = ("https://api.llama.fi/overview/fees?dataType=dailyHoldersRevenue"
            "&excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")

PONS_TOKEN = "0x39dBED3a2bd333467115dE45665cC57F813C4571"
PONS_DEAD = "0x000000000000000000000000000000000000dEaD"
STONK_MINT = "6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx"
STONK_INITIAL = 1_000_000_000.0

# 同行对比口径：CoinGecko 的市值 / 24h 成交额（pump.fun 用来跟我们对同一把尺子）
CG_URL = ("https://api.coingecko.com/api/v3/simple/price?ids=pump-fun,pons,stonk-3"
          "&vs_currencies=usd&include_24hr_vol=true&include_market_cap=true")
CG_MAP = {"pons": "pons", "stonkfun": "stonk-3", "pumpfun": "pump-fun"}

# 同行对照：链名 / 口径修正（DefiLlama slug → 展示名）
PEER_CHAINS = {
    "hyperliquid-perps": "Hyperliquid", "pump.fun": "Solana", "uniswap-v3": "Ethereum + L2s",
    "aerodrome-slipstream": "Base", "sky-lending": "Ethereum", "raydium-amm": "Solana",
    "bonk.fun-launchpad": "Solana", "lighter-perps": "Lighter L2", "jupiter-aggregator": "Solana",
}
# 剔除：公链的「销毁」= 烧 gas，不是回购，混进来会误导
PEER_SKIP_CATEGORY = {"Chain"}
PEER_TOP = 7                 # 榜首保留前几名（不含我们自己）


def rpc(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "curl/8"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def eth_call(to, data):
    out = rpc(RH_RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]})
    return int(out["result"], 16)


def fetch_chain():
    """链上真实烧毁量（两个代币各自的原始依据）。"""
    chain = {}
    try:
        dead = eth_call(PONS_TOKEN, "0x70a08231" + "0" * 24 + PONS_DEAD[2:])
        total = eth_call(PONS_TOKEN, "0x18160ddd")
        chain["pons"] = {
            "burned": round(dead / 1e18, 2), "supply": round(total / 1e18, 2),
            "pct": round(dead / total * 100, 2), "addr": PONS_DEAD,
            "explorer": "https://robinhoodchain.blockscout.com/token/" + PONS_TOKEN,
            "src": "Robinhood Chain RPC · 死地址余额",
        }
    except Exception as exc:
        print("warn: pons chain:", exc, file=sys.stderr)
    last = None
    for _ in range(3):
        for url in SOL_RPCS:
            try:
                out = rpc(url, {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply",
                                "params": [STONK_MINT]})["result"]["value"]
                supply = float(out["uiAmountString"])
                burned = STONK_INITIAL - supply
                chain["stonkfun"] = {
                    "burned": round(burned, 2), "supply": STONK_INITIAL,
                    "pct": round(burned / STONK_INITIAL * 100, 2), "addr": STONK_MINT,
                    "explorer": "https://solscan.io/token/" + STONK_MINT,
                    "src": "Solana RPC · 初始 10 亿 − 当前供应",
                }
                last = None
                break
            except Exception as exc:
                last = exc
        if not last:
            break
    if last:
        print("warn: stonk chain:", last, file=sys.stderr)
    return chain


def fetch_peers(protocols):
    """回购强度：DefiLlama 的 holders revenue（24h / 30d / 累计）。"""
    rows = []
    for p in protocols:
        slug = (p.get("slug") or "").strip()
        if not slug or (p.get("category") or "").strip() in PEER_SKIP_CATEGORY:
            continue
        rows.append({
            "slug": slug, "n": (p.get("displayName") or p.get("name") or slug).strip(),
            "c": PEER_CHAINS.get(slug, (p.get("category") or "").strip()),
            "h24": round(float(p.get("total24h") or 0), 2),
            "d30": round(float(p.get("total30d") or 0), 2),
            "all": round(float(p.get("totalAllTime") or 0), 2),
        })
    rows.sort(key=lambda r: -r["d30"])
    total = len(rows)
    mine = {"pons-v1", "stonkfun"}
    out, seen = [], set()
    for i, r in enumerate(rows):
        is_me = r["slug"] in mine
        if not is_me and (len([x for x in out if not x["me"]]) >= PEER_TOP):
            continue
        if r["slug"] in seen:
            continue
        seen.add(r["slug"])
        out.append(dict(r, r30=i + 1, me=is_me))
    out.sort(key=lambda r: r["r30"])
    return {"rows": out, "total": total}


def fetch_market():
    """同行对比要用的市值/成交额，外加 pump.fun 的 7 日 / 30 日回购额（同口径比）。"""
    out = {}
    try:
        j = get(CG_URL)
        for key, cid in CG_MAP.items():
            x = j.get(cid) or {}
            out[key] = {"mcap": round(float(x.get("usd_market_cap") or 0), 2),
                        "vol24h": round(float(x.get("usd_24h_vol") or 0), 2),
                        "price": x.get("usd")}
    except Exception as exc:
        print("warn: market:", exc, file=sys.stderr)
    try:
        s = get("https://api.llama.fi/summary/fees/pump.fun?dataType=dailyHoldersRevenue")
        ch = [[int(ts), float(v)] for ts, v in (s.get("totalDataChart") or [])]
        if ch:
            out.setdefault("pumpfun", {})
            out["pumpfun"]["s7"] = round(sum(v for _, v in ch[-7:]), 2)
            out["pumpfun"]["s30"] = round(sum(v for _, v in ch[-30:]), 2)
    except Exception as exc:
        print("warn: pumpfun series:", exc, file=sys.stderr)
    return out


def fetch_burn(old=None):
    burn = {}
    try:
        protocols = (get(OVERVIEW) or {}).get("protocols") or []
    except Exception as exc:
        print("warn: overview:", exc, file=sys.stderr)
        protocols = []
    if protocols:
        burn["peers"] = fetch_peers(protocols)
    chain = fetch_chain()
    if chain:
        burn["chain"] = chain
    market = fetch_market()
    if market:
        burn["market"] = market
    if old:
        burn.setdefault("peers", old.get("peers"))
        burn.setdefault("market", old.get("market"))
        old_chain = old.get("chain") or {}
        chain = burn.get("chain") or {}
        for k in ("pons", "stonkfun"):
            if k not in chain and k in old_chain:
                chain[k] = old_chain[k]
        if chain:
            burn["chain"] = chain
    return burn


def main():
    try:
        old = json.load(open(DATA, encoding="utf-8"))
    except Exception:
        old = {}
    burn = fetch_burn(old.get("burn"))
    old["burn"] = burn
    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump(old, fh, ensure_ascii=False)
    print(json.dumps(burn, ensure_ascii=False, indent=1)[:2000])


if __name__ == "__main__":
    main()
