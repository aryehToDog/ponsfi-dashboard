#!/usr/bin/env python3
"""Keep the overseas revenue collector running without relying on GitHub cron."""
import json
import os
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = 'https://api.github.com/repos/aryehToDog/ponsfi-dashboard'
STATE = Path(os.environ.get('PONSPULSE_WATCHDOG_DIR', '/var/lib/pons-live-watchdog'))
TOKEN_FILE = Path('/home/ubuntu/ponspulse/.gh-token')
ACTIVE = {'in_progress'}
PENDING = {'queued', 'pending', 'waiting', 'requested'}


def run_age(run, now):
    stamp = run.get('run_started_at') or run.get('created_at')
    return now - datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()


def decide(runs, revenue, now):
    running = [r for r in runs if r['status'] in ACTIVE]
    pending = [r for r in runs if r['status'] in PENDING]
    received = revenue.get('receivedAt') or 0
    source = revenue.get('asOf') or 0
    stale = now - min(received, source) > 300
    # A queued successor can start immediately when the current 110m run ends.
    # Healthy current runs are never cancelled by a scheduled or manual start.
    dispatch = not pending and (not running or any(run_age(r, now) >= 95 * 60 for r in running) or (stale and any(run_age(r, now) > 300 for r in running)))
    cancel = [r['id'] for r in running if stale and run_age(r, now) > 300]
    return dispatch, cancel


def api(path, method='GET', payload=None):
    token = TOKEN_FILE.read_text().strip()
    req = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'User-Agent': 'PonsPulse-live-watchdog'})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read() or b'{}')


def main():
    now = time.time()
    STATE.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen('http://127.0.0.1:8789/revenue', timeout=5) as response:
            revenue = json.load(response)
    except (OSError, ValueError):
        revenue = {}
    runs = api('/actions/workflows/stonk-live.yml/runs?per_page=10')['workflow_runs']
    dispatch, cancel = decide(runs, revenue, now)
    last_file = STATE / 'last-dispatch'
    try:
        last_dispatch = float(last_file.read_text())
    except (OSError, ValueError):
        last_dispatch = 0
    if dispatch and now - last_dispatch >= 180:
        api('/actions/workflows/stonk-live.yml/dispatches', 'POST', {'ref': 'main'})
        last_file.write_text(str(now))
        print('Requested revenue collector; waiting for official data.', flush=True)
    # Queue the replacement before cancelling a stalled runner.
    for run_id in cancel:
        api('/actions/runs/' + str(run_id) + '/cancel', 'POST')
        print('Cancelled stalled collector:', run_id, flush=True)
    if not dispatch and not cancel:
        print('Collector healthy or successor already queued.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # HTTP exception strings contain no authorization headers or secret values.
        raise SystemExit('Watchdog check failed: ' + str(exc))
