#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STONK 深度页数据（v3.27）→ work/stonk-page.json，并注入 dashboard-data.json 的 stonkPage 字段。

数据源（全部公开、无需 key）：
  · StonkFun 官方 API：累计值 /api/revenue、日线 /api/v2/revenue/daily、销毁流水 /api/v2/revenue/burns
    （国内直连被墙，复用 hourly.py 的海外中转；CI 里 PONSPULSE_SF_DIRECT=1 直连）
  · GeckoTerminal：主池（STONK/SOL）实时行情 + 买卖笔数、代币信息（持币人数 / 持仓分布 / 权限）、
    日线 90 天、含 STONK 的全部资金池
  · RugCheck：全市场流动性、资金池数量、转账税、风险标记、Top 持币、各池储备
  · 本站状态：sf-ledger.json（官方逐笔账本）、hourly.json（72 小时）、dashboard-data.json（榜单/市值）

诚实口径：
  · 拿不到的字段写 null，前端显示「—」；绝不用估算值冒充实测。
  · 持币人数变化、主池净流入这类「历史差」靠 work/stonk-page.json 自己采样积累，
    采样不足时前端明确写「记录中」。
"""
import datetime, json, os, sys, time
import urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import hourly as H  # noqa: E402  —— 复用官方接口中转 / GeckoTerminal 抓取 / 原子写
import wallet_flow as WF  # noqa: E402  —— 钱包分层净流入（v3.29，GT 成交采样 + 链上余额）

OUT = os.path.join(HERE, "stonk-page.json")
DD = os.path.join(HERE, "dashboard-data.json")
MINT = "6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx"
POOL = H.POOLS["stonk"][1]
GT = "https://api.geckoterminal.com/api/v2"
RUG = "https://api.rugcheck.xyz/v1/tokens/%s/report" % MINT
SNAP_KEEP = 400          # 采样滚动窗口（每小时一条 ≈ 16 天）
SF_BURNS_FEED = 12       # 最近销毁列表条数

DEX_NAMES = {
    "meteoraDlmm": "Meteora DLMM", "meteora_damm_v2": "Meteora DAMM v2",
    "meteora": "Meteora", "orca": "Orca", "raydium": "Raydium",
    "raydiumClmm": "Raydium CLMM", "raydiumCpmm": "Raydium CPMM",
    "pumpswap": "PumpSwap", "pumpfun": "pump.fun", "fluxbeam": "Fluxbeam",
    "lifinity": "Lifinity", "saber": "Saber", "mercurial": "Mercurial",
}


def fnum(v):
    """宽松转 float：None / 空串 / 非数字 → None（前端按「—」显示）。"""
    try:
        if v is None or v == "":
            return None
        x = float(v)
        return x if x == x else None          # NaN → None
    except Exception:
        return None


def sf_revenue_usd(day):
    """官网 Total revenue = revenueUsd + $STONK quote revenue（向后兼容旧 API）。"""
    total = fnum(day.get("totalRevenueUsd"))
    if total is not None:
        return total
    base = fnum(day.get("revenueUsd")) or 0
    quote = fnum(day.get("quoteRevenueUsd"))
    if quote is None:
        quote = fnum(day.get("stonkQuoteRevenueUsd"))
    return base + (quote or 0)


def jload(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def sf_daily_all():
    """官方日线全量（v3.29.20）：?limit=100 → 目前一次拿全 85 天（07-23 起）。

    坑：H._sf_get 走 translate.goog 会把 query 吃掉（只剩默认 25 天），所以这里用
    「保留 query」的中转拼法（同 _sf_ledger_urls），国内/海外都能拿全量。"""
    target = H.SF_DAILY_API + "?limit=100"
    u = urllib.parse.urlparse(target)
    q = urllib.parse.quote(target, safe="")
    tr = ("https://%s.translate.goog%s?" % (u.netloc.replace(".", "-"), u.path)
          + (u.query + "&" if u.query else "")
          + "_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en")
    urls = [tr,
            "https://api.cors.lol/?url=" + q,
            "https://r.jina.ai/" + target,
            "https://api.allorigins.win/raw?url=" + q,
            "https://api.codetabs.com/v1/proxy?quest=" + q]
    if os.environ.get("PONSPULSE_SF_DIRECT") == "1":
        urls.insert(0, target)          # 海外节点（GitHub Actions）直连最快最稳
    last = None
    for url in urls:
        for i in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                           "Accept": "application/json,text/plain,*/*",
                                                           "Connection": "close"})
                body = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
                j = H._sf_parse(body)
                days = (j or {}).get("days") if isinstance(j, dict) else None
                if days:
                    return days
                last = ValueError("bad payload: %s" % body[:80])
            except Exception as exc:
                last = exc; time.sleep(1.2 + i)
    print("warn: sf daily all: %s" % last, file=sys.stderr)
    return None


def safe_get(url, tries=2, label=""):
    try:
        return H.get(url, tries=tries)
    except Exception as exc:
        print("warn: %s: %s" % (label or url.split("?")[0], exc), file=sys.stderr)
        return None


def gt_get(url, label="", tries=3):
    """GeckoTerminal 专用：连续请求会被限流（HTTP 429），命中就多等一会儿再试。

    2026-10-08 实测：CI 里 hourly.py 刚跑完会吃掉这一分钟的大部分配额，
    本脚本的四次请求里最后那次（资金池列表）经常直接 429，等待时间太短会连败三次，
    页面上「资金池分布」就空了。这里把 429 的退避拉长（20s/30s/40s）。"""
    last = None
    for i in range(tries):
        try:
            return H.get(url, tries=1)
        except Exception as exc:
            last = exc
            msg = str(exc)
            wait = (20 + 10 * i) if "429" in msg else (5 + 4 * i)
            print("warn: %s attempt %d: %s（%ds 后重试）" % (label or url.split("?")[0], i + 1, msg, wait), file=sys.stderr)
            time.sleep(wait)
    return None


def parse_gt_pools(src):
    """把 GeckoTerminal 的代币池子列表裁成前端要的四个字段，按储备（流动性）从大到小。"""
    out = []
    for p in ((src or {}).get("data") or []):
        a = p.get("attributes") or {}
        rel = p.get("relationships") or {}
        dex = ((rel.get("dex") or {}).get("data") or {}).get("id") or ""
        liq = fnum(a.get("reserve_in_usd"))
        if liq is None:
            continue
        out.append({
            "name": (a.get("name") or "").strip(),
            "dex": DEX_NAMES.get(dex, dex or "—"),
            "liq": round(liq, 2),
            "vol": round(fnum((a.get("volume_usd") or {}).get("h24")) or 0, 2),
            "addr": a.get("address") or "",
        })
    out.sort(key=lambda x: x["liq"], reverse=True)
    return out


def parse_flywheel(sf_fly):
    """StonkFun 飞轮名单 → 前端精简结构；拿不到就 None（前端隐藏该板块）。

    字段口径（2026-10-11 实测 /api/flywheel）：
      roster[]: rank / symbol / name / imageUrl / quoteSymbol / marketCapUsd / weight(小数)
      totals:   totalValueUsd（名单代币总市值）/ buybackCount（累计回购笔数）/ targetCount
    """
    roster = []
    for r in (sf_fly.get("roster") or []):
        if not isinstance(r, dict) or not r.get("symbol"):
            continue
        try:
            rank = int(fnum(r.get("rank")) or len(roster) + 1)
        except Exception:
            rank = len(roster) + 1
        roster.append({
            "rank": rank,
            "sym": str(r.get("symbol")),
            "name": str(r.get("name") or r.get("symbol")),
            "img": r.get("imageUrl") or "",
            "quote": r.get("quoteSymbol") or "SOL",
            "mcap": fnum(r.get("marketCapUsd")),
            "weight": fnum(r.get("weight")),
        })
    if not roster:
        return None
    roster.sort(key=lambda x: x["rank"])
    totals = sf_fly.get("totals") or {}
    return {
        "enabled": bool(sf_fly.get("enabled", True)),
        "topCount": int(fnum(sf_fly.get("topCount")) or len(roster)),
        "sharePct": fnum(sf_fly.get("sharePct")),
        "roster": roster,
        "totalValueUsd": fnum(totals.get("totalValueUsd")),
        "buybackCount": int(fnum(totals.get("buybackCount")) or 0) or None,
        "targetCount": int(fnum(totals.get("targetCount")) or 0) or None,
        "pending": bool(sf_fly.get("marketDataPending")),
    }


def iso_ms(s):
    try:
        return H._iso_ms(s)
    except Exception:
        return None


# ---------------- 采样历史（自积累：持币人数 / 净流入 / 价格） ----------------
def load_snaps():
    st = jload(OUT, {}) or {}
    snaps = st.get("snaps")
    return snaps if isinstance(snaps, list) else []


def nearest_snap(snaps, ts_target, max_gap):
    """离 ts_target 最近、且误差 ≤ max_gap 秒的一条采样；没有就 None。"""
    best, bestd = None, None
    for s in snaps:
        d = abs((s.get("t") or 0) - ts_target)
        if bestd is None or d < bestd:
            best, bestd = s, d
    if best is None or bestd is None or bestd > max_gap:
        return None
    return best


def delta_pct(now_v, then_v):
    if now_v is None or then_v in (None, 0):
        return None
    try:
        return (now_v - then_v) / then_v
    except Exception:
        return None


def build_snaps(snaps, now, price, mcap, vol24, reserve, holders, main_base, main_quote_usd):
    cur = {"t": now, "price": price, "mcap": mcap, "vol24": vol24, "reserve": reserve,
           "holders": holders, "baseTok": main_base, "quoteUsd": main_quote_usd}
    if snaps and int((snaps[-1].get("t") or 0) // 3600) == int(now // 3600):
        snaps[-1] = cur                     # 同一小时更新末条，跨小时追加
    else:
        snaps.append(cur)
    snaps = snaps[-SNAP_KEEP:]
    return snaps


def snap_delta(snaps, now, key, seconds, tol):
    then = nearest_snap(snaps, now - seconds, tol)
    if not then or then.get(key) is None:
        return None
    now_v = snaps[-1].get(key) if snaps else None
    if now_v is None:
        return None
    return now_v - then[key]


# ---------------- 主流程 ----------------
def main():
    now = int(time.time())
    hourly = jload(os.path.join(HERE, "hourly.json"), {}) or {}
    dd = jload(DD, {}) or {}
    ms = ((hourly.get("milestone") or {}).get("stonk") or {})
    old_snaps = load_snaps()

    gt_pool = gt_get("%s/networks/solana/pools/%s?include=base_token,quote_token" % (GT, POOL), label="gt-pool") or {}
    time.sleep(1.2)
    gt_info = gt_get("%s/networks/solana/tokens/%s/info" % (GT, MINT), label="gt-info") or {}
    time.sleep(1.2)
    gt_day = gt_get("%s/networks/solana/pools/%s/ohlcv/day?limit=90&aggregate=1" % (GT, POOL), label="gt-day") or {}
    time.sleep(1.2)
    gt_pools = gt_get("%s/networks/solana/tokens/%s/pools?page=1" % (GT, MINT), label="gt-pools") or {}
    rug = safe_get(RUG, tries=1, label="rugcheck") or {}
    sf_tot = H._sf_get(H.SF_API) or {}
    sf_daily = H._sf_get(H.SF_DAILY_API) or {}
    sf_daily_all_days = sf_daily_all() or (sf_daily.get("days") or [])   # 全量 85 天（v3.29.20 90 天收入图用）
    sf_burns = H._sf_ledger_get(H.SF_BURNS_API) or {}
    sf_fly = H._sf_get(H.SF_FLY_API) or {}

    # ---- GeckoTerminal 主池 ----
    pa = ((gt_pool.get("data") or {}).get("attributes") or {})
    price = fnum(pa.get("base_token_price_usd"))
    mcap = fnum(pa.get("market_cap_usd")) or fnum(pa.get("fdv_usd"))
    fdv = fnum(pa.get("fdv_usd"))
    vol24 = fnum((pa.get("volume_usd") or {}).get("h24"))
    reserve = fnum(pa.get("reserve_in_usd"))
    chg = pa.get("price_change_percentage") or {}
    txw = pa.get("transactions") or {}
    tx24 = txw.get("h24") or {}
    buys, sells = fnum(tx24.get("buys")), fnum(tx24.get("sells"))
    buyers, sellers = fnum(tx24.get("buyers")), fnum(tx24.get("sellers"))

    # ---- 代币信息：持币人数 / 分布 / 权限 ----
    ia = ((gt_info.get("data") or {}).get("attributes") or {})
    hd = ia.get("holders") or {}
    holders = fnum(hd.get("count"))
    dist = hd.get("distribution_percentage") or {}
    mint_auth = ia.get("mint_authority")
    freeze_auth = ia.get("freeze_authority")

    # ---- RugCheck：流动性 / 资金池 / 税 / 风险 ----
    rug_liq = fnum(rug.get("totalMarketLiquidity"))
    rug_markets = rug.get("markets") or []
    rug_tok = rug.get("token") or {}
    tfee = ((rug.get("transferFee") or {}).get("pct"))
    top_holders = rug.get("topHolders") or []
    try:
        top10_pct = sum(sorted([fnum(h.get("pct")) or 0 for h in top_holders], reverse=True)[:10])
    except Exception:
        top10_pct = None

    def mkt_usd(m):
        lp = m.get("lp") or {}
        return (fnum(lp.get("baseUSD")) or 0) + (fnum(lp.get("quoteUSD")) or 0)

    mk_sorted = sorted(rug_markets, key=mkt_usd, reverse=True)
    main_mkt = mk_sorted[0] if mk_sorted else {}
    main_lp = main_mkt.get("lp") or {}
    if main_lp.get("baseMint") == MINT:
        main_base, main_quote_usd = fnum(main_lp.get("base")), fnum(main_lp.get("quoteUSD"))
    else:
        main_base, main_quote_usd = fnum(main_lp.get("quote")), fnum(main_lp.get("baseUSD"))

    # ---- StonkFun 官方累计 ----
    tot = (sf_tot or {}).get("totals") or {}
    split = (sf_tot or {}).get("platformTokenSplit") or {}
    supply0 = fnum(ms.get("supply")) or float(H.STONK_SUPPLY)
    burned_tot = fnum(tot.get("stonkBurnedTokens")) or fnum(ms.get("burned"))
    burned_usd_now = fnum(tot.get("stonkBurnedCurrentUsd"))
    burn_pct = (burned_tot / supply0) if (burned_tot and supply0) else None
    circ = (supply0 - burned_tot) if (burned_tot and supply0) else None

    # ---- 最近销毁（带签名，前端可跳 Solscan） ----
    burns_feed = []
    for r in (sf_burns.get("rows") or [])[:SF_BURNS_FEED]:
        if r.get("mint") != MINT:
            continue
        t = iso_ms(r.get("createdAt"))
        tok = fnum(r.get("amountTokens"))
        if not t or not tok:
            continue
        burns_feed.append({"t": t, "tok": round(tok, 4), "usd": round(fnum(r.get("valueUsd")) or 0, 2),
                           "sig": r.get("signature") or ""})

    # ---- 官方日线（30 天：收入 / 买回 / 销毁） ----
    days = [d for d in (sf_daily.get("days") or []) if isinstance(d, dict) and d.get("date")]
    days.sort(key=lambda d: d["date"])
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    days = [d for d in days if d["date"] < today][-30:]
    dly = {
        "dates": [d["date"][5:] for d in days],
        "rev": [round(sf_revenue_usd(d), 2) for d in days],
        "buyback": [round(fnum(d.get("buybackUsd")) or 0, 2) for d in days],
        "burn": [round(fnum(d.get("stonkBurnedTokens")) or 0, 2) for d in days],
        "count": [int(fnum(d.get("buybackCount")) or 0) for d in days],
        "bought": [round(fnum(d.get("boughtTokens")) or 0, 4) for d in days],
    }

    # ---- 官方日线全量（v3.29.20）：90 天收入柱状图（只取完整日，不含未过完的今天） ----
    fa = [d for d in (sf_daily_all_days or []) if isinstance(d, dict) and d.get("date")]
    fa.sort(key=lambda d: d["date"])
    fa = [d for d in fa if d["date"] < today][-90:]
    rv90 = []
    for d in fa:
        v90 = sf_revenue_usd(d)
        rv90.append(round(v90, 2) if v90 is not None else None)
    rev90 = {"dates": [d["date"] for d in fa], "rev": rv90}
    rev90["n"] = len(rev90["rev"])
    if rev90["rev"]:
        vals = [v for v in rev90["rev"] if v is not None]
        tot90 = sum(vals) if vals else None
        mx90 = max(vals) if vals else None
        rev90["sum"] = round(tot90, 2) if tot90 is not None else None
        rev90["avg"] = round(tot90 / len(vals), 2) if (tot90 is not None and vals) else None
        rev90["max"] = round(mx90, 2) if mx90 is not None else None
        rev90["maxDate"] = rev90["dates"][rev90["rev"].index(mx90)] if mx90 is not None else None

    def avg(seq):
        seq = [x for x in seq if x is not None]
        return (sum(seq) / len(seq)) if seq else None

    rev7 = avg(dly["rev"][-7:])
    rev7p = avg(dly["rev"][-14:-7])
    chg7 = ((rev7 - rev7p) / rev7p) if (rev7 and rev7p) else None
    bb7 = sum(dly["buyback"][-7:]) if dly["buyback"] else None
    bb_day = (bb7 / 7) if bb7 else None
    bought7 = sum(dly["bought"][-7:]) if dly["bought"] else None
    avg_px7 = (bb7 / bought7) if (bb7 and bought7) else None
    burn7 = sum(dly["burn"][-7:]) if dly["burn"] else None
    burn_day = (burn7 / 7) if burn7 else None
    burn_vel = ((burn_day / supply0) * 100) if (burn_day and supply0) else None
    buyback_share = fnum(tot.get("buybackShare")) or ((hourly.get("stonk") or {}).get("ledger") or {}).get("ratio") or 0.6

    # ---- 资金池：GT 列表（按储备排序）+ RugCheck 兜底 ----
    pools = parse_gt_pools(gt_pools)
    if not pools:
        print("warn: 资金池列表为空（多半是 GT 限流），等 25 秒单独再要一次", file=sys.stderr)
        time.sleep(25)
        gt_pools = gt_get("%s/networks/solana/tokens/%s/pools?page=1" % (GT, MINT), label="gt-pools-retry", tries=3) or {}
        pools = parse_gt_pools(gt_pools)
    stonk_quoted = [p for p in pools if p["name"].upper().endswith("/ STONK")]

    # ---- 价格历史（90 天，日线收盘） ----
    ph = []
    for row in (((gt_day.get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []):
        try:
            ph.append([int(row[0]), float(row[4])])
        except Exception:
            continue
    ph.sort(key=lambda x: x[0])

    # ---- 采样增量（持币人数变化 / 主池净流入） ----
    snaps = build_snaps(list(old_snaps), now, price, mcap, vol24, reserve, holders, main_base, main_quote_usd)
    h1 = snap_delta(snaps, now, "holders", 3600, 2400)
    h24 = snap_delta(snaps, now, "holders", 86400, 14400)
    h7d = snap_delta(snaps, now, "holders", 7 * 86400, 43200)
    span_h = round((snaps[-1]["t"] - snaps[0]["t"]) / 3600.0, 1) if len(snaps) > 1 else 0
    net24 = None
    if span_h >= 12:
        tol = 14400 if span_h >= 24 else 3600 * (span_h / 2 - 0.5)
        base_then = nearest_snap(snaps, now - 86400, max(tol, 3600))
        if base_then and base_then.get("baseTok") and main_base and price:
            net24 = (base_then["baseTok"] - main_base) * price     # 储备下降 = 净买入

    # ---- 评分卡：每条都是「数值 + 阈值」，页面上一目了然 ----
    def score_item(key, status, value, thresh):
        return {"k": key, "s": status, "v": value, "t": thresh}

    buyback_24h = dly["buyback"][-1] if dly["buyback"] else None
    burn_24h = dly["burn"][-1] if dly["burn"] else None
    vs_vol = (bb_day / vol24) if (bb_day and vol24) else None
    sf_px = fnum((dd.get("market") or {}).get("stonkfun", {}).get("price")) if isinstance(dd.get("market"), dict) else None
    # v3.27.1 全站一个价：本页优先用总览页同源的官方价（取不到才退回 GT 主池价），市值也跟着
    # 用同一个价重算 —— 深度页与总览页显示的价格/市值永远一致（以前一个走官方一个走池子，能差 3%）。
    px_use = sf_px or price
    mcap_use = (px_use * circ) if (px_use and circ) else mcap
    depth_ratio = (reserve / mcap_use) if (reserve and mcap_use) else None
    liq_ratio = (rug_liq / mcap_use) if (rug_liq and mcap_use) else None
    buy_share = (buys / (buys + sells)) if (buys is not None and sells is not None and (buys + sells) > 0) else None
    ps7 = (mcap_use / (rev7 * 365)) if (mcap_use and rev7) else None
    px_ratio = (px_use / avg_px7) if (px_use and avg_px7) else None
    rug_ok = bool(rug)
    mint_rev = (mint_auth == "no") or (rug_ok and rug.get("mintAuthority") is None)
    freeze_rev = (freeze_auth == "no") or (rug_ok and rug.get("freezeAuthority") is None)
    cap_ok = bool(mint_rev and freeze_rev) or (rug_ok and (mint_auth is None) and (freeze_auth is None))

    items = [
        score_item("buybackAlive", "good" if (buyback_24h or 0) > 0 else "risk", buyback_24h, "> 0"),
        score_item("burnAlive", "good" if (burn_24h or 0) > 0 else "risk", burn_24h, "> 0"),
        score_item("buybackForce", ("good" if (vs_vol or 0) >= 0.10 else "neu" if (vs_vol or 0) >= 0.05 else "risk"), vs_vol, "≥ 10%"),
        score_item("revTrend", ("good" if (chg7 or 0) > 0.02 else "neu" if (chg7 or 0) > -0.25 else "risk"), chg7, "> -25%"),
        score_item("burnSpeed", ("good" if (burn_vel or 0) >= 0.10 else "neu" if (burn_vel or 0) >= 0.05 else "risk"), burn_vel, "≥ 0.10%/天"),
        score_item("valuation", ("good" if (ps7 or 99) < 1.5 else "neu" if (ps7 or 99) < 4 else "risk"), ps7, "< 1.5x"),
        score_item("depth", ("good" if (depth_ratio or 0) >= 0.015 else "neu" if (depth_ratio or 0) >= 0.008 else "risk"), depth_ratio, "≥ 1.5%"),
        score_item("buyShare", ("good" if (buy_share or 0) >= 0.55 else "neu" if (buy_share or 0) >= 0.45 else "risk"), buy_share, "≥ 55%"),
        score_item("holders", ("good" if (h24 or 0) > 0 else "neu" if h24 is None else "risk"), h24, "> 0"),
        score_item("security", "good" if (mint_rev and freeze_rev) else ("risk" if rug_ok or mint_auth is not None else "na"), None, "无增发 / 无冻结"),
        score_item("liquidity", ("good" if (liq_ratio or 0) >= 0.02 else "neu" if (liq_ratio or 0) >= 0.01 else "risk"), liq_ratio, "≥ 2%"),
        score_item("netflow", ("na" if net24 is None else "good" if net24 > 0 else "risk"), net24, "> 0"),
    ]
    tally = {"bull": sum(1 for i in items if i["s"] == "good"),
             "neu": sum(1 for i in items if i["s"] == "neu"),
             "risk": sum(1 for i in items if i["s"] == "risk"),
             "na": sum(1 for i in items if i["s"] == "na")}

    # ---- 钱包分层净流入（v3.29）：本站采样，账本文件滚动攒 24h ----
    pool_addrs = [p.get("addr") for p in sorted(pools, key=lambda x: x.get("vol") or 0, reverse=True)
                  if p.get("addr")]
    wf = None
    try:
        # 成本线折算用的小时收盘价（v3.29.29）：直接复用 hourly.json（hourly.py 刚写过，
        # 与 _fetch_px_hist 同源同口径：GT ohlcv/hour 的 close，按整点分桶），不再额外发
        # GT 请求 —— CI 里本脚本紧跟 hourly.py 之后跑，再补一次请求会被 429 限流，
        # 成本线整块变空（v3.29.28 线上实测）；hourly.json 缺失时才退回联网兜底。
        px_hist = []
        for _t, _p in zip(hourly.get("hours") or [], ((hourly.get("stonk") or {}).get("close") or [])):
            try:
                if _t and _p:
                    px_hist.append((int(_t) // 3600 * 3600, float(_p)))
            except Exception:
                pass
        wf = WF.sample(pool_addrs, px_use, px_hist=(px_hist or None))
    except Exception as exc:
        print("warn: wallet-flow: %s" % (exc,), file=sys.stderr)

    payload = {
        "generated": now,
        "hero": {
            "price": px_use, "chg24": fnum(chg.get("h24")), "chg1h": fnum(chg.get("h1")),
            "mcap": mcap_use, "fdv": fdv, "vol24": vol24, "reserve": reserve,
            "holders": int(holders) if holders else None,
            "burnPct": burn_pct, "burnedTok": burned_tot, "burnedUsdNow": burned_usd_now,
            "lastBurn": burns_feed[0] if burns_feed else None,
            "sfPrice": sf_px, "gtPrice": price, "btcPair": None,
        },
        "supply": {
            "initial": supply0, "burned": burned_tot, "circ": circ,
            "buybackBurned": fnum(tot.get("buybackBurnTokens")),
            "quoteBurn": fnum(tot.get("quoteRevenueBurnTokens")),
            "feeBurnUsd": fnum(tot.get("feeBurnUsd")),
            "buybackCount": int(fnum(tot.get("buybackCount")) or 0) or None,
            "lastBuybackAt": tot.get("lastBuybackAt"),
            "burnedUsdAtBurn": fnum(tot.get("stonkBurnedUsd")),
            "burnedUsdNow": burned_usd_now,
        },
        "burns": burns_feed,
        "flywheel": {
            "rev90": rev90,
            "dates": dly["dates"], "rev": dly["rev"], "buyback": dly["buyback"], "burnTok": dly["burn"],
            "count": dly["count"],
            "rev7": rev7, "rev7prev": rev7p, "chg7": chg7,
            "buyback7": bb7, "buybackDay": bb_day, "bought7": bought7, "avgPx7": avg_px7,
            "burn7": burn7, "burnDay": burn_day, "burnVel": burn_vel,
            "share": buyback_share, "vsVol": vs_vol, "pxRatio": px_ratio,
            "hourly": {
                "hours": (hourly.get("hours") or []),
                "rev": ((hourly.get("stonk") or {}).get("rev") or []),
                "burn": ((hourly.get("stonk") or {}).get("burn") or []),
                "vol": ((hourly.get("stonk") or {}).get("vol") or []),
            },
        },
        "demand": {
            "buys": int(buys) if buys else None, "sells": int(sells) if sells else None,
            "buyers": int(buyers) if buyers else None, "sellers": int(sellers) if sellers else None,
            "buyShare": buy_share, "turnover": (vol24 / mcap) if (vol24 and mcap) else None,
            "pools": pools[:6], "poolCount": len(pools) or len(rug_markets),
            "stonkQuoted": stonk_quoted[:5],
            "holders": {
                "count": int(holders) if holders else None,
                "top10": fnum(dist.get("top_10")), "top11_20": fnum(dist.get("11_20")),
                "top21_40": fnum(dist.get("21_40")), "rest": fnum(dist.get("rest")),
                "top10_rug": round(top10_pct, 2) if top10_pct else None,
                "updated": hd.get("last_updated"),
                "d1h": h1, "d24h": h24, "d7d": h7d,
            },
            "liquidity": {"total": rug_liq, "pools": len(rug_markets) or None,
                          "topShare": (mkt_usd(main_mkt) / rug_liq) if (rug_liq and main_mkt) else None,
                          "providers": rug.get("totalLPProviders")},
            "net24h": net24, "snapHours": span_h, "snapN": len(snaps),
            "createdAt": pa.get("pool_created_at"),
        },
        "value": {
            "ps7": ps7, "annRev": (rev7 * 365) if rev7 else None, "mcap": mcap_use,
            "rank": (dd.get("leaderboard") or {}).get("board", {}).get("total24h", {}).get("rank", {}) if isinstance(dd.get("leaderboard"), dict) else {},
            "rankNear": (((dd.get("leaderboard") or {}).get("board") or {}).get("total24h") or {}).get("near", {}) if isinstance(dd.get("leaderboard"), dict) else {},
            "rankUpdated": (dd.get("leaderboard") or {}).get("updated") if isinstance(dd.get("leaderboard"), dict) else None,
            "platform": {
                "volTotal": fnum(tot.get("estimatedVolumeUsd")), "revTotal": fnum(tot.get("totalRevenueUsd")),
                "buybackTotal": fnum(tot.get("totalBuybackUsd")), "launches": int(fnum(split.get("launchCount")) or 0) or None,
                "feeRate": fnum(tot.get("platformFeeRate")), "since": split.get("startedAt"),
            },
            "share": ((hourly.get("share") or {}).get("stonk") or None),
        },
        "score": {"items": items, "tally": tally},
        "model": {"price": px_use, "supply": supply0, "circ": circ,
                  "quoteDepth": main_quote_usd, "rev7": rev7, "share": buyback_share,
                  "poolName": (pa.get("name") or "STONK / SOL")},
        "safety": {
            "mintRevoked": mint_rev,
            "freezeRevoked": freeze_rev,
            "taxPct": tfee, "rugged": bool(rug.get("rugged")),
            "risks": len(rug.get("risks") or []),
        },
        "priceHist": ph,
        "snaps": snaps,
        "flywheelRank": parse_flywheel(sf_fly),
        "walletFlow": wf,
        "srcNote": "StonkFun 官方 API + GeckoTerminal + RugCheck + DefiLlama",
    }

    H.atomic_dump(payload, OUT)
    dd["stonkPage"] = payload
    H.atomic_dump(dd, DD)
    print("stonk-page: price=%s (gt=%s) mcap=%s burned=%s holders=%s pools=%s bulls=%s/%s snaps=%s rev90=%s" % (
        px_use, price, mcap_use, burned_tot, holders, len(pools), tally["bull"], len(items), len(snaps), rev90["n"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
