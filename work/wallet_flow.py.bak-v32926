#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""钱包分层净流入（v3.29）—— 按钱包持币规模分层，统计 24 小时净买入。

为什么这样设计（只认实测，不估算）：
  · 成交：GeckoTerminal 各资金池「最近一页」成交（每池最多 300 笔）。GT 不给翻页，
    所以每次构建采样一次、滚动攒 24 小时账本（work/wallet-flow.json）；相邻两次
    构建的窗口重叠，用「交易指纹」去重（tx_hash+池+方向+金额 的摘要）。
  · 分层：钱包「当前」持币市值 = 链上余额 × 现价：
      巨鲸 ≥ $1M ｜ 鲨鱼 $100K–$1M ｜ 海豚 $10K–$100K ｜ 小鱼 < $10K
    余额查询（v3.29.3 重写）：ATA（关联代币账户）地址纯本地推导（sha256 即可，无需 RPC），
    再用 getMultipleAccounts 一次 100 个地址批量取余额 —— 2026-10-11 实测公共节点对
    逐钱包查询（getTokenAccountsByOwner）限流极严，批量地址位图才是能跑通的形态。
    余额结果缓存归档（TTL 48 小时）；查不到的钱包进「未识别」桶，单列不充数。
  · 局限（前端原样标注）：只覆盖 DEX 成交（转帐 / OTC 不算）；做市商没有公开标签
    （截图类产品的 MM 档无公开数据源，不硬造）；分层用当前余额，窗口内刚清仓 /
    刚建仓的钱包可能归错档。

