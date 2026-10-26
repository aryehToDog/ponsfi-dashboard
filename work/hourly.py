#!/usr/bin/env python3
"""小时级监控数据（最近 72 小时）→ work/hourly.json

数据源（全部公开、无需 key）：
  1. 交易量（每小时）→ GeckoTerminal OHLCV hour（真小时线，允许跨域，浏览器也能直连）
       PONS  → robinhood / 0xed50bdee… (PONS/WETH)
       STONK → solana    / zxTpi4Bt…   (STONK/SOL)
  2. 销毁（每小时）→ Robinhood Chain eth_getLogs 筛 Transfer→0x…dEaD，按小时分桶（真链上）
       STONK → StonkFun 官方逐笔销毁流水按小时归类（v3.26 起，精确到每一笔）；
       账本没盖到的小时退回官方累计值差值、再退 burn-history 快照
  3. 收入（每小时）→ Pons 给一列「链上推算」＝ 小时回购支出 × 校准比率（v3.29.15 起弃用
       固定 ÷0.8；v3.29.16 起逐日校准：历史日各取当天官方日线「收入÷回购」，当天取
       「当天官方部分值÷当天链上回购」并以最近 3 日加权比率的 [0.5×, 2.5×] 夹住），
       明确标注为推算；
       StonkFun → 官方逐笔买回流水按小时归类后 ÷ 官方比例（约 60%，按最近 3 个完整日自动校准）
       （流水接口 stonkfun.xyz/api/v2/revenue/buybacks|burns；国内直连被墙、走海外中转）
  4. 销毁里程碑（v3.15）→ burn-history 快照 + sf-history 累计值：算「已烧掉多少、按最近
       24h 速度还要几天过下一个 1%」，产出 hourly.json → milestone（前端「销毁里程碑」板块）
"""
import datetime, json, os, sys, tempfile, time, urllib.request, urllib.parse

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
# PONS 小时收入换算比率 = 收入 ÷ 回购（DefiLlama 口径，按最近 3 个完整日自动校准）。
# 旧口径「80% 收入用于回购」自 2026-10-09 起失效：回购动用金库，链上回购额已达收入 4~5 倍。
PONS_RATIO_FALLBACK = 0.25   # 校准取不到时的兜底（回退顺序：DL 日线 → 旧 hourly.json → 此值）
PONS_RATIO_BAND = (0.05, 1.5)
DL_FEES_API = "https://api.llama.fi/summary/fees/%s?dataType=%s"
# STONK 官方原始供应（不是整 10 亿；同 buyback.py 的 STONK_INITIAL，2026-10-06 对账修正）
STONK_SUPPLY = 999_969_797.91
SF_API = "https://www.stonkfun.xyz/api/revenue"   # StonkFun 官方收入/回购/销毁（国内被墙，走海外中转）
SF_DAILY_API = "https://www.stonkfun.xyz/api/v2/revenue/daily"   # 官方日线（v3.18 起用于日度对账）
SF_HIST = os.path.join(HERE, "sf-history.json")    # 官方累计值快照（每小时一条）
SF_LEDGER = os.path.join(HERE, "sf-ledger.json")    # 官方逐笔流水账本（买回 / 销毁），滚动保留 ~110h
SF_BUYBACKS_API = "https://www.stonkfun.xyz/api/v2/revenue/buybacks?limit=100"
SF_BURNS_API = "https://www.stonkfun.xyz/api/v2/revenue/burns?limit=100"
SF_FLY_API = "https://www.stonkfun.xyz/api/flywheel"   # 飞轮名单（平台代币 Top10 市值权重，v3.29）
SF_RATIO_FALLBACK = 0.5976     # 官方历史实测「买回 ÷ 收入」比例（2026-10-08）；每次构建用最近 3 个完整日自动校准
SF_LEDGER_KEEP_H = 110         # 账本滚动窗口：72h 图 + 回填余量


def atomic_dump(obj, path):
    """先写同目录临时文件再 os.replace：中途被杀不会留下半个 JSON"""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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


def _sf_relays(target):
    """海外中转线路（按实测可用性排序）。

    translate.goog 是 2026-10-06 复测最稳的一条（官方站点 Vercel + 国内直连被墙），
    其余是历史备胎：cors.lol 会限流、allorigins/codetabs 经常 5xx、jina 偶尔超时。
    """
    q = urllib.parse.quote(target, safe="")
    path = urllib.parse.urlparse(target).path
    return [
        "https://www-stonkfun-xyz.translate.goog" + path
        + "?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en",
        "https://api.cors.lol/?url=" + q,
        "https://r.jina.ai/" + target,
        "https://api.allorigins.win/raw?url=" + q,
        "https://api.codetabs.com/v1/proxy?quest=" + q,
    ]


def _sf_get(target):
    """经海外中转 GET 官方接口 → 解析后的 JSON；全部线路失败返回 None。

    PONSPULSE_SF_DIRECT=1 时先直连一次：海外节点（GitHub Actions）直连更快更稳，
    国内（本机）不设这个变量，行为与以前完全一致。
    """
    last = None
    urls = list(_sf_relays(target))
    if os.environ.get("PONSPULSE_SF_DIRECT") == "1":
        urls.insert(0, target)
    for url in urls:
        for i in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                           "Accept": "application/json,text/plain,*/*",
                                                           "Connection": "close"})
                body = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
                return _sf_parse(body)
            except Exception as exc:
                last = exc; time.sleep(1.5 + i)
    print("warn: sf api %s: %s" % (target, last), file=sys.stderr)
    return None


# ---- 官方逐笔流水账本（v3.26）：买回 / 销毁都带时间戳，按小时精确归类 ----
def _iso_ms(s):
    dt = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp() * 1000)


def _sf_ledger_urls(target):
    """流水接口的中转线路（和 _sf_relays 同序；这里保留 query —— cursor 翻页必须带参）。"""
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
    return urls


