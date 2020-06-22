import json
import time
from unittest.mock import patch

import pandas as pd
from backend.database.helpers import query_to_dict
from backend.logic.base import (
    during_trading_day
)
from backend.logic.games import (
    process_order,
    add_game,
    place_order,
    get_all_open_orders,
    get_current_stock_holding,
    get_current_game_cash_balance,
    DEFAULT_INVITE_OPEN_WINDOW,
    DEFAULT_VIRTUAL_CASH
)
from backend.tasks.definitions import (
    async_process_all_open_orders,
    async_update_symbols_table,
    async_suggest_symbols,
    async_respond_to_game_invite,
    async_service_open_games,
    async_make_the_field_charts,
    async_serialize_current_balances,
    async_serialize_open_orders,
    async_calculate_game_metrics,
    async_get_friends_details,
    async_get_friend_invites,
    async_suggest_friends,
    async_service_one_open_game,
    async_cache_price
)
from backend.tasks.redis import (
    rds,
    unpack_redis_json
)
from backend.tests import BaseTestCase
from logic.base import fetch_iex_price


class TestStockDataTasks(BaseTestCase):

    def test_price_caching(self):
        symbol = "AMZN"
        with self.engine.connect() as conn:
            pre_count = conn.execute("SELECT COUNT(*) FROM prices;").fetchone()[0]

        # replicate internal dynamics of async_fetch_and_cache_prices
        with patch("backend.tasks.definitions.during_trading_day") as trading_day_mock:
            trading_day_mock.return_value = True

            price, timestamp = fetch_iex_price(symbol)
            async_cache_price.apply(args=[symbol, price, timestamp])

            price, timestamp = fetch_iex_price(symbol)
            async_cache_price.apply(args=[symbol, price, timestamp])

            price, timestamp = fetch_iex_price(symbol)
            async_cache_price.apply(args=[symbol, price, timestamp])

        with self.engine.connect() as conn:
            post_count = conn.execute("SELECT COUNT(*) FROM prices;").fetchone()[0]
        self.assertEqual(post_count - pre_count, 3)

    @patch("backend.tasks.definitions.get_symbols_table")
    def test_stock_data_tasks(self, mocked_symbols_table):
        df = pd.DataFrame([{'symbol': "ACME", "name": "ACME CORP"}, {"symbol": "PSCS", "name": "PISCES VENTURES"}])
        mocked_symbols_table.return_value = df
        async_update_symbols_table.apply()  # (use apply for local execution in order to pass in the mock)
        with self.engine.connect() as conn:
            stored_df = pd.read_sql("SELECT * FROM symbols;", conn)

        self.assertEqual(stored_df["id"].to_list(), [1, 2])
        del stored_df["id"]
        pd.testing.assert_frame_equal(df, stored_df)


