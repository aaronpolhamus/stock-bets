import unittest
import time

import jwt
import requests
from sqlalchemy import create_engine

from config import Config
from backend.database.fixtures.mock_data import make_mock_data
from backend.api.routes import (
    INVALID_SIGNATURE_ERROR_MSG,
    LOGIN_ERROR_MSG,
    SESSION_EXP_ERROR_MSG,
    TOKEN_ID_MISSING_MSG,
    create_jwt
)

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

    def test_api(self):
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

        # authentication errors

        # expired token...
        session_token = create_jwt(email, 123, mins_per_session=1/60)
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

        # set username endpoint test
        user_id, name, email, pic, user_name, created_at = self.conn.execute("SELECT * FROM users WHERE name = 'dummy';").fetchone()
        self.assertIsNone(user_name)
        session_token = create_jwt(email, user_id)
        res = self.session.post(f"{HOST_URL}/set_username", json={"username": "dummy"}, cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        conn = self.engine.connect()
        updated_username = conn.execute("SELECT username FROM users WHERE name = 'dummy';").fetchone()[0]
        self.assertEqual("dummy", updated_username)
