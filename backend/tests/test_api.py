import time
import unittest
from datetime import datetime as dt, timedelta

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
from backend.database.helpers import retrieve_meta_data
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
    DEFAULT_SIDEBET_PERIOD,
    DEFAULT_INVITE_OPEN_WINDOW
)
from config import Config
from sqlalchemy import create_engine, select

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
        session_token = create_jwt(email, user_id, None, mins_per_session=1 / 60)
        time.sleep(2)
        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, SESSION_EXP_ERROR_MSG)

        # no session token sent -- user tried to skip the login step and go directly to landing page
        res = self.session.post(f"{HOST_URL}/home", verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, LOGIN_ERROR_MSG)

        # session token sent, but wasn't encrypted with our SECRET_KEY
        session_token = create_jwt(email, user_id, None, secret_key="itsasecret")
        res = self.session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, INVALID_SIGNATURE_ERROR_MSG)

    def test_set_username(self):
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
        # least-code way that I could find to persist DB changes to sqlalchemy API, but feels janky...
        updated_username = self.engine.execute("SELECT username FROM users WHERE name = 'dummy';").fetchone()[0]
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

    def test_game_defaults(self):
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
            "available_invitees"
        ]

        for key in expected_keys:
            self.assertIn(key, game_defaults.keys())

        games_description = self.conn.execute("SHOW COLUMNS FROM games;").fetchall()
        column_names = [column[0] for column in games_description if column[0] != "id"]
        # For ease of use, make sure that the JSON object being passed back and forth with the
        # database has the same field names as the db table
        for column in column_names:
            self.assertIn(column, game_defaults.keys())

        self.assertEqual(len(game_defaults["available_invitees"]), 3)

        dropdown_fields_dict = {
            "game_modes": GameModes,
            "benchmarks": Benchmarks,
            "sidebet_periods": SideBetPeriods
        }

        for field, enum_class in dropdown_fields_dict.items():
            field_items = unpack_enumerated_field_mappings(enum_class)
            db_values = [item.name for item in enum_class]
            frontend_labels = [item.value for item in enum_class]
            for key, value in field_items.items():
                self.assertIn(key, db_values)
                self.assertIn(value, frontend_labels)

        self.assertIsNotNone(game_defaults["title"])
        self.assertEqual(game_defaults["mode"], DEFAULT_GAME_MODE)
        self.assertEqual(game_defaults["duration"], DEFAULT_GAME_DURATION)
        self.assertEqual(game_defaults["buy_in"], DEFAULT_BUYIN)
        self.assertEqual(game_defaults["n_rebuys"], DEFAULT_REBUYS)
        self.assertEqual(game_defaults["benchmark"], DEFAULT_BENCHMARK)
        self.assertEqual(game_defaults["side_bets_perc"], DEFAULT_SIDEBET_PERCENT)
        self.assertEqual(game_defaults["side_bets_period"], DEFAULT_SIDEBET_PERIOD)

    def test_create_game(self):
        user_id, name, email, pic, user_name, created_at = self.conn.execute(
            "SELECT * FROM users WHERE name = 'Aaron';").fetchone()
        session_token = create_jwt(email, user_id, user_name)
        game_settings = {
            "benchmark": "sharpe_ratio",
            "buy_in": 1000,
            "duration": 365,
            "mode": "winner_takes_all",
            "n_rebuys": 3,
            "invitees": ["miguel", "toofast", "murcitdev", "peaches"],
            "side_bets_perc": 50,
            "side_bets_period": "weekly",
            "title": "stupified northcutt"
        }
        res = self.session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token}, verify=False,
                                json=game_settings)
        self.assertEqual(res.status_code, 200)
        # inspect subsequent DB entries
        game_id, title, mode, duration, buy_in, n_rebuys, benchmark, side_bets_perc, side_bets_period = self.engine.execute(
            "SELECT * FROM games WHERE title = %s;", game_settings["title"]).fetchone()
        status_id, game_id_status, status, updated_at = self.engine.execute(
            "SELECT * FROM game_status WHERE game_id = %s;", game_id).fetchone()
        invite_entries = self.engine.execute("SELECT * FROM game_invites WHERE game_id = %s", game_id).fetchall()

        self.assertEqual(game_settings["buy_in"], buy_in)
        self.assertEqual(game_settings["duration"], duration)
        self.assertEqual(game_settings["mode"], mode)
        self.assertEqual(game_settings["n_rebuys"], n_rebuys)
        self.assertEqual(game_settings["benchmark"], benchmark)
        self.assertEqual(game_settings["side_bets_perc"], side_bets_perc)
        self.assertEqual(game_settings["side_bets_period"], side_bets_period)
        self.assertEqual(game_settings["title"], title)

        self.assertEqual(game_id, game_id_status)
        self.assertEqual(status, "pending")

        self.assertEqual(user_id, invite_entries[0][1])
        self.assertEqual(game_id, invite_entries[0][3])
        self.assertEqual(updated_at + timedelta(hours=DEFAULT_INVITE_OPEN_WINDOW), invite_entries[0][4])
        self.assertEqual(updated_at, invite_entries[0][5])

        metadata = retrieve_meta_data()
        users = metadata.tables["users"]
        invitees = tuple(game_settings["invitees"])
        lookup_invitee_ids = self.engine.execute(select([users.c.id], users.c.username.in_(invitees))).fetchall()
        lookup_invitee_ids = [entry[0] for entry in lookup_invitee_ids]
        invite_table_invitees = [entry[2] for entry in invite_entries]
        self.assertEqual(set(lookup_invitee_ids), set(invite_table_invitees))
