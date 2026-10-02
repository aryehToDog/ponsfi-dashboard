#!/usr/bin/env python3
"""Pons / StonkFun 每日检查（纯脚本，不经过模型）。

1) 刷新看板数据并重建面板（调用同目录 build_monitor.py）
2) 按既定规则判断：7 日均收入 vs 离场/警戒线、环比跌幅、回购是否持续、P/S 估值
3) 结果写入 work/daily-check.log；只有触发告警时才弹 macOS 通知（默认保持安静）

用法: python3 work/daily_check.py [--force-notify]
"""
import datetime
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(HERE, "daily-check.log")
DATA = os.path.join(HERE, "dashboard-data.json")

RULES = {
    "pons": {"label": "Pons ($PONS)", "exit": 100_000, "warn": 150_000},
    "stonkfun": {"label": "StonkFun ($STONK)", "exit": 200_000, "warn": 280_000},
}


def log(line):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def notify(title, message):
    script = 'display notification {} with title {}'.format(
        json.dumps(message, ensure_ascii=False), json.dumps(title, ensure_ascii=False)
    )
    try:
        proc = subprocess.run(["osascript", "-e", script], timeout=20,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            log("通知失败: " + (proc.stderr or "").strip()[:200])
        else:
            log("已发送系统通知")
    except Exception as exc:
        log(f"通知异常: {exc}")


def refresh_panel():
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "build_monitor.py")],
        capture_output=True, text=True, timeout=300,
    )
    out = (proc.stdout or "").strip().splitlines()
    err = (proc.stderr or "").strip().splitlines()
    if proc.returncode not in (0, 2):
        log(f"面板刷新失败 rc={proc.returncode} {err[-1] if err else ''}")
        return False
    tag = "面板已刷新" if proc.returncode == 0 else "面板已刷新（部分数据源失败，已用抓到的数据更新）"
    log(tag + ": " + (out[-1] if out else "ok"))
    if err:
        log("抓取告警: " + "; ".join(err[:3]))
    return True


def mean(points):
    return sum(v for _, v in points) / len(points)


def check():
    data = json.load(open(DATA, encoding="utf-8"))
    alerts = []
    notes = []
    for slug, rule in RULES.items():
        series = data["series"].get(f"{slug}.dailyRevenue") or []
        holders = data["series"].get(f"{slug}.dailyHoldersRevenue") or []
        if len(series) < 14:
            notes.append(f"{rule['label']} 数据不足（{len(series)} 天）")
            continue
        last7, prev7 = mean(series[-7:]), mean(series[-14:-7])
        change = (last7 / prev7 - 1) * 100 if prev7 else 0
        mcap = (data["meta"].get(slug) or {}).get("mcap") or 0
        ps = (mcap / (last7 * 365)) if last7 else None
        buyback7 = sum(v for _, v in holders[-7:]) if holders else 0

        notes.append(
            f"{rule['label']} 7日均 ${last7:,.0f}（环比 {change:+.1f}%），"
            f"回购7日 ${buyback7:,.0f}，P/S {ps:.2f}x" if ps else f"{rule['label']} 7日均 ${last7:,.0f}"
        )
        if last7 < rule["exit"]:
            alerts.append(f"{rule['label']} 7日均收入 ${last7:,.0f} 跌破离场线 ${rule['exit']:,}")
        elif last7 < rule["warn"]:
            alerts.append(f"{rule['label']} 7日均收入 ${last7:,.0f} 跌破警戒线 ${rule['warn']:,}")
        if change < -25:
            alerts.append(f"{rule['label']} 收入环比 {change:+.1f}%（跌幅超 25%）")
        if buyback7 <= 0:
            alerts.append(f"{rule['label']} 最近 7 日回购为 0，回购可能已停止")
        if ps and ps > 4:
            notes.append(f"{rule['label']} P/S {ps:.2f}x 偏贵（>4x）")
    return alerts, notes


def main():
    force = "--force-notify" in sys.argv
    ok = refresh_panel()
    if not ok:
        notify("Pons / StonkFun 监控", "今日数据抓取失败，看板未更新，请检查网络。")
        return 1
    alerts, notes = check()
    log(" | ".join(notes))
    if alerts:
        log("告警: " + "；".join(alerts))
        notify("Pons / StonkFun 告警", "；".join(alerts[:3]))
    elif force:
        notify("Pons / StonkFun 监控", "检查完成：" + "；".join(notes[:2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
