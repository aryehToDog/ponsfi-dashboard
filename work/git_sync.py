#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上线后把最新状态同步到 GitHub（任何失败都只记日志，绝不影响上线）。

分工：
  · main 分支      —— 代码 / 模板 / 脚本等源文件。只在真的有源文件改动时提交推送。
                      每次上线都会刷新的 HTML、JSON 数据产物不进 main，避免仓库按小时膨胀。
  · snapshots 分支 —— 每次上线的「整站最新快照」。孤儿提交 + 强制推送，远端永远只有
                      最新一份（被顶下去的旧对象由 GitHub 自动回收）。

由 work/hourly_check.py 在上线成功后自动调用：
    python3 work/git_sync.py
"""
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(HERE, "git-sync.log")
REMOTE = "origin"
MAIN_BRANCH = "main"
SNAPSHOT_BRANCH = "snapshots"

# 每次上线都会刷新的数据产物：只进 snapshots 分支，不进 main
DATA_PATHS = [
    "deploy/index.html",
    "outputs/pons-stonkfun-monitor.html",
    "outputs/小时监控-STONK官方数据-预览.png",
    "work/dashboard-data.json",
    "work/hourly.json",
    "work/sf-history.json",
    "work/burn-history.json",
    "work/burns.json",
    "work/burn_events.json",
]


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg)
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _env(extra=None):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    if extra:
        env.update(extra)
    return env


def run(args, timeout=240, env_extra=None):
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                              env=_env(env_extra), timeout=timeout)
    except subprocess.TimeoutExpired:
        log("超时：%s" % " ".join(args[:3]))
        return None


def git(*args, **kw):
    return run(["git"] + list(args), **kw)


def sync_main():
    """源文件改动 -> main 分支"""
    r = git("remote", "get-url", REMOTE)
    if r is None or r.returncode != 0:
        log("没有配置 origin 远端，跳过同步")
        return False

    git("config", "core.hooksPath", ".githooks")

    git("add", "-A")
    existing = [p for p in DATA_PATHS if os.path.exists(os.path.join(ROOT, p))]
    if existing:
        git("reset", "-q", "--", *existing)

    d = git("diff", "--cached", "--quiet")
    if d is not None and d.returncode == 0:
        log("main：没有源文件改动")
        return True

    msg = "自动同步：上线源文件更新 " + time.strftime("%Y-%m-%d %H:%M")
    c = git("commit", "-q", "-m", msg)
    if c is None or c.returncode != 0:
        log("main：提交失败 " + ((c.stderr or "").strip()[:200] if c else ""))
        return False
    p = git("push", REMOTE, MAIN_BRANCH)
    ok = p is not None and p.returncode == 0
    log("main 推送：" + ("成功" if ok else ((p.stderr or "").strip()[:200] if p else "超时")))
    return ok


def push_snapshot():
    """整站最新快照 -> snapshots 分支（孤儿提交，远端只保留最新一份）"""
    idx = tempfile.mktemp(prefix="ponsfi-index-")
    env_extra = {"GIT_INDEX_FILE": idx}
    try:
        a = run(["git", "add", "-A"], env_extra=env_extra, timeout=300)
        if a is None or a.returncode != 0:
            log("snapshots：暂存失败")
            return False
        t = run(["git", "write-tree"], env_extra=env_extra)
        tree = (t.stdout or "").strip() if t else ""
        if not tree:
            log("snapshots：write-tree 失败")
            return False
        msg = "上线快照 " + time.strftime("%Y-%m-%d %H:%M")
        c = git("commit-tree", tree, "-m", msg)
        commit = (c.stdout or "").strip() if c else ""
        if not commit:
            log("snapshots：commit-tree 失败")
            return False
        git("update-ref", "refs/heads/" + SNAPSHOT_BRANCH, commit)
        p = git("push", "-f", REMOTE, SNAPSHOT_BRANCH)
        ok = p is not None and p.returncode == 0
        if ok:
            log("snapshots 推送：成功 " + commit[:8])
        else:
            log("snapshots 推送：" + ((p.stderr or "").strip()[:200] if p else "超时"))
        return ok
    finally:
        try:
            os.remove(idx)
        except Exception:
            pass


def main():
    try:
        sync_main()
        push_snapshot()
        log("GitHub 同步完成")
    except Exception as exc:
        log("GitHub 同步异常：%s" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