class TestGameIntegration(BaseTestCase):

    def test_play_game_tasks(self):
        text = "A"
        expected_suggestions = [
            {"symbol": "AAPL", "label": "AAPL (APPLE)"},
            {"symbol": "AMZN", "label": "AMZN (AMAZON)"},
            {"symbol": "GOOG", "label": "GOOG (ALPHABET CLASS C)"},
            {"symbol": "GOOGL", "label": "GOOGL (ALPHABET CLASS A)"},
            {"symbol": "T", "label": "T (AT&T)"},
        ]

        result = async_suggest_symbols.apply(args=[text]).result
        self.assertEqual(result, expected_suggestions)

        start_time = time.time()
        game_title = "lucky few"
        creator_id = 1
        mock_game = {
            "creator_id": creator_id,
            "title": game_title,
            "mode": "winner_takes_all",
            "duration": 180,
            "buy_in": 100,
            "n_rebuys": 0,
            "benchmark": "return_ratio",
            "side_bets_perc": 50,
            "side_bets_period": "weekly",
            "invitees": ["miguel", "murcitdev", "toofast"]
        }

        add_game(
            mock_game["creator_id"],
            mock_game["title"],
            mock_game["mode"],
            mock_game["duration"],
            mock_game["buy_in"],
            mock_game["n_rebuys"],
            mock_game["benchmark"],
            mock_game["side_bets_perc"],
            mock_game["side_bets_period"],
            mock_game["invitees"]
        )

        game_entry = query_to_dict("SELECT * FROM games WHERE title = %s", game_title)

        # Check the game entry table
        # OK for these results to shift with the test fixtures
        game_id = 6
        self.assertEqual(game_entry["id"], game_id)
        for k, v in mock_game.items():
            if k == "invitees":
                continue
            self.assertAlmostEqual(game_entry[k], v, 1)

        # Confirm that game status was updated as expected
        # ------------------------------------------------
        game_status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s", game_id)
        self.assertEqual(game_status_entry["id"], 8)
        self.assertEqual(game_status_entry["game_id"], game_id)
        self.assertEqual(game_status_entry["status"], "pending")
        users_from_db = json.loads(game_status_entry["users"])
        self.assertEqual(users_from_db, [3, 4, 5, 1])

        # and that the game invites table is working as well
        # --------------------------------------------------
        with self.engine.connect() as conn:
            game_invites_df = pd.read_sql("SELECT * FROM game_invites WHERE game_id = %s", conn, params=[game_id])

        self.assertEqual(game_invites_df.shape, (4, 5))
        for _, row in game_invites_df.iterrows():
            self.assertIn(row["user_id"], users_from_db)
            status = "invited"
            if row["user_id"] == creator_id:
                status = "joined"
            self.assertEqual(row["status"], status)
            # less than a two-second difference between when we sent the data and when it was logged. If the local
            # celery worked is gummed up and not working properly this can fail
            self.assertTrue(row["timestamp"] - start_time < 2)

        # we'll mock in a time value for the current game in a moment, but first check that async_service_open_games is
        # working as expected

        with self.engine.connect() as conn:
            gi_count_pre = conn.execute("SELECT COUNT(*) FROM game_invites;").fetchone()[0]

        async_service_open_games.apply()

        with self.engine.connect() as conn:
            gi_count_post = conn.execute("SELECT COUNT(*) FROM game_invites;").fetchone()[0]

        self.assertEqual(gi_count_post - gi_count_pre, 6)  # We expect to see two expired invites
        with self.engine.connect() as conn:
            df = pd.read_sql("SELECT game_id, user_id, status FROM game_invites WHERE game_id in (1, 2)", conn)
            self.assertEqual(df[df["user_id"] == 5]["status"].to_list(), ["invited", "expired"])
            self.assertEqual(df[(df["user_id"] == 3) & (df["game_id"] == 2)]["status"].to_list(), ["joined", "expired"])

        # murcitdev is going to decline to play, toofast and miguel will play and receive their virtual cash balances
        # -----------------------------------------------------------------------------------------------------------
        for user_id in [3, 4]:
            async_respond_to_game_invite.apply(args=[game_id, user_id, "joined"])
        async_respond_to_game_invite.apply(args=[game_id, 5, "declined"])

        # So far so good. Pretend that we're now past the invite open window and it's time to play
        # ----------------------------------------------------------------------------------------
        game_start_time = time.time() + DEFAULT_INVITE_OPEN_WINDOW + 1
        with patch("backend.logic.games.time") as mock_time:
            # users have joined, and we're past the invite window
            mock_time.time.return_value = game_start_time
            async_service_open_games.apply()  # Execute locally wth apply in order to use time mock

            with self.engine.connect() as conn:
                # Verify game updated to active status and active players
                game_status = conn.execute(
                    "SELECT status, users FROM game_status WHERE game_id = %s ORDER BY id DESC LIMIT 0, 1",
                    game_id).fetchone()
                self.assertEqual(game_status[0], "active")
                self.assertEqual(len(set(json.loads(game_status[1])) - {1, 3, 4}), 0)

                # Verify that we have three plays for game 5 with $1,000,000 virtual cash balances
                res = conn.execute(
                    "SELECT balance FROM game_balances WHERE game_id = %s AND balance_type = 'virtual_cash';",
                    game_id).fetchall()
                balances = [x[0] for x in res]
                self.assertIs(len(balances), 3)
                self.assertTrue(all([x == DEFAULT_VIRTUAL_CASH for x in balances]))

        # For now I've tried to keep things simple and divorce the ordering part of the integration test from game
        # startup. May need to close the loop on this later when expanding the test to cover payouts
        game_start_time = 1590508896
        # Place two market orders and a buy limit order
        with patch("backend.logic.games.time") as mock_game_time, patch(
                "backend.logic.base.time") as mock_data_time:
            time_list = [
                game_start_time + 300,
                game_start_time + 300,
                game_start_time + 300
            ]
            mock_game_time.time.side_effect = mock_data_time.time.side_effect = time_list

            # Everything working as expected. Place a couple buy orders to get things started
            stock_pick = "AMZN"
            user_id = 1
            order_quantity = 500_000
            amzn_price, _ = fetch_iex_price(stock_pick)

            cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            place_order(
                user_id=user_id,
                game_id=game_id,
                symbol=stock_pick,
                buy_or_sell="buy",
                cash_balance=cash_balance,
                current_holding=current_holding,
                order_type="market",
                quantity_type="USD",
                market_price=amzn_price,
                amount=order_quantity,
                time_in_force="day"
            )

            original_amzn_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            updated_cash = get_current_game_cash_balance(user_id, game_id)
            expected_quantity = order_quantity // amzn_price
            expected_cost = expected_quantity * amzn_price
            self.assertEqual(original_amzn_holding, expected_quantity)
            test_user_original_cash = DEFAULT_VIRTUAL_CASH - expected_cost
            self.assertAlmostEqual(updated_cash, test_user_original_cash, 2)

            stock_pick = "MELI"
            user_id = 4
            order_quantity = 600
            meli_price = 600

            cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            place_order(
                user_id=user_id,
                game_id=game_id,
                symbol=stock_pick,
                buy_or_sell="buy",
                cash_balance=cash_balance,
                current_holding=current_holding,
                order_type="market",
                quantity_type="Shares",
                market_price=meli_price,
                amount=order_quantity,
                time_in_force="day"
            )

            original_meli_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            original_miguel_cash = get_current_game_cash_balance(user_id, game_id)
            self.assertEqual(original_meli_holding, order_quantity)
            miguel_cash = DEFAULT_VIRTUAL_CASH - order_quantity * meli_price
            self.assertAlmostEqual(original_miguel_cash, miguel_cash, 2)

            stock_pick = "NVDA"
            user_id = 3
            order_quantity = 1420
            nvda_limit_ratio = 0.95
            nvda_price = 350
            stop_limit_price = nvda_price * nvda_limit_ratio

            cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            place_order(
                user_id=user_id,
                game_id=game_id,
                symbol=stock_pick,
                buy_or_sell="buy",
                cash_balance=cash_balance,
                current_holding=current_holding,
                order_type="limit",
                quantity_type="Shares",
                market_price=nvda_price,
                amount=order_quantity,
                time_in_force="until_cancelled",
                stop_limit_price=stop_limit_price
            )

            updated_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            updated_cash = get_current_game_cash_balance(user_id, game_id)
            self.assertEqual(updated_holding, 0)
            self.assertEqual(updated_cash, DEFAULT_VIRTUAL_CASH)

        with patch("backend.logic.games.fetch_iex_price") as mock_price_fetch, patch(
                "backend.logic.base.time") as mock_data_time, patch("backend.logic.games.time") as mock_game_time:

            order_clear_price = stop_limit_price - 5

            amzn_stop_ratio = 0.9
            meli_limit_ratio = 1.1
            mock_price_fetch.side_effect = [
                (order_clear_price, None),
                (amzn_stop_ratio * amzn_price - 1, None),
                (meli_limit_ratio * meli_price + 1, None),
            ]
            mock_game_time.time.side_effect = [
                game_start_time + 24 * 60 * 60,  # NVDA order from above
                game_start_time + 24 * 60 * 60,
                game_start_time + 24 * 60 * 60,
                game_start_time + 24 * 60 * 60,
                game_start_time + 24 * 60 * 60,
                game_start_time + 24 * 60 * 60 + 1000,  # AMZN order needs to clear on the same day
                game_start_time + 48 * 60 * 60,  # MELI order is open until being cancelled
                game_start_time + 48 * 60 * 60,
            ]

            mock_data_time.time.side_effect = [
                game_start_time + 24 * 60 * 60,
                game_start_time + 24 * 60 * 60,
                game_start_time + 24 * 60 * 60 + 1000,
                game_start_time + 24 * 60 * 60 + 1000,
                game_start_time + 48 * 60 * 60,
                game_start_time + 48 * 60 * 60,
            ]

            # First let's go ahead and clear that last transaction that we had above
            with self.engine.connect() as conn:
                open_order_id = conn.execute("""
                                             SELECT id 
                                             FROM orders 
                                             WHERE user_id = %s AND game_id = %s AND symbol = %s;""",
                                             user_id, game_id, stock_pick).fetchone()[0]

            process_order(open_order_id)
            updated_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            updated_cash = get_current_game_cash_balance(user_id, game_id)
            self.assertEqual(updated_holding, order_quantity)
            self.assertAlmostEqual(updated_cash, DEFAULT_VIRTUAL_CASH - order_clear_price * order_quantity, 3)

            # Now let's go ahead and place stop-loss and stop-limit orders against existing positions
            stock_pick = "AMZN"
            user_id = 1
            order_quantity = 250_000

            cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            stop_limit_price = amzn_stop_ratio * amzn_price
            place_order(
                user_id=user_id,
                game_id=game_id,
                symbol=stock_pick,
                buy_or_sell="sell",
                cash_balance=cash_balance,
                current_holding=current_holding,
                order_type="stop",
                quantity_type="USD",
                market_price=stop_limit_price + 10,
                amount=order_quantity,
                time_in_force="day",
                stop_limit_price=stop_limit_price
            )

            with self.engine.connect() as conn:
                amzn_open_order_id = conn.execute("""
                                                  SELECT id 
                                                  FROM orders 
                                                  WHERE user_id = %s AND game_id = %s AND symbol = %s
                                                  ORDER BY id DESC LIMIT 0, 1;""",
                                                  user_id, game_id, stock_pick).fetchone()[0]

            stock_pick = "MELI"
            user_id = 4
            miguel_order_quantity = 300

            cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, stock_pick)
            place_order(
                user_id=user_id,
                game_id=game_id,
                symbol=stock_pick,
                buy_or_sell="sell",
                cash_balance=cash_balance,
                current_holding=current_holding,
                order_type="limit",
                quantity_type="Shares",
                market_price=meli_limit_ratio * meli_price - 10,
                amount=miguel_order_quantity,
                time_in_force="until_cancelled",
                stop_limit_price=meli_limit_ratio * meli_price
            )

            with self.engine.connect() as conn:
                meli_open_order_id = conn.execute("""
                                                  SELECT id 
                                                  FROM orders 
                                                  WHERE user_id = %s AND game_id = %s AND symbol = %s
                                                  ORDER BY id DESC LIMIT 0, 1;""",
                                                  user_id, game_id, stock_pick).fetchone()[0]

            process_order(amzn_open_order_id)
            process_order(meli_open_order_id)

            with self.engine.connect() as conn:
                query = """
                    SELECT o.user_id, o.id, o.symbol, os.clear_price
                    FROM orders o
                    INNER JOIN
                    order_status os
                    ON
                      o.id = os.order_id
                    WHERE
                      os.status = 'fulfilled' AND
                      game_id = %s;
                """
                df = pd.read_sql(query, conn, params=[game_id])

            test_user_id = 1
            test_user_stock = "AMZN"
            updated_holding = get_current_stock_holding(test_user_id, game_id, test_user_stock)
            updated_cash = get_current_game_cash_balance(test_user_id, game_id)
            amzn_clear_price = df[df["id"] == amzn_open_order_id].iloc[0]["clear_price"]
            shares_sold = 250_000 // amzn_clear_price
            # This test is a little bit awkward because of how we are handling floating point for prices and
            # doing integer round here. This may need to become more precise in the future
            self.assertTrue((updated_holding - (original_amzn_holding - shares_sold) <= 1))
            self.assertAlmostEqual(updated_cash, test_user_original_cash + shares_sold * amzn_clear_price, 2)

            test_user_id = 4
            test_user_stock = "MELI"
            updated_holding = get_current_stock_holding(test_user_id, game_id, test_user_stock)
            updated_cash = get_current_game_cash_balance(test_user_id, game_id)
            meli_clear_price = df[df["id"] == meli_open_order_id].iloc[0]["clear_price"]
            shares_sold = miguel_order_quantity
            self.assertEqual(updated_holding, original_meli_holding - shares_sold)
            self.assertAlmostEqual(updated_cash, original_miguel_cash + shares_sold * meli_clear_price, 2)


