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
import re
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
        return False

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


def _last_version_tag():
    """形如 v3.5 / v3.5.1 的最大版本标签 -> ((3,5,1), "v3.5.1")"""
    r = git("tag", "--list", "v[0-9]*")
    best = None
    for line in ((r.stdout or "").splitlines() if r else []):
        m = re.match(r"^v(\d+)\.(\d+)(?:\.(\d+))?$", line.strip())
        if not m:
            continue
        key = (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
        if best is None or key > best[0]:
            best = (key, line.strip())
    return best


def _page_version():
    """页脚版本号（work/render_only.py 的 VER，如 v3.5）—— 有它就用它当标签名。"""
    r = git("show", "HEAD:work/render_only.py")
    if r is None or r.returncode != 0:
        return None
    m = re.search(r'^VER\s*=\s*"(v[\d.]+)', r.stdout or "", re.M)
    return m.group(1) if m else None


def push_release_tag():
    """源文件上线后：自动打版本标签（附更新说明）并推送。"""
    tags = set(((git("tag", "--list").stdout or "").split()))
    prev = _last_version_tag()
    prev_name = prev[1] if prev else None
    page = _page_version()
    if page and page not in tags:
        new = page
    elif prev:
        new = "v%d.%d.%d" % (prev[0][0], prev[0][1], prev[0][2] + 1)
    else:
        new = "v0.1"
    rng = (prev_name + "..HEAD") if prev_name else "HEAD"
    cnt = (git("rev-list", "--count", rng).stdout or "?").strip()
    lg = git("log", "--pretty=\u00b7 %h %s", rng)
    st = git("diff", "--stat", rng) if prev_name else git("show", "--stat", "--format=", "HEAD")
    msg = "\n".join([
        "自动发布 \u00b7 " + time.strftime("%Y-%m-%d %H:%M"),
        "",
        "自 %s 起的源文件改动（%s 个提交）：" % (prev_name or "仓库起点", cnt),
        (lg.stdout or "").strip(),
        "",
        "改动文件：",
        (st.stdout or "").strip(),
    ])
    c = git("tag", "-a", new, "-m", msg)
    if c is None or c.returncode != 0:
        log("版本标签：创建失败 " + ((c.stderr or "").strip()[:200] if c else ""))
        return False
    p2 = git("push", REMOTE, new)
    ok = p2 is not None and p2.returncode == 0
    log("版本标签：" + new + (" 已创建并推送" if ok else
        (" 已创建，推送失败：" + (p2.stderr or "").strip()[:160] if p2 else " 已创建，推送超时")))
    return ok


def main():
    try:
        if sync_main():
            push_release_tag()
        push_snapshot()
        log("GitHub 同步完成")
    except Exception as exc:
        log("GitHub 同步异常：%s" % exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
