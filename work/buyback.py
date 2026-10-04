#!/usr/bin/env python3
"""回购 / 销毁数据：链上真实烧毁量 + 24h 链上回购 + DefiLlama 回购强度 + 同行对照。

数据源（全部公开、无需 key）：
  1. PONS 死地址余额   → Robinhood Chain RPC  eth_call balanceOf(0x…dEaD) / totalSupply
  1b. PONS 近 24h 回购 → 同一 RPC eth_getLogs，筛 Transfer → 0x…dEaD（真·实时，不依赖 DefiLlama）
  2. STONK 累计销毁    → Solana RPC getTokenSupply（初始 10 亿 − 当前供应）
  2b. STONK 近 24h 销毁 → 本脚本自己攒的 burn-history.json 快照差值（攒满一天后自动生效）
  3. 回购强度 / 同行    → DefiLlama overview（dataType=dailyHoldersRevenue）的
                          total24h / total30d / totalAllTime

用法：python3 work/buyback.py            # 单独更新快照并打印
      from buyback import fetch_burn     # 供 build_monitor.py 调用
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "dashboard-data.json")
HIST = os.path.join(HERE, "burn-history.json")   # 每天一条快照，用来算「近 24h 销毁」

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


def rpc(url, payload, tries=4):
    """RPC 偶尔会抽风（连接被掐 / 超时），所以自带重试。"""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json",
                                                  "User-Agent": "curl/8", "Connection": "close"})
            out = json.load(urllib.request.urlopen(req, timeout=30))
            if "error" in out:
                raise RuntimeError(str(out["error"])[:200])
            return out
        except Exception as exc:
            last = exc
            time.sleep(1.0 + i)
    raise last


def get(url):
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8", "Connection": "close"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as exc:
            last = exc
            time.sleep(1.0 + i)
    raise last


def eth_call(to, data):
    out = rpc(RH_RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]})
    return int(out["result"], 16)


TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def block_ts(n):
    b = rpc(RH_RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber",
                     "params": [hex(n), False]})["result"]
    return int(b["timestamp"], 16)


def pons_burn_24h(hours=24):
    """近 24 小时打进死地址的 PONS —— 链上现读，一直算到最新区块，不等 DefiLlama。"""
    bn = int(rpc(RH_RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber",
                          "params": []})["result"], 16)
    ts_now = block_ts(bn)
    bps = 60000 / max(1, ts_now - block_ts(bn - 60000))      # 出块速度（块/秒）
    target = ts_now - hours * 3600
    est = bn - int((ts_now - target) * bps)
    for _ in range(4):
        delta = block_ts(max(0, est)) - target
        if abs(delta) <= 30:
            break
        est = max(0, int(est - delta * bps))
    from_block = max(0, est)
    logs = rpc(RH_RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{
        "fromBlock": hex(from_block), "toBlock": hex(bn), "address": PONS_TOKEN,
        "topics": [TRANSFER_TOPIC, None, "0x" + "0" * 24 + PONS_DEAD[2:]]}]})["result"]
    amount = sum(int(l.get("data") or "0x0", 16) for l in logs) / 1e18
    return {"amount": round(amount, 2), "count": len(logs), "from_block": from_block,
            "to_block": bn, "hours": round((ts_now - block_ts(from_block)) / 3600, 2), "ts": ts_now}


def load_hist():
    try:
        return json.load(open(HIST, encoding="utf-8"))
    except Exception:
        return []


def update_history(chain):
    """攒每日快照：STONK 只能靠供应量差值算「近 24h 销毁」，攒满一天就自动生效。"""
    hist = load_hist()
    now = time.time()
    cur = {"t": int(now),
           "pons": (chain.get("pons") or {}).get("burned"),
           "stonk": (chain.get("stonkfun") or {}).get("burned")}
    if cur["pons"] is not None or cur["stonk"] is not None:
        if not hist or now - hist[-1].get("t", 0) > 3600:
            hist.append(cur)
        else:
            hist[-1] = cur
        try:
            json.dump(hist[-400:], open(HIST, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception as exc:
            print("warn: hist write:", exc, file=sys.stderr)
    # 近 24h 销毁（快照差值）
    for key in ("stonk", "pons"):
        best, best_gap = None, 1e9
        for e in hist:
            age = (now - e.get("t", 0)) / 3600
            if 18 <= age <= 30 and e.get(key) is not None and cur.get(key) is not None:
                gap = abs(age - 24)
                if gap < best_gap:
                    best, best_gap = e, gap
        if best:
            d = cur[key] - best[key]
            node = chain.get("stonkfun" if key == "stonk" else "pons")
            if node is not None and d >= 0:
                node["burn24h"] = round(d, 2)
                node["burn24hSrc"] = "snapshot"
                node["burn24hHours"] = round((now - best["t"]) / 3600, 2)
    return chain


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
        try:
            b24 = pons_burn_24h()
            chain["pons"].update({
                "burn24h": b24["amount"], "burn24hSrc": "chain", "burn24hTxs": b24["count"],
                "burn24hHours": b24["hours"], "burn24hBlock": b24["to_block"], "burn24hTs": b24["ts"],
            })
        except Exception as exc:
            print("warn: pons 24h logs:", exc, file=sys.stderr)
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
    """回购强度：DefiLlama 的 holders revenue（24h / 30d / 累计），两个口径都算名次。

    榜单保留「24h 前列」∪「30d 前列」∪ 我们自己 —— 前端按所选口径排序，
    这样切到任一口径，前几名都是完整的、每行的名次也都是真的（共 1000+ 个协议里的真实排名）。
    """
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
    total = len(rows)
    mine = {"pons-v1", "stonkfun"}
    by24 = sorted(rows, key=lambda r: -r["h24"])
    by30 = sorted(rows, key=lambda r: -r["d30"])
    r24 = {r["slug"]: i + 1 for i, r in enumerate(by24)}
    r30 = {r["slug"]: i + 1 for i, r in enumerate(by30)}
    keep = set(mine)
    keep |= {r["slug"] for r in by24[:PEER_TOP + 1]}
    keep |= {r["slug"] for r in by30[:PEER_TOP + 1]}
    out = [dict(r, r24=r24[r["slug"]], r30=r30[r["slug"]], me=r["slug"] in mine)
           for r in rows if r["slug"] in keep]
    out.sort(key=lambda r: r["r24"])
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
        chain = update_history(chain)
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
