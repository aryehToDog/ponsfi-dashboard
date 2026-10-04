#!/usr/bin/env python3
"""小时级监控数据（最近 72 小时）→ work/hourly.json

数据源（全部公开、无需 key）：
  1. 交易量（每小时）→ GeckoTerminal OHLCV hour（真小时线，允许跨域，浏览器也能直连）
       PONS  → robinhood / 0xed50bdee… (PONS/WETH)
       STONK → solana    / zxTpi4Bt…   (STONK/SOL)
  2. 销毁（每小时）→ Robinhood Chain eth_getLogs 筛 Transfer→0x…dEaD，按小时分桶（真链上）
       STONK → StonkFun 官方接口的累计销毁量每小时差值（真值）；拿不到时退回 burn-history 快照累积
  3. 收入（每小时）→ Pons 给一列「链上推算」＝ 小时回购支出 ÷ 80%（回购占比），明确标注为推算；
       StonkFun → 官方接口 stonkfun.xyz/api/revenue 的累计收入每小时差值（真值，国内直连被墙、走海外中转）
"""
import json, os, sys, time, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hourly.json")
HIST = os.path.join(HERE, "burn-history.json")
RH_RPC = "https://rpc.mainnet.chain.robinhood.com"
PONS_TOKEN = "0x39dBED3a2bd333467115dE45665cC57F813C4571"
PONS_DEAD = "0x000000000000000000000000000000000000dEaD"
TR = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
GECKO = "https://api.geckoterminal.com/api/v2/networks/%s/pools/%s/ohlcv/hour?limit=%d&aggregate=1"
POOLS = {"pons": ("robinhood", "0xed50bdeea8adc232f159486192a4157281d722ff"),
         "stonk": ("solana", "zxTpi4BtaWX3mgdAPoezkMD1hxx8CdeCfrqXMWvSCLX")}
HOURS = 72
BUYBACK_SHARE = 0.8          # Pons 公开口径：80% 收入用于回购
SF_API = "https://www.stonkfun.xyz/api/revenue"   # StonkFun 官方收入/回购/销毁（国内被墙，走海外中转）
SF_HIST = os.path.join(HERE, "sf-history.json")    # 官方累计值快照（每小时一条）


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8", "Connection": "close"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as exc:
            last = exc; time.sleep(1 + i)
    raise last


def jrpc(method, params, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(RH_RPC, data=json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "curl/8", "Connection": "close"})
            out = json.load(urllib.request.urlopen(req, timeout=45))
            if "error" in out:
                raise RuntimeError(str(out["error"])[:160])
            return out["result"]
        except Exception as exc:
            last = exc; time.sleep(1.2 + i)
    raise last


