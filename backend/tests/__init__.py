import unittest

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from backend.database.fixtures.mock_data import make_mock_data
from backend.database.helpers import retrieve_meta_data
from config import Config


class BaseTestCase(unittest.TestCase):
    """The base test case sets up a connection with a live DB, mocks fresh data, and has metadata and API request
    properties that are useful in our testing environment. It doesn't need to be invoked in a context where checks
    against the DB or calls to the API server aren't necessary, since it does imply some setup costs.
    """

    def setUp(self):
        # Establish data base API and setup mock data
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
        self.requests_session = requests.Session()
        self.meta = retrieve_meta_data(self.engine)
        make_mock_data()

    def tearDown(self):
        self.db_session.remove()
        self.requests_session.close()
        self.engine.dispose()
