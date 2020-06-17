"""There's a lot of overlap between these tests and a few other tests files, but what defines this group of tests is
that they are logic-level tests of how what the users do impacts what the users see
"""

from unittest.mock import patch

import pandas as pd
from backend.logic.base import get_user_id
from backend.logic.games import (
    get_current_game_cash_balance,
    get_current_stock_holding,
    respond_to_invite,
    get_user_invite_statuses_for_pending_game,
    start_game_if_all_invites_responded,
    place_order,
    DEFAULT_VIRTUAL_CASH
)
from backend.logic.visuals import (
    serialize_and_pack_orders_open_orders,
    serialize_and_pack_current_balances,
    serialize_and_pack_balances_chart,
    compile_and_pack_player_sidebar_stats,
    make_balances_chart_data,
    SIDEBAR_STATS_PREFIX,
    OPEN_ORDERS_PREFIX,
    CURRENT_BALANCES_PREFIX,
    FIELD_CHART_PREFIX,
    BALANCES_CHART_PREFIX,
    NULL_RGBA
)
from backend.tasks.redis import (
    rds,
    unpack_redis_json
)
from backend.tests import BaseTestCase


class TestGameKickoff(BaseTestCase):
    """Charts should be populated with blank data until at least one user places an order, regardless of whether the
    game starts on or off of a trading day. This test guarantees that that happens
    """

    def _start_game_runner(self, start_time, game_id):
        user_statuses = get_user_invite_statuses_for_pending_game(game_id)
        pending_user_usernames = [x["username"] for x in user_statuses if x["status"] == "invited"]
        pending_user_ids = [get_user_id(x) for x in pending_user_usernames]

        # get all user IDs for the game. For this test case everyone is going ot accept
        with self.engine.connect() as conn:
            result = conn.execute("SELECT DISTINCT user_id FROM game_invites WHERE game_id = %s", game_id).fetchall()
        all_ids = [x[0] for x in result]
        self.user_id = all_ids[0]

        # this sequence simulates that happens inside async_respond_to_game_invite
        for user_id in pending_user_ids:
            respond_to_invite(game_id, user_id, "joined", start_time)

        # check that we have the balances that we expect
        sql = "SELECT balance, user_id from game_balances WHERE game_id = %s;"
        with self.engine.connect() as conn:
            df = pd.read_sql(sql, conn, params=[game_id])
        self.assertTrue(df.shape, (0, 2))

        # this sequence simulates that happens inside async_respond_to_game_invite
        with patch("backend.logic.games.time") as game_time_mock, patch("backend.logic.base.time") as base_time_mock:
            game_time_mock.time.return_value = start_time
            base_time_mock.time.side_effect = [start_time] * len(all_ids) * 2 * 2
            for user_id in pending_user_ids:
                respond_to_invite(game_id, user_id, "joined", start_time)

            start_game_if_all_invites_responded(game_id)

        sql = "SELECT balance, user_id from game_balances WHERE game_id = %s;"
        with self.engine.connect() as conn:
            df = pd.read_sql(sql, conn, params=[game_id])
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

        a_current_balance_table = unpack_redis_json(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(a_current_balance_table["data"], [])
        self.assertEqual(len(a_current_balance_table["headers"]), 5)

        an_open_orders_table = unpack_redis_json(f"{OPEN_ORDERS_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(an_open_orders_table["data"], [])
        self.assertEqual(len(an_open_orders_table["headers"]), 7)

        a_balances_chart = unpack_redis_json(f"{BALANCES_CHART_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(len(a_balances_chart["line_data"]), 1)
        self.assertEqual(a_balances_chart["line_data"][0]["id"], "Cash")
        self.assertEqual(len(a_balances_chart["colors"]), 1)
        self.assertEqual(a_balances_chart["colors"][0], NULL_RGBA)

        # now have a user put in a couple orders. These should go straight to the queue and be reflected in the open
        # orders table, but they should not have any impact on the user's balances
        self.stock_pick = "TSLA"
        self.market_price = 1_000
        with patch("backend.logic.games.time") as game_time_mock, patch("backend.logic.base.time") as base_time_mock:
            game_time_mock.time.side_effect = [start_time] * 2
            base_time_mock.time.return_value = start_time
            stock_pick = self.stock_pick
            cash_balance = get_current_game_cash_balance(self.user_id, game_id)
            current_holding = get_current_stock_holding(self.user_id, game_id, stock_pick)
            rds.flushall()  # clear out the initial and verify that it rebuilds visual assets properly
            place_order(
                user_id=self.user_id,
                game_id=game_id,
                symbol=self.stock_pick,
                buy_or_sell="buy",
                cash_balance=cash_balance,
                current_holding=current_holding,
                order_type="market",
                quantity_type="Shares",
                market_price=self.market_price,
                amount=1,
                time_in_force="day"
            )

    def test_visuals_after_hours(self):
        game_id = 5
        start_time = 1591923966
        self._start_game_runner(start_time, game_id)

        # These are the internals of the celery tasks that called to update their state
        serialize_and_pack_orders_open_orders(game_id, self.user_id)
        open_orders = unpack_redis_json(f"{OPEN_ORDERS_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(open_orders["data"][0]["Symbol"], self.stock_pick)
        self.assertEqual(len(open_orders["data"]), 1)

        serialize_and_pack_current_balances(game_id, self.user_id)
        current_balances = unpack_redis_json(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(len(current_balances["data"]), 0)

        with patch("backend.logic.base.time") as base_time_mock:
            base_time_mock.time.side_effect = [start_time] * 2 * 2
            df = make_balances_chart_data(game_id, self.user_id)
            serialize_and_pack_balances_chart(df, game_id, self.user_id)
            balances_chart = unpack_redis_json(f"{BALANCES_CHART_PREFIX}_{game_id}_{self.user_id}")
            self.assertEqual(len(balances_chart["line_data"]), 1)
            self.assertEqual(balances_chart["line_data"][0]["id"], "Cash")
            self.assertEqual(len(balances_chart["colors"]), 1)
            self.assertEqual(balances_chart["colors"][0], NULL_RGBA)

            compile_and_pack_player_sidebar_stats(game_id)
            sidebar_stats = unpack_redis_json(f"{SIDEBAR_STATS_PREFIX}_{game_id}")
            self.assertTrue(all([x["cash_balance"] == DEFAULT_VIRTUAL_CASH for x in sidebar_stats["records"]]))

        # The number of cached transactions that we expect an order to refresh
        self.assertEqual(len(rds.keys()), 4)

    def test_visuals_during_trading(self):
        game_id = 5
        start_time = 1591978045
        self._start_game_runner(start_time, game_id)

        # now have a user put in a couple orders. Valid market orders should clear and reflect in the balances table,
        # valid stop/limit orders should post to pending orders, and if they're good
        # These are the internals of the celery tasks that called to update their state
        serialize_and_pack_orders_open_orders(game_id, self.user_id)
        open_orders = unpack_redis_json(f"{OPEN_ORDERS_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(len(open_orders["data"]), 0)

        serialize_and_pack_current_balances(game_id, self.user_id)
        current_balances = unpack_redis_json(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{self.user_id}")
        self.assertEqual(len(current_balances["data"]), 1)

        with patch("backend.logic.base.time") as base_time_mock:
            base_time_mock.time.side_effect = [start_time] * 2 * 2
            df = make_balances_chart_data(game_id, self.user_id)
            serialize_and_pack_balances_chart(df, game_id, self.user_id)
            balances_chart = unpack_redis_json(f"{BALANCES_CHART_PREFIX}_{game_id}_{self.user_id}")

            self.assertEqual(len(balances_chart["line_data"]), 2)
            stocks = set([x["id"] for x in balances_chart["line_data"]])
            self.assertEqual(stocks, {"Cash", self.stock_pick})
            self.assertEqual(len(balances_chart["colors"]), 2)
            self.assertNotIn(NULL_RGBA, balances_chart["colors"])

            compile_and_pack_player_sidebar_stats(game_id)
            sidebar_stats = unpack_redis_json(f"{SIDEBAR_STATS_PREFIX}_{game_id}")
            user_stat_entry = [x for x in sidebar_stats["records"] if x["id"] == self.user_id][0]
            self.assertEqual(user_stat_entry["cash_balance"], DEFAULT_VIRTUAL_CASH - self.market_price)
            self.assertTrue(all([x["cash_balance"] == DEFAULT_VIRTUAL_CASH for x in sidebar_stats["records"] if
                                 x["id"] != self.user_id]))

        # The number of cached transactions that we expect an order to refresh
        self.assertEqual(len(rds.keys()), 4)
