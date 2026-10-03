#!/usr/bin/env python3
"""ponsfi.xyz 极简浏览计数器 —— 只用 Python 标准库，不需要装任何依赖。

  GET /hit          计一次浏览（PV +1；同一天同一 IP 去重算 UV），返回统计
  GET /stats        只读统计，不计数
  GET /likes                 只读点赞总数
  GET /likes?d=N             「共勉」栏点赞 +N（只能加不能减；N 上限 20，
                             连点由前端攒成一批发过来，少几个请求）
  GET /like?d=N             同上（两个路径都接）
  GET /health       存活检查

数据落在 $COUNTER_DIR/counts.json（默认 /var/lib/pons-counter），
先写临时文件再 os.replace，进程被杀也不会写坏；每天保留最近 400 天。
由 systemd 托管，nginx 把 /api/hits 反代到本机 8788 端口。
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import threading
import urllib.parse
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA_DIR = os.environ.get("COUNTER_DIR", "/var/lib/pons-counter")
DATA = os.path.join(DATA_DIR, "counts.json")
PORT = int(os.environ.get("COUNTER_PORT", "8788"))
TZ = timezone(timedelta(hours=8))          # 按北京时间分天
KEEP_DAYS = 400
SALT = os.environ.get("COUNTER_SALT", "ponsfi.xyz")

# 爬虫 / 探针 / 监控不计数（Cloudflare 已挡掉一部分，这里再挡一层）
BOT = re.compile(
    r"(bot|spider|crawler|slurp|bingpreview|facebookexternalhit|curl|wget|"
    r"python-requests|go-http-client|headless|phantomjs|uptime|monitor|"
    r"pingdom|statuscake|lighthouse)",
    re.I,
)

_lock = threading.Lock()


def today():
    return datetime.now(TZ).strftime("%Y-%m-%d")


def load():
    try:
        with open(DATA, encoding="utf-8") as fh:
            d = json.load(fh)
        if not isinstance(d, dict) or "days" not in d:
            raise ValueError
    except Exception:
        d = {"total": 0, "days": {}, "since": today()}
    d.setdefault("total", 0)
    d.setdefault("days", {})
    d.setdefault("since", today())
    d.setdefault("likes", 0)
    d.setdefault("likeDays", {})
    return d


def save(d):
    os.makedirs(DATA_DIR, exist_ok=True)
    for key in sorted(d["days"])[:-KEEP_DAYS]:
        d["days"].pop(key, None)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, prefix=".counts-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, DATA)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def snapshot(d):
    t = today()
    day = d["days"].get(t) or {"pv": 0, "uv": []}
    return {
        "total": int(d["total"]),
        "today": int(day.get("pv", 0)),
        "uvToday": len(day.get("uv") or []),
        "likes": int(d.get("likes", 0)),
        "likesToday": int((d.get("likeDays") or {}).get(t, 0)),
        "day": t,
        "since": d.get("since", t),
    }


def likes_only(d):
    """只读：共勉栏的累计点赞数（六句话共用同一个数）。"""
    return {"likes": int(d.get("likes", 0)),
            "likesToday": int((d.get("likeDays") or {}).get(today(), 0))}


def like(delta):
    """点赞 +delta（delta > 0）；返回新的总数。只加不减，所以永远不小于 0。"""
    day_key = today()
    with _lock:
        d = load()
        cur = max(0, int(d.get("likes", 0)) + int(delta))
        d["likes"] = cur
        ld = d.setdefault("likeDays", {})
        ld[day_key] = max(0, int(ld.get(day_key, 0)) + int(delta))
        save(d)
        return {"likes": cur, "likesToday": int(ld.get(day_key, 0))}


def visitor_hash(ip, day):
    """不存原始 IP：只存「IP + 当天 + 盐」的 SHA-256 前 16 位。"""
    return hashlib.sha256(f"{ip}|{day}|{SALT}".encode()).hexdigest()[:16]


def hit(ip, ua):
    if BOT.search(ua or ""):
        with _lock:
            return snapshot(load()), False
    day_key = today()
    h = visitor_hash(ip, day_key)
    with _lock:
        d = load()
        day = d["days"].setdefault(day_key, {"pv": 0, "uv": []})
        day["pv"] = int(day.get("pv", 0)) + 1
        if h not in day["uv"]:
            day["uv"].append(h)
        d["total"] = int(d["total"]) + 1
        save(d)
        return snapshot(d), True


class Handler(BaseHTTPRequestHandler):
    server_version = "pons-counter/1.0"
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass                                # 不刷日志，需要时看 systemd journal

    def _delta(self):
        """从 ?d=N 取增量。只认正数（点赞只加不减），非法/负数一律当 0＝只读；单次最多 20。"""
        try:
            q = urllib.parse.urlparse(self.path).query
            v = int(urllib.parse.parse_qs(q).get("d", ["0"])[0])
        except Exception:
            return 0
        return min(v, 20) if v > 0 else 0

    def do_GET(self):
        raw = self.path
        path = raw.split("?")[0].rstrip("/") or "/hit"
        ip = (self.headers.get("CF-Connecting-IP")
              or self.headers.get("X-Real-IP")
              or self.client_address[0])
        ua = self.headers.get("User-Agent", "")
        try:
            if path in ("/hit", "/"):
                data, _counted = hit(ip, ua)
                self._send(200, data)
            elif path == "/stats":
                with _lock:
                    self._send(200, snapshot(load()))
            elif path in ("/likes", "/like"):
                # nginx 把 /api/likes 统一转到 /likes：带 ?d=1 / ?d=-1 才是点赞/取消，
                # 不带 d（或 d=0）＝只读。两个路径都接，少一层出错的可能。
                delta = self._delta()
                if delta:
                    self._send(200, like(delta))
                else:
                    with _lock:
                        self._send(200, likes_only(load()))
            elif path == "/health":
                self._send(200, {"ok": True})
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:            # 出错也别把服务打挂
            self._send(500, {"error": str(exc)})


def main():
    counts = snapshot(load())
    print(f"pons-counter 启动 · 端口 {PORT} · 目录 {DATA_DIR} · 已有 {counts['total']} 次浏览"
          f" · {counts['likes']} 个赞", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
