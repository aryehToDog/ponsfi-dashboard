#!/usr/bin/env python3
"""Publish official daily revenue every minute from an overseas Actions runner.
No derived cumulative deltas. No git commits or snapshot/history changes.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse

SOURCE = 'https://www.stonkfun.xyz/api/v2/revenue/daily?limit=2'
DESTINATION = 'https://stonk1000x.top/api/stonk-revenue'


def publish():
    request = urllib.request.Request(SOURCE, headers={'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible; PonsPulse/4.0.3)'})
    with urllib.request.urlopen(request, timeout=20) as response:
        official = json.load(response)
    # The receiver validates all dates, timestamps and components before storing.
    request = urllib.request.Request(DESTINATION, data=json.dumps({'official': official}).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0', 'Authorization': 'Bearer ' + os.environ['STONK_LIVE_PUSH_TOKEN']}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        accepted = json.load(response)
    print('Official revenue published:', official.get('generatedAt'), accepted.get('ok'), flush=True)


def main():
    deadline = time.monotonic() + int(os.environ.get('STONK_LIVE_SECONDS', '6600'))
    failures = 0
    while time.monotonic() < deadline:
        started = time.monotonic()
        try:
            publish()
            failures = 0
        except Exception as exc:
            # Never print headers, credentials, or full upstream responses.
            host = urllib.parse.urlsplit(getattr(exc, 'url', '')).hostname or 'collector'
            print('Revenue refresh failed:', host, type(exc).__name__, str(exc), file=sys.stderr, flush=True)
            failures += 1
            if failures >= 3:
                raise SystemExit('Three consecutive refresh failures')
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(remaining, max(1, 60 - (time.monotonic() - started))))


if __name__ == '__main__':
    main()