def block_ts(n):
    return int(jrpc("eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)


def blk_at(ts, hi):
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def gecko_series(key, buckets):
    """→ (vol[], close[]) 与 hours 对齐；缺的小时留 None"""
    net, pool = POOLS[key]
    j = get(GECKO % (net, pool, HOURS + 4))
    rows = ((j or {}).get("data") or {}).get("attributes", {}).get("ohlcv_list") or []
    vol = {b: None for b in buckets}
    close = {b: None for b in buckets}
    for ts, _o, _h, _l, c, v in rows:
        b = int(ts) // 3600 * 3600
        if b in vol:
            vol[b] = float(v); close[b] = float(c)
    return [vol[b] for b in buckets], [close[b] for b in buckets]


def pons_burn_hourly(buckets):
    """链上按小时分桶：块号↔时间的分段线性映射（3 个锚点）＋ 6 小时一段 getLogs"""
    h_start, h_end = buckets[0], buckets[-1] + 3600
    bn = int(jrpc("eth_blockNumber", []), 16)
    ts_now = block_ts(bn)
    anchors = []
    for t in (h_start, h_start + (h_end - h_start) // 2, min(h_end, ts_now)):
        anchors.append((t, min(bn, blk_at(t, bn))))
    def blk_of(ts):
        for i in range(len(anchors) - 1):
            t0, b0 = anchors[i]; t1, b1 = anchors[i + 1]
            if t0 <= ts <= t1 and t1 > t0:
                return b0 + (b1 - b0) * (ts - t0) / (t1 - t0)
        return anchors[-1][1]
    out = {b: 0.0 for b in buckets}
    tx = {b: 0 for b in buckets}
    span = 6 * 3600
    t = h_start
    while t < min(h_end, ts_now):
        t2 = min(t + span, ts_now)
        f, tt = int(blk_of(t)), int(blk_of(t2))
        if tt <= f:
            break
        logs = jrpc("eth_getLogs", [{"fromBlock": hex(f), "toBlock": hex(tt), "address": PONS_TOKEN,
                                     "topics": [TR, None, "0x" + "0" * 24 + PONS_DEAD[2:]]}])
        for l in logs or []:
            blk = int(l["blockNumber"], 16)
            approx = t + (tt - f and (blk - f) / (tt - f)) * (t2 - t)
            b = int(approx // 3600 * 3600)
            if b in out:
                out[b] += int(l.get("data") or "0x0", 16) / 1e18
                tx[b] += 1
        t = t2
    return [round(out[b], 2) for b in buckets], [tx[b] for b in buckets]


def stonk_burn_hourly(buckets):
    """STONK：只能用 burn-history 快照的差值，落到后一个快照所在的小时（攒满才有人字形）"""
    try:
        hist = json.load(open(HIST, encoding="utf-8"))
    except Exception:
        hist = []
    hist = [h for h in hist if h.get("stonk") is not None]
    hist.sort(key=lambda h: h["t"])
    out = {b: None for b in buckets}
    for a, b in zip(hist, hist[1:]):
        d = b["stonk"] - a["stonk"]
        if d <= 0:
            continue
        if (b["t"] - a["t"]) > 2.5 * 3600:      # 快照间隔太大，落桶会误导 → 不画
            continue
        bucket = int(b["t"] // 3600 * 3600)
        if bucket in out:
            out[bucket] = round((out[bucket] or 0) + d, 2)
    return [out[b] for b in buckets]


# ---- StonkFun 官方接口（stonkfun.xyz/api/revenue）：国内被墙，走海外中转 ----
def sf_load_hist():
    try:
        h = json.load(open(SF_HIST, encoding="utf-8"))
        return h if isinstance(h, list) else []
    except Exception:
        return []


def _sf_parse(body):
    """中转返回的不一定是纯 JSON：jina 会加 "Title/URL Source/Markdown Content" 前缀，
    所以先直解，失败就取第一个 "{" 开始的部分。"""
    try:
        return json.loads(body)
    except Exception:
        i = body.find('{"')
        if i < 0:
            raise
        return json.loads(body[i:])


def sf_fetch():
    """返回官方 totals 快照 dict；失败返回 None（下一小时再试）。

    官方站点在 Vercel、国内直连被墙，靠海外中转取数。中转本身会抽风/限流
    （allorigins、codetabs 实测经常 5xx），所以按"实测可用性"排序依次接力：
    cors.lol（原样 JSON）→ r.jina.ai（带前缀，能解析）→ allorigins → codetabs。
    """
    q = urllib.parse.quote(SF_API, safe="")
    relays = [
        "https://api.cors.lol/?url=" + q,
        "https://r.jina.ai/" + SF_API,
        "https://api.allorigins.win/raw?url=" + q,
        "https://api.codetabs.com/v1/proxy?quest=" + q,
    ]
    last = None
    for url in relays:
        for i in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                           "Accept": "application/json,text/plain,*/*",
                                                           "Connection": "close"})
                body = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
                j = _sf_parse(body)
                t = j.get("totals") or {}
                if t.get("totalRevenueUsd") is None:
                    raise RuntimeError("totals missing")
                return {"ts": int(time.time()),
                        "revUsd": float(t["totalRevenueUsd"]),
                        "buybackUsd": float(t.get("totalBuybackUsd") or 0),
                        "buybackCount": int(t.get("buybackCount") or 0),
                        "burnTokens": float(t.get("stonkBurnedTokens") or 0),
                        "burnUsd": float(t.get("stonkBurnedUsd") or 0),
                        "priceUsd": float(t.get("platformTokenPriceUsd") or 0)}
            except Exception as exc:
                last = exc; time.sleep(1.5 + i)
    print("warn: sf api: %s" % last, file=sys.stderr)
    return None


def sf_record(cur):
    """存快照：同一小时内更新末条，跨小时追加；只留最近 400 条。"""
    hist = sf_load_hist()
    if not hist or int(cur["ts"] // 3600) != int(int(hist[-1].get("ts") or 0) // 3600):
        hist.append(cur)
    else:
        hist[-1] = cur
    json.dump(hist[-400:], open(SF_HIST, "w", encoding="utf-8"), ensure_ascii=False)


def sf_series(buckets):
    """官方累计值 → 每小时差值：(收入USD[], 销毁STONK[])；间隔 >2.5h 的那一跳不落桶（会误导）。"""
    hist = [h for h in sf_load_hist() if isinstance(h, dict) and h.get("ts")]
    hist.sort(key=lambda h: h["ts"])
    rev = {b: None for b in buckets}
    burn = {b: None for b in buckets}
    for a, b in zip(hist, hist[1:]):
        gap = b["ts"] - a["ts"]
        if gap <= 0 or gap > 2.5 * 3600:
            continue
        bucket = int(b["ts"] // 3600 * 3600)
        if bucket not in rev:
            continue
        dr = (b.get("revUsd") or 0) - (a.get("revUsd") or 0)
        db = (b.get("burnTokens") or 0) - (a.get("burnTokens") or 0)
        if dr >= 0:
            rev[bucket] = round((rev[bucket] or 0) + dr, 2)
        if db >= 0:
            burn[bucket] = round((burn[bucket] or 0) + db, 2)
    return [rev[b] for b in buckets], [burn[b] for b in buckets]


def main():
    now = time.time()
    h_now = int(now // 3600 * 3600)
    buckets = [h_now - (HOURS - 1 - i) * 3600 for i in range(HOURS)]
    old = {}
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        pass

    out = {"generated": int(now), "hours": buckets, "buybackShare": BUYBACK_SHARE,
           "pons": {}, "stonk": {}}
    for key, node in (("pons", out["pons"]), ("stonk", out["stonk"])):
        try:
            vol, close = gecko_series(key, buckets)
            node["vol"], node["close"] = vol, close
        except Exception as exc:
            print("warn: gecko %s: %s" % (key, exc), file=sys.stderr)
            node["vol"] = (old.get(key) or {}).get("vol", [None] * HOURS)
            node["close"] = (old.get(key) or {}).get("close", [None] * HOURS)

    try:
        burn, tx = pons_burn_hourly(buckets)
        out["pons"]["burn"], out["pons"]["burnTx"] = burn, tx
        out["pons"]["burnSrc"] = "chain"
    except Exception as exc:
        print("warn: pons burn: %s" % exc, file=sys.stderr)
        out["pons"]["burn"] = (old.get("pons") or {}).get("burn", [None] * HOURS)
        out["pons"]["burnTx"] = (old.get("pons") or {}).get("burnTx", [None] * HOURS)
        out["pons"]["burnSrc"] = "stale"

    # StonkFun 官方接口（经海外中转）：累计值 → 每小时差值 = 真实收入 / 真实销毁
    sf_cur = sf_fetch()
    if sf_cur:
        sf_record(sf_cur)
    srev, sburn = sf_series(buckets)
    if any(v is not None for v in sburn):
        out["stonk"]["burn"], out["stonk"]["burnSrc"] = sburn, "official"
    else:
        try:  # 官方两点还没攒够 → 退回旧的 Solana 供应量快照差值
            out["stonk"]["burn"] = stonk_burn_hourly(buckets)
            out["stonk"]["burnSrc"] = "snapshot"
        except Exception as exc:
            print("warn: stonk burn: %s" % exc, file=sys.stderr)
            out["stonk"]["burn"] = [None] * HOURS
            out["stonk"]["burnSrc"] = "none"

    # 收入：Pons 用「小时回购支出 ÷ 80%」推算；StonkFun 用官方累计值的每小时差值（真值）
    pv = []
    for b, c in zip(out["pons"]["burn"], out["pons"]["close"]):
        pv.append(round(b * c / BUYBACK_SHARE, 2) if (b and c) else None)
    out["pons"]["rev"], out["pons"]["revEst"] = pv, True
    out["stonk"]["rev"], out["stonk"]["revEst"] = srev, False
    out["stonk"]["revSrc"] = "official" if any(v is not None for v in srev) else "official-pending"

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    pb = [x for x in out["pons"]["burn"] if x]
    print("hourly.json ok · 小时数 %d · PONS 72h 销毁 %s · 交易量 PONS %s / STONK %s"
          % (HOURS, round(sum(pb), 1),
             sum(x for x in out["pons"]["vol"] if x), sum(x for x in out["stonk"]["vol"] if x)))
    return out


if __name__ == "__main__":
    main()
