#!/usr/bin/env python3
"""Publish official daily revenue every minute from an overseas Actions runner.
No derived cumulative deltas. No git commits or snapshot/history changes.
"""
import json
import os
import sys
import time
import urllib.request

SOURCE = 'https://www.stonkfun.xyz/api/v2/revenue/daily?limit=2'
DESTINATION = 'https://stonk1000x.top/api/stonk-revenue'


def publish():
    request = urllib.request.Request(SOURCE, headers={'Accept': 'application/json', 'User-Agent': 'PonsPulse/4.0.3'})
    with urllib.request.urlopen(request, timeout=20) as response:
        official = json.load(response)
    # The receiver validates all dates, timestamps and components before storing.
    request = urllib.request.Request(DESTINATION, data=json.dumps({'official': official}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.environ['STONK_LIVE_PUSH_TOKEN']}, method='POST')
    with urllib.request.urlopen(request, timeout=20) as response:
        accepted = json.load(response)
    print('Official revenue published:', official.get('generatedAt'), accepted.get('ok'), flush=True)


def main():
    deadline = time.monotonic() + int(os.environ.get('STONK_LIVE_SECONDS', '6600'))
    while time.monotonic() < deadline:
        started = time.monotonic()
        try:
            publish()
        except Exception as exc:
            # Never print headers, credentials, or full upstream responses.
            print('Revenue refresh failed:', type(exc).__name__, str(exc), file=sys.stderr, flush=True)
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(remaining, max(1, 60 - (time.monotonic() - started))))


if __name__ == '__main__':
    main()
