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
BUYBACK_SHARE = 0.8          # Pons 公开口径：80% 收入用于回购
# STONK 官方原始供应（不是整 10 亿；同 buyback.py 的 STONK_INITIAL，2026-10-06 对账修正）
STONK_SUPPLY = 999_969_797.91
SF_API = "https://www.stonkfun.xyz/api/revenue"   # StonkFun 官方收入/回购/销毁（国内被墙，走海外中转）
SF_DAILY_API = "https://www.stonkfun.xyz/api/v2/revenue/daily"   # 官方日线（v3.18 起用于日度对账）
SF_HIST = os.path.join(HERE, "sf-history.json")    # 官方累计值快照（每小时一条）


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
    return {"ts": int(time.time()),
            "revUsd": float(t["totalRevenueUsd"]),
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
        days[d] = {"rev": round(float(r.get("revenueUsd") or 0), 2),
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
    """官方累计值 → 每小时差值：(收入USD[], 销毁STONK[], 回填小时[])。

    间隔 >2.5h 的那一跳以前是直接丢掉的 —— 电脑睡眠 / 接口抽风 / 中转挂掉一晚上，
    第二天就有十几个小时的柱子全空（2026-10-07 用户反馈「小时级 STONK 数据都没了」）。
    现在改成：这一跳的总量按小时平均摊回中间那几个小时，并记进 span；
    前端把那几根柱子画成斜纹 + 标注「回填估算」，既不留白，也不假装是实测值。
    """
    hist = [h for h in sf_load_hist() if isinstance(h, dict) and h.get("ts")]
    hist.sort(key=lambda h: h["ts"])
    rev = {b: None for b in buckets}
    burn = {b: None for b in buckets}
    span = set()          # 并集（前端不区分口径时用）
    spanR, spanB = set(), set()
    for a, b in zip(hist, hist[1:]):
        gap = b["ts"] - a["ts"]
        if gap <= 0:
            continue
        ha = int(a["ts"] // 3600 * 3600)
        hb = int(b["ts"] // 3600 * 3600)
        n = max(1, min(48, (hb - ha) // 3600))      # 这一跳覆盖了几个整点
        dr = (b.get("revUsd") or 0) - (a.get("revUsd") or 0)
        db = (b.get("burnTokens") or 0) - (a.get("burnTokens") or 0)
        for k in range(n):
            hour = ha + k * 3600
            if hour not in rev:
                continue
            if dr > 0:
                rev[hour] = round((rev[hour] or 0) + dr / n, 2)
                if n > 1:
                    spanR.add(hour)
            if db > 0:
                burn[hour] = round((burn[hour] or 0) + db / n, 2)
                if n > 1:
                    spanB.add(hour)
            if n > 1 and hour in spanR and hour in spanB:
                span.add(hour)
    keep = lambda st: sorted(h for h in st if h in rev)
    return ([rev[b] for b in buckets], [burn[b] for b in buckets],
            keep(span), keep(spanR), keep(spanB))


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
    srev, sburn, sspan, sspanR, sspanB = sf_series(buckets)
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
    # v3.22：断档回填的小时（前端用斜纹柱 + 文案标注「估算」，不当成实测）
    out["stonk"]["span"], out["stonk"]["spanR"], out["stonk"]["spanB"] = sspan, sspanR, sspanB

    # 日度补充（v3.9.1）：DefiLlama 日度会晚 1~2 天出数，缺的那几天用更快的源补上 ——
    #   PONS ＝链上（收入＝回购支出÷80%，与小时级同一口径，回购销毁＝收入×80%）
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
            d["hold"] += rev * BUYBACK_SHARE
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
                "rev": round((hb.get("revUsd") or 0) - (ha.get("revUsd") or 0), 2),
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

    # 官方日线（v3.18）：STONK 日度与官网对账用；拿不到沿用上一份
    try:
        out["sfDaily"] = sf_official_daily() or (old.get("sfDaily") if isinstance(old.get("sfDaily"), dict) else None)
    except Exception as exc:
        print("warn: sfDaily: %s" % exc, file=sys.stderr)
        out["sfDaily"] = old.get("sfDaily") if isinstance(old.get("sfDaily"), dict) else None

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
    print("hourly.json ok · 小时数 %d · PONS 72h 销毁 %s · 交易量 PONS %s / STONK %s"
          % (HOURS, round(sum(pb), 1),
             sum(x for x in out["pons"]["vol"] if x), sum(x for x in out["stonk"]["vol"] if x)))
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
    else:
        main()
