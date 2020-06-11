import unittest

import requests

from backend.database.helpers import reset_db
from backend.database.db import (
    db_session,
    db_metadata
)
from backend.logic.auth import create_jwt
from backend.database.fixtures.mock_data import make_mock_data
from tasks.redis import rds


class BaseTestCase(unittest.TestCase):
    """The base test case sets up a connection with a live DB, mocks fresh data, and has metadata and API request
    properties that are useful in our testing environment. It doesn't need to be invoked in a context where checks
    against the DB or calls to the API server aren't necessary, since it does imply some setup costs.
    """

    def setUp(self):
        # Establish data base API and setup mock data
        self.db_session = db_session
        self.db_metadata = db_metadata
        self.requests_session = requests.Session()
        rds.flushall()
        reset_db()
        make_mock_data()

    def tearDown(self):
        self.db_session.remove()
        self.requests_session.close()

    def make_test_token_from_email(self, user_email: str):
        with self.db_session.connection() as conn:
            user_id, _, email, _, user_name, _, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", user_email).fetchone()
            self.db_session.remove()
        return create_jwt(email, user_id, user_name)
