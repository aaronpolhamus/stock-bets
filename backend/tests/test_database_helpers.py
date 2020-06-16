import time

from tests import BaseTestCase

from logic.base import get_game_info
from backend.logic.base import get_user_information
from backend.database.helpers import (
    table_updater,
    orm_rows_to_dict,
    retrieve_meta_data,
    represent_table
)


class TestDBHelpers(BaseTestCase):

    def test_basic_helpers(self):
        symbols = represent_table("symbols")
        dummy_symbol = "ACME"
        dummy_name = "ACME CORP"
        with self.db_session.connection() as conn:
            meta_table_inventory = retrieve_meta_data().tables.keys()
            database_tables = [x[0] for x in conn.execute("SHOW TABLES;").fetchall()]
            table_diff = set(meta_table_inventory) - set(database_tables)
            self.assertIs(len(table_diff), 0)
            self.db_session.remove()

        result = table_updater(symbols, symbol=dummy_symbol, name=dummy_name)
        # There's nothing special about primary key #27. If we update the mocks this will need to
        # update, too. This just shows that table_updater worked
        self.assertEqual(result.inserted_primary_key[0], 27)
        row = self.db_session.query(symbols).filter(symbols.c.symbol == dummy_symbol)
        acme_entry = orm_rows_to_dict(row)
        self.assertEqual(acme_entry["symbol"], dummy_symbol)
        self.assertEqual(acme_entry["name"], dummy_name)

    def test_meta_data_interactions(self):
        users = represent_table("users")
        result = table_updater(users,
                               name="diane browne",
                               email="db@sysadmin.com",
                               profile_pic="private",
                               username="db",
                               created_at=time.time(),
                               provider="twitter",
                               resource_uuid="aaa")
        new_entry = get_user_information(result.inserted_primary_key)
        self.assertEqual(new_entry["name"], "diane browne")

        games = represent_table("games")
        result = table_updater(games,
                               creator_id=1,
                               title="db test",
                               mode="winner_takes_all",
                               duration=1_000,
                               buy_in=0,
                               n_rebuys=0,
                               benchmark="return_ratio",
                               side_bets_perc=0,
                               invite_window=time.time() + 1_000_000_000_000)

        game_status = represent_table("game_status")
        table_updater(game_status,
                      game_id=result.inserted_primary_key,
                      status="pending",
                      users=[1, 1],
                      timestamp=time.time())

        new_entry = get_game_info(result.inserted_primary_key)
        self.assertEqual(new_entry["title"], "db test")

        # simulate what database.helpers.reset_db does
        db_metadata = retrieve_meta_data()
        db_metadata.drop_all()
        with self.db_session.connection() as conn:
            table_names = conn.execute("SHOW TABLES;").fetchall()
        self.assertEqual(table_names, [])
