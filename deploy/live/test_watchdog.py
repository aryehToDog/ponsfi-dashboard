import unittest
from watchdog import decide
from datetime import datetime, timezone

NOW = 1800000000


def run(status='in_progress', age=600, id=1):
    return {'id': id, 'status': status,
            'run_started_at': datetime.fromtimestamp(NOW-age, timezone.utc).isoformat()}


class Recovery(unittest.TestCase):
    def test_missing_cron_starts_collector(self):
        self.assertEqual(decide([], {}, NOW), (True, []))

    def test_healthy_run_continues(self):
        self.assertEqual(decide([run()], {'receivedAt': NOW, 'asOf': NOW}, NOW), (False, []))

    def test_prequeue_before_normal_deadline(self):
        self.assertEqual(decide([run(age=95*60)], {'receivedAt': NOW, 'asOf': NOW}, NOW), (True, []))

    def test_no_duplicate_dispatch_when_pending(self):
        self.assertEqual(decide([run(age=100*60), run('queued', id=2)], {'receivedAt': NOW, 'asOf': NOW}, NOW), (False, []))

    def test_stalled_run_is_replaced(self):
        self.assertEqual(decide([run()], {'receivedAt': NOW-600, 'asOf': NOW-600}, NOW), (True, [1]))

    def test_queued_successor_not_cancelled_during_recovery(self):
        self.assertEqual(decide([run(), run('queued', id=2)], {}, NOW), (False, [1]))

    def test_allow_initial_startup_grace(self):
        self.assertEqual(decide([run(age=60)], {}, NOW), (False, []))


if __name__ == '__main__':
    unittest.main()