class TestVisualAssetsTasks(BaseTestCase):

    def test_async_process_all_open_orders(self):
        # TODO: this task can only run during trading hours, but since it's so critical to the app we allow it to be
        # here, in spite of being time-dependent
        if during_trading_day():

            user_id = 1
            game_id = 3

            # Place a guaranteed-to-clear order
            buy_stock = "MSFT"
            mock_buy_order = {"amount": 1,
                              "buy_or_sell": "buy",
                              "game_id": 3,
                              "order_type": "stop",
                              "stop_limit_price": 1,
                              "market_price": 0.5,
                              "quantity_type": "Shares",
                              "symbol": buy_stock,
                              "time_in_force": "until_cancelled"
                              }
            current_cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
            place_order(user_id,
                        game_id,
                        mock_buy_order["symbol"],
                        mock_buy_order["buy_or_sell"],
                        current_cash_balance,
                        current_holding,
                        mock_buy_order["order_type"],
                        mock_buy_order["quantity_type"],
                        mock_buy_order["market_price"],
                        mock_buy_order["amount"],
                        mock_buy_order["time_in_force"],
                        mock_buy_order["stop_limit_price"])

            # Place a guaranteed-to-clear order
            buy_stock = "AAPL"
            mock_buy_order = {"amount": 1,
                              "buy_or_sell": "buy",
                              "game_id": 3,
                              "order_type": "stop",
                              "stop_limit_price": 1,
                              "market_price": 0.5,
                              "quantity_type": "Shares",
                              "symbol": buy_stock,
                              "time_in_force": "until_cancelled"
                              }
            current_cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
            place_order(user_id,
                        game_id,
                        mock_buy_order["symbol"],
                        mock_buy_order["buy_or_sell"],
                        current_cash_balance,
                        current_holding,
                        mock_buy_order["order_type"],
                        mock_buy_order["quantity_type"],
                        mock_buy_order["market_price"],
                        mock_buy_order["amount"],
                        mock_buy_order["time_in_force"],
                        mock_buy_order["stop_limit_price"])

            open_orders = get_all_open_orders()
            starting_open_orders = len(open_orders)
            self.assertEqual(starting_open_orders, 6)
            res = async_process_all_open_orders.delay()
            while not res.ready():
                continue
            new_open_orders = get_all_open_orders()
            self.assertLessEqual(starting_open_orders - len(new_open_orders), 4)

    def test_line_charts(self):
        # TODO: This test throws errors related to missing data in games 1 and 4. For now we're not worried about this,
        # since game #3 is our realistic test case, but could be worth going back and debugging later.
        game_id = 3
        user_ids = [1, 3, 4]
        async_service_one_open_game.apply(args=[game_id])

        # this is basically the internals of async_update_play_game_visuals for one game
        task_results = list()
        task_results.append(async_make_the_field_charts.delay(game_id))
        for user_id in user_ids:
            task_results.append(async_serialize_open_orders.delay(game_id, user_id))
            task_results.append(async_serialize_current_balances.delay(game_id, user_id))

        # Verify that the JSON objects for chart visuals were computed and cached as expected
        field_chart = unpack_redis_json("field_chart_3")
        while field_chart is None:
            field_chart = unpack_redis_json("field_chart_3")
        self.assertIsNotNone(unpack_redis_json("current_balances_3_1"))
        self.assertIsNotNone(unpack_redis_json("current_balances_3_3"))
        self.assertIsNotNone(unpack_redis_json("current_balances_3_4"))


