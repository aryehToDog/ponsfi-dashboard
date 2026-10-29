#!/usr/bin/env python3
"""Fixed-source STONK UTC revenue receiver. The overseas collector posts official daily data."""
import hmac
import json
import math
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = os.environ.get('PONSPULSE_LIVE_DIR', '/var/lib/pons-live')
TOKEN = os.environ.get('PONSPULSE_LIVE_TOKEN', '')
LOCK = threading.Lock()


def utcday():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def amount(row, keys):
    for key in keys:
        if row.get(key) is not None:
            value = row[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('invalid amount')
            return value
    raise ValueError('missing amount')


def normalize(body, now=None):
    now = time.time() if now is None else now
    source = body['official']
    stamp = datetime.fromisoformat(source['generatedAt'].replace('Z', '+00:00')).timestamp()
    if stamp > now + 60 or stamp < now - 900:
        raise ValueError('source timestamp outside acceptance window')
    rows = source['days']
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError('invalid days')
    current = next((row for row in rows if row.get('date') == utcday()), None)
    result = {'source': 'official-daily', 'sourceUrl': 'https://www.stonkfun.xyz/revenue',
              'asOf': stamp, 'receivedAt': now, 'refreshSeconds': 60, 'current': None}
    if current is not None:
        base = amount(current, ['revenueUsd'])
        quote = amount(current, ['quoteRevenueUsd', 'stonkQuoteRevenueUsd', 'quoteTokenRevenueUsd'])
        result['current'] = {'date': current['date'], 'rev': base + quote,
                             'baseRev': base, 'quoteRev': quote, 'asOf': stamp, 'partial': True}
    return result


def read():
    try:
        with open(os.path.join(STATE, 'revenue.json')) as handle:
            result = json.load(handle)
    except (OSError, ValueError):
        result = {'current': None, 'asOf': None, 'refreshSeconds': 60}
    if result.get('current') and result['current'].get('date') != utcday():
        result['current'] = None
    result['date'] = utcday()
    result['stale'] = not result.get('current') or not result.get('asOf') or time.time() - result['asOf'] > 180
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, payload):
        body = json.dumps(payload, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?')[0] != '/revenue':
            return self.send(404, {'error': 'not found'})
        with LOCK:
            self.send(200, read())

    def do_POST(self):
        if self.path != '/revenue':
            return self.send(404, {'error': 'not found'})
        if not TOKEN or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + TOKEN):
            return self.send(403, {'error': 'forbidden'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 100000:
                return self.send(413, {'error': 'invalid body size'})
            self.connection.settimeout(10)
            result = normalize(json.loads(self.rfile.read(size)))
            with LOCK:
                previous = read()
                if previous.get('asOf', 0) and result['asOf'] < previous['asOf']:
                    return self.send(409, {'error': 'older source data'})
                os.makedirs(STATE, exist_ok=True)
                fd, path = tempfile.mkstemp(dir=STATE)
                try:
                    with os.fdopen(fd, 'w') as handle:
                        json.dump(result, handle, allow_nan=False)
                    os.replace(path, os.path.join(STATE, 'revenue.json'))
                finally:
                    if os.path.exists(path):
                        os.unlink(path)
            self.send(200, {'ok': True, 'asOf': result['asOf']})
        except (ValueError, KeyError, TypeError, AttributeError):
            self.send(400, {'error': 'invalid official daily payload'})


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('PONSPULSE_LIVE_PORT', '8789'))), Handler).serve_forever()
