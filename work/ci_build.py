#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Actions 云端构建：抓取 → 合并 → 渲染 → 快照回推（整条链路不依赖本机、不依赖服务器）。

为什么要有它（2026-10-07）：
  以前「每小时刷新」跑在作者 Mac 上（LaunchAgent → hourly_check.py → scp 上传）。
  电脑一关机/睡眠，小时级数据就断档；服务器在上海，GeckoTerminal / CoinGecko /
  StonkFun 官网这几个源被墙，也没法自己抓。
  现在改成：GitHub Actions（海外节点，全部源直连）每小时跑这一份脚本，
  产物 + 状态文件压回 snapshots 分支（孤儿提交、强推，仓库不会按时长胖）；
  服务器只跑 deploy/pull_publish.sh 每 5 分钟拉一次最新快照换上线。

用法：
    python3 work/ci_build.py --mode auto --push      # Actions 里这么跑
    python3 work/ci_build.py --mode hourly --no-push # 本地调试

模式：
    hourly  小时级（hourly.py + 合并 + 渲染）—— 每小时第 5 分钟（UTC）
    daily   全量（build_monitor.py：DefiLlama 日线 / 收入榜 / 回购 / 小时级）—— 每天 01:05 UTC
    auto    按 UTC 小时自动选：01 点走 daily；另外，只要最近一次全量已经超过
            24 小时（GitHub 定时被延迟/漏跑、或刚迁移过来还没跑过全量），下一个
            整点就自动补一轮 daily —— 日线数据不会一直卡在旧日期；其余走 hourly

状态文件（由 workflow 先从 snapshots 分支取出，跑完再压回去）：
    work/dashboard-data.json / work/hourly.json / work/sf-history.json /
    work/burn-history.json / work/burns.json / work/burn_events.json
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_HTML = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
DEPLOY_HTML = os.path.join(ROOT, "deploy", "index.html")

SNAPSHOT_FILES = [
    "deploy/index.html",
    "outputs/pons-stonkfun-monitor.html",
    "work/dashboard-data.json",
    "work/hourly.json",
    "work/sf-history.json",
    "work/burn-history.json",
    "work/burns.json",
    "work/burn_events.json",
]


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + str(msg), flush=True)


def run(args):
    log("$ " + " ".join(args))
    proc = subprocess.run(args, cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit("命令失败（exit %d）：%s" % (proc.returncode, " ".join(args)))


def atomic_json(obj, path):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)
    os.replace(tmp, path)


def merge_hourly():
    """hourly.json → dashboard-data.json（与 work/hourly_check.py 的合并口径一致）。

    patch_official_stonk 复用 hourly_check 里的实现：把 STONK 卡片数字换成官方累计值，
    官方快照超过 6 小时没更新就不动（宁可显示旧值，也不拿过期数据冒充实时）。
    """
    sys.path.insert(0, HERE)
    from hourly_check import patch_official_stonk
    dp = os.path.join(HERE, "dashboard-data.json")
    d = json.load(open(dp, encoding="utf-8"))
    d["hourly"] = json.load(open(os.path.join(HERE, "hourly.json"), encoding="utf-8"))
    patch_official_stonk(d)
    atomic_json(d, dp)


def daily_age_hours(path=None):
    """最近一次全量（daily）构建距今多少小时。

    读 dashboard-data.json 的顶层 generated（build_monitor.py 写入的 ISO 时间）。
    读不到 / 解析失败 → 返回 None，调用方按「需要全量」处理（宁可多跑一次 daily，
    也不要让日线数据一直停在旧日期 —— 2026-10-07 迁移当天就是这么欠了一轮）。
    """
    path = path or os.path.join(HERE, "dashboard-data.json")
    try:
        ts = json.load(open(path, encoding="utf-8")).get("generated")
        if not isinstance(ts, str):
            return None
        when = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - when).total_seconds() / 3600.0
    except Exception:
        return None


def publish_deploy():
    os.makedirs(os.path.dirname(DEPLOY_HTML), exist_ok=True)
    shutil.copyfile(OUT_HTML, DEPLOY_HTML)


def push_snapshot(mode):
    """把产物 + 状态文件打成孤儿提交，强推 snapshots 分支（仓库里永远只留最新一份）。"""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not (token and repo):
        log("跳过快照推送：没有 GITHUB_TOKEN / GITHUB_REPOSITORY")
        return
    tmp = tempfile.mkdtemp(prefix="snap-")
    for rel in SNAPSHOT_FILES:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")

    def git(*args):
        subprocess.run(["git", *args], cwd=tmp, check=True, env=env)

    git("init", "-q", "-b", "snapshots")
    git("add", "-A")
    stamp = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    msg = "快照 %s（%s · GitHub Actions 自动生成，服务器每 5 分钟拉取上线）" % (stamp, mode)
    subprocess.run(["git", "-c", "user.name=ponspulse-bot",
                    "-c", "user.email=ponspulse-bot@users.noreply.github.com",
                    "commit", "-qm", msg], cwd=tmp, check=True, env=env)
    url = "https://x-access-token:%s@github.com/%s.git" % (token, repo)
    last = None
    for attempt in range(3):
        try:
            subprocess.run(["git", "push", "-q", "--force", url, "snapshots"],
                           cwd=tmp, check=True, env=env, capture_output=True, text=True)
            last = None
            break
        except subprocess.CalledProcessError as exc:
            last = exc
            time.sleep(3 + attempt * 5)
    if last is not None:
        detail = ((last.stderr or "") + (last.stdout or "") + str(last)).replace(token, "***")
        print("快照推送失败：%s" % detail[-400:], file=sys.stderr)
        raise SystemExit(1)
    log("快照已推送 → snapshots 分支（%s）" % stamp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["auto", "hourly", "daily"], default="auto")
    ap.add_argument("--push", action="store_true", help="跑完把产物压回 snapshots 分支")
    args = ap.parse_args()
    mode = args.mode
    if mode == "auto":
        if time.gmtime().tm_hour == 1:
            mode = "daily"
        else:
            age = daily_age_hours()
            if age is None or age > 24:
                mode = "daily"
                log("最近一次全量在 %s，超过 24 小时，本次自动补一轮全量" %
                    ("？(读不到时间戳)" if age is None else "%.1f 小时前" % age))
            else:
                mode = "hourly"
    log("构建模式：%s（UTC %s）" % (mode, time.strftime("%Y-%m-%d %H:%M", time.gmtime())))
    os.makedirs(os.path.join(ROOT, "outputs"), exist_ok=True)   # 全新 checkout 里可能还没有
    if mode == "daily":
        run([sys.executable, os.path.join(HERE, "build_monitor.py")])
    else:
        run([sys.executable, os.path.join(HERE, "hourly.py")])
        merge_hourly()
        run([sys.executable, os.path.join(HERE, "render_only.py")])
    publish_deploy()
    if args.push:
        push_snapshot(mode)
    log("完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
