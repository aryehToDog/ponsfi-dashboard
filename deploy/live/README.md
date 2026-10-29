# STONK UTC live revenue

The detail hero uses the official daily row for the current UTC date:
`revenueUsd + stonkQuoteRevenueUsd` (the official **Total revenue** column).
It does not use all-time balance deltas, rolling 24h revenue, or estimates.

The domestic server cannot reliably reach StonkFun. `stonk-live.yml` therefore
runs an overseas collector, bypasses cached daily API responses with a per-request
query timestamp, and posts the official response to the fixed
`/api/stonk-revenue` receiver every 60 seconds. A scheduled runner starts every
30 minutes and replaces the previous collector; each collector can bridge a
missed schedule for up to 110 minutes. GitHub scheduling/outages may delay data;
the page marks source data older than 180 seconds as delayed. This does not
change historical charts, snapshot commits, completed-day averages, or counters.

The receiver listens on loopback port 8789, validates source timestamps and both
nonnegative finite income components, rejects regressing source timestamps,
and stores the last successful response atomically in `/var/lib/pons-live`.
GET is public; POST requires `STONK_LIVE_PUSH_TOKEN`, which must match
`PONSPULSE_LIVE_TOKEN` in the root-only `/etc/pons-live.env` file.
Never commit this value. The receiver hides a saved row after UTC midnight.

Install `revenue.py` at `/opt/pons-live/revenue.py`, install the supplied systemd
unit, configure the matching GitHub Actions secret, then enable `pons-live`.
Add this location to the existing dashboard Nginx server and validate/reload:

```nginx
location = /api/stonk-revenue {
    client_max_body_size 100k;
    proxy_pass http://127.0.0.1:8789/revenue;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 15s;
    add_header Cache-Control "no-store, max-age=0" always;
}
```

Check the public endpoint and `journalctl -u pons-live`. The workflow log shows
only official timestamps and publish success, never credentials. To recover
from a delayed scheduled job, dispatch `STONK 实时收入` manually. Disabling this
workflow stops updates; the UI will then show the last source time and delayed
status. Python standard library only; no runtime packages are required.

Validation: `python3 -m unittest discover -s deploy/live -p 'test_*.py'`.
