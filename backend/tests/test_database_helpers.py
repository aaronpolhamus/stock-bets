import json
from freezegun import freeze_time
import time

import pandas as pd
from backend.database.fixtures.mock_data import (
    simulation_start_time,
    simulation_end_time
)
from backend.database.helpers import (
    add_row,
    query_to_dict
)
from backend.logic.base import (
    get_game_info,
    make_date_offset,
    posix_to_datetime,
    get_user_information,
    make_historical_balances_and_prices_table
)
from backend.logic.metrics import calculate_metrics
from backend.tests import BaseTestCase


class TestDBHelpers(BaseTestCase):

    def test_db_helpers(self):
        dummy_symbol = "ACME"
        dummy_name = "ACME CORP"
        symbol_id = add_row("symbols", symbol=dummy_symbol, name=dummy_name)
        # There's nothing special about primary key #27. If we update the mocks this will need to update, too.
        self.assertEqual(symbol_id, 27)
        acme_entry = query_to_dict("SELECT * FROM symbols WHERE symbol = %s", dummy_symbol)[0]
        self.assertEqual(acme_entry["symbol"], dummy_symbol)
        self.assertEqual(acme_entry["name"], dummy_name)

        user_id = add_row("users",
                          name="diane browne",
                          email="db@sysadmin.com",
                          profile_pic="private",
                          username="db",
                          created_at=time.time(),
                          provider="twitter",
                          resource_uuid="aaa")
        new_entry = get_user_information(user_id)
        self.assertEqual(new_entry["name"], "diane browne")

        game_id = add_row("games",
                          creator_id=1,
                          title="db test",
                          game_mode="multi_player",
                          duration=1_000,
                          buy_in=0,
                          benchmark="return_ratio",
                          side_bets_perc=0,
                          invite_window=time.time() + 1_000_000_000_000)

        add_row("game_status",
                game_id=game_id,
                status="pending",
                users=[1, 1],
                timestamp=time.time())
        new_entry = get_game_info(game_id)
        self.assertEqual(new_entry["title"], "db test")

    def test_mock_price_data(self):
        with open("./database/fixtures/stock_data.json") as json_file:
            stock_data = json.load(json_file)

        with self.engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM prices;", conn)

        df.sort_values(["symbol", "timestamp"])
        amzn_subset = df[df["symbol"] == "AMZN"]
        self.assertEqual(amzn_subset.iloc[0]["price"], stock_data["AMZN"][0]["average"])

        nvda_subset = df[df["symbol"] == "NVDA"]
        self.assertEqual(nvda_subset.iloc[-1]["price"], stock_data["NVDA"][-1]["average"])

        self.assertEqual(df["timestamp"].min(), simulation_start_time)
        self.assertEqual(df["timestamp"].max(), simulation_end_time)


class TestDerivedDataCaching(BaseTestCase):

    def test_make_historical_balances_and_prices_table_caching(self):
        """We'll test that make_historical_balances_and_prices_table is able to operate effectively on different time
        segments, and then we'll verify the integrity of the output by repeating the test result from TestMetrics."""
        game_id = 3
        user_id = 1

        start = time.time()
        original_df = make_historical_balances_and_prices_table(game_id, user_id, simulation_start_time,
                                                                simulation_end_time)
        fresh_load_time = time.time() - start
        with self.engine.connect() as conn:
            conn.execute("TRUNCATE balances_and_prices_cache;")

        first_segment_end = simulation_start_time + (simulation_end_time - simulation_start_time) / 2
        _ = make_historical_balances_and_prices_table(game_id, user_id, simulation_start_time, first_segment_end)

        start = time.time()
        second_segment_df = make_historical_balances_and_prices_table(game_id, user_id, simulation_start_time,
                                                                      simulation_end_time)
        partial_load_time = time.time() - start
        df1 = original_df.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
        df2 = second_segment_df.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(df1, df2)

        start = time.time()
        cache_loaded_df = make_historical_balances_and_prices_table(game_id, user_id, simulation_start_time,
                                                                    simulation_end_time)
        cache_load_time = time.time() - start
        df3 = cache_loaded_df.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(df1, df3)

        self.assertLess(partial_load_time, fresh_load_time)
        self.assertLess(cache_load_time, fresh_load_time)

        game_info = get_game_info(game_id)
        offset = make_date_offset(game_info["side_bets_period"])
        with freeze_time(posix_to_datetime(simulation_start_time - 60) + offset):
            return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, simulation_start_time, time.time())
            self.assertAlmostEqual(return_ratio, -0.6133719, 4)
            self.assertAlmostEqual(sharpe_ratio, -0.5495623, 4)