用法：由 stonk_page.py 调用 sample()；本文件可单独跑 --selftest 做本机验证。
"""
import base64
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
    # 2026-10-11 实测：官方节点是唯一可用的公共节点（逐钱包查询 1.5s 间隔可用；
    # 批量就 429）。publicnode 已改成「索引类请求要付费」（403），Metaplex /
    # ExtraNode 域名已下线，drpc 免费套餐不含 Solana，OnFinality / Ankr 要 Key。
    # v3.29.3 起不再逐钱包查询，改用 ATA 推导 + getMultipleAccounts（见 fetch_holdings）。
    "https://api.mainnet-beta.solana.com",
]
LEDGER_KEEP_H = 25          # 账本滚动窗口（24h + 1h 余量）
TIER_TTL_H = 48             # 余额快照有效期
ATA_BATCH = 100             # getMultipleAccounts 单次上限（协议规定 100 个地址）
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


def _rpc_single(method, params, timeout=RPC_TIMEOUT):
    """单条 JSON-RPC 请求 → result（RPC 报错 / 网络失败都抛异常，由调用方重试）。"""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    req = urllib.request.Request(RPC_ENDPOINTS[0], data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Connection": "close",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        got = json.loads(resp.read().decode("utf-8", "replace"))
    if not isinstance(got, dict) or got.get("error"):
        raise RuntimeError("rpc error: %s" % str(got.get("error"))[:120])
    return got.get("result")


# ---- Base58 / ATA 地址本地推导（纯 sha256 + ed25519 曲线判定，不需要任何 RPC） ----
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    pad = len(s) - len(s.lstrip("1"))
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * pad + body


def _b58encode(raw):
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    pad = len(raw) - len(raw.lstrip(b"\x00"))
    return "1" * pad + (out or "")


_FP = 2 ** 255 - 19                      # ed25519 素域
_FD = -121665 * pow(121666, _FP - 2, _FP) % _FP


def _on_curve(raw):
    y = int.from_bytes(raw, "little") & ((1 << 255) - 1)
    if y >= _FP:
        return False
    y2 = y * y % _FP
    u = (y2 - 1) % _FP
    v = (_FD * y2 + 1) % _FP
    x2 = u * pow(v, _FP - 2, _FP) % _FP
    x = pow(x2, (_FP + 3) // 8, _FP)
    if (x * x - x2) % _FP != 0:
        x = x * pow(2, (_FP - 1) // 4, _FP) % _FP
    return x * x % _FP == x2


def _find_pda(seeds, program):
    for bump in range(255, -1, -1):
        h = hashlib.sha256()
        for s in seeds:
            h.update(s)
        h.update(bytes([bump]))
        h.update(program)
        h.update(b"ProgramDerivedAddress")
        digest = h.digest()
        if not _on_curve(digest):
            return _b58encode(digest)
    raise RuntimeError("pda not found")


_ATA_PROGRAM = _b58decode("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
_TOKEN_PROGRAM = _b58decode("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
_MINT_RAW = None
_DECIMALS = None


def _ata(owner):
    """wallet 的 STONK 关联代币账户（ATA）地址。"""
    global _MINT_RAW
    if _MINT_RAW is None:
        _MINT_RAW = _b58decode(MINT)
    return _find_pda([_b58decode(owner), _TOKEN_PROGRAM, _MINT_RAW], _ATA_PROGRAM)


def _mint_decimals():
    global _DECIMALS
    if _DECIMALS is None:
        info = _rpc_single("getAccountInfo", [MINT, {"encoding": "base64"}])
        raw = base64.b64decode(((info or {}).get("value") or {}).get("data", [""])[0])
        _DECIMALS = raw[44] if len(raw) > 44 else 9   # SPL mint 布局：decimals 在第 45 字节
    return _DECIMALS


def fetch_holdings(wallets, budget_s=HOLDINGS_BUDGET_S, deadline=None):
    """批量查这些钱包当前持有的 STONK → ({wallet: tokens}, diag)。

    为什么这样写（2026-10-11 实测教训）：
      · 公共 RPC 对 getTokenAccountsByOwner 的限制极严：官方节点一次批量 5 个就 429
        （单个 + 1.5s 间隔才基本可用）；publicnode 一个请求只允许 1 个该调用、
        「索引类请求」还要付费（403）；Metaplex / ExtraNode / drpc 等已下线或要 Key。
      · 但 ATA 地址可以纯本地推导（sha256，见 _ata，不需要任何 RPC）；再用
        getMultipleAccounts 一次 100 个地址批量取余额（每次 ~0.5s，实测连续多次无 429）
        —— 478 个钱包 5 次调用、几秒钟查完，且对节点非常友好。
      · ATA 不存在 = 当前不持有（抽样 8/8 回查确认 token 账户数为 0），记 0 归小鱼档。
      · 误差局限：极少数用非 ATA 账户持仓的钱包会被记 0（页面口径已注明「按当前余额分层」）。
    """
    out = {}
    todo = list(wallets)[:MAX_CHECK_PER_RUN]
    t0 = time.time()
    if deadline is not None:
        budget_s = min(budget_s, max(0.0, deadline - t0))
    diag = {"chunks": 0, "batches": 0, "nulls": 0, "err": [], "decimals": None}
    try:
        decimals = _mint_decimals()
        diag["decimals"] = decimals
    except Exception as exc:
        decimals = 9
        diag["err"].append("mint:%s" % str(exc)[:70])
    for i in range(0, len(todo), ATA_BATCH):
        if time.time() - t0 > budget_s:
            diag["budgetOut"] = len(todo) - i
            break
        chunk = todo[i:i + ATA_BATCH]
        try:
            atas = [_ata(w) for w in chunk]
        except Exception as exc:
            diag["err"].append("pda:%s" % str(exc)[:70])
            continue
        got = None
        last = None
        for attempt in range(3):
            try:
                got = _rpc_single("getMultipleAccounts", [atas, {"encoding": "base64"}])
                break
            except Exception as exc:
                last = exc
                time.sleep(1.5 + 1.5 * attempt)
        diag["chunks"] += 1
        vals = (got or {}).get("value") if isinstance(got, dict) else None
        if not isinstance(vals, list):
            diag["err"].append("gma%d:%s" % (i // ATA_BATCH, str(last)[:70]))
            continue
        diag["batches"] += 1
        for w, v in zip(chunk, vals):
            if v is None:
                out[w] = 0.0
                diag["nulls"] += 1
                continue
            try:
                raw = base64.b64decode((v.get("data") or [""])[0])
                out[w] = int.from_bytes(raw[64:72], "little") / (10 ** decimals)
            except Exception:
                diag["err"].append("parse:%s" % w[:6])
        time.sleep(0.8)
    return out, diag


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
            hold, hdiag = fetch_holdings(need)
            for w, amt in hold.items():
                tiers[w] = [round(amt * price, 2), now]
            wf_dbg = {"need": len(need), "ok": len(hold), "rpc": hdiag}
            print("wallet-flow: checked %d wallets (%d ok, %d null-ATA)"
                  % (len(need), len(hold), (hdiag or {}).get("nulls") or 0))
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
