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
  · 前 20 榜（v3.29.26）：在分层之上，按 24 小时成交额列出「买入榜 / 卖出榜」各 20 名，
    每行给 地址 / 成交金额 / 代币数量 / 当前余额（同样是实测值，不估算）。
    代币数量来自 GT 每笔成交的 from/to_token_amount（自 v3.29.26 起随账本记录，
    滚动 24 小时后完整；更早入库的旧条目没有这个字段，显示 —）。
    机器人 / 交易所过滤是行为启发式（页面口径如实标注，不硬说 100% 干净）：
      ① gas 档：已核实的 gas 竞价机器人地址名单；
      ② 高频档：24h ≥ 300 笔，或 ≥ 60 笔且平均单笔 ≤ $1,000（刷单形态）；
      ③ 对刷档：24h ≥ 40 笔、买卖两边体量相当且净额 ≤ 双向总额 15%（做市/对冲形态）。
    被过滤的地址不参与排名，但会在页面「已过滤」折叠里列出（地址/成交额/原因），
    数字可对账 —— 宁可少写几个名字，也不假装标签百分百准确。
  · 局限（前端原样标注）：只覆盖 DEX 成交（转帐 / OTC 不算）；做市商没有公开标签
    （截图类产品的 MM 档无公开数据源，不硬造）；分层用当前余额，窗口内刚清仓 /
    刚建仓的钱包可能归错档。
  · 成本线 / 浮盈浮亏（v3.29.28）：「窗口买入均价 = 窗口买入额 ÷ 枚数」与现价比，
    回答作者的问题「这个地址是赚钱买入还是亏钱买入」。枚数优先用成交自带的实测值
    （v3.29.26 起入库的条目）；更早的条目没有这个字段，按「成交当小时收盘价」
    折算（GT ohlcv/hour，实测 587 笔有枚数的成交：折算价与真实成交单价偏差中位数
    0.35%、95.4% 在 ±1% 内，2026-10-17 验证）。含折算的行前端标 ≈，不硬说实测。
    注意：这只是「窗口内买入」的成本线，不是钱包的全仓成本（窗口之外的老仓无法回溯）。

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
TOP_N = 20                  # 买入榜 / 卖出榜各取前 20
FILT_SHOW = 30              # 页面「已过滤」折叠里最多列 30 个（按成交额排序）
BOT_HARD_N = 300            # 24h ≥ 300 笔：一律按机器处理
BOT_MIN_N = 60              # 高频档：24h ≥ 60 笔 …
BOT_MAX_AVG = 1000          # … 且平均单笔 ≤ $1,000（真人很少以这个频率刷小额）
MM_MIN_N = 40               # 对刷档：24h ≥ 40 笔 …
MM_MAX_NET = 0.15           # … 且净额 ≤ 双向总额的 15% …
MM_MIN_SIDE = 0.35          # … 且买卖两边都 ≥ 对方的 35%（在两边来回倒，不是在真买/真卖）
# 已核实的机器人 / 基础设施地址（前两个前缀 gas 的即 gas 竞价机器人，GT 成交里高频出现）
KNOWN_BOTS = frozenset([
    "gasBidSWW5zmwXs3gn8TG2ijzKkrwpyM7ucwjgDQst6",
    "gasTzr94Pmp4Gf8vknQnqxeYxdgwFjbgdJa4msYRpnB",
])


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


