import unittest
from sqlalchemy import create_engine

from config import Config
from backend.database.fixtures.mock_data import make_mock_data
from backend.database.helpers import (
    table_updater,
    retrieve_meta_data,
    make_db_session,
    orm_row_to_dict
)


class TestDBHelpers(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.session = make_db_session(self.engine)
        self.meta = retrieve_meta_data(self.engine)
        make_mock_data()

    def test_basic_helpers(self):
        symbols = self.meta.tables["symbols"]
        dummy_symbol = "ACME"
        dummy_name = "ACME CORP"
        with self.engine.connect() as conn:
            meta_table_inventory = self.meta.tables.keys()
            database_tables = [x[0] for x in conn.execute("SHOW TABLES;").fetchall()]
            table_diff = set(meta_table_inventory) - set(database_tables)
            self.assertIs(len(table_diff), 0)

            result = table_updater(conn, symbols, symbol=dummy_symbol, name=dummy_name)
            # There's nothing special about primary key #27. If we update the mocks this will need to
            # update, too. This just shows that table_updater worked
            self.assertEqual(result.inserted_primary_key[0], 27)
            row = self.session.query(symbols).filter(symbols.c.symbol == dummy_symbol)
            acme_entry = orm_row_to_dict(row)
            self.assertEqual(acme_entry["symbol"], dummy_symbol)
            self.assertEqual(acme_entry["name"], dummy_name)
