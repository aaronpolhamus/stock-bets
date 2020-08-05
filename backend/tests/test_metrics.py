from backend.tests import BaseTestCase
from unittest import TestCase
from unittest.mock import patch

from backend.logic.metrics import (
    calculate_metrics,
    check_if_payout_time
)
from backend.logic.base import (
    datetime_to_posix,
    posix_to_datetime,
    get_game_info
)
from backend.logic.base import make_date_offset
from backend.database.fixtures.mock_data import simulation_start_time


class TestMetrics(BaseTestCase):

    @patch("backend.logic.base.time")
    def test_metrics(self, base_time_mock):
        """The canonical game #3 has 5 days worth of stock data in it. We'll use that data here to test canonical values
        for the game winning metrics
        """
        game_id = 3
        user_id = 1

        game_info = get_game_info(game_id)
        offset = make_date_offset(game_info["side_bets_period"])
        end_time = datetime_to_posix(posix_to_datetime(simulation_start_time) + offset)
        base_time_mock.time.return_value = end_time
        return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, simulation_start_time, end_time)

        self.assertAlmostEqual(return_ratio, -0.6133719, 4)
        self.assertAlmostEqual(sharpe_ratio, -0.5490682, 4)


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