def _sf_ledger_get(target):
    """流水接口 → dict（rows/page）；所有线路都失败返回 None（这轮先不抓，下次再试）。"""
    last = None
    for url in _sf_ledger_urls(target):
        for i in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                           "Accept": "application/json,text/plain,*/*",
                                                           "Connection": "close"})
                body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
                j = _sf_parse(body)
                if isinstance(j, dict) and isinstance(j.get("rows"), list):
                    return j
                last = ValueError("bad payload: %s" % body[:80])
            except Exception as exc:
                last = exc; time.sleep(1.0 + i)
    print("warn: sf ledger %s: %s" % (target.split("?")[0], last), file=sys.stderr)
    return None


def _sf_ledger_load():
    try:
        st = json.load(open(SF_LEDGER, encoding="utf-8"))
        return st if isinstance(st, dict) else {}
    except Exception:
        return {}


def _cov_merge(cov):
    """覆盖区间合并（重叠或 1 秒内相邻视为连续）→ 升序 [[a,b],…]。"""
    out = []
    for a, b in sorted(cov):
        if out and a <= out[-1][1] + 1000:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _parse_buyback(r):
    try:
        ts = _iso_ms(r.get("createdAt"))
        usd = float(r.get("spentValueUsd") or 0)
        if ts <= 0 or usd <= 0:
            return None
        return [ts, round(usd, 6)]
    except Exception:
        return None


def _parse_burn(r):
    try:
        ts = _iso_ms(r.get("createdAt"))
        tok = float(r.get("amountTokens") or 0)
        if ts <= 0 or tok <= 0:
            return None
        return [ts, round(tok, 6)]
    except Exception:
        return None


def _sf_ledger_sync_stream(node, base, parse_row, budget, now_ms):
    """单条流水（买回 / 销毁）增量同步。

    策略（每轮构建跑一次）：
      · 从最新一页往回拉，接到「账本里已有最新一条」为止 —— 补上最近这小时的流水；
      · 账本还不够老（没盖满滚动窗口）时，顺着 pend 续点往更早翻，每轮最多 budget 页；
      · 翻过的连续区间记进 cov：区间盖住的小时，没流水就是真 0（不是没采到）。
    接口按游标严格降序翻页，连续翻页 = 连续覆盖，中间不会丢记录。
    """
    rows = node.setdefault("rows", [])          # [[ts_ms, 数值], …] 降序
    cov = node.setdefault("cov", [])
    pend = node.get("pend")
    pre_max = rows[0][0] if rows else None
    horizon = now_ms - SF_LEDGER_KEEP_H * 3600 * 1000
    phase = "top" if rows else "deep"           # 首次（账本空）：直接当回填，一直往回挖
    new, pages, fresh_top, net_fail = [], 0, False, False
    cur = None
    while pages < budget:
        url = base + (("&cursor=" + urllib.parse.quote(cur, safe="")) if cur else "")
        j = _sf_ledger_get(url)
        if j is None:
            net_fail = True
            break
        pages += 1
        if cur is None:
            fresh_top = True
        rs = [p for p in (parse_row(r) for r in (j.get("rows") or [])) if p]
        new.extend(rs)
        lo = min((r[0] for r in rs), default=None)
        nxt = (j.get("page") or {}).get("nextCursor") or None
        if nxt is None:                         # 翻到官方流水最早的一页：没有更早的了
            cur = None
            break
        if phase == "top" and pre_max is not None and lo is not None and lo <= pre_max:
            if pend:                            # 顶部接上 → 转去补更早的欠账
                phase, cur = "deep", pend
            else:
                cur = None
                break
        elif phase == "deep" and lo is not None and lo <= horizon:
            cur = None
            break                               # 已挖到滚动窗口之外 → 回填完成
        else:
            cur = nxt
        if pages < budget:
            time.sleep(0.3)
    if net_fail:
        pass                                    # 网络失败：pend 原样保留，下次继续
    elif phase == "top":
        if node.get("pend") is None and cur is not None:
            node["pend"] = cur                  # 顶部没接上（极少见）：下次优先补
    elif phase == "deep":
        node["pend"] = cur                      # None=回填完成；否则下次接着翻
    else:
        node["pend"] = None
    if new:
        na = min(r[0] for r in new)
        nb = max(r[0] for r in new)
        if fresh_top:
            nb = max(nb, now_ms)                # 从最新一页开始拉的 → 截至抓取时刻没有遗漏
        rows.extend(new)
        rows.sort(key=lambda r: r[0], reverse=True)
        seen, dedup = set(), []
        for r in rows:
            k = (r[0], r[1])
            if k in seen:
                continue
            seen.add(k)
            dedup.append(r)
        cut = now_ms - SF_LEDGER_KEEP_H * 3600 * 1000
        node["rows"] = [r for r in dedup if r[0] >= cut]
        node["cov"] = _cov_merge([[max(a, cut), b] for a, b in cov + [[na, nb]] if b >= cut])
    return pages, net_fail


def sf_ledger_sync(max_pages=None):
    """同步官方逐笔流水账本（买回 + 销毁）→ sf-ledger.json；返回存量摘要（调试/回填也用）。"""
    budget = int(max_pages or os.environ.get("PONSPULSE_LEDGER_MAX_PAGES") or 10)
    now_ms = int(time.time() * 1000)
    st = _sf_ledger_load()
    st["v"] = 1
    r1 = _sf_ledger_sync_stream(st.setdefault("buy", {"rows": [], "cov": [], "pend": None}),
                                SF_BUYBACKS_API, _parse_buyback, budget, now_ms)
    r2 = _sf_ledger_sync_stream(st.setdefault("burn", {"rows": [], "cov": [], "pend": None}),
                                SF_BURNS_API, _parse_burn, budget, now_ms)
    st["synced"] = int(time.time())
    atomic_dump(st, SF_LEDGER)
    return {"pages": r1[0] + r2[0], "failed": bool(r1[1] or r2[1]),
            "buy": len(st["buy"].get("rows") or []), "burn": len(st["burn"].get("rows") or []),
            "covBuy": st["buy"].get("cov") or [], "covBurn": st["burn"].get("cov") or []}


