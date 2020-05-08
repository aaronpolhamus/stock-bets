import time
import unittest

import jwt
import requests
from backend.api.routes import (
    INVALID_SIGNATURE_ERROR_MSG,
    LOGIN_ERROR_MSG,
    SESSION_EXP_ERROR_MSG,
    TOKEN_ID_MISSING_MSG,
    USERNAME_TAKE_ERROR_MSG,
    create_jwt
)
from backend.database.fixtures.mock_data import make_mock_data
from backend.database.models import GameModes, Benchmarks, SideBetPeriods
from backend.logic.games import (
    unpack_enumerated_field_mappings,
    DEFAULT_GAME_MODE,
    DEFAULT_GAME_DURATION,
    DEFAULT_BUYIN,
    DEFAULT_REBUYS,
    DEFAULT_BENCHMARK,
    DEFAULT_SIDEBET_PERCENT,
    DEFAULT_SIDEBET_PERIOD
)
from config import Config
from sqlalchemy import create_engine

HOST_URL = 'https://localhost:5000/api'


class TestAPI(unittest.TestCase):

    def setUp(self):
        # Establish data base API and setup mock data
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.conn = self.engine.connect()
        self.session = requests.Session()
        make_mock_data()

    def tearDown(self):
        self.session.close()
        self.conn.close()

    def test_jwt_and_authentication(self):
        # TODO: Missing a good test for routes.register_user -- OAuth dependency is trick
        # registration error with faked token
        res = self.session.post(f"{HOST_URL}/login", json={"msg": "dummy_token"}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, TOKEN_ID_MISSING_MSG)

        # token creation and landing
        test_user = "dummy"
        user_id, name, email, pic, username, created_at = self.conn.execute("SELECT * FROM users WHERE name = %s;",
                                                                             test_user).fetchone()
        session_token = create_jwt(email, user_id, username)
        self.assertEqual(jwt.decode(session_token, Config.SECRET_KEY)["email"], email)
        self.assertEqual(jwt.decode(session_token, Config.SECRET_KEY)["user_id"], user_id)
        self.assertIsNone(jwt.decode(session_token, Config.SECRET_KEY)["username"])

        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], email)
        self.assertEqual(res.json()["name"], name)
        self.assertIsNone(res.json()["username"])
        self.assertEqual(res.json()["profile_pic"], pic)

        # logout -- this should blow away the previously created session token, logging out the user
        res = self.session.post(f"{HOST_URL}/logout", cookies={"session_token": session_token}, verify=False)
        erase_cookie_msg = 'session_token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly; Path=/'
        self.assertEqual(res.headers['Set-Cookie'], erase_cookie_msg)

        # expired token...
        session_token = create_jwt(email, 123, None, mins_per_session=1 / 60)
        time.sleep(2)
        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, SESSION_EXP_ERROR_MSG)

        # no session token sent -- user tried to skip the login step and go directly to landing page
        res = self.session.post(f"{HOST_URL}/home", verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, LOGIN_ERROR_MSG)

        # session token sent, but wasn't encrypted with our SECRET_KEY
        session_token = create_jwt(email, 123, None, secret_key="itsasecret")
        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, INVALID_SIGNATURE_ERROR_MSG)

    def test_profile_info(self):
        test_user = "dummy"
        # set username endpoint test
        user_id, name, email, pic, username, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = %s;", test_user).fetchone()
        self.assertIsNone(username)
        session_token = create_jwt(email, user_id, username)
        new_username = "peaches"
        res = self.session.post(f"{HOST_URL}/set_username", json={"username": new_username},
                                cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        conn = self.engine.connect()
        # least-code way that I could find to persist DB changes to sqlalchemy API, but feels janky...
        updated_username = conn.execute("SELECT username FROM users WHERE name = 'dummy';").fetchone()[0]
        self.assertEqual(new_username, updated_username)
        # check the cookie to be sure that it has been updated with the new proper username as well
        decoded_token = jwt.decode(res.cookies.get("session_token"), Config.SECRET_KEY)
        self.assertEqual(decoded_token["username"], new_username)
        self.assertEqual(decoded_token["email"], email)

        # take username fails with 400 error
        user_id, name, email, pic, user_name, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = 'Aaron';").fetchone()
        session_token = create_jwt(email, user_id, user_name)
        res = self.session.post(f"{HOST_URL}/set_username", json={"username": new_username},
                                cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, USERNAME_TAKE_ERROR_MSG)

    def test_game_endpoints(self):
        user_id, name, email, pic, user_name, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = 'Aaron';").fetchone()
        session_token = create_jwt(email, user_id, user_name)
        res = self.session.post(f"{HOST_URL}/game_defaults", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        game_defaults = res.json()

        expected_keys = [
            "title",
            "mode",
            "game_modes",
            "duration",
            "buy_in",
            "n_rebuys",
            "benchmark",
            "side_bets_perc",
            "side_bets_period",
            "sidebet_periods",
            "benchmarks",
            "available_participants"
        ]

        for key in expected_keys:
            self.assertIn(key, game_defaults.keys())

        games_description = self.conn.execute("SHOW COLUMNS FROM games;").fetchall()
        import ipdb;ipdb.set_trace()
        column_names = [column[0] for column in games_description if column[0] != "id"]
        for column in column_names:
            self.assertIn(column, game_defaults.keys())

        self.assertEqual(len(game_defaults["available_participants"]), 3)

        dropdown_fields_dict = {
            "game_modes": GameModes,
            "benchmarks": Benchmarks,
            "sidebet_periods": SideBetPeriods
        }
        for field, db_def in dropdown_fields_dict.items():
            field_items = unpack_enumerated_field_mappings(db_def)
            for key, value in field_items.items():
                self.assertIn(value, field_items[key])

        self.assertIsNotNone(game_defaults["title"])
        self.assertEqual(game_defaults["mode"], DEFAULT_GAME_MODE)
        self.assertEqual(game_defaults["duration"], DEFAULT_GAME_DURATION)
        self.assertEqual(game_defaults["buy_in"], DEFAULT_BUYIN)
        self.assertEqual(game_defaults["n_rebuys"], DEFAULT_REBUYS)
        self.assertEqual(game_defaults["benchmark"], DEFAULT_BENCHMARK)
        self.assertEqual(game_defaults["side_bets_perc"], DEFAULT_SIDEBET_PERCENT)
        self.assertEqual(game_defaults["side_bets_period"], DEFAULT_SIDEBET_PERIOD)
