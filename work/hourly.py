#!/usr/bin/env python3
"""小时级监控数据（最近 72 小时）→ work/hourly.json

数据源（全部公开、无需 key）：
  1. 交易量（每小时）→ GeckoTerminal OHLCV hour（真小时线，允许跨域，浏览器也能直连）
       PONS  → robinhood / 0xed50bdee… (PONS/WETH)
       STONK → solana    / zxTpi4Bt…   (STONK/SOL)
  2. 销毁（每小时）→ Robinhood Chain eth_getLogs 筛 Transfer→0x…dEaD，按小时分桶（真链上）
       STONK 没有公开的小时级销毁（公共 RPC 限流、只能读当前供应量）→ 靠 burn-history 快照累积
  3. 收入（每小时）→ 没有任何公开小时级收入源（DefiLlama 只有日级）。
       Pons 给一列「链上推算」＝ 小时回购支出 ÷ 80%（回购占比），明确标注为推算；
       真实小时级收入靠本脚本每小时跑一次、往 hourly.json 里累积。
"""
import json, os, sys, time, urllib.request

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

    try:
        out["stonk"]["burn"] = stonk_burn_hourly(buckets)
        out["stonk"]["burnSrc"] = "snapshot"
    except Exception as exc:
        print("warn: stonk burn: %s" % exc, file=sys.stderr)
        out["stonk"]["burn"] = [None] * HOURS
        out["stonk"]["burnSrc"] = "none"

    # 收入：Pons 用「小时回购支出 ÷ 80%」推算；StonkFun 暂缺（没有小时级销毁 → 无法推算）
    pv = []
    for b, c in zip(out["pons"]["burn"], out["pons"]["close"]):
        pv.append(round(b * c / BUYBACK_SHARE, 2) if (b and c) else None)
    out["pons"]["rev"], out["pons"]["revEst"] = pv, True
    out["stonk"]["rev"], out["stonk"]["revEst"] = [None] * HOURS, True

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    pb = [x for x in out["pons"]["burn"] if x]
    print("hourly.json ok · 小时数 %d · PONS 72h 销毁 %s · 交易量 PONS %s / STONK %s"
          % (HOURS, round(sum(pb), 1),
             sum(x for x in out["pons"]["vol"] if x), sum(x for x in out["stonk"]["vol"] if x)))
    return out


if __name__ == "__main__":
    main()
