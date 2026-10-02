#!/usr/bin/env python3
"""ponsfi.xyz 解析生效检查（纯脚本，不经过模型）。

由 launchd（com.ponspulse.dns-check）每 30 分钟运行一次：
- 任一公共 DNS 能解析 且 http://ponsfi.xyz/ 返回 200 → 弹系统通知，然后停用本定时任务
- 超过 2026-10-03 10:35 还没生效 → 通知一次说明情况，然后停用
- 其余情况：安静退出（仅写一行日志）

用法: python3 domain_check.py [--test]
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "domain-check.log")
DONE = os.path.join(HERE, "domain-check.done")
LABEL = "com.ponspulse.dns-check"
DOMAIN = "ponsfi.xyz"
DEADLINE = datetime.datetime(2026, 10, 3, 10, 35)


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
    resolved = False
    for server in ("223.5.5.5", "119.29.29.29", "8.8.8.8"):
        answer = "(空)"
        try:
            out = subprocess.run(
                ["dig", "+short", "+time=3", DOMAIN, "@" + server],
                capture_output=True, text=True, timeout=12,
            ).stdout.strip().splitlines()
            first = out[0].strip() if out else ""
            if first:
                answer = first
                resolved = True
        except Exception as exc:
            answer = f"err({type(exc).__name__})"
        detail.append(f"{server}->{answer}")
    code = "000"
    try:
        code = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "20",
             f"http://{DOMAIN}/"],
            capture_output=True, text=True, timeout=40,
        ).stdout.strip() or "000"
    except Exception:
        pass
    return resolved, code, " ".join(detail) + f" http={code}"


def main():
    if "--test" in sys.argv:
        notify("PonsPulse 测试", "这是一条域名监控测试通知，收到即表示通知功能正常。")
        return 0
    if os.path.exists(DONE):
        return 0
    resolved, code, detail = check()
    now = datetime.datetime.now()
    if resolved and code == "200":
        log("域名已生效: " + detail)
        notify("ponsfi.xyz 已生效", "域名 ponsfi.xyz 已在公网生效，可以用 http://ponsfi.xyz 直接分享给朋友了。（2027-10-02 到期，未开自动续费）")
        open(DONE, "w", encoding="utf-8").write(now.isoformat())
        stop_self()
        return 0
    if now >= DEADLINE:
        log("超过 24 小时仍未生效: " + detail)
        notify("ponsfi.xyz 还没生效", "已经等了 24 小时：域名已注册、解析已配好，但注册局委派还没完全同步。建议再等等，或联系腾讯云客服看看。")
        open(DONE, "w", encoding="utf-8").write(now.isoformat())
        stop_self()
        return 0
    log("未生效 " + detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