def _led_covers(cov, hs_ms, he_ms, now_ms):
    """该小时是否完整落在账本覆盖区间里（正在进行的最后一个小时按「到目前为止」算）。"""
    for a, b in cov:
        if a <= hs_ms and (b >= he_ms or (now_ms < he_ms and b >= hs_ms)):
            return True
    return False


def sf_ledger_hours(buckets, ratio):
    """账本 → 每小时序列 (收入USD[], 销毁STONK[])；覆盖不到的记 None（前端「未采样」）。

    · 收入：官方买回流水 ÷ ratio（官方「买回 ÷ 收入」比例，约 60%，每次构建按最近 3 个完整日校准）
    · 销毁：官方销毁流水逐笔求和（和平台自己页面同一个数据源）
    · 覆盖到的小时：有流水＝精确求和，没流水＝真 0；覆盖不到＝None（不猜、不摊、不回填）
    """
    st = _sf_ledger_load()
    now_ms = int(time.time() * 1000)
    buy_h, burn_h = {}, {}
    for r in (st.get("buy", {}).get("rows") or []):
        h = r[0] // 3600000
        buy_h[h] = (buy_h.get(h) or 0.0) + float(r[1])
    for r in (st.get("burn", {}).get("rows") or []):
        h = r[0] // 3600000
        burn_h[h] = (burn_h.get(h) or 0.0) + float(r[1])
    rev, burn = [], []
    for b in buckets:
        hs, he = b * 1000, (b + 3600) * 1000
        key = hs // 3600000
        rev.append(round(buy_h.get(key, 0.0) / ratio, 2)
                   if _led_covers(st.get("buy", {}).get("cov") or [], hs, he, now_ms) else None)
        burn.append(round(burn_h.get(key, 0.0), 2)
                    if _led_covers(st.get("burn", {}).get("cov") or [], hs, he, now_ms) else None)
    return rev, burn


def sf_fetch():
    """返回官方 totals 快照 dict；失败返回 None（下一小时再试）。

    走过的坑：官方站点在 Vercel、国内直连被墙，中转本身也会抽风/限流；
    2026-10-06 起把实测最稳的 translate.goog 放第一位，其余线路兜底。
    """
    j = _sf_get(SF_API)
    if not j:
        return None
    t = j.get("totals") or {}
    if t.get("totalRevenueUsd") is None:
        print("warn: sf api: totals missing", file=sys.stderr)
        return None
    quote_rev = t.get("quoteRevenueUsd")
    if quote_rev is None:
        quote_rev = t.get("stonkQuoteRevenueUsd")
    if quote_rev is None:
        quote_rev = t.get("quoteTokenRevenueUsd")
    quote_rev_est = False
    if quote_rev is None:
        # Current /api/revenue exposes quoteRevenueBurnUsd, not gross quoteRevenueUsd.
        # Convert by the official share for intraday shape; complete UTC days are then
        # reconciled to the exact daily Total revenue endpoint below.
        try:
            quote_burn = float(t.get("quoteRevenueBurnUsd"))
            share = float(t.get("buybackShare"))
        except (TypeError, ValueError):
            quote_burn, share = None, None
        if quote_burn is not None and share is not None and share > 0:
            quote_rev = quote_burn / share
            quote_rev_est = True
    return {"ts": int(time.time()),
            "revUsd": float(t["totalRevenueUsd"]),
            "quoteRevUsd": float(quote_rev) if quote_rev is not None else None,
            "quoteRevEstimated": quote_rev_est,
            "buybackUsd": float(t.get("totalBuybackUsd") or 0),
            "buybackCount": int(t.get("buybackCount") or 0),
            "burnTokens": float(t.get("stonkBurnedTokens") or 0),
            "burnUsd": float(t.get("stonkBurnedUsd") or 0),
            "priceUsd": float(t.get("platformTokenPriceUsd") or 0)}


def sf_official_daily():
    """官方日线（/api/v2/revenue/daily）→ {日期: {rev, hold, burn}}（剔除今天：可能不满一天）。

    v3.18 新增：STONK 日度明细改读官方口径（与 stonkfun.xyz 一致），
    前端 build() 用它覆盖 DefiLlama 序列；官方断流时才退回 DefiLlama。
    """
    j = _sf_get(SF_DAILY_API)
    if not j or not isinstance(j.get("days"), list):
        return None
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    days = {}
    for r in j["days"]:
        d = (r.get("date") or "")[:10]
        if not d or d >= today:          # 今天不满一天，不混进来
            continue
        # 官网现将收入拆成基础收入 + $STONK 计价收入；看板收入列按两项相加
        # 对齐官网「Total revenue」。只有组件字段缺失时才退回总值旧字段。
        quote = (r.get("quoteRevenueUsd") if r.get("quoteRevenueUsd") is not None
                 else r.get("stonkQuoteRevenueUsd"))
        if quote is None:
            quote = r.get("quoteTokenRevenueUsd")
        base = float(r.get("revenueUsd") or 0)
        total = base + float(quote or 0)
        if r.get("revenueUsd") is None and r.get("totalRevenueUsd") is not None:
            total = float(r["totalRevenueUsd"])
        days[d] = {"rev": round(total, 2),
                   "baseRev": round(base, 2),
                   "quoteRev": round(float(quote or 0), 2),
                   "hold": round(float(r.get("buybackUsd") or 0), 2),
                   "burn": round(float(r.get("stonkBurnedTokens") or 0), 2)}
    if not days:
        return None
    return {"days": days, "generated": int(time.time())}


