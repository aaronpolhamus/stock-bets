from os import getenv
import unittest

from config import Config


class TestConfig(unittest.TestCase):

    def test_config(self):
        self.assertEqual(Config.GOOGLE_VALIDATION_URL, "https://www.googleapis.com/oauth2/v3/tokeninfo")
        self.assertEqual(Config.SECRET_KEY, getenv("SECRET_KEY"))
        self.assertEqual(Config.MINUTES_PER_SESSION, int(getenv("MINUTES_PER_SESSION")))
        db_user = getenv("DB_USER")
        db_password = getenv("DB_PASSWORD")
        db_host = getenv("DB_HOST")
        db_port = getenv("DB_PORT")
        db_name = getenv("DB_NAME")
        db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
        self.assertEqual(Config.SQLALCHEMY_DATABASE_URI, db_uri)
        self.assertEqual(Config.SQLALCHEMY_TRACK_MODIFICATIONS, getenv("SQLALCHEMY_TRACK_MODIFICATIONS"))
        self.assertEqual(Config.SQLALCHEMY_ECHO, bool(getenv("SQLALCHEMY_ECHO")))
        self.assertEqual(Config.DEBUG_MODE, bool(getenv("DEBUG_MODE") == "True"))
        self.assertEqual(Config.JWT_ENCODE_ALGORITHM, "HS256")
