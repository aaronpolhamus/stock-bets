import json
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
)
from backend.logic.visuals import get_user_information
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
