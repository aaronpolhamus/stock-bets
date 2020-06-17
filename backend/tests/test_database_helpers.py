import time

from tests import BaseTestCase

from logic.base import get_game_info
from backend.logic.base import get_user_information
from backend.database.helpers import (
    add_row,
    query_to_dict
)


class TestDBHelpers(BaseTestCase):

    def test_db_helpers(self):
        dummy_symbol = "ACME"
        dummy_name = "ACME CORP"
        symbol_id = add_row("symbols", symbol=dummy_symbol, name=dummy_name)
        # There's nothing special about primary key #27. If we update the mocks this will need to update, too.
        self.assertEqual(symbol_id, 27)
        acme_entry = query_to_dict("SELECT * FROM symbols WHERE symbol = %s", dummy_symbol)
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
                          mode="winner_takes_all",
                          duration=1_000,
                          buy_in=0,
                          n_rebuys=0,
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
