#!/usr/bin/env python3
"""ponsfi.xyz 生效检查 v2（Cloudflare 隧道方案）。

由 launchd（com.ponspulse.dns-check）每 10 分钟跑一次：
1) 若 https://ponsfi.xyz/ 返回 200 且页面大小正常 → 弹系统通知（可分享），并自我停用
2) 若 NS 已切到 Cloudflare 但连续 3 轮站点仍打不开 → 通知一次（需人工介入）
3) 超过 2026-10-03 20:00 仍未生效 → 通知一次说明情况，并自我停用
4) 其余情况：安静退出（只写日志）
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "domain-check.log")
DONE = os.path.join(HERE, "domain-check.done")
STUCK = os.path.join(HERE, "domain-check.stuck")
LABEL = "com.ponspulse.dns-check"
DOMAIN = "ponsfi.xyz"
DEADLINE = datetime.datetime(2026, 10, 3, 20, 0)


def log(line):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {line}\n")
    except Exception:
        pass


def notify(title, message):
    script = 'display notification {} with title {}'.format(
        json.dumps(message, ensure_ascii=False), json.dumps(title, ensure_ascii=False)
    )
    try:
        proc = subprocess.run(["osascript", "-e", script], timeout=20,
                              capture_output=True, text=True)
        log("已发送系统通知" if proc.returncode == 0 else "通知失败: " + (proc.stderr or "").strip()[:200])
    except Exception as exc:
        log(f"通知异常: {exc}")


def stop_self():
    for cmd in (
        ["launchctl", "disable", f"gui/{os.getuid()}/{LABEL}"],
        ["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"],
    ):
        try:
            subprocess.run(cmd, capture_output=True, timeout=15)
        except Exception:
            pass


def check():
    detail = []
    cf_ns = False
    for server in ("223.5.5.5", "119.29.29.29", "8.8.8.8"):
        answer = "(空)"
        try:
            out = subprocess.run(
                ["dig", "+short", "+time=3", "NS", DOMAIN, "@" + server],
                capture_output=True, text=True, timeout=12,
            ).stdout.strip().splitlines()
            names = [x.strip() for x in out if x.strip()]
            if names:
                answer = ",".join(names)
                if any("cloudflare" in n for n in names):
                    cf_ns = True
        except Exception as exc:
            answer = f"err({type(exc).__name__})"
        detail.append(f"{server}->{answer}")
    code, size = "000", "0"
    try:
        out = subprocess.run(
            ["curl", "-s", "-L", "-o", "/tmp/ponsfi-check.html", "-w", "%{http_code} %{size_download}",
             "--max-time", "25", f"https://{DOMAIN}/"],
            capture_output=True, text=True, timeout=45,
        ).stdout.strip()
        if out:
            parts = out.split()
            code, size = parts[0], (parts[1] if len(parts) > 1 else "0")
    except Exception:
        pass
    ok = code == "200" and size.isdigit() and int(size) > 10000
    return ok, cf_ns, code, size, " ".join(detail) + f" https={code} size={size}"


def main():
    if "--test" in sys.argv:
        notify("PonsPulse 测试", "这是一条域名监控测试通知，收到即表示通知功能正常。")
        return 0
    if os.path.exists(DONE):
        return 0
    ok, cf_ns, code, size, detail = check()
    if ok:
        log("域名已生效: " + detail)
        notify("ponsfi.xyz 已生效 ✅",
               "现在可以直接分享给朋友了：https://ponsfi.xyz （www.ponsfi.xyz 同样可用）。域名 2027-10-02 到期，目前未开自动续费。")
        open(DONE, "w", encoding="utf-8").write(datetime.datetime.now().isoformat())
        stop_self()
        return 0
    now = datetime.datetime.now()
    if cf_ns:
        rounds = 0
        if os.path.exists(STUCK):
            try:
                rounds = int(open(STUCK, encoding="utf-8").read().strip() or "0")
            except Exception:
                rounds = 0
        rounds += 1
        open(STUCK, "w", encoding="utf-8").write(str(rounds))
        log(f"NS 已是 Cloudflare，站点未通({code}) 第 {rounds} 轮: " + detail)
        if rounds == 3:
            notify("ponsfi.xyz 需要检查",
                   "域名已经切到 Cloudflare，但网站还没打开（可能 Cloudflare 正在激活或隧道异常）。可以让我检查一下。")
        return 0
    if now >= DEADLINE:
        log("超期未生效: " + detail)
        notify("ponsfi.xyz 还没生效",
               "域名已注册、DNS 已改到 Cloudflare，但注册局委派一直没同步。建议让我手动处理（点 Cloudflare 的激活检查，或把 NS 改回原方案）。")
        open(DONE, "w", encoding="utf-8").write(now.isoformat())
        stop_self()
        return 0
    log("未生效 " + detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