def sf_record(cur):
    """存快照：同一小时内更新末条，跨小时追加；只留最近 400 条。"""
    hist = sf_load_hist()
    if not hist or int(cur["ts"] // 3600) != int(int(hist[-1].get("ts") or 0) // 3600):
        hist.append(cur)
    else:
        hist[-1] = cur
    atomic_dump(hist[-400:], SF_HIST)


def sf_series(buckets):
    """官方累计值 → 每小时差值：(收入USD[], 销毁STONK[], 空, 空, 空)。

    只认「实测小时」：相邻两次采样的整点差 ≤1（同一小时、或紧挨的两个小时）时，
    这一跳的增量记在较早的那个整点；采样断档超过 1 个整点，中间小时**留空** ——
    不回填、不估算（2026-10-08 作者要求：均值回填 + 斜纹柱用户看不懂，宁缺毋假；
    采样密度由服务器兜底触发器保证：快照超时就用 workflow_dispatch 踢云端构建）。
    最后三个返回值是 v3.22 斜纹柱的标记位，保留占位、恒为空（前端已不再使用）。
    """
    hist = [h for h in sf_load_hist() if isinstance(h, dict) and h.get("ts")]
    hist.sort(key=lambda h: h["ts"])
    rev = {b: None for b in buckets}
    burn = {b: None for b in buckets}
    for a, b in zip(hist, hist[1:]):
        if b["ts"] - a["ts"] <= 0:
            continue
        ha = int(a["ts"] // 3600 * 3600)
        hb = int(b["ts"] // 3600 * 3600)
        if (hb - ha) // 3600 > 1:       # 断档：中间小时没有实测 → 留空，不回填
            continue
        if ha not in rev:
            continue
        # quote 累计字段缺一端时，收入这小时不完整，留空；销毁仍可独立使用。
        qa, qb = a.get("quoteRevUsd"), b.get("quoteRevUsd")
        dr = None
        if (qa is None) == (qb is None):
            dr = (b.get("revUsd") or 0) - (a.get("revUsd") or 0)
            if qa is not None:
                dr += qb - qa
        db = (b.get("burnTokens") or 0) - (a.get("burnTokens") or 0)
        if dr is not None and dr >= 0:
            rev[ha] = round((rev[ha] or 0) + dr, 2)
        if db >= 0:
            burn[ha] = round((burn[ha] or 0) + db, 2)
    return ([rev[b] for b in buckets], [burn[b] for b in buckets], [], [], [])


def align_sf_complete_days(rev, burn, buckets, official_days):
    """完整 UTC 日按官方 daily API 总额校准小时分布；只缩放已有快照值，不补空小时。"""
    if not official_days:
        return {"rev": [], "burn": []}
    indices = {}
    for i, ts in enumerate(buckets):
        day = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        indices.setdefault(day, []).append(i)
    aligned = {"rev": [], "burn": []}
    for day, ids in indices.items():
        target = official_days.get(day)
        if not isinstance(target, dict) or len(ids) != 24:
            continue
        for series, field in ((rev, "rev"), (burn, "burn")):
            values = [series[i] for i in ids]
            official = target.get(field)
            if (official is None or any(v is None for v in values)
                    or sum(values) <= 0):
                continue
            official = float(official)
            total = sum(values)
            # Preserve the observed hourly shape, but make the 24h sum equal the
            # official full-day value. This is an hourly allocation estimate.
            for i, value in zip(ids[:-1], values[:-1]):
                series[i] = round(value * official / total, 2)
            series[ids[-1]] = round(official - sum(series[i] for i in ids[:-1]), 2)
            aligned[field].append(day)
    return {key: sorted(set(value)) for key, value in aligned.items()}


def sf_daily():
    """官方累计值 → 按 UTC 自然日做差 = 官方口径的「日收入 / 日回购 / 日销毁」。

    只产出**完整天**：相邻两个取样点要分别落在各自日子的尾部（≥21:00 UTC），
    且两点间隔 22~26 小时 —— 半天的数据宁可不出，也不拿来冒充一整天
    （页面上「日度明细」里 DefiLlama 滞后那两天，就是这么被官方口径补上的）。

    注意：官方口径与 DefiLlama 的统计基准不同（实测 STONK 官方约为 DefiLlama 的 2 倍），
    所以这里**单独出一份**，前端并列标注，绝不混进同一条序列。
    """
    hist = [h for h in sf_load_hist() if isinstance(h, dict) and h.get("ts")]
    hist.sort(key=lambda h: h["ts"])
    if not hist:
        return None
    by_day = {}
    for h in hist:                      # 每天只留最晚的一条
        day = datetime.datetime.utcfromtimestamp(h["ts"]).strftime("%Y-%m-%d")
        if day not in by_day or h["ts"] > by_day[day]["ts"]:
            by_day[day] = h
    days = sorted(by_day)
    out = {"rev": {}, "hold": {}, "burn": {}, "hours": {},
           "snapshots": len(hist), "from": days[0] if days else None}
    for a, b in zip(days, days[1:]):
        ha, hb = by_day[a], by_day[b]
        gap = hb["ts"] - ha["ts"]
        if not (22 * 3600 <= gap <= 26 * 3600):
            continue
        ta = datetime.datetime.utcfromtimestamp(ha["ts"])
        tb = datetime.datetime.utcfromtimestamp(hb["ts"])
        if ta.hour < 21 or tb.hour < 21:
            continue
        dr = (hb.get("revUsd") or 0) - (ha.get("revUsd") or 0)
        if ha.get("quoteRevUsd") is not None and hb.get("quoteRevUsd") is not None:
            dr += hb["quoteRevUsd"] - ha["quoteRevUsd"]
        dh = (hb.get("buybackUsd") or 0) - (ha.get("buybackUsd") or 0)
        db = (hb.get("burnTokens") or 0) - (ha.get("burnTokens") or 0)
        if dr >= 0: out["rev"][b] = round(dr, 2)
        if dh >= 0: out["hold"][b] = round(dh, 2)
        if db >= 0: out["burn"][b] = round(db, 2)
        out["hours"][b] = round(gap / 3600, 1)
        out["last"] = max(out["rev"]) if out["rev"] else None
        return out


# ---- 市场占有率（DefiLlama DEX 口径：分子＝协议成交量、分母＝所在链全部 DEX 成交量）----
SHARE_SUM = "https://api.llama.fi/summary/dexs/%s?dataType=dailyVolume"
SHARE_CHAIN = "https://api.llama.fi/overview/dexs/%s?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true"


def _chart_map(chart):
    out = {}
    for row in chart or []:
        try:
            ts, v = int(row[0]), float(row[1])
        except Exception:
            continue
        if v >= 0:
            out[ts] = v
    return out


def _rank_in(protocols, slugs):
    """在链协议列表里按 24h 成交量排名 → (名次, 协议总数)；找不到给 (None, 总数)"""
    arr = sorted(protocols or [], key=lambda p: -(p.get("total24h") or 0))
    for i, p in enumerate(arr):
        if p.get("slug") in slugs:
            return i + 1, len(arr)
    return None, len(arr)


def _share_hist(a, b, days=14):
    """两条日线相除 → 最近 N 天的占比序列 [[ts, share], ...]（缺的天自动跳过）"""
    am, bm = _chart_map(a.get("totalDataChart")), _chart_map(b.get("totalDataChart"))
    keys = sorted(set(am) & set(bm))[-days:]
    return [[k, round(am[k] / bm[k], 6) if bm[k] else None] for k in keys]


def market_share():
    """PONS÷Robinhood Chain、STONK÷Solana 的 24h 成交量份额；STONK 另附与 pump.fun 的对比。

    全部取 DefiLlama 的 DEX 口径（同源同尺）：占比＝本品成交量 ÷ 该链全部 DEX 成交量。
    另给链内名次（这一列排第几）和最近 14 天占比走势（日线）。
    """
    pons = get(SHARE_SUM % "pons")
    stonk = get(SHARE_SUM % "stonkfun")
    pump = get(SHARE_SUM % "pump.fun")
    rh = get(SHARE_CHAIN % urllib.parse.quote("Robinhood Chain"))
    sol = get(SHARE_CHAIN % "solana")
    pv, sv, uv = (float(x.get("total24h") or 0) for x in (pons, stonk, pump))
    rv, ov = float(rh.get("total24h") or 0), float(sol.get("total24h") or 0)
    pr, prn = _rank_in(rh.get("protocols"), {"pons-v2", "pons"})
    sr, srn = _rank_in(sol.get("protocols"), {"stonkfun"})
    ur, urn = _rank_in(sol.get("protocols"), {"pump.fun"})
    return {
        "generated": int(time.time()),
        "src": "DefiLlama · DEX volume",
        "pons": {"chain": "Robinhood Chain", "vol24h": round(pv, 2),
                 "chainVol24h": round(rv, 2), "share": round(pv / rv, 6) if rv else None,
                 "rank": pr, "total": prn, "hist": _share_hist(pons, rh)},
        "stonk": {"chain": "Solana", "vol24h": round(sv, 2),
                  "chainVol24h": round(ov, 2), "share": round(sv / ov, 6) if ov else None,
                  "rank": sr, "total": srn,
                  "pumpVol24h": round(uv, 2), "pumpRank": ur, "pumpTotal": urn,
                  "vsPump": round(sv / uv, 6) if uv else None,
                  "pumpShare": round(uv / ov, 6) if ov else None,
                  "hist": _share_hist(stonk, sol), "vsPumpHist": _share_hist(stonk, pump)},
    }


# ---- 销毁里程碑（v3.15）：烧掉多少 / 烧多快 / 离下一个 1% 还有多久 ----
def _ms_snaps():
    """burn-history 快照（[{t, pons, stonk}]）→ 按时间升序。"""
    try:
        rows = json.load(open(HIST, encoding="utf-8"))
    except Exception:
        return []
    return sorted([r for r in rows if isinstance(r, dict) and isinstance(r.get("t"), (int, float))],
                  key=lambda r: r["t"])


def _ms_sf_rows():
    """官方 sf-history 快照（含 burnTokens / priceUsd）→ 按时间升序。"""
    try:
        rows = json.load(open(SF_HIST, encoding="utf-8"))
    except Exception:
        return []
    return sorted([r for r in rows if isinstance(r, dict) and r.get("ts")],
                  key=lambda r: r["ts"])


def _burn_speed(points):
    """累计销毁序列 [(ts, value)] → (per_day, win_days, t0, t1)；算不出给 None。

    优先取「最近一跳本来就≈一天」（20~28 小时）的差值——最贴近「最近 24 小时速度」；
    否则退到 7 天窗口内最早的可用点做首尾差（窗口越长越稳）。负增长（取数回退）丢弃。
    """
    pts = [(int(t), float(v)) for t, v in points if v is not None]
    if len(pts) < 2:
        return None
    t1, v1 = pts[-1]
    for t0, v0 in reversed(pts[:-1]):
        gap = t1 - t0
        if gap > 28 * 3600:
            break
        if gap >= 20 * 3600 and v1 > v0:
            return ((v1 - v0) / (gap / 86400.0), gap / 86400.0, t0, t1)
    for t0, v0 in pts[:-1]:
        gap = t1 - t0
        if gap <= 7 * 86400 and v1 > v0:
            return ((v1 - v0) / (gap / 86400.0), gap / 86400.0, t0, t1)
    return None


def milestone(ho):
    """销毁里程碑（v3.15）：已销毁占比、最近 24h 速度、下一个整数关口倒计时。

    · PONS：累计＝burn-history 死地址余额快照（每天一条，最准）；速度优先快照差值，
      快照不够时退回 72h 链上分桶合计（标 src=chain72）。
    · STONK：累计与速度优先官方接口累计值（sf-history，每小时一条）；退回快照。
    · 价格：STONK 优先官方报价，PONS 用池子最新收盘价；算不出的字段留空，
      前端显示「—」，绝不因为一个字段拿不到就让整轮抓取失败。
    """
    now = int(time.time())
    out = {"generated": now, "step": 1.0}
    snaps = _ms_snaps()
    sfr = _ms_sf_rows()

    def last_close(key):
        for v in reversed((ho.get(key) or {}).get("close") or []):
            if v:
                return float(v)
        return None

    def pack(burned, supply, price, speed, src):
        d = {"burned": round(burned, 2), "supply": supply, "src": src,
             "pct": round(burned / supply * 100.0, 4)}
        if price:
            d["price"] = round(price, 6)
            d["burnedUsd"] = round(burned * price, 2)
        if speed:
            per_day, win_days, t0, t1 = speed
            d["perDay"] = round(per_day, 1)
            d["speedPct"] = round(per_day / supply * 100.0, 4)
            d["winDays"] = round(win_days, 1)
            step_tok = supply / 100.0                      # 1% ＝ 总量的 1/100
            to_next = step_tok - (burned % step_tok)
            d["nextPct"] = int(burned // step_tok) + 1
            d["toNext"] = round(to_next, 1)
            if per_day > 0:
                d["daysTo"] = round(to_next / per_day, 1)
        return d

    # —— PONS ——
    try:
        burned = float(snaps[-1]["pons"]) if snaps and snaps[-1].get("pons") else None
        speed = _burn_speed([(s["t"], s.get("pons")) for s in snaps]) if snaps else None
        src = "snapshot"
        if speed is None:                                  # 快照还没攒够 → 退回 72h 链上分桶
            arr = (ho.get("pons") or {}).get("burn") or []
            hrs = ho.get("hours") or []
            tot = sum(v for v in arr if v)
            span = (hrs[-1] + 3600 - hrs[0]) if len(hrs) > 1 else 0
            if tot > 0 and span >= 24 * 3600:
                speed = (tot / (span / 86400.0), span / 86400.0, hrs[0], hrs[-1] + 3600)
                src = "chain72"
        if burned:
            out["pons"] = pack(burned, 1_000_000_000.0, last_close("pons"), speed, src)
    except Exception as exc:
        print("warn: milestone pons: %s" % exc, file=sys.stderr)

    # —— STONK ——
    try:
        burned = price = None
        speed = None
        src = "official"
        if sfr:
            burned = float(sfr[-1].get("burnTokens") or 0) or None
            price = float(sfr[-1].get("priceUsd") or 0) or None
            speed = _burn_speed([(r["ts"], r.get("burnTokens")) for r in sfr])
        if burned is None and snaps and snaps[-1].get("stonk"):
            burned = float(snaps[-1]["stonk"])
            src = "snapshot"
        if speed is None and snaps:
            speed = _burn_speed([(s["t"], s.get("stonk")) for s in snaps])
            if speed is not None and src == "official":
                src = "snapshot"
        if burned:
            out["stonk"] = pack(burned, STONK_SUPPLY, price or last_close("stonk"), speed, src)
    except Exception as exc:
        print("warn: milestone stonk: %s" % exc, file=sys.stderr)

    pr = (out.get("pons") or {}).get("speedPct")
    sr = (out.get("stonk") or {}).get("speedPct")
    if pr and sr:
        if sr >= pr:
            out["versus"] = {"faster": "StonkFun", "ratio": round(sr / pr, 1)}
        else:
            out["versus"] = {"faster": "Pons", "ratio": round(pr / sr, 1)}
    return out


def ts_day(ts):
    return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")


def pons_rev_ratios(old, hold_by_day):
    """PONS 小时收入换算比率（v3.29.16 起逐日校准）。

    为什么不再固定 ÷0.8：官方「80% 收入用于回购」是历史口径；2026-10-09 起回购动用了
    金库，链上回购额已是当日收入的 2~5 倍，固定 0.8 会把收入放大数倍。

    返回 (by_day, live, src)：
      · by_day {YYYY-MM-DD: ratio}：各完整日取官方日线「收入 ÷ 回购」；官方回购还没出
        （滞后约 1 天）时改用链上回购（hold_by_day）。这样小时柱按天求和 ≈ 每日明细表。
      · live：当天所用比率 —— 官方已出当天部分值且链上有当天回购时，取「当天官方收入 ÷
        当天链上回购」，并用最近 3 日加权比率 R3 的 [0.5×, 2.5×] 夹住（防上游异常）；
        拿不到就退回 R3。
      · 兜底顺序：R3 → 旧 hourly.json 的 ponsRevRatio → PONS_RATIO_FALLBACK。
    """
    now = int(time.time())
    today = ts_day(now)
    dl = {}
    try:
        for dt, bag in (("dailyRevenue", "rev"), ("dailyHoldersRevenue", "hold")):
            for ts, v in (get(DL_FEES_API % ("pons", dt)).get("totalDataChart") or []):
                try:
                    ts, v = int(ts), float(v)
                except (TypeError, ValueError):
                    continue
                dl.setdefault(ts_day(ts), {})[bag] = v
    except Exception as exc:
        print("warn: pons ratios: %s" % exc, file=sys.stderr)

    days = sorted(d for d in dl if d < today)
    by_day = {}
    for d in days[-6:]:
        row = dl[d]
        hold = row.get("hold") or hold_by_day.get(d)
        if row.get("rev") and hold:
            r = row["rev"] / hold
            if PONS_RATIO_BAND[0] <= r <= PONS_RATIO_BAND[1]:
                by_day[d] = round(r, 4)

    # R3：最近 ≤3 个完整日的加权比率（越近权重越大）
    r3 = None
    use = days[-3:]
    weights = [0.2, 0.3, 0.5][-len(use):] if use else []
    num = den = 0.0
    for d, wt in zip(use, weights):
        row = dl.get(d) or {}
        hold = row.get("hold") or hold_by_day.get(d)
        if row.get("rev") and hold:
            num += wt * row["rev"]
            den += wt * hold
    if den > 0:
        cand = num / den
        if PONS_RATIO_BAND[0] <= cand <= PONS_RATIO_BAND[1]:
            r3 = cand

    src, live = "dl-3d", r3
    row = dl.get(today) or {}
    hold_today = hold_by_day.get(today)
    if row.get("rev") and hold_today:
        cand = row["rev"] / hold_today
        if r3:
            cand = min(max(cand, 0.5 * r3), 2.5 * r3)
        if PONS_RATIO_BAND[0] <= cand <= PONS_RATIO_BAND[1]:
            live, src = cand, "today-live"
    if live is None:
        src, live = "stale", None
        if isinstance(old, dict):
            try:
                prev = float(old.get("ponsRevRatio"))
                if PONS_RATIO_BAND[0] <= prev <= PONS_RATIO_BAND[1]:
                    live = prev
            except (TypeError, ValueError):
                pass
        if live is None:
            live, src = PONS_RATIO_FALLBACK, "fallback"
    return by_day, round(live, 4), src


def main():
    now = time.time()
    h_now = int(now // 3600 * 3600)
    buckets = [h_now - (HOURS - 1 - i) * 3600 for i in range(HOURS)]
    old = {}
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        pass

    out = {"generated": int(now), "hours": buckets, "pons": {}, "stonk": {}}
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
    srev, sburn, sspan, sspanR, sspanB = sf_series(buckets)

    # 同步官方逐笔流水供深度页使用与交叉核对；小时图以官方累计 API 的相邻快照差值为准。
    # 流水覆盖并不保证与官网日累计口径一致，因此不能用「买回÷比例」或逐笔销毁值覆盖累计差值。
    sfday_now = None
    try:
        sfday_now = sf_official_daily()
    except Exception as exc:
        print("warn: sf official daily: %s" % exc, file=sys.stderr)
    aligned_days = align_sf_complete_days(
        srev, sburn, buckets, (sfday_now or {}).get("days") or {})
    ratio = SF_RATIO_FALLBACK
    if sfday_now and sfday_now.get("days"):
        ds = sorted(sfday_now["days"])[-3:]
        hold = sum(float(sfday_now["days"][d].get("hold") or 0) for d in ds)
        revs = sum(float(sfday_now["days"][d].get("rev") or 0) for d in ds)
        if revs > 0 and 0.40 <= hold / revs <= 0.85:
            ratio = round(hold / revs, 4)
    led = None
    try:
        led = sf_ledger_sync()
        out["stonk"]["ledger"] = {"buyRows": led["buy"], "burnRows": led["burn"],
                                  "ratio": ratio,
                                  "chartSource": "official-cumulative-snapshots"}
        if led["failed"]:
            out["stonk"]["ledger"]["failed"] = True
    except Exception as exc:
        print("warn: sf ledger: %s" % exc, file=sys.stderr)
    if any(v is not None for v in sburn):
        out["stonk"]["burn"], out["stonk"]["burnSrc"] = sburn, "official-cumulative"
    else:
        # 官方累计值不可用时留空，不用另一种统计口径冒充官方小时数。
        out["stonk"]["burn"] = [None] * HOURS
        out["stonk"]["burnSrc"] = "official-pending"

    # 收入：Pons 用「小时回购支出 × 校准比率」推算（v3.29.16 逐日校准：
    # 历史日各用当天官方日线比率、当天用实时比率，兜底链上/旧值）；
    # StonkFun 小时收入与销毁均使用官方累计 API 相邻快照差值；未采到的时段留空。
    hold_by_day = {}
    for b, c, t0 in zip(out["pons"]["burn"], out["pons"]["close"], buckets):
        if b is not None and c:
            d0 = ts_day(t0)
            hold_by_day[d0] = hold_by_day.get(d0, 0.0) + b * c
    ratio_by_day, pons_ratio, pons_ratio_src = pons_rev_ratios(old, hold_by_day)
    out["ponsRevRatio"], out["ponsRevRatioSrc"] = pons_ratio, pons_ratio_src
    out["ponsRevRatioByDay"] = ratio_by_day
    pv = []
    for b, c, t0 in zip(out["pons"]["burn"], out["pons"]["close"], buckets):
        if b is not None and c:
            pv.append(round(b * c * ratio_by_day.get(ts_day(t0), pons_ratio), 2))
        else:
            pv.append(None)
    out["pons"]["rev"], out["pons"]["revEst"] = pv, True
    quote_est = any(bool(row.get("quoteRevEstimated"))
                    for row in sf_load_hist()
                    if isinstance(row, dict) and row.get("ts", 0) >= buckets[0])
    rev_day_scaled = bool(aligned_days["rev"])
    burn_day_scaled = bool(aligned_days["burn"])
    out["stonk"]["rev"], out["stonk"]["revEst"] = srev, (quote_est or rev_day_scaled)
    out["stonk"]["revSrc"] = ("official-daily-calibrated" if rev_day_scaled else
                                  "official-cumulative-quote-estimate" if quote_est else
                                  "official-cumulative" if any(v is not None for v in srev) else
                                  "official-pending")
    out["stonk"]["burnEst"] = burn_day_scaled
    out["stonk"]["dailyAligned"] = aligned_days
    # v3.22：断档回填的小时（前端用斜纹柱 + 文案标注「估算」，不当成实测）
    out["stonk"]["span"], out["stonk"]["spanR"], out["stonk"]["spanB"] = sspan, sspanR, sspanB

    # 日度补充（v3.9.1）：DefiLlama 日度会晚 1~2 天出数，缺的那几天用更快的源补上 ——
    #   PONS ＝链上（收入＝回购支出×逐日校准比率，与小时级同一口径；回购＝链上回购量×价格）
    #   STONK＝官方接口累计快照差值
    #   差几个小时就标几个小时（front-end 会写明「链上·8h」这种），绝不拿半天冒充整天。
    #   前端只在「待更新」的格子里用它，不混进 DefiLlama 序列。
    def daily_supp():
        supp = {"pons": {}, "stonk": {}}
        for i, b in enumerate(buckets):
            rev = out["pons"]["rev"][i] if i < len(out["pons"]["rev"]) else None
            if rev is None:
                continue
            day = datetime.datetime.utcfromtimestamp(b).strftime("%Y-%m-%d")
            d = supp["pons"].setdefault(day, {"rev": 0.0, "hold": 0.0, "hours": 0})
            d["rev"] += rev
            d["hold"] += (out["pons"]["burn"][i] or 0) * (out["pons"]["close"][i] or 0)
            d["hours"] += 1
        for day, d in supp["pons"].items():
            d["rev"] = round(d["rev"], 2)
            d["hold"] = round(d["hold"], 2)
            d["partial"] = d["hours"] < 24
        hist = [h for h in sf_load_hist() if isinstance(h, dict) and h.get("ts")]
        hist.sort(key=lambda h: h["ts"])
        by_day = {}
        for h in hist:
            by_day.setdefault(datetime.datetime.utcfromtimestamp(h["ts"]).strftime("%Y-%m-%d"), []).append(h)
        days = sorted(by_day)
        for i, b in enumerate(days):
            hb = by_day[b][-1]
            # 起点：上一天的最后一条；没有上一天（我们刚开始记录）就用当天第一条 —— 覆盖几小时就标几小时
            ha = by_day[days[i - 1]][-1] if i > 0 else by_day[b][0]
            gap = hb["ts"] - ha["ts"]
            if not (6 * 3600 <= gap <= 26 * 3600):
                continue
            supp["stonk"][b] = {
                "rev": round((hb.get("revUsd") or 0) - (ha.get("revUsd") or 0)
                              + ((hb.get("quoteRevUsd") or 0) - (ha.get("quoteRevUsd") or 0)
                                 if ha.get("quoteRevUsd") is not None and hb.get("quoteRevUsd") is not None else 0), 2),
                "hold": round((hb.get("buybackUsd") or 0) - (ha.get("buybackUsd") or 0), 2),
                "hours": round(gap / 3600, 1),
                "partial": gap < 22 * 3600,
            }
        return supp
    try:
        out["dailySupp"] = daily_supp()
    except Exception as exc:
        print("warn: dailySupp: %s" % exc, file=sys.stderr)
        out["dailySupp"] = old.get("dailySupp") if isinstance(old, dict) else None

    # 官方口径日线（另一套统计基准，只用于「数据源体检」板块，不混进 DefiLlama 那条序列）
    try:
        out["stonkDaily"] = sf_daily()
    except Exception as exc:
        print("warn: sf_daily: %s" % exc, file=sys.stderr)
        out["stonkDaily"] = (old.get("stonkDaily") if isinstance(old, dict) else None)

    # 官方日线（v3.18）：STONK 日度与官网对账用；拿不到沿用上一份（账本同步时已抓过一次，直接复用）
    out["sfDaily"] = sfday_now or (old.get("sfDaily") if isinstance(old.get("sfDaily"), dict) else None)

    # 市场占有率：拿不到就沿用上一份，绝不让整轮抓取失败
    try:
        out["share"] = market_share()
    except Exception as exc:
        print("warn: market share: %s" % exc, file=sys.stderr)
        out["share"] = (old.get("share") if isinstance(old, dict) else None)

    # 销毁里程碑（v3.15）：同样「拿不到就沿用上一份」，绝不拖垮整轮
    try:
        out["milestone"] = milestone(out)
    except Exception as exc:
        print("warn: milestone: %s" % exc, file=sys.stderr)
        out["milestone"] = (old.get("milestone") if isinstance(old, dict) else None)

    atomic_dump(out, OUT)
    pb = [x for x in out["pons"]["burn"] if x]
    print("hourly.json ok · 小时数 %d · PONS 72h 销毁 %s · 交易量 PONS %s / STONK %s · STONK 官方累计快照 %s"
          % (HOURS, round(sum(pb), 1),
             sum(x for x in out["pons"]["vol"] if x), sum(x for x in out["stonk"]["vol"] if x),
             sum(x is not None for x in out["stonk"]["rev"])))
    return out


if __name__ == "__main__":
    if "--share-only" in sys.argv:      # 调试用：只刷新市场占有率，不重跑整条管道
        _old = json.load(open(OUT, encoding="utf-8"))
        _old["share"] = market_share()
        atomic_dump(_old, OUT)
        print(json.dumps(_old["share"], ensure_ascii=False)[:400])
    elif "--milestone-only" in sys.argv:  # 调试用：只刷新销毁里程碑，不重跑整条管道
        _old = json.load(open(OUT, encoding="utf-8"))
        _old["milestone"] = milestone(_old)
        atomic_dump(_old, OUT)
        print(json.dumps(_old["milestone"], ensure_ascii=False)[:400])
    elif "--ledger-only" in sys.argv:     # 调试/回填：只同步官方流水账本（PONSPULSE_LEDGER_MAX_PAGES 可加大页数）
        _t0 = time.time()
        _info = sf_ledger_sync()
        _info["seconds"] = round(time.time() - _t0, 1)
        print(json.dumps(_info, ensure_ascii=False))
    else:
        main()
