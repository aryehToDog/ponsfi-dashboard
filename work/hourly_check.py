#!/usr/bin/env python3
"""每小时跑一次：刷新小时级数据 → 重新渲染 → 推上线。

由 LaunchAgent com.ponspulse.hourly 每小时第 5 分钟调用。
日志：work/hourly-check.log
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(HERE, "hourly-check.log")
OUT = os.path.join(ROOT, "outputs", "pons-stonkfun-monitor.html")
TMP = "/tmp/publish-index.html"


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
        json.dump(d, open(data_p, "w", encoding="utf-8"), ensure_ascii=False)
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