def _fetch_px_hist(pool, limit=26):
    """主池最近 N 小时的小时收盘价（GT ohlcv/hour）→ [(bucket_ts, close)]，失败返回 []。

    用途（v3.29.28）：成本线要「枚数」才能算均价，而账本里 v3.29.26 之前入库的成交
    没有枚数字段 → 用成交当小时的收盘价把美元额折算成枚数。这不是拍脑袋的近似：
    2026-10-17 拿 587 笔同时有枚数的真实成交回测，折算价与成交单价的偏差中位数 0.35%、
    95.4% 在 ±1% 内（STONK 小时内的价格波动本来就小）。前端对含折算的行标 ≈。
    """
    net, _ = H.POOLS["stonk"]
    url = "%s/networks/%s/pools/%s/ohlcv/hour?limit=%d&aggregate=1" % (GT, net, pool, limit)
    j = H.get(url)
    rows = (((j or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    out = []
    for r in rows:
        try:
            out.append((int(r[0]) // 3600 * 3600, float(r[4])))
        except Exception:
            continue
    return out


def _tier_of(usd):
    for key, lo in TIER_ORDER:
        if usd >= lo:
            return key
    return "fish"


def _wallet_tok(a, kind):
    """这笔成交里「钱包这一侧」收/付的 STONK 枚数（GT 的 to/from_token_amount）。

    买：钱包收到代币 → to_token_amount ；卖：钱包付出代币 → from_token_amount。
    拿不到 / 非正数返回 None（前端显示 —，不估算）。
    """
    try:
        v = float(a.get("to_token_amount") if kind == "b" else a.get("from_token_amount"))
    except Exception:
        return None
    return round(v, 4) if v > 0 else None


def _bot_reason(w, n, buy, sell):
    """钱包的「机器 / 机构」标签（None = 正常参与排名）。见文件头 v3.29.26 说明。"""
    if w in KNOWN_BOTS:
        return "gas"
    tv = buy + sell
    if n >= BOT_HARD_N:
        return "hf"
    mx, mn = (buy, sell) if buy >= sell else (sell, buy)
    if n >= MM_MIN_N and tv > 0 and abs(buy - sell) <= MM_MAX_NET * tv and mn >= MM_MIN_SIDE * mx:
        return "mm"
    if n >= BOT_MIN_N and tv / n <= BOT_MAX_AVG:
        return "hf"
    return None


def sample(pool_addrs, price, now=None, state_path=STATE, trade_fetcher=None, px_hist=None):
    """采样一轮 → 聚合结果 dict；price 拿不到 / 完全没数据时返回 None。

    trade_fetcher(pool) → [attributes]；默认 H.get 拉 GT。测试时可注入。
    px_hist = [(bucket_ts, close)]：成本线里给旧条目折算枚数用的小时收盘价（v3.29.28）；
    不传且走真实网络时自动拉主池（测试注入 trade_fetcher 时不会联网）。
    """
    now = int(now or time.time())
    fetcher = trade_fetcher or _fetch_pool_trades
    errs = []
    if px_hist is None and trade_fetcher is None and pool_addrs:
        try:
            px_hist = _fetch_px_hist(pool_addrs[0])
        except Exception as exc:
            px_hist = []
            errs.append("px:%s" % str(exc)[:70])
    pxmap = {}
    for it in (px_hist or []):
        try:
            pxmap[int(it[0]) // 3600 * 3600] = float(it[1])
        except Exception:
            pass
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
            # v3.29.26：账本加记这一侧收/付的代币枚数（旧条目没这个字段，读时按 4 元组兜底）
            tr[fp] = [t, a["tx_from_address"], kind, round(u, 2), _wallet_tok(a, kind)]
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
                # [市值USD, 查询时间, 代币枚数]（第三项 v3.29.26 起才有）
                tiers[w] = [round(amt * price, 2), now, round(amt, 4)]
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
    per = {}                     # 钱包 → 窗口内买卖合计（前 20 榜用）
    tok_tr = tok_have = 0        # 数量字段覆盖率（旧账本条目没有，页面如实标注）
    fold_usd = all_usd = 0.0     # 成本线里「按小时收盘价折算枚数」的成交额占比（v3.29.28）
    for entry in tr.values():
        t, w, kind, u = entry[0], entry[1], entry[2], entry[3]
        tok = entry[4] if len(entry) > 4 else None
        # 成本线用的「有效枚数」：实测优先；旧条目没有枚数字段时按当小时收盘价折算
        tok_eff, folded = tok, False
        if tok is None and u and pxmap:
            fpx = pxmap.get(int(t // 3600 * 3600))
            if fpx:
                tok_eff, folded = u / fpx, True
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
        p = per.get(w)
        if p is None:
            p = per[w] = {"buy": 0.0, "sell": 0.0, "btok": 0.0, "stok": 0.0,
                          "bq": 0.0, "sq": 0.0, "foldB": 0.0, "foldS": 0.0,
                          "nb": 0, "ns": 0, "miss": 0}
        all_usd += u
        if folded:
            fold_usd += u
        if kind == "b":
            p["buy"] += u
            p["nb"] += 1
            if tok_eff:
                p["bq"] += tok_eff
                if folded:
                    p["foldB"] += u
        else:
            p["sell"] += u
            p["ns"] += 1
            if tok_eff:
                p["sq"] += tok_eff
                if folded:
                    p["foldS"] += u
        tok_tr += 1
        if tok:
            tok_have += 1
            if kind == "b":
                p["btok"] += tok
            else:
                p["stok"] += tok
        else:
            p["miss"] += 1
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

    # ---- 5) 前 20 榜（买入 / 卖出），先按行为特征剔机器，再按成交额排名 ----
    def _row(w, p):
        tv = tiers.get(w)
        bal, balt, bal_ts = None, None, None
        if tv:
            bal = tv[0]
            if len(tv) > 1:
                bal_ts = tv[1]
            if len(tv) > 2:
                balt = tv[2]
        return {
            "w": w,
            "balTs": bal_ts,
            "buy": round(p["buy"], 2), "sell": round(p["sell"], 2),
            # 数量：只有该钱包窗口内每一笔都带数量字段才给合计（缺一条就显示 —，不估算）
            "btok": round(p["btok"], 4) if (p["btok"] and not p["miss"]) else None,
            "stok": round(p["stok"], 4) if (p["stok"] and not p["miss"]) else None,
            "nb": p["nb"], "ns": p["ns"],
            "bal": bal, "balt": balt,
            # 成本线（v3.29.28）：均价 = 金额 ÷ 有效枚数（实测 + 按小时收盘价折算）；
            # apxB / apxS = 该方向成交额里「折算」占的百分比（>0 前端标 ≈，0 = 全实测）
            "bq": round(p["bq"], 4) if p["bq"] else None,
            "sq": round(p["sq"], 4) if p["sq"] else None,
            "bavg": round(p["buy"] / p["bq"], 8) if p["bq"] else None,
            "savg": round(p["sell"] / p["sq"], 8) if p["sq"] else None,
            "apxB": round(p["foldB"] / p["buy"] * 100, 1) if p["buy"] else 0,
            "apxS": round(p["foldS"] / p["sell"] * 100, 1) if p["sell"] else 0,
        }

    for w, p in per.items():
        p["r"] = _bot_reason(w, p["nb"] + p["ns"], p["buy"], p["sell"])
    clean = sorted((w for w in per if not per[w]["r"]),
                   key=lambda w: -(per[w]["buy"] + per[w]["sell"]))
    botw = sorted((w for w in per if per[w]["r"]),
                  key=lambda w: -(per[w]["buy"] + per[w]["sell"]))
    top_buy = [_row(w, per[w]) for w in sorted(clean, key=lambda w: -per[w]["buy"])[:TOP_N]]
    top_sell = [_row(w, per[w]) for w in sorted(clean, key=lambda w: -per[w]["sell"])[:TOP_N]]
    bot_filt = [{"w": w, "v": round(per[w]["buy"] + per[w]["sell"], 2),
                 "n": per[w]["nb"] + per[w]["ns"], "r": per[w]["r"]} for w in botw[:FILT_SHOW]]
    bot_vol = sum(per[w]["buy"] + per[w]["sell"] for w in botw)
    bot_mix = {}
    for w in botw:
        bot_mix[per[w]["r"]] = bot_mix.get(per[w]["r"], 0) + 1

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
        "topBuy": top_buy,
        "topSell": top_sell,
        "botFilt": bot_filt,
        "botN": len(botw),
        "botVol": round(bot_vol, 2),
        "botMix": bot_mix,
        "tokCover": round(tok_have / tok_tr * 100, 1) if tok_tr else None,
        "foldPct": round(fold_usd / all_usd * 100, 1) if all_usd else None,
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
