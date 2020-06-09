import json
import time

import jwt
from backend.api.routes import (
    INVALID_SIGNATURE_ERROR_MSG,
    LOGIN_ERROR_MSG,
    SESSION_EXP_ERROR_MSG,
    USERNAME_TAKE_ERROR_MSG,
    OAUTH_ERROR_MSG,
    INVALID_OAUTH_PROVIDER_MSG,
)
from backend.database.helpers import orm_rows_to_dict
from backend.database.models import GameModes, Benchmarks, SideBetPeriods
from backend.logic.auth import create_jwt
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
from backend.tasks.definitions import (
    async_fetch_price,
    async_calculate_game_metrics,
    async_compile_player_sidebar_stats
)
from backend.tasks.redis import rds
from backend.tests import BaseTestCase
from config import Config
from sqlalchemy import select

HOST_URL = 'https://localhost:5000/api'


class TestUserManagement(BaseTestCase):

    def test_jwt_and_authentication(self):
        # TODO: Missing a good test for routes.login -- OAuth dependency is trick
        # registration error with faked token
        res = self.requests_session.post(f"{HOST_URL}/login", json={"msg": "dummy_token", "provider": "google"},
                                         verify=False)
        self.assertEqual(res.status_code, 411)
        self.assertEqual(res.text, OAUTH_ERROR_MSG)

        res = self.requests_session.post(f"{HOST_URL}/login", json={"msg": "dummy_token", "provider": "fake"},
                                         verify=False)
        self.assertEqual(res.status_code, 411)
        self.assertEqual(res.text, INVALID_OAUTH_PROVIDER_MSG)

        # token creation and landing
        with self.db_session.connection() as conn:
            user_id, name, email, pic, username, created_at, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", Config.TEST_CASE_EMAIL).fetchone()
            self.db_session.remove()
        session_token = create_jwt(email, user_id, username)
        decoded_token = jwt.decode(session_token, Config.SECRET_KEY, algorithms=Config.JWT_ENCODE_ALGORITHM)
        self.assertEqual(decoded_token["email"], email)
        self.assertEqual(decoded_token["user_id"], user_id)
        self.assertEqual(decoded_token["username"], username)

        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # check basic profile info
        self.assertEqual(data["email"], email)
        self.assertEqual(data["name"], name)
        self.assertEqual(data["username"], username)
        self.assertEqual(data["profile_pic"], pic)

        # check valid output from the /home endpoint. There should be one pending invite for valiant roset, with
        # test game being active
        self.assertEqual(len(data["game_info"]), 2)
        for game_data in data["game_info"]:
            if game_data["title"] == "valiant roset":
                self.assertEqual(game_data["game_status"], "pending")

            if game_data["title"] == "test game":
                self.assertEqual(game_data["game_status"], "active")

        # logout -- this should blow away the previously created session token, logging out the user
        res = self.requests_session.post(f"{HOST_URL}/logout", cookies={"session_token": session_token}, verify=False)
        msg = 'session_token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; Secure; HttpOnly; Path=/; SameSite=None'
        self.assertEqual(res.headers['Set-Cookie'], msg)

        # expired token...
        session_token = create_jwt(email, user_id, None, mins_per_session=1 / 60)
        time.sleep(2)
        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, SESSION_EXP_ERROR_MSG)

        # no session token sent -- user tried to skip the login step and go directly to landing page
        res = self.requests_session.post(f"{HOST_URL}/home", verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, LOGIN_ERROR_MSG)

        # session token sent, but wasn't encrypted with our SECRET_KEY
        session_token = create_jwt(email, user_id, None, secret_key="itsasecret")
        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.text, INVALID_SIGNATURE_ERROR_MSG)

    def test_set_username(self):
        # set username endpoint test
        with self.db_session.connection() as conn:
            user_id, name, email, pic, username, created_at, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", "dummy@example.test").fetchone()
            self.db_session.remove()
        self.assertIsNone(username)
        session_token = create_jwt(email, user_id, username)
        new_username = "peaches"
        res = self.requests_session.post(f"{HOST_URL}/set_username", json={"username": new_username},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        # least-code way that I could find to persist DB changes to sqlalchemy API, but feels janky...
        with self.db_session.connection() as conn:
            updated_username = conn.execute("SELECT username FROM users WHERE name = 'dummy';").fetchone()[0]
            self.db_session.remove()
        self.assertEqual(new_username, updated_username)
        # check the cookie to be sure that it has been updated with the new proper username as well
        decoded_token = jwt.decode(res.cookies.get("session_token"), Config.SECRET_KEY,
                                   algorithms=Config.JWT_ENCODE_ALGORITHM)
        self.assertEqual(decoded_token["username"], new_username)
        self.assertEqual(decoded_token["email"], email)

        # take username fails with 400 error
        with self.db_session.connection() as conn:
            user_id, name, email, pic, user_name, created_at, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", "dummy@example.test").fetchone()
            self.db_session.remove()
        session_token = create_jwt(email, user_id, user_name)
        res = self.requests_session.post(f"{HOST_URL}/set_username", json={"username": new_username},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, USERNAME_TAKE_ERROR_MSG)


class TestCreateGame(BaseTestCase):

    def test_game_defaults(self):
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        res = self.requests_session.post(f"{HOST_URL}/game_defaults", cookies={"session_token": session_token},
                                         verify=False)
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

        # For ease of use, make sure that the JSON object being passed back and forth with the  database has the same
        # column names, and that we are being explicit about declaring games fields that are handled server-side
        with self.db_session.connection() as conn:
            games_description = conn.execute("SHOW COLUMNS FROM games;").fetchall()
            self.db_session.remove()
        server_side_fields = ["id", "creator_id", "invite_window"]
        column_names = [column[0] for column in games_description if column[0] not in server_side_fields]
        for column in column_names:
            self.assertIn(column, game_defaults.keys())

        expected_available_invitees = {'toofast', 'miguel'}
        self.assertEqual(set(game_defaults["available_invitees"]), expected_available_invitees)

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
        user_id = 1
        user_name = "cheetos"
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        game_settings = {
            "benchmark": "sharpe_ratio",
            "buy_in": 1000,
            "duration": 365,
            "mode": "winner_takes_all",
            "n_rebuys": 3,
            "invitees": ["miguel", "toofast", "murcitdev"],
            "side_bets_perc": 50,
            "side_bets_period": "weekly",
            "title": "stupified northcutt",
        }
        res = self.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token},
                                         verify=False, json=game_settings)
        current_time = time.time()
        self.assertEqual(res.status_code, 200)

        # inspect subsequent DB entries
        with self.db_session.connection() as conn:
            games_entry = conn.execute(
                "SELECT * FROM games WHERE title = %s;", game_settings["title"]).fetchone()
            game_id = games_entry[0]
            self.db_session.remove()

        with self.db_session.connection() as conn:
            status_entry = conn.execute("SELECT * FROM game_status WHERE game_id = %s;", game_id).fetchone()
            self.db_session.remove()

        # games table tests
        for field in games_entry:  # make sure that we're test-writing all fields
            self.assertIsNotNone(field)
        self.assertEqual(game_settings["buy_in"], games_entry[5])
        self.assertEqual(game_settings["duration"], games_entry[4])
        self.assertEqual(game_settings["mode"], games_entry[3])
        self.assertEqual(game_settings["n_rebuys"], games_entry[6])
        self.assertEqual(game_settings["benchmark"], games_entry[7])
        self.assertEqual(game_settings["side_bets_perc"], games_entry[8])
        self.assertEqual(game_settings["side_bets_period"], games_entry[9])
        self.assertEqual(game_settings["title"], games_entry[2])
        self.assertEqual(user_id, games_entry[1])
        # Quick note: this test is non-determinstic: it could fail to do API server performance issues, which would be
        # something worth looking at
        window = (games_entry[10] - current_time)
        self.assertAlmostEqual(window, DEFAULT_INVITE_OPEN_WINDOW, 0)

        # game_status table tests
        for field in games_entry:  # make sure that we're test-writing all fields
            self.assertIsNotNone(field)
        self.assertEqual(status_entry[1], game_id)
        self.assertEqual(status_entry[2], "pending")
        # Same as note above about performance issue
        time_diff = abs((status_entry[4] - current_time))
        self.assertLess(time_diff, 1)
        invited_users = json.loads(status_entry[3])
        users = self.db_metadata.tables["users"]
        invitees = tuple(game_settings["invitees"] + [user_name])
        with self.db_session.connection() as conn:
            lookup_invitee_ids = conn.execute(select([users.c.id], users.c.username.in_(invitees))).fetchall()
            self.db_session.remove()
        lookup_invitee_ids = [entry[0] for entry in lookup_invitee_ids]
        self.assertEqual(set(lookup_invitee_ids), set(invited_users))

    def test_pending_game_management(self):
        user_id = 1
        game_id = 5
        test_user_session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)

        res = self.requests_session.post(f"{HOST_URL}/get_user_info",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], user_id)
        self.assertEqual(res.json()["email"], Config.TEST_CASE_EMAIL)

        res = self.requests_session.post(f"{HOST_URL}/get_pending_game_info", json={"game_id": game_id},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(set([x["username"] for x in res.json()]), {"cheetos", "toofast", "miguel", "murcitdev"})
        self.assertEqual(set([x["status"] for x in res.json()]), {"joined", "invited", "invited", "invited"})

        res = self.requests_session.post(f"{HOST_URL}/respond_to_game_invite",
                                         json={"game_id": game_id, "decision": "joined"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/get_pending_game_info", json={"game_id": game_id},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        for user_entry in res.json():
            if user_entry["username"] in ["murcitdev", "cheetos"]:
                self.assertEqual(user_entry["status"], "joined")
            else:
                self.assertEqual(user_entry["status"], "invited")


class TestPlayGame(BaseTestCase):

    def test_play_game(self):
        """Use the canonical game #3 to interact with the game play API
        """
        rds.flushall()
        user_id = 1
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        game_id = 3
        stock_pick = "JETS"
        order_quantity = 25

        res = async_fetch_price.delay(stock_pick)
        while not res.ready():
            continue
        market_price, _ = res.result

        order_ticket = {
            "user_id": user_id,
            "game_id": game_id,
            "symbol": stock_pick,
            "order_type": "limit",
            "stop_limit_price": 0,  # we want to be 100% sure that that this order doesn't automatically clear
            "shares_or_usd": "Shares",
            "market_price": market_price,
            "amount": order_quantity,
            "buy_or_sell": "buy",
            "time_in_force": "until_cancelled"
        }
        rds.delete(f"balances_chart_{game_id}_{user_id}")
        res = self.requests_session.post(f"{HOST_URL}/place_order", cookies={"session_token": session_token},
                                         verify=False, json=order_ticket)
        self.assertEqual(res.status_code, 200)
        res = rds.get(f"open_orders_{game_id}_{user_id}")
        while res is None:
            res = rds.get(f"open_orders_{game_id}_{user_id}")

        with self.db_session.connection() as conn:
            last_order = conn.execute("""
                SELECT symbol FROM orders
                ORDER BY id DESC LIMIT 0, 1;
                """
                                      ).fetchone()[0]
            self.db_session.remove()
        self.assertEqual(last_order, stock_pick)
        res = self.requests_session.post(f"{HOST_URL}/get_open_orders_table", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)
        stocks_in_table_response = [x["Symbol"] for x in res.json()["data"]]
        self.assertIn(stock_pick, stocks_in_table_response)

        balances_chart = rds.get(f"balances_chart_{game_id}_{user_id}")
        while balances_chart is None:
            balances_chart = rds.get(f"balances_chart_{game_id}_{user_id}")

        res = self.requests_session.post(f"{HOST_URL}/balances_chart", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)
        expected_current_balances_series = {'AMZN', 'Cash', 'LYFT', 'NVDA', 'SPXU', 'TSLA'}
        returned_current_balances_series = set([x['id'] for x in res.json()])
        self.assertEqual(expected_current_balances_series, returned_current_balances_series)


class TestGetGameStats(BaseTestCase):

    def test_sidebar_stats(self):
        rds.flushall()

        game_id = 3
        async_calculate_game_metrics.apply(args=(game_id, 1))
        async_calculate_game_metrics.apply(args=(game_id, 3))
        async_calculate_game_metrics.apply(args=(game_id, 4))

        res = async_compile_player_sidebar_stats.delay(game_id)
        while not res.ready():
            continue

        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        res = self.requests_session.post(f"{HOST_URL}/get_sidebar_stats", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 2)
        records = res.json()["records"]
        self.assertEqual(len(records), 3)
        expected_usernames = {"miguel", "toofast", "cheetos"}
        returned_usernames = set([x["username"] for x in records])
        self.assertEqual(expected_usernames, returned_usernames)

    def test_get_game_info(self):
        game_id = 3
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)

        res = self.requests_session.post(f"{HOST_URL}/game_info", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)

        games = self.db_metadata.tables["games"]
        row = self.db_session.query(games).filter(games.c.id == game_id)
        db_dict = orm_rows_to_dict(row)
        for k, v in res.json().items():
            if k in ["creator_username", "mode", "benchmark"]:
                continue
            self.assertEqual(db_dict[k], v)

        self.assertEqual(res.json()["creator_username"], "cheetos")
        self.assertEqual(res.json()["benchmark"], "RETURN RATIO")
        self.assertEqual(res.json()["mode"], "RETURN WEIGHTED")


class TestFriendManagement(BaseTestCase):

    def test_friend_management(self):
        """Integration test of the API's ability to interface with the celery functions tested in
        test_celery_tasks.TestFriendManagement
        """
        test_username = "cheetos"
        dummy_username = "dummy2"
        test_user_session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        dummy_user_session_token = self.make_test_token_from_email("dummy2@example.test")
        jack_session_token = self.make_test_token_from_email("jack@black.pearl")

        # look at our list of test user's friends
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friends",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        expected_friends = {"toofast", "miguel"}
        self.assertEqual(set([x["username"] for x in res.json()]), expected_friends)

        # is there anyone that the test user isn't (a) friends with already or (b) hasn't sent him an invite? there
        # should be just one, the dummy user. we'll confirm this, but won't send an invite
        res = self.requests_session.post(f"{HOST_URL}/suggest_friend_invites", json={"text": "j"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(len(res.json()), 4)
        for entry in res.json():
            if entry["username"] == "murcitdev":
                self.assertEqual(entry["label"], "invited_you")

            if entry["username"] == "jack":
                self.assertEqual(entry["label"], "you_invited")

            if entry["username"] in ["johnnie", "jadis"]:
                self.assertEqual(entry["label"], "suggested")

        # what friend invites does test user currently have pending?
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friend_invites",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.json(), ["murcitdev"])

        # the test user get's a new friend invite: does that show up as expected?
        res = self.requests_session.post(f"{HOST_URL}/send_friend_request", json={"friend_invitee": test_username},
                                         cookies={"session_token": dummy_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        # check the invites again. we should have the dummy user in there
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friend_invites",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(set(res.json()), {dummy_username, "murcitdev"})

        #  the test user rejects the invite. He'll accept the outstanding invite from murcitdev, though
        res = self.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                                         json={"requester_username": dummy_username, "decision": "declined"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                                         json={"requester_username": "murcitdev", "decision": "accepted"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        # the test user has responded to all friend invites, so there shouldn't be any pending
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friend_invites",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertTrue(len(res.json()) == 0)

        # the test user is ready to make a game. murcitdev should now show up in their list of friend possibilities
        res = self.requests_session.post(f"{HOST_URL}/game_defaults",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(set(res.json()["available_invitees"]), {"miguel", "murcitdev", "toofast"})

        # finally, confirm that the new friends list looks good
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friends",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        expected_friends = {"toofast", "miguel", "murcitdev"}
        self.assertEqual(set([x["username"] for x in res.json()]), expected_friends)

        # jack sparrow is too cool for the user and rejects his invite. since test user just accepted murcitdev's
        # invite we'll now excepted a list with 2 "suggested" entries, with no outstanding sent or received invitations
        res = self.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                                         json={"requester_username": test_username, "decision": "declined"},
                                         cookies={"session_token": jack_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/suggest_friend_invites", json={"text": "j"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(len(res.json()), 2)
        self.assertNotIn("jack", [x["username"] for x in res.json()])
        for entry in res.json():
            self.assertEqual(entry["label"], "suggested")


class TestHomePage(BaseTestCase):

    def test_home_page(self):
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        # verify that the test page landing looks like we expect it to
        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["game_info"]), 2)
        for game_entry in res.json()["game_info"]:
            if game_entry["title"] == "test game":
                self.assertEqual(game_entry["invite_status"], "joined")
                self.assertEqual(game_entry["creator_username"], "cheetos")
                self.assertEqual(game_entry["creator_id"], 1)

            if game_entry["title"] == "valiant roset":
                self.assertEqual(game_entry["invite_status"], "invited")
                self.assertEqual(game_entry["creator_username"], "murcitdev")
                self.assertEqual(game_entry["creator_id"], 5)

        # now accept a game invite, and verify that while that game's info still posts, the test user's invite status
        # is now updated to "joined
        game_id = 5
        res = self.requests_session.post(f"{HOST_URL}/respond_to_game_invite",
                                         json={"game_id": game_id, "decision": "joined"},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["game_info"]), 2)
        for game_entry in res.json()["game_info"]:
            self.assertEqual(game_entry["invite_status"], "joined")
