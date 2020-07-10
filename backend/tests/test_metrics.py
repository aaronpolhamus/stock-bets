from backend.tests import BaseTestCase


from backend.logic.payouts import calculate_metrics
from backend.logic.base import (
    posix_to_datetime,
    get_game_info
)
from backend.logic.base import make_date_offset
from backend.database.fixtures.mock_data import simulation_start_time


class TestMetrics(BaseTestCase):

    def test_metrics(self):
        """The canonical game #3 has 5 days worth of stock data in it. We'll use that data here to test canonical values
        for the game winning metrics
        """
        game_id = 3
        user_id = 1

        game_info = get_game_info(game_id)
        offset = make_date_offset(game_info["side_bets_period"])
        start_date = posix_to_datetime(simulation_start_time)
        end_date = posix_to_datetime(simulation_start_time) + offset
        return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, start_date, end_date)

        self.assertAlmostEqual(return_ratio, -0.61337, 4)
        self.assertAlmostEqual(sharpe_ratio, -0.54906, 4)