class TestStatsProduction(BaseTestCase):

    def test_game_player_stats(self):
        game_id = 3
        async_calculate_game_metrics.apply(args=(game_id, 1))
        async_calculate_game_metrics.apply(args=(game_id, 3))
        async_calculate_game_metrics.apply(args=(game_id, 4))

        sharpe_ratio_3_4 = rds.get("sharpe_ratio_3_4")
        while sharpe_ratio_3_4 is None:
            sharpe_ratio_3_4 = rds.get("sharpe_ratio_3_4")
        sharpe_ratio_3_3 = rds.get("sharpe_ratio_3_3")
        sharpe_ratio_3_1 = rds.get("sharpe_ratio_3_1")
        total_return_3_1 = rds.get("total_return_3_1")
        total_return_3_3 = rds.get("total_return_3_3")
        total_return_3_4 = rds.get("total_return_3_4")
        self.assertIsNotNone(sharpe_ratio_3_3)
        self.assertIsNotNone(sharpe_ratio_3_1)
        self.assertIsNotNone(total_return_3_1)
        self.assertIsNotNone(total_return_3_3)
        self.assertIsNotNone(total_return_3_4)


class TestFriendManagement(BaseTestCase):

    def test_friend_management(self):
        user_id = 1
        # check out who the tests user's friends are currently:
        res = async_get_friends_details.apply(args=[user_id])
        expected_friends = {"toofast", "miguel"}
        self.assertEqual(set([x["username"] for x in res.get()]), expected_friends)

        # what friend invites does the test user have pending?
        res = async_get_friend_invites.apply(args=[user_id])
        self.assertEqual(res.get(), ["murcitdev"])

        # if the test user wants to invite some friends, who's available? We shouldn't see the invite from murcitdev,
        # and we shouldn't the original dummy user, who hasn't picked a username yet
        result = async_suggest_friends.apply(args=[user_id, "d"]).result
        dummy_match = [x["username"] for x in result if x["label"] == "suggested"]
        self.assertEqual(dummy_match, ["dummy2"])


class TestDataAccess(BaseTestCase):

    def test_get_symbols(self):
        """For now we pull data from IEX cloud. We also scrape their daily published listing of available symbols to
        build the selection inventory for the frontend. Although the core data source will change in the future, these
        operations need to remain intact.
        """
        n_rows = 3
        res = async_update_symbols_table.delay(n_rows)
        while not res.ready():
            continue
        with self.engine.connect() as conn:
            symbols_table = pd.read_sql("SELECT * FROM symbols", conn)
        self.assertEqual(symbols_table.shape, (n_rows, 3))
        self.assertEqual(symbols_table.iloc[0]["symbol"][0], 'A')
