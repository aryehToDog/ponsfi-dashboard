#!/usr/bin/env python3
"""Collect the public Blockworks Solana launchpad charts without credentials.

Revenue uses chart 15562/query 9289. Volume and launched-token market caps use
chart 5968/query 3105. The latter query's total_revenue_usd is deliberately not
used: it is a different revenue definition. All comparisons use the most recent
completed UTC date in each source, and market caps are point-in-time values.
"""
import copy
import datetime as dt
import http.client
import json
import math
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


SOURCE_URL = "https://app.blockworks.com/projects/solana/analytics/solana-launchpads"
ENDPOINT = "https://app.blockworks.com/api/blockworks-studio/dashboard/339/visualization/{}/execution"
CHARTS = {"revenue": "15562", "volume": "5968", "marketcap": "5968"}
QUERY_IDS = {"15562": 9289, "5968": 3105, "7603": 3105}
FIELDS = {
    "revenue": ("date", "parent_slug", "revenue_usd"),
    "volume": ("block_date", "launchpad_id", "total_volume_usd"),
    "marketcap": ("block_date", "launchpad_id", "total_marketcap_usd"),
}
ALIASES = {"pump": "pumpfun", "bonk": "bonkfun", "jupiter": "jup-studio"}
NAMES = {
    "stonkfun": "StonkFun", "pumpfun": "Pump.fun", "bonkfun": "BONKfun",
    "raydium": "Raydium LaunchLab", "meteora": "Meteora DBC", "bags": "Bags",
    "metadao": "MetaDAO", "moonshot": "Moonshot", "jup-studio": "Jup Studio",
    "printr": "Printr", "believe": "Believe", "dubdub": "DubDub",
}
DEFINITIONS = {
    "revenue": "Blockworks Solana: Launchpad Revenue（query 9289），按日平台收入；不替代 STONK 官方实时收入。",
    "volume": "按代币最初发射平台归属，统计 bonding curve、毕业池及其他池的总成交量。",
    "marketcap": "各平台发射代币的期末总市值，不是平台币（如 $STONK）自身市值；不跨日期累加。",
}


def _utc_now(now=None):
    if now is None:
        return dt.datetime.now(dt.timezone.utc)
    if isinstance(now, (int, float)):
        return dt.datetime.fromtimestamp(now, dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return now.astimezone(dt.timezone.utc)


def _iso_timestamp(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("missing execution timestamp")
    # The public proxy reports execution_ended_at in milliseconds.
    stamp = dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc)
    return stamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def _valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _validate_execution(payload, chart):
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("invalid execution response")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("execution"), dict):
        raise ValueError("invalid execution metadata")
    execution = metadata["execution"]
    rows = payload["data"]
    schema = execution.get("metadata")
    if not isinstance(schema, dict):
        raise ValueError("invalid execution schema")
    expected = schema.get("rowCount")
    if execution.get("state") != "success" or not execution.get("execution_id"):
        raise ValueError("execution is not successful")
    if execution.get("query_id") != QUERY_IDS[str(chart)]:
        raise ValueError("unexpected query identity")
    if not rows or payload.get("total") != len(rows) or expected != len(rows):
        raise ValueError("incomplete execution rows")
    _iso_timestamp(execution.get("execution_ended_at"))
    return rows, execution


def _daily_metric(rows, metric, date):
    date_field, id_field, value_field = FIELDS[metric]
    values = []
    missing = 0
    partial = 0
    missing_source_rows = 0
    seen = set()
    for row in rows:
        platform_id = row.get(id_field)
        if not isinstance(platform_id, str) or not platform_id:
            raise ValueError("missing platform identity")
        platform_id = ALIASES.get(platform_id, platform_id)
        if platform_id in seen:
            raise ValueError("duplicate platform on one date")
        seen.add(platform_id)
        if metric == "revenue" and row.get("blockchain") != "solana":
            raise ValueError("unexpected blockchain in Solana revenue")
        value = row.get(value_field)
        incomplete = False
        if metric == "revenue":
            count = row.get("missing_revenue_rows")
            if not isinstance(count, int) or count < 0:
                raise ValueError("invalid revenue coverage")
            if count:
                # Retain the reported value to match the source chart, while
                # explicitly disclosing any absent underlying source rows.
                incomplete = True
                missing_source_rows += count
        if value is None:
            missing += 1
            continue
        if not _valid_number(value):
            raise ValueError("invalid monetary value")
        name = NAMES.get(platform_id) or row.get("launchpad_name") or row.get("launchpad_series") or platform_id
        values.append({"id": platform_id, "name": name, "value": value, "incomplete": incomplete})
        partial += int(incomplete)
    stonk = next((p["value"] for p in values if p["id"] == "stonkfun"), None)
    if stonk is None:
        raise ValueError("STONK missing from latest completed date")
    total = math.fsum(p["value"] for p in values)
    if not total > 0:
        raise ValueError("empty platform denominator")
    values.sort(key=lambda p: (-p["value"], p["id"]))
    for platform in values:
        platform["share"] = platform["value"] / total * 100
    return {
        "date": date, "period": "snapshot" if metric == "marketcap" else "1d", "unit": "USD",
        "stonk": stonk, "total": total, "share": stonk / total * 100,
        "rank": 1 + sum(p["value"] > stonk for p in values),
        "platformCount": len(values), "missingCount": missing, "partialCount": partial, "platforms": values,
        "missingSourceRows": missing_source_rows,
        "stonkIncomplete": any(p["id"] == "stonkfun" and p["incomplete"] for p in values),
        "available": True,
    }


