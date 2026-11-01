"""Offline source-contract checks for the Blockworks collector."""
import copy
import datetime as dt
import http.client
import json
import unittest
from unittest.mock import patch

from launchpad import _fetch_execution, build_payload


NOW = dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc)


def execution(query_id, rows):
    return {"data": rows, "total": len(rows), "metadata": {"execution": {
        "state": "success", "execution_id": "test-%s" % query_id, "query_id": query_id,
        "execution_ended_at": 1793446159493, "metadata": {"rowCount": len(rows)},
    }}}


def revenue(date, platform, value, missing=0):
    return {"date": date, "parent_slug": platform, "blockchain": "solana",
            "revenue_usd": value, "missing_revenue_rows": missing}


def cohort(date, platform, volume, marketcap):
    return {"block_date": date, "launchpad_id": platform, "launchpad_name": None,
            "total_volume_usd": volume, "total_marketcap_usd": marketcap,
            "total_revenue_usd": 99999999}


class IncompleteChunkResponse:
    """Public proxy sometimes supplies all JSON but omits its final chunk."""
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        raise http.client.IncompleteRead(self.body)


class LaunchpadContractTests(unittest.TestCase):
    def setUp(self):
        self.sources = {
            "15562": execution(9289, [
                revenue("2026-10-30", "stonkfun", 20), revenue("2026-10-30", "pump", 80),
                revenue("2026-11-01", "stonkfun", 999), revenue("2026-11-01", "pump", 1),
            ]),
            "5968": execution(3105, [
                cohort("2026-10-29", "stonkfun", 10, 100), cohort("2026-10-29", "pumpfun", 90, 900),
                cohort("2026-10-30", "stonkfun", 30, 200), cohort("2026-10-30", "pumpfun", 70, 800),
                cohort("2026-10-30", "unknown", 100, None),
            ]),
        }

    def test_completed_utc_day_and_correct_revenue_source(self):
        result = build_payload(self.sources, NOW)
        revenue_metric = result["metrics"]["revenue"]
        self.assertEqual((revenue_metric["date"], revenue_metric["stonk"], revenue_metric["total"]),
                         ("2026-10-30", 20, 100))
        self.assertEqual(revenue_metric["share"], 20)
        self.assertEqual(revenue_metric["rank"], 2)
        self.assertEqual(revenue_metric["platforms"][0]["id"], "pumpfun")

    def test_marketcap_is_snapshot_and_null_is_not_zero(self):
        result = build_payload(self.sources, NOW)
        marketcap = result["metrics"]["marketcap"]
        self.assertEqual((marketcap["stonk"], marketcap["total"], marketcap["period"]), (200, 1000, "snapshot"))
        self.assertEqual((marketcap["platformCount"], marketcap["missingCount"]), (2, 1))
        self.assertEqual([p["name"] for p in marketcap["platforms"]], ["Pump.fun", "StonkFun"])
        self.assertEqual(result["metrics"]["volume"]["total"], 200)
        self.assertEqual(result["metrics"]["volume"]["missingCount"], 0)

    def test_truncated_result_rejected_and_other_metrics_refresh(self):
        previous = build_payload(self.sources, NOW)
        broken = copy.deepcopy(self.sources)
        broken["15562"]["total"] += 1
        broken["5968"]["data"][2]["total_volume_usd"] = 60
        refreshed = build_payload(broken, NOW, previous)
        self.assertTrue(refreshed["metrics"]["revenue"]["stale"])
        self.assertEqual(refreshed["metrics"]["revenue"]["stonk"], 20)
        self.assertFalse(refreshed["metrics"]["volume"]["stale"])
        self.assertEqual(refreshed["metrics"]["volume"]["stonk"], 60)
        self.assertEqual(previous["metrics"]["revenue"].get("error"), None)

    def test_missing_stonk_unavailable_not_fabricated_zero(self):
        self.sources["5968"]["data"][2]["total_marketcap_usd"] = None
        result = build_payload(self.sources, NOW)
        self.assertFalse(result["metrics"]["marketcap"]["available"])
        self.assertIsNone(result["metrics"]["marketcap"]["stonk"])
        self.assertTrue(result["metrics"]["volume"]["available"])

    def test_partial_revenue_keeps_reported_amount_and_flags_source_gap(self):
        rows = self.sources["15562"]["data"] + [revenue("2026-10-30", "believe", 500, missing=1)]
        self.sources["15562"] = execution(9289, rows)
        result = build_payload(self.sources, NOW)["metrics"]["revenue"]
        self.assertEqual((result["total"], result["missingCount"], result["partialCount"], result["platformCount"]), (600, 0, 1, 3))
        self.assertEqual(result["missingSourceRows"], 1)

    def test_malformed_row_preserves_only_affected_metric_and_marks_stale(self):
        previous = build_payload(self.sources, NOW)
        self.sources["15562"]["data"][0] = None
        result = build_payload(self.sources, NOW, previous)
        self.assertTrue(result["metrics"]["revenue"]["stale"])
        self.assertEqual(result["metrics"]["revenue"]["stonk"], previous["metrics"]["revenue"]["stonk"])
        self.assertEqual(result["metrics"]["revenue"]["sourceUpdated"], previous["metrics"]["revenue"]["sourceUpdated"])
        self.assertEqual(result["metrics"]["revenue"]["date"], previous["metrics"]["revenue"]["date"])
        self.assertFalse(result["metrics"]["volume"]["stale"])
        without_cache = build_payload(self.sources, NOW)
        self.assertFalse(without_cache["metrics"]["revenue"]["available"])
        self.assertIsNone(without_cache["metrics"]["revenue"]["stonk"])

    def test_malformed_metadata_is_unavailable_and_source_delay_is_explicit(self):
        self.sources["15562"]["metadata"] = None
        result = build_payload(self.sources, NOW)
        self.assertFalse(result["metrics"]["revenue"]["available"])
        self.assertTrue(result["metrics"]["volume"]["sourceDelayed"])
        self.assertEqual(result["metrics"]["volume"]["sourceLagDays"], 2)

    def test_query_identity_and_duplicates_rejected(self):
        self.sources["15562"]["metadata"]["execution"]["query_id"] = 3105
        self.sources["5968"]["data"].append(cohort("2026-10-30", "stonkfun", 1, 1))
        self.sources["5968"]["total"] += 1
        self.sources["5968"]["metadata"]["execution"]["metadata"]["rowCount"] += 1
        result = build_payload(self.sources, NOW)
        self.assertFalse(result["metrics"]["revenue"]["available"])
        self.assertFalse(result["metrics"]["volume"]["available"])

    def test_missing_http_chunk_accepted_only_with_complete_validated_json(self):
        body = json.dumps(self.sources["15562"]).encode()
        with patch("launchpad.urllib.request.urlopen", return_value=IncompleteChunkResponse(body)) as request:
            actual = _fetch_execution("15562")
        self.assertEqual(actual, self.sources["15562"])
        self.assertEqual(request.call_count, 1)

    def test_truncated_http_json_is_retried_then_rejected(self):
        body = json.dumps(self.sources["15562"]).encode()[:-20]
        with patch("launchpad.urllib.request.urlopen", return_value=IncompleteChunkResponse(body)) as request, patch("launchpad.time.sleep"):
            with self.assertRaises(ValueError):
                _fetch_execution("15562")
        self.assertEqual(request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
