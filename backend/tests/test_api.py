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
        user_id, name, email, pic, user_name, created_at = self.conn.execute("SELECT * FROM users;").fetchone()
        session_token = create_jwt(email, user_id)
        self.assertEqual(jwt.decode(session_token, Config.SECRET_KEY)["email"], email)
        self.assertEqual(jwt.decode(session_token, Config.SECRET_KEY)["user_id"], user_id)

        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], email)
        self.assertEqual(res.json()["name"], name)
        self.assertEqual(res.json()["profile_pic"], pic)

        # logout -- this should blow away the previously created session token, logging out the user
        res = self.session.post(f"{HOST_URL}/logout", cookies={"session_token": session_token}, verify=False)
        erase_cookie_msg = 'session_token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; HttpOnly; Path=/'
        self.assertEqual(res.headers['Set-Cookie'], erase_cookie_msg)

        # expired token...
        session_token = create_jwt(email, 123, mins_per_session=1 / 60)
        time.sleep(2)
        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, SESSION_EXP_ERROR_MSG)

        # no session token sent -- user tried to skip the login step and go directly to landing page
        res = self.session.post(f"{HOST_URL}/home", verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, LOGIN_ERROR_MSG)

        # session token sent, but wasn't encrypted with our SECRET_KEY
        session_token = create_jwt(email, 123, secret_key="itsasecret")
        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, INVALID_SIGNATURE_ERROR_MSG)

    def test_profile_info(self):
        # set username endpoint test
        user_id, name, email, pic, user_name, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = 'dummy';").fetchone()
        self.assertIsNone(user_name)
        session_token = create_jwt(email, user_id)
        new_user_name = "cheetos"
        res = self.session.post(f"{HOST_URL}/set_username", json={"username": new_user_name},
                                cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        conn = self.engine.connect()
        # least-code way that I could find to persist DB changes to sqlalchemy API, but feels janky...
        updated_username = conn.execute("SELECT username FROM users WHERE name = 'dummy';").fetchone()[0]
        self.assertEqual(new_user_name, updated_username)

        # take username fails with 400 error
        user_id, name, email, pic, user_name, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = 'Aaron';").fetchone()
        session_token = create_jwt(email, user_id)
        res = self.session.post(f"{HOST_URL}/set_username", json={"username": new_user_name},
                                cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, USERNAME_TAKE_ERROR_MSG)

    def test_game_endpoints(self):
        user_id, name, email, pic, user_name, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = 'Aaron';").fetchone()
        session_token = create_jwt(email, user_id)
        res = self.session.post(f"{HOST_URL}/game_defaults", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        game_defaults = res.json()

        expected_keys = [
            "default_title",
            "default_game_mode",
            "game_modes",
            "default_duration",
            "default_buyin",
            "default_rebuys",
            "default_benchmark",
            "default_sidebet_pct",
            "default_sidebet_period",
            "sidebet_periods",
            "benchmarks",
            "available_participants"
        ]
        for key in expected_keys:
            self.assertIn(key, expected_keys)

        self.assertEqual(len(game_defaults["available_participants"]), 2)

        dropdown_fields_dict = {
            "game_modes": GameModes,
            "benchmarks": Benchmarks,
            "sidebet_periods": SideBetPeriods
        }
        for field, db_def in dropdown_fields_dict.items():
            field_list = unpack_enumerated_field_mappings(db_def)
            for entry in field_list:
                self.assertIn(entry, game_defaults[field])

        self.assertIsNotNone(game_defaults["default_title"])
        self.assertEqual(game_defaults["default_game_mode"], DEFAULT_GAME_MODE)
        self.assertEqual(game_defaults["default_duration"], DEFAULT_GAME_DURATION)
        self.assertEqual(game_defaults["default_buyin"], DEFAULT_BUYIN)
        self.assertEqual(game_defaults["default_rebuys"], DEFAULT_REBUYS)
        self.assertEqual(game_defaults["default_benchmark"], DEFAULT_BENCHMARK)
        self.assertEqual(game_defaults["default_sidebet_pct"], DEFAULT_SIDEBET_PERCENT)
        self.assertEqual(game_defaults["default_sidebet_period"], DEFAULT_SIDEBET_PERIOD)
