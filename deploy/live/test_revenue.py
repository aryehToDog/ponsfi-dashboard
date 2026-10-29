import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
import revenue


class OfficialRevenue(unittest.TestCase):
    def setUp(self):
        self.now = time.time()
        self.body = {'official': {'generatedAt': datetime.fromtimestamp(self.now, timezone.utc).isoformat(),
            'days': [{'date': revenue.utcday(), 'revenueUsd': 39204, 'stonkQuoteRevenueUsd': 7648}]}}

    def test_official_total_includes_both_sources(self):
        result = revenue.normalize(self.body, self.now)
        self.assertEqual(result['current']['rev'], 46852)
        self.assertEqual(result['current']['quoteRev'], 7648)

    def test_zero_is_real_data(self):
        self.body['official']['days'][0].update(revenueUsd=0, stonkQuoteRevenueUsd=0)
        self.assertEqual(revenue.normalize(self.body, self.now)['current']['rev'], 0)

    def test_missing_component_never_becomes_zero(self):
        del self.body['official']['days'][0]['stonkQuoteRevenueUsd']
        with self.assertRaises(ValueError):
            revenue.normalize(self.body, self.now)

    def test_invalid_amounts_rejected(self):
        for value in [None, -1, float('nan'), float('inf'), True, '123']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.body['official']['days'][0]['revenueUsd'] = value
                revenue.normalize(self.body, self.now)

    def test_old_or_future_source_cannot_be_relabelled_live(self):
        for offset in [-120, 1000]:
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                revenue.normalize(self.body, self.now + offset)

    def test_yesterday_is_not_today(self):
        self.body['official']['days'][0]['date'] = '2000-01-01'
        self.assertIsNone(revenue.normalize(self.body, self.now)['current'])

    def test_midnight_hides_previously_saved_total(self):
        data = revenue.normalize(self.body, self.now)
        with tempfile.TemporaryDirectory() as directory, patch.object(revenue, 'STATE', directory):
            with open(directory + '/revenue.json', 'w') as handle:
                json.dump(data, handle)
            with patch.object(revenue, 'utcday', return_value='2099-01-01'):
                self.assertIsNone(revenue.read()['current'])


if __name__ == '__main__':
    unittest.main()
