from os import getenv
import unittest

from config import Config


class TestConfig(unittest.TestCase):

    def test_config(self):
        self.assertEqual(Config.GOOGLE_VALIDATION_URL, "https://www.googleapis.com/oauth2/v3/tokeninfo")
        self.assertEqual(Config.SECRET_KEY, getenv("SECRET_KEY"))
        self.assertIsNotNone(Config.SECRET_KEY)
        self.assertEqual(Config.MINUTES_PER_SESSION, int(getenv("MINUTES_PER_SESSION")))
        self.assertIsNotNone(Config.MINUTES_PER_SESSION)
        self.assertEqual(Config.TEST_CASE_EMAIL, getenv("TEST_CASE_EMAIL"))
        self.assertIsNotNone(Config.TEST_CASE_EMAIL)
        db_user = getenv("MYSQL_USER")
        self.assertIsNotNone(db_user)
        db_password = getenv("MYSQL_ROOT_PASSWORD")
        self.assertIsNotNone(db_password)
        db_host = getenv("MYSQL_HOST")
        self.assertIsNotNone(db_host)
        db_port = getenv("MYSQL_PORT")
        self.assertIsNotNone(db_port)
        db_name = getenv("MYSQL_DATABASE")
        self.assertIsNotNone(db_name)
        db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
        self.assertEqual(Config.SQLALCHEMY_DATABASE_URI, db_uri)
        self.assertIsNotNone(Config.SQLALCHEMY_DATABASE_URI)
        self.assertEqual(Config.SQLALCHEMY_TRACK_MODIFICATIONS, getenv("SQLALCHEMY_TRACK_MODIFICATIONS"))
        self.assertIsNotNone(Config.SQLALCHEMY_TRACK_MODIFICATIONS)
        self.assertEqual(Config.SQLALCHEMY_ECHO, bool(getenv("SQLALCHEMY_ECHO") == "True"))
        self.assertIsNotNone(Config.SQLALCHEMY_ECHO)
        self.assertEqual(Config.DEBUG_MODE, bool(getenv("DEBUG_MODE") == "True"))
        self.assertIsNotNone(Config.DEBUG_MODE)
        self.assertEqual(Config.JWT_ENCODE_ALGORITHM, "HS256")
        self.assertIsNotNone(Config.JWT_ENCODE_ALGORITHM)
