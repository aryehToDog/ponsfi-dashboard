#!/usr/bin/env python3
"""每小时跑一次：刷新小时级数据 → 重新渲染 → 推上线。

由 LaunchAgent com.ponspulse.hourly 每小时第 5 分钟调用。
日志：work/hourly-check.log
"""
import json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(HERE, "hourly-check.log")
OUT = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
TMP = "/tmp/publish-index.html"


STONK_SUPPLY = 999_969_797.91   # 官方原始供应（不是整 10 亿，见 buyback.py 同名常量）


def patch_official_stonk(d):
    """把 STONK 卡片数字换成官方累计值（每小时跑一次）：与 stonkfun.xyz 完全对齐。

    为什么需要：buyback.py 的链上读数每天才刷一次（build_monitor 09:00），官方接口
    是分钟级更新 —— 不覆盖就会出现「卡片 199.85M vs 官网 200.11M」这种滞后差
    （2026-10-06 用户对账时发现）。官方快照超过 6 小时没更新时不动，宁可显示旧值
    也不拿过期数据冒充实时。
    """
    path = os.path.join(HERE, "sf-history.json")
    hist = [r for r in json.load(open(path, encoding="utf-8"))
            if isinstance(r, dict) and r.get("ts")]
    hist.sort(key=lambda r: r["ts"])
    if not hist:
        return
    last = hist[-1]
    if time.time() - last["ts"] > 6 * 3600:
        return
    # 每小时刷新官方币价，避免首页 / 深度页估值继续使用每日全量留下的旧价格。
    price = float(last.get("priceUsd") or 0)
    if price > 0:
        burned = float(last.get("burnTokens") or 0)
        mcap = price * (STONK_SUPPLY - burned)
        d.setdefault("price", {})["stonkfun"] = price
        d.setdefault("market", {}).setdefault("stonkfun", {}).update(price=price, mcap=mcap)
        d.setdefault("meta", {}).setdefault("stonkfun", {})["mcap"] = mcap
    node = ((d.get("burn") or {}).get("chain") or {}).get("stonkfun")
    burned = float(last.get("burnTokens") or 0)
    if not node or burned <= 0:
        return
    node["burned"] = round(burned, 2)
    node["supply"] = STONK_SUPPLY
    node["pct"] = round(burned / STONK_SUPPLY * 100, 2)
    node["src"] = "StonkFun 官方接口 · 累计销毁（每小时刷新）"
    # 官方 24h：找离「24 小时前」最近的一条快照做差（±3h 容差，找不到就保留原值）
    target = last["ts"] - 24 * 3600
    base = None
    for r in hist:
        if abs(r["ts"] - target) <= 3 * 3600 and (base is None or abs(r["ts"] - target) < abs(base["ts"] - target)):
            base = r
    if base is not None:
        if last.get("buybackUsd") is not None and base.get("buybackUsd") is not None:
            cash = float(last["buybackUsd"]) - float(base["buybackUsd"])
            if cash >= 0:
                node["buyback24hUsd"] = round(cash, 2)
                node["buyback24hHours"] = round((last["ts"] - base["ts"]) / 3600, 2)
        delta = burned - float(base.get("burnTokens") or 0)
        if delta >= 0:
            node["burn24h"] = round(delta, 2)
            node["burn24hSrc"] = "official"
            node["burn24hHours"] = round((last["ts"] - base["ts"]) / 3600, 2)
            node.pop("burn24hLive", None)


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg)
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def main():
    r = subprocess.run([sys.executable, os.path.join(HERE, "hourly.py")],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        log("hourly.py 失败：" + ((r.stderr or r.stdout or "")[-300:]).replace("\n", " "))
        return 1
    log((r.stdout or "").strip()[:200])

    try:
        data_p = os.path.join(HERE, "dashboard-data.json")
        d = json.load(open(data_p, encoding="utf-8"))
        d["hourly"] = json.load(open(os.path.join(HERE, "hourly.json"), encoding="utf-8"))
        patch_official_stonk(d)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(data_p), prefix=".tmp-data-")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
        os.replace(tmp, data_p)
    except Exception as exc:
        log("合并 hourly.json 失败：%s" % exc)
        return 1

    r = subprocess.run([sys.executable, os.path.join(HERE, "render_only.py")],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        log("render 失败：" + ((r.stderr or "")[-300:]).replace("\n", " "))
        return 1

    subprocess.run(["cp", "-f", OUT, TMP], check=True)
    subprocess.run(["cp", "-f", OUT, os.path.join(ROOT, "deploy", "index.html")], check=True)
    r = subprocess.run(["expect", os.path.join(HERE, "scp.exp"), TMP],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        log("上传失败：" + ((r.stderr or r.stdout or "")[-200:]).replace("\n", " "))
        return 1
    r = subprocess.run(["expect", os.path.join(HERE, "rsh.exp"),
                        "sudo -S cp -f /var/www/pons-dashboard/index.html /tmp/index-hourly.bak 2>/dev/null; "
                        "sudo -S mv -f /tmp/index.html /var/www/pons-dashboard/index.html && "
                        "sudo -S chmod 644 /var/www/pons-dashboard/index.html"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        log("上线失败：" + ((r.stderr or r.stdout or "")[-200:]).replace("\n", " "))
        return 1
    log("已上线 · 小时级数据已刷新")
    try:
        g = subprocess.run([sys.executable, os.path.join(HERE, "git_sync.py")],
                           cwd=ROOT, capture_output=True, text=True, timeout=300)
        out = (g.stdout or "").strip().splitlines()
        if out:
            log("GitHub 同步：" + out[-1][-200:])
    except Exception as exc:
        log("GitHub 同步异常：%s" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
