import time
import json

from sqlalchemy import select

from backend.tests import BaseTestCase
from backend.tasks.definitions import (
    update_game_table,
    update_symbols_table,
    fetch_price,
    cache_price,
    fetch_symbols,
    place_order,
    process_single_order,
    process_open_orders
)


class TestCeleryTasks(BaseTestCase):

    def test_data_tasks(self):
        pass

    def test_game_tasks(self):
        game_title = "noble bucket"
        invited_users = ['miguel', 'toofast', 'murcitdev']
        game_settings = {
            "creator_id": 1,
            "title": game_title,
            "mode": "return_weighted",
            "duration": 7,
            "buy_in": 100,
            "n_rebuys": 5,
            "benchmark": "return_ratio",
            "side_bets_perc": 0,
            "side_bets_period": "weekly",
            "invite_window": time.time() + 100_000,
            "invitees": invited_users
        }
        result = update_game_table.delay(game_settings)
        while not result.ready():
            continue

        with self.engine.connect() as conn:
            games_entry = conn.execute(
                "SELECT * FROM games WHERE title = %s;", game_settings["title"]).fetchone()
            status_entry = conn.execute("SELECT * FROM game_status WHERE game_id = %s;", games_entry[0]).fetchone()

            self.assertEqual(games_entry[2], game_title)
            invitees_from_db = json.loads(status_entry[3])

            users = self.meta.tables["users"]
            lookup_invitee_ids = conn.execute(select([users.c.id], users.c.username.in_(invited_users))).fetchall()
            lookup_invitee_ids = [x[0] for x in lookup_invitee_ids]
            self.assertIs(len(set(lookup_invitee_ids) - set(invitees_from_db)), 0)
