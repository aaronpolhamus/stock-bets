import os
import unittest
import time

import requests

from backend.database.helpers import reset_db
from backend.database.db import engine
from backend.logic.auth import create_jwt
from tasks.redis import rds


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
        rds.flushall()
        reset_db()
        os.system("mysql -h db -uroot main < mockdata.sql")

    def tearDown(self):
        self.requests_session.close()
        t = time.time() - self.start_time
        print('%s: ran in %.3f seconds' % (self.id(), t))
        with open("test_times.csv", "a") as outfile:
            outfile.write(f"{self.id()},{t}\n")

    def make_test_token_from_email(self, user_email: str):
        with self.engine.connect() as conn:
            user_id, _, email, _, user_name, _, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", user_email).fetchone()
        return create_jwt(email, user_id, user_name)
