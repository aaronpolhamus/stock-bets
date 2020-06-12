from unittest.mock import patch

import pandas as pd

from backend.tests import BaseTestCase
from backend.tasks.redis import (
    rds,
    unpack_redis_json
)
from backend.logic.base import get_user_id
from backend.logic.games import (
    respond_to_invite,
    get_user_invite_statuses_for_pending_game,
    start_game_if_all_invites_responded,
    DEFAULT_VIRTUAL_CASH
)
from backend.logic.visuals import (
    SIDEBAR_STATS_PREFIX,
    OPEN_ORDERS_PREFIX,
    CURRENT_BALANCES_PREFIX,
    FIELD_CHART_PREFIX,
    BALANCES_CHART_PREFIX,
    NULL_RGBA
)


class TestGameKickoff(BaseTestCase):
    """Charts should be populated with blank data until at least one user places an order, regardless of whether the
    game starts on or off of a trading day. This test guarantees that that happens
    """

    def _start_game_runner(self, start_time, game_id):
        user_statuses = get_user_invite_statuses_for_pending_game(game_id)
        pending_user_usernames = [x["username"] for x in user_statuses if x["status"] == "invited"]
        pending_user_ids = [get_user_id(x) for x in pending_user_usernames]

        # get all user IDs for the game. For this test case everyone is going ot accept
        with self.db_session.connection() as conn:
            result = conn.execute("SELECT DISTINCT user_id FROM game_invites WHERE game_id = %s", game_id).fetchall()
            self.db_session.remove()
        all_ids = [x[0] for x in result]
        user_id = all_ids[0]

        # this sequence simulates that happens inside async_respond_to_game_invite
        for user_id in pending_user_ids:
            respond_to_invite(game_id, user_id, "joined", start_time)

        # check that we have the balances that we expect
        sql = "SELECT balance, user_id from game_balances WHERE game_id = %s;"
        df = pd.read_sql(sql, self.db_session.connection(), params=[game_id])
        self.assertTrue(df.shape, (0, 2))

        # this sequence simulates that happens inside async_respond_to_game_invite
        with patch("backend.logic.games.time") as game_time_mock, patch("backend.logic.base.time") as base_time_mock:
            game_time_mock.time.return_value = start_time
            base_time_mock.time.side_effect = [start_time] * len(all_ids) * 2 * 2
            for user_id in pending_user_ids:
                respond_to_invite(game_id, user_id, "joined", start_time)

            start_game_if_all_invites_responded(game_id)

        sql = "SELECT balance, user_id from game_balances WHERE game_id = %s;"
        df = pd.read_sql(sql, self.db_session.connection(), params=[game_id])
        self.assertTrue(df.shape, (4, 2))

        # a couple things should have just happened here. We expect to have the following assets available to us
        # now in our redis cache: (1) an empty open orders table for each user, (2) an empty current balances table for
        # each user, (3) an empty field chart for each user, (4) an empty field chart, and (5) an initial game stats
        # list
        cache_keys = rds.keys()
        self.assertIn(f"{SIDEBAR_STATS_PREFIX}_{game_id}", cache_keys)
        self.assertIn(f"{FIELD_CHART_PREFIX}_{game_id}", cache_keys)
        for user_id in all_ids:
            self.assertIn(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{user_id}", cache_keys)
            self.assertIn(f"{OPEN_ORDERS_PREFIX}_{game_id}_{user_id}", cache_keys)
            self.assertIn(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}", cache_keys)

        # quickly verify the structure of the chart assets. They should be blank, with transparent colors
        field_chart = unpack_redis_json(f"{FIELD_CHART_PREFIX}_{game_id}")
        self.assertEqual(len(field_chart["line_data"]), len(all_ids))
        self.assertTrue(all([x == NULL_RGBA for x in field_chart["colors"]]))

        sidebar_stats = unpack_redis_json(f"{SIDEBAR_STATS_PREFIX}_{game_id}")
        self.assertEqual(len(sidebar_stats["records"]), len(all_ids))
        self.assertTrue(all([x["cash_balance"] == DEFAULT_VIRTUAL_CASH for x in sidebar_stats["records"]]))

        a_current_balance_table = unpack_redis_json(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{user_id}")
        self.assertEqual(a_current_balance_table["data"], [])
        self.assertEqual(len(a_current_balance_table["headers"]), 5)

        an_open_orders_table = unpack_redis_json(f"{OPEN_ORDERS_PREFIX}_{game_id}_{user_id}")
        self.assertEqual(an_open_orders_table["data"], [])
        self.assertEqual(len(an_open_orders_table["headers"]), 7)

        a_balances_chart = unpack_redis_json(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}")
        self.assertEqual(len(a_balances_chart["line_data"]), 1)
        self.assertEqual(a_balances_chart["line_data"][0]["id"], "Cash")
        self.assertEqual(len(a_balances_chart["colors"]), 1)
        self.assertEqual(a_balances_chart["colors"][0], NULL_RGBA)

    def test_kickoff_after_hours(self):
        game_id = 5
        start_time = 1591923966
        self._start_game_runner(start_time, game_id)

    def test_kickoff_during_trading(self):
        game_id = 5
        start_time = 1591978045
        self._start_game_runner(start_time, game_id)