def _normalize_metric(payload, metric, chart, now):
    rows, execution = _validate_execution(payload, chart)
    date_field = FIELDS[metric][0]
    by_date = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid execution row")
        raw_date = row.get(date_field)
        if not isinstance(raw_date, str):
            raise ValueError("invalid source date")
        parsed = dt.date.fromisoformat(raw_date[:10])
        # Exclude any in-progress UTC day, including future-dated source rows.
        if parsed < now.date():
            by_date[parsed.isoformat()].append(row)
    if not by_date:
        raise ValueError("no completed UTC date")
    latest_date = max(by_date)
    current = _daily_metric(by_date[latest_date], metric, latest_date)
    current.update({
        "sourceUpdated": _iso_timestamp(execution["execution_ended_at"]),
        "sourceQueryId": execution["query_id"], "executionId": execution["execution_id"],
        "sourceChartId": int(chart), "stale": False, "definition": DEFINITIONS[metric],
        "coverage": "Blockworks 已覆盖且当日有披露数值的平台；缺失数值不作零处理，源数据缺项单独标注；占比不代表整个 Solana 生态。",
        "sourceLagDays": (now.date() - dt.date.fromisoformat(latest_date)).days,
        "sourceDelayed": (now.date() - dt.date.fromisoformat(latest_date)).days > 1,
    })
    history = []
    for date in sorted(by_date)[-90:]:
        try:
            daily = current if date == latest_date else _daily_metric(by_date[date], metric, date)
        except ValueError:
            # A hole in source reporting remains a gap, never a fabricated 0.
            continue
        history.append({key: daily[key] for key in (
            "date", "stonk", "total", "share", "rank", "platformCount", "missingCount", "partialCount")})
    return current, history


def _unavailable(metric, error):
    return {
        "date": None, "period": "snapshot" if metric == "marketcap" else "1d", "unit": "USD",
        "stonk": None, "total": None, "share": None, "rank": None, "platformCount": 0,
        "missingCount": None, "partialCount": None, "platforms": [], "sourceUpdated": None,
        "available": False, "stale": True, "error": error,
        "definition": DEFINITIONS[metric],
    }


def build_payload(executions, now=None, previous=None):
    """Normalize chart-id-keyed public responses; supports offline fixtures.

    ``now`` is a UTC-aware datetime or Unix seconds. Invalid/missing metrics
    preserve their own previous snapshot and become stale, without hiding a
    successful refresh of the other metrics.
    """
    now = _utc_now(now)
    previous = previous if isinstance(previous, dict) else {}
    result = {
        "generated": int(now.timestamp()), "source": "blockworks", "sourceUrl": SOURCE_URL,
        "timezone": "UTC", "metrics": {}, "history": {},
        "coverage": "仅比较 Blockworks Solana Launchpads 数据集已覆盖平台，三项指标分别使用同源同日分子和分母。",
    }
    previous_metrics = previous.get("metrics") if isinstance(previous.get("metrics"), dict) else {}
    previous_history = previous.get("history") if isinstance(previous.get("history"), dict) else {}
    for metric, chart in CHARTS.items():
        payload = executions.get(chart, executions.get(int(chart)))
        if payload is None and chart == "5968":
            payload = executions.get("7603", executions.get(7603))
            if payload is not None:
                chart = "7603"
        try:
            current, history = _normalize_metric(payload, metric, chart, now)
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            error = str(exc) if isinstance(exc, ValueError) else "invalid source response"
            prior = previous_metrics.get(metric)
            if isinstance(prior, dict) and prior.get("available", prior.get("stonk") is not None):
                current = copy.deepcopy(prior)
                current.update({"stale": True, "error": error})
                history = copy.deepcopy(previous_history.get(metric, []))[-90:]
            else:
                current, history = _unavailable(metric, error), []
        result["metrics"][metric] = current
        result["history"][metric] = history
    return result


def _fetch_execution(chart):
    """Two attempts, each bounded to 20 seconds; no keys or login required."""
    request = urllib.request.Request(ENDPOINT.format(chart), headers={
        "Accept": "application/json", "User-Agent": "StonkPulse/1.0 (public chart monitoring)",
    })
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                try:
                    body = response.read()
                except http.client.IncompleteRead as exc:
                    # Some proxy responses omit the last HTTP chunk marker.
                    # Accept only valid JSON with the exact successful row count.
                    body = exc.partial
            payload = json.loads(body)
            _validate_execution(payload, chart)
            return payload
        except (OSError, ValueError, http.client.HTTPException):
            if attempt:
                raise
            time.sleep(0.25)


def fetch_launchpads(previous=None):
    """Return normalized daily revenue, volume and token-cohort market caps."""
    executions = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = {chart: executor.submit(_fetch_execution, chart) for chart in ("15562", "5968")}
        for chart, job in jobs.items():
            try:
                executions[chart] = job.result()
            except Exception as exc:
                # Log no response bodies or auth data; preserve cached values.
                print("Blockworks chart %s refresh failed: %s" % (chart, type(exc).__name__), flush=True)
    return build_payload(executions, previous=previous)


if __name__ == "__main__":
    print(json.dumps(fetch_launchpads(), ensure_ascii=False, separators=(",", ":")))
