#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""钱包分层净流入（v3.29）—— 按钱包持币规模分层，统计 24 小时净买入。

为什么这样设计（只认实测，不估算）：
  · 成交：GeckoTerminal 各资金池「最近一页」成交（每池最多 300 笔）。GT 不给翻页，
    所以每次构建采样一次、滚动攒 24 小时账本（work/wallet-flow.json）；相邻两次
    构建的窗口重叠，用「交易指纹」去重（tx_hash+池+方向+金额 的摘要）。
  · 分层：钱包「当前」持币市值 = 链上余额（Solana RPC 批量查，jsonParsed）× 现价：
      巨鲸 ≥ $1M ｜ 鲨鱼 $100K–$1M ｜ 海豚 $10K–$100K ｜ 小鱼 < $10K
    余额结果缓存归档（TTL 48 小时）；查不到的钱包进「未识别」桶，单列不充数。
  · 局限（前端原样标注）：只覆盖 DEX 成交（转帐 / OTC 不算）；做市商没有公开标签
    （截图类产品的 MM 档无公开数据源，不硬造）；分层用当前余额，窗口内刚清仓 /
    刚建仓的钱包可能归错档。

用法：由 stonk_page.py 调用 sample()；本文件可单独跑 --selftest 做本机验证。
"""
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hourly as H  # noqa: E402

STATE = os.path.join(HERE, "wallet-flow.json")
MINT = "6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx"
GT = "https://api.geckoterminal.com/api/v2"
RPC_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
    "https://api.metaplex.solana.com",
]
LEDGER_KEEP_H = 25          # 账本滚动窗口（24h + 1h 余量）
TIER_TTL_H = 48             # 余额快照有效期
BATCH = 50                  # 每次 RPC 批量的钱包数
WINDOW_H = 24               # 展示窗口
MAX_LEDGER = 60000          # 账本安全上限（防异常膨胀）
POOL_N = 5                  # 只采成交量前 5 的资金池（约占全市场 ~97% 成交额）
RPC_TIMEOUT = 15            # 单次 RPC 请求超时（秒）——2026-10-11 教训：默认 30s × 重试会拖垮整条管道
HOLDINGS_BUDGET_S = 240     # 每轮构建查余额的总预算：查不完的钱包留给下一小时（有 48h 缓存）
MAX_CHECK_PER_RUN = 800     # 单轮最多查的钱包数（按最近活跃排序，优先查新鲜的）
TRADES_BUDGET_S = 150       # 拉成交的总预算：拉不完的资金池直接跳过（下轮再补）
TIER_ORDER = [("whale", 1_000_000), ("shark", 100_000), ("dolphin", 10_000), ("fish", 0)]


def jload(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def _fingerprint(tx_hash, pool, kind, usd):
    raw = "%s|%s|%s|%.2f" % (tx_hash, pool, kind, usd)
    return hashlib.md5(raw.encode()).hexdigest()[:14]


def _rpc_post(endpoint, calls, timeout=RPC_TIMEOUT):
    body = json.dumps(calls).encode()
    req = urllib.request.Request(endpoint, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Connection": "close",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def fetch_holdings(wallets, budget_s=HOLDINGS_BUDGET_S, deadline=None):
    """批量查这些钱包的 STONK 余额 → {wallet: tokens}。查不到的 wallet 不在结果里。

    带时间预算（默认 240s）：查不完的留给下一小时继续（余额有 48h 缓存，覆盖很快补齐）。
    2026-10-11 实测教训：个别公共 RPC 会「连接上但不回包」，30s 超时 × 3 尝试 × N 批次
    能把整条云端管道拖到超时；这里改成 15s 超时 + 每个批次最多 2 轮、节点优选，
    再加全局预算兜底。
    """
    out = {}
    todo = list(wallets)[:MAX_CHECK_PER_RUN]
    t0 = time.time()
    if deadline is not None:
        budget_s = min(budget_s, max(0.0, deadline - t0))
    order = list(RPC_ENDPOINTS)          # 本轮内优选用过的节点
    for i in range(0, len(todo), BATCH):
        if time.time() - t0 > budget_s:
            print("wallet-flow: holdings 预算用尽（%.0fs），%d 个钱包留给下一轮"
                  % (budget_s, len(todo) - i), file=sys.stderr)
            break
        chunk = todo[i:i + BATCH]
        calls = [{"jsonrpc": "2.0", "id": j, "method": "getTokenAccountsByOwner",
                  "params": [w, {"mint": MINT}, {"encoding": "jsonParsed"}]}
                 for j, w in enumerate(chunk)]
        got = None
        last = None
        for attempt in range(2):
            for ep in order:
                try:
                    got = _rpc_post(ep, calls)
                except Exception as exc:
                    last = exc
                    continue
                if order[0] != ep:       # 这个节点能用 → 本轮后续批次优先用它
                    order.remove(ep)
                    order.insert(0, ep)
                break
            if isinstance(got, list):
                break
            if time.time() - t0 > budget_s:
                break
            time.sleep(1.5 + 1.5 * attempt)
        if not isinstance(got, list):
            print("warn: wallet-flow holdings batch failed: %s" % (last,), file=sys.stderr)
            continue
        for item in got:
            j = item.get("id")
            if not isinstance(j, int) or j >= len(chunk) or item.get("error"):
                continue
            amt = 0.0
            for acc in ((item.get("result") or {}).get("value") or []):
                try:
                    info = (((acc.get("account") or {}).get("data") or {}).get("parsed") or {}).get("info") or {}
                    amt += float((info.get("tokenAmount") or {}).get("uiAmount") or 0)
                except Exception:
                    pass
            out[chunk[j]] = amt
        time.sleep(0.3)
    return out


def _fetch_pool_trades(pool):
    """一页成交（最多 300 笔，新→旧）。超时 20s；GT 限流（429）时多等一会儿再重试。"""
    url = "%s/networks/solana/pools/%s/trades" % (GT, pool)
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "curl/8", "Accept": "application/json", "Connection": "close"})
            data = json.load(urllib.request.urlopen(req, timeout=20))
            break
        except Exception as exc:
            last = exc
            wait = (15 + 6 * i) if "429" in str(exc) else (3 + 3 * i)
            print("warn: wallet-flow trades %s attempt %d: %s（%ds 后重试）"
                  % (pool[:8], i + 1, exc, wait), file=sys.stderr)
            time.sleep(wait)
    else:
        raise last
    out = []
    for item in (data.get("data") or []):
        a = item.get("attributes") or {}
        if a.get("block_timestamp") and a.get("tx_from_address") and a.get("volume_in_usd") is not None:
            out.append(a)
    return out


def _tier_of(usd):
    for key, lo in TIER_ORDER:
        if usd >= lo:
            return key
    return "fish"


def sample(pool_addrs, price, now=None, state_path=STATE, trade_fetcher=None):
    """采样一轮 → 聚合结果 dict；price 拿不到 / 完全没数据时返回 None。

    trade_fetcher(pool) → [attributes]；默认 H.get 拉 GT。测试时可注入。
    """
    now = int(now or time.time())
    fetcher = trade_fetcher or _fetch_pool_trades
    errs = []
    st = jload(state_path, {}) or {}
    tr = st.get("tr") or {}
    tiers = st.get("tiers") or {}
    if not isinstance(tr, dict):
        tr = {}
    if not isinstance(tiers, dict):
        tiers = {}

    # ---- 1) 采样 + 入账（窗口内去重；总量预算内） ----
    got_any = False
    t_wf = time.time()
    for pool in pool_addrs[:POOL_N]:
        if time.time() - t_wf > TRADES_BUDGET_S:
            print("wallet-flow: trades 预算用尽，剩余资金池跳过（下轮再补）", file=sys.stderr)
            break
        try:
            rows = fetcher(pool)
            got_any = True
        except Exception as exc:
            errs.append("tr:%s:%s" % (pool[:6], str(exc)[:90]))
            print("warn: wallet-flow trades %s: %s" % (pool[:8], exc), file=sys.stderr)
            continue
        for a in rows:
            try:
                t = H._iso_ms(a["block_timestamp"]) // 1000
                u = float(a["volume_in_usd"])
            except Exception:
                continue
            if t < now - LEDGER_KEEP_H * 3600:
                continue
            kind = "b" if a.get("kind") == "buy" else "s"
            fp = _fingerprint(str(a.get("tx_hash") or ""), pool, kind, u)
            if fp in tr:
                continue
            tr[fp] = [t, a["tx_from_address"], kind, round(u, 2)]
    if not got_any and not tr:
        H.atomic_dump({"v": 1, "tr": tr, "tiers": tiers, "built": now,
                       "dbg": {"empty": True, "tradesErr": errs[:5]}}, state_path)
        return None

    # ---- 2) 账本滚动窗口 + 安全上限 ----
    cut = now - LEDGER_KEEP_H * 3600
    tr = {k: v for k, v in tr.items() if v and v[0] >= cut}
    if len(tr) > MAX_LEDGER:
        keep = sorted(tr.items(), key=lambda kv: kv[1][0], reverse=True)[:MAX_LEDGER]
        tr = dict(keep)
    # 先把账本落盘：万一后面查余额/聚合异常，这一轮采到的成交也不至于白采
    H.atomic_dump({"v": 1, "tr": tr, "tiers": tiers, "built": now, "dbg": {"stage": "trades"}}, state_path)

    # ---- 3) 分层（新钱包 + 过期钱包查链上余额；按最近活跃优先） ----
    wallets = {v[1] for v in tr.values()}
    wf_dbg = {}
    if price:
        last_t = {}
        for v in tr.values():
            w0, t0v = v[1], v[0]
            if w0 not in last_t or t0v > last_t[w0]:
                last_t[w0] = t0v
        need = [w for w in wallets
                if w not in tiers or (now - int((tiers[w] or [0, 0])[1] or 0)) > TIER_TTL_H * 3600]
        need.sort(key=lambda w: last_t.get(w, 0), reverse=True)
        if need:
            hold = fetch_holdings(need)
            for w, amt in hold.items():
                tiers[w] = [round(amt * price, 2), now]
            wf_dbg = {"need": len(need), "ok": len(hold)}
            print("wallet-flow: checked %d wallets (%d ok)" % (len(need), len(hold)))
    tiers = {w: v for w, v in tiers.items() if w in wallets}

    # ---- 4) 聚合近 24 小时 ----
    cutoff = now - WINDOW_H * 3600
    agg = {}
    for key, _ in TIER_ORDER:
        agg[key] = {"net": 0.0, "buy": 0.0, "sell": 0.0, "n": 0, "wh": set()}
    agg["na"] = {"net": 0.0, "buy": 0.0, "sell": 0.0, "n": 0, "wh": set()}
    span_lo, span_hi = None, None
    for t, w, kind, u in tr.values():
        if t < cutoff:
            continue
        tv = tiers.get(w)
        key = _tier_of(tv[0]) if (tv and tv[0] is not None) else "na"
        b = agg[key]
        if kind == "b":
            b["buy"] += u
            b["net"] += u
        else:
            b["sell"] += u
            b["net"] -= u
        b["n"] += 1
        b["wh"].add(w)
        span_lo = t if span_lo is None else min(span_lo, t)
        span_hi = t if span_hi is None else max(span_hi, t)

    vol = sum(agg[k]["buy"] + agg[k]["sell"] for k in agg)
    na_vol = agg["na"]["buy"] + agg["na"]["sell"]
    out_tiers = []
    for key, _ in TIER_ORDER:
        b = agg[key]
        out_tiers.append({"k": key, "net": round(b["net"], 2), "buy": round(b["buy"], 2),
                          "sell": round(b["sell"], 2), "n": b["n"], "wh": len(b["wh"])})
    if agg["na"]["n"]:
        b = agg["na"]
        out_tiers.append({"k": "na", "net": round(b["net"], 2), "buy": round(b["buy"], 2),
                          "sell": round(b["sell"], 2), "n": b["n"], "wh": len(b["wh"])})

    result = {
        "updatedAt": now,
        "spanH": round((span_hi - span_lo) / 3600.0, 1) if (span_hi and span_lo) else None,
        "windowH": WINDOW_H,
        "coveragePct": round((1 - na_vol / vol) * 100, 1) if vol > 0 else None,
        "trades": sum(a["n"] for a in agg.values()),
        "wallets": len({v[1] for v in tr.values() if v[0] >= cutoff}),
        "volume": round(vol, 2),
        "thresholds": {"whale": 1_000_000, "shark": 100_000, "dolphin": 10_000},
        "tiers": out_tiers,
        "srcNote": "GeckoTerminal 成交 + Solana RPC 余额（本站采样）",
    }
    H.atomic_dump({"v": 1, "tr": tr, "tiers": tiers, "built": now,
                   "dbg": {"tradesErr": errs[:5], "hold": wf_dbg}}, state_path)
    return result


def _selftest():
    """本机自测：拉 STONK 前 5 池 + 查余额 + 打印结果（会写真实状态文件）。"""
    pools = json.load(open(os.path.join(HERE, "stonk-page.json"), encoding="utf-8"))
    plist = ((pools.get("demand") or {}).get("pools") or [])
    addrs = [p.get("addr") for p in sorted(plist, key=lambda x: x.get("vol") or 0, reverse=True) if p.get("addr")]
    price = ((pools.get("hero") or {}).get("price"))
    print("selftest pools:", len(addrs), "price:", price)
    res = sample(addrs, price)
    print(json.dumps(res, ensure_ascii=False, indent=1)[:2400])


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print("usage: python3 wallet_flow.py --selftest")
