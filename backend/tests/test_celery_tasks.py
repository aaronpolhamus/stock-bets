import time
from unittest.mock import patch

import json
import pandas as pd

from backend.tasks.redis import rds
from backend.tests import BaseTestCase
from backend.database.helpers import orm_rows_to_dict
from backend.logic.games import DEFAULT_INVITE_OPEN_WINDOW
from backend.tasks.definitions import (
    async_update_symbols_table,
    async_fetch_price,
    async_cache_price,
    async_suggest_symbols,
    async_add_game,
    async_respond_to_invite,
    async_service_open_games
)


class TestCeleryTasks(BaseTestCase):

    @patch("backend.tasks.definitions.get_symbols_table")
    def test_stock_data_tasks(self, mocked_symbols_table):
        update_time = time.time()
        symbol = "ACME"
        res = async_cache_price.delay(symbol, 99, update_time)
        while not res.ready():
            continue

        cache_price, cache_time = rds.get(symbol).split("_")
        self.assertEqual(float(cache_price), 99)
        self.assertEqual(float(cache_time), update_time)

        symbol = "AMZN"
        res = async_fetch_price.delay(symbol)
        while not res.ready():
            continue

        price, _ = res.result
        self.assertIsNotNone(price)
        self.assertTrue(price > 0)

        df = pd.DataFrame([{'symbol': "ACME", "name": "ACME CORP"}, {"symbol": "PSCS", "name": "PISCES VENTURES"}])
        mocked_symbols_table.return_value = df
        res = async_update_symbols_table.apply()  # (use apply for local execution in order to pass in the mock)
        while not res.ready():
            continue

        with self.engine.connect() as conn:
            stored_df = pd.read_sql("SELECT * FROM symbols;", conn)

        self.assertEqual(stored_df["id"].to_list(), [1, 2])
        del stored_df["id"]
        pd.testing.assert_frame_equal(df, stored_df)

    def test_play_game_tasks(self):
        text = "A"
        expected_suggestions = [
            {"symbol": "AAPL", "label": "AAPL (APPLE)"},
            {"symbol": "AMZN", "label": "AMZN (AMAZON)"},
            {"symbol": "GOOG", "label": "GOOG (ALPHABET CLASS C)"},
            {"symbol": "GOOGL", "label": "GOOGL (ALPHABET CLASS A)"},
            {"symbol": "T", "label": "T (AT&T)"},
        ]

        res = async_suggest_symbols.delay(text)
        while not res.ready():
            continue

        self.assertEqual(res.result, expected_suggestions)

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

        res = async_add_game.delay(mock_game)
        while not res.ready():
            continue

        games = self.meta.tables["games"]
        row = self.db_session.query(games).filter(games.c.title == game_title)
        game_entry = orm_rows_to_dict(row)

        # Check the game entry table
        # OK for these results to shift with the test fixtures
        game_id = 5
        self.assertEqual(game_entry["id"], game_id)
        for k, v in mock_game.items():
            if k == "invitees":
                continue
            self.assertAlmostEqual(game_entry[k], v, 1)

        # Confirm that game status was updated as expected
        # ------------------------------------------------
        game_status = self.meta.tables["game_status"]
        row = self.db_session.query(game_status).filter(game_status.c.game_id == game_id)
        game_status_entry = orm_rows_to_dict(row)
        self.assertEqual(game_status_entry["id"], 7)
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

        # murcitdev is going to decline to play, toofast and miguel will play and receive their virtual cash balances
        # -----------------------------------------------------------------------------------------------------------
        for user_id in [3, 4]:
            async_respond_to_invite.delay(game_id, user_id, "joined")
        async_respond_to_invite.delay(game_id, 5, "declined")

        with patch("backend.logic.games.time") as mock_time:
            mock_time.time.side_effect = [
                time.time() + DEFAULT_INVITE_OPEN_WINDOW + 1,  # users have joined, and we're past the open invite window
            ]
            async_service_open_games.apply()
