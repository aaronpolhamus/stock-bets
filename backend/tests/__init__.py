import os
import time
import unittest

import requests
from backend.database.db import engine
from backend.database.helpers import add_row
from backend.database.helpers import (
    reset_db,
    query_to_dict,
    drop_all_tables
)
from backend.logic.auth import create_jwt
from backend.logic.metrics import STARTING_ELO_SCORE
from backend.logic.stock_data import TRACKED_INDEXES
from backend.tasks import s3_cache


class BaseTestCase(unittest.TestCase):
    """The base test case sets up a connection with a live DB, mocks fresh data, and has metadata and API request
    properties that are useful in our testing environment. It doesn't need to be invoked in a context where checks
    against the DB or calls to the API server aren't necessary, since it does imply some setup costs.
    """

    def setUp(self):
        self.start_time = time.time()
        # Establish data base API and setup mock data
        self.engine = engine
        self.requests_session = requests.Session()
        s3_cache.flushall()
        reset_db()
        os.system("mysql -h db -uroot main < mockdata.sql")

    def tearDown(self):
        self.requests_session.close()
        t = time.time() - self.start_time
        print('%s: ran in %.3f seconds' % (self.id(), t))
        with open("test_times.csv", "a") as outfile:
            outfile.write(f"{self.id()},{t}\n")

    @staticmethod
    def make_test_token_from_email(email: str):
        user_entry = query_to_dict("SELECT * FROM users WHERE email = %s", email)[0]
        return create_jwt(user_entry["email"], user_entry["id"], user_entry["username"])


class CanonicalSplitsCase(unittest.TestCase):

    def setUp(self):
        self.game_id = 82
        self.user_id = 1
        self.start_time = time.time()
        self.engine = engine
        self.requests_session = requests.Session()
        s3_cache.flushall()
        drop_all_tables()
        os.system(f"mysql -h db -uroot main < database/fixtures/canonical_games/game_id_{self.game_id}.sql")

    def tearDown(self):
        self.requests_session.close()
        t = time.time() - self.start_time
        print('%s: ran in %.3f seconds' % (self.id(), t))
        with open("test_times.csv", "a") as outfile:
            outfile.write(f"{self.id()},{t}\n")


class StockbetsRatingCase(unittest.TestCase):

    def setUp(self):
        self.game_id = 47
        self.start_time = time.time()
        self.engine = engine
        self.requests_session = requests.Session()
        s3_cache.flushall()
        drop_all_tables()
        os.system(f"mysql -h db -uroot main < database/fixtures/canonical_games/game_id_{self.game_id}.sql")
        last_row = query_to_dict("SELECT * FROM stockbets_rating ORDER BY id DESC LIMIT 0, 1")[0]
        _id = last_row["id"]

        # manually add the indexes that we want to track to the scores table
        for index in TRACKED_INDEXES:
            add_row("stockbets_rating", id=_id, index_symbol=index, rating=STARTING_ELO_SCORE, update_type="sign_up",
                    timestamp=-99)
            _id += 1

    def tearDown(self):
        self.requests_session.close()
        t = time.time() - self.start_time
        print('%s: ran in %.3f seconds' % (self.id(), t))
        with open("test_times.csv", "a") as outfile:
            outfile.write(f"{self.id()},{t}\n")
