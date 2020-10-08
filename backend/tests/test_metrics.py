from freezegun import freeze_time
from unittest import TestCase
from unittest.mock import patch
import time

from backend.logic.metrics import (
    calculate_metrics,
    check_if_payout_time,
    elo_update,
    expected_elo
)
from backend.logic.base import (
    posix_to_datetime,
    get_game_info
)
from backend.logic.base import make_date_offset
from backend.database.fixtures.mock_data import simulation_start_time
from backend.tests import BaseTestCase


class TestMetrics(BaseTestCase):

    def test_metrics(self):
        """The canonical game #3 has 5 days worth of stock data in it. We'll use that data here to test canonical values
        for the game winning metrics
        """
        game_id = 3
        user_id = 1
        game_info = get_game_info(game_id)
        offset = make_date_offset(game_info["side_bets_period"])
        with freeze_time(posix_to_datetime(simulation_start_time - 60) + offset):
            return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, simulation_start_time, time.time())

        self.assertAlmostEqual(return_ratio, -0.6133719, 4)
        self.assertAlmostEqual(sharpe_ratio, -0.5495623, 4)


class TestCheckPayoutTime(TestCase):

    def test_check_payout_time(self):
        with patch("backend.logic.base.time") as base_time_mock:
            # scenario 0: current time is greater than next payout time
            base_time_mock.time.return_value = current_time = 1594402834.874968
            payout_time = 1594402834.874968 - 60
            self.assertTrue(check_if_payout_time(current_time, payout_time))

            # scenario 1: during trading day, prior to next payout date
            base_time_mock.time.return_value = current_time = 1594402834.874968
            payout_time = 1594402834.874968 + 60
            self.assertFalse(check_if_payout_time(current_time, payout_time))

            # scenario 2: after trading, prior to next payout date, but next payout time is during next trading day
            base_time_mock.time.return_value = current_time = 1594338309.5143447
            payout_time = 1594402834.874968
            self.assertFalse(check_if_payout_time(current_time, payout_time))

            # scenario 3: after trading, prior to next payout date, but next payout date is before next trade opening
            base_time_mock.time.return_value = current_time = 1594403158.059148 + 4 * 60 * 60
            payout_time = 1594403158.059148 + 8 * 60 * 60
            self.assertTrue(check_if_payout_time(current_time, payout_time))


class TestEloRating(TestCase):

    def test_elo_rating(self):
        self.assertEqual(round(expected_elo(1613, 1609), 3), 0.506)
        self.assertEqual(round(expected_elo(1613, 1477), 3), 0.686)
        self.assertEqual(round(expected_elo(1613, 1388), 3), 0.785)
        self.assertEqual(round(expected_elo(1613, 1586), 3), 0.539)
        self.assertEqual(round(expected_elo(1613, 1720), 3), 0.351)

        pairs = [
            (0, 0),
            (1, 1),
            (10, 20),
            (123, 456),
            (2400, 2500),
        ]

        for a, b in pairs:
            self.assertEqual(round(expected_elo(a, b) + expected_elo(b, a), 3), 1.0)

        exp = 0
        exp += expected_elo(1613, 1609)
        exp += expected_elo(1613, 1477)
        exp += expected_elo(1613, 1388)
        exp += expected_elo(1613, 1586)
        exp += expected_elo(1613, 1720)
        score = (0 + 0.5 + 1 + 1 + 0)

        self.assertEqual(round(elo_update(1613, exp, score, k=32)), 1601)
        self.assertEqual(round(elo_update(1613, exp, 3, k=32)), 1617)
