import json
import time

import jwt
import pandas as pd
from backend.api.routes import (
    INVALID_SIGNATURE_ERROR_MSG,
    LOGIN_ERROR_MSG,
    SESSION_EXP_ERROR_MSG,
    USERNAME_TAKE_ERROR_MSG,
    OAUTH_ERROR_MSG,
    INVALID_OAUTH_PROVIDER_MSG,
    EMAIL_NOT_FOUND_MSG,
    EMAIL_ALREADY_LOGGED_MSG
)
from backend.config import Config
from backend.database.fixtures.mock_data import populate_table
from backend.database.helpers import (
    reset_db,
    unpack_enumerated_field_mappings,
    query_to_dict
)
from backend.database.models import GameModes, Benchmarks, SideBetPeriods
from backend.logic.auth import create_jwt
from backend.logic.base import (
    SECONDS_IN_A_DAY,
    USD_FORMAT,
    during_trading_day,
    fetch_price)
from backend.logic.games import (
    DEFAULT_GAME_DURATION,
    DEFAULT_BUYIN,
    DEFAULT_BENCHMARK,
    DEFAULT_SIDEBET_PERCENT,
    DEFAULT_SIDEBET_PERIOD,
    DEFAULT_INVITE_OPEN_WINDOW,
    DEFAULT_VIRTUAL_CASH,
    InsufficientHoldings,
    InsufficientFunds,
    LimitError
)
from backend.logic.visuals import (
    compile_and_pack_player_leaderboard,
    make_user_balances_chart_data,
    serialize_and_pack_balances_chart,
    serialize_and_pack_winners_table,
    serialize_and_pack_order_details,
    calculate_and_pack_game_metrics,
    LEADERBOARD_PREFIX,
    CURRENT_BALANCES_PREFIX,
    PENDING_ORDERS_PREFIX,
    FULFILLED_ORDER_PREFIX,
    PAYOUTS_PREFIX,
    BALANCES_CHART_PREFIX
)
from backend.tasks.airflow import trigger_dag
from backend.tasks.redis import (
    rds,
    unpack_redis_json
)

from backend.tests import BaseTestCase
from tasks import s3_cache

HOST_URL = 'https://localhost:5000/api'


class TestUserManagement(BaseTestCase):

    def test_jwt_and_authentication(self):
        # registration error with faked token
        res = self.requests_session.post(f"{HOST_URL}/login",
                                         json={"provider": "google", "tokenId": "bad", "googleId": "fake"},
                                         verify=False)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, OAUTH_ERROR_MSG)

        res = self.requests_session.post(f"{HOST_URL}/login", json={"msg": "dummy_token", "provider": "fake"},
                                         verify=False)
        self.assertEqual(res.status_code, 411)
        self.assertEqual(res.text, INVALID_OAUTH_PROVIDER_MSG)

        # token creation and landing
        with self.engine.connect() as conn:
            user_id, name, email, pic, username, created_at, _, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", Config.TEST_CASE_EMAIL).fetchone()

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
        for game_data in data["game_info"]:
            if game_data["title"] == "valiant roset":
                self.assertEqual(game_data["game_status"], "pending")

            if game_data["title"] == "test game":
                self.assertEqual(game_data["game_status"], "active")

            if game_data["title"] == "finished game to show":
                self.assertEqual(game_data["game_status"], "finished")

            if game_data["title"] == "finished game to hide":
                self.assertEqual(game_data["game_status"], "finished")

        # logout -- this should blow away the previously created session token, logging out the user
        res = self.requests_session.post(f"{HOST_URL}/logout", cookies={"session_token": session_token}, verify=False)
        msg = 'session_token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; Secure; HttpOnly; Path=/'
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
        with self.engine.connect() as conn:
            user_id, name, email, pic, username, created_at, _, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", "dummy@example.test").fetchone()

        self.assertIsNone(username)
        session_token = create_jwt(email, user_id, username)
        new_username = "peaches"
        res = self.requests_session.post(f"{HOST_URL}/set_username", json={"username": new_username},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        # least-code way that I could find to persist DB changes to sqlalchemy API, but feels janky...
        with self.engine.connect() as conn:
            updated_username = conn.execute("SELECT username FROM users WHERE name = 'dummy';").fetchone()[0]
        self.assertEqual(new_username, updated_username)
        # check the cookie to be sure that it has been updated with the new proper username as well
        decoded_token = jwt.decode(res.cookies.get("session_token"), Config.SECRET_KEY,
                                   algorithms=Config.JWT_ENCODE_ALGORITHM)
        self.assertEqual(decoded_token["username"], new_username)
        self.assertEqual(decoded_token["email"], email)

        # take username fails with 400 error
        with self.engine.connect() as conn:
            user_id, name, email, pic, user_name, created_at, _, _, _ = conn.execute(
                "SELECT * FROM users WHERE email = %s;", "dummy@example.test").fetchone()
        session_token = create_jwt(email, user_id, user_name)
        res = self.requests_session.post(f"{HOST_URL}/set_username", json={"username": new_username},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, USERNAME_TAKE_ERROR_MSG)

    def test_username_and_pwd_login(self):
        email = "me@example.com"
        password = "secret"
        res = self.requests_session.post(f"{HOST_URL}/login",
                                         json=dict(provider="stockbets", password=password, email=email),
                                         verify=False)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.text, EMAIL_NOT_FOUND_MSG)

        res = self.requests_session.post(f"{HOST_URL}/login",
                                         json=dict(provider="stockbets", password=password, email=email,
                                                   is_sign_up=True), verify=False)
        self.assertEqual(res.status_code, 200)
        user_entry = query_to_dict("SELECT * FROM users WHERE email = %s;", email)[0]
        self.assertEqual(user_entry["password"], password)

        res = self.requests_session.post(f"{HOST_URL}/login",
                                         json=dict(provider="stockbets", password=password, email=email,
                                                   is_sign_up=True), verify=False)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.text, EMAIL_ALREADY_LOGGED_MSG)

        res = self.requests_session.post(f"{HOST_URL}/login",
                                         json=dict(provider="stockbets", password=password, email=email), verify=False)
        self.assertEqual(res.status_code, 200)


class TestCreateGame(BaseTestCase):

    def test_game_defaults(self):
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        res = self.requests_session.post(f"{HOST_URL}/game_defaults", json={"game_mode": "multi_player"},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        game_defaults = res.json()

        expected_keys = [
            "title",
            "duration",
            "buy_in",
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
        with self.engine.connect() as conn:
            games_description = conn.execute("SHOW COLUMNS FROM games;").fetchall()
        server_side_fields = ["id", "creator_id", "invite_window"]
        column_names = [column[0] for column in games_description if column[0] not in server_side_fields]

        for column in column_names:
            # we won't set a default for game_mode, since this will be handled on a separate form
            if column == "game_mode":
                continue
            self.assertIn(column, game_defaults.keys())

        expected_available_invitees = set(['toofast', 'miguel'] + [f"minion{x}" for x in range(1, 31)])
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
        self.assertEqual(game_defaults["duration"], DEFAULT_GAME_DURATION)
        self.assertEqual(game_defaults["buy_in"], DEFAULT_BUYIN)
        self.assertEqual(game_defaults["benchmark"], DEFAULT_BENCHMARK)
        self.assertEqual(game_defaults["side_bets_perc"], DEFAULT_SIDEBET_PERCENT)
        self.assertEqual(game_defaults["side_bets_period"], DEFAULT_SIDEBET_PERIOD)

    def test_create_and_play_multiplayer_game(self):
        user_id = 1
        user_name = "cheetos"
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        game_duration = 365
        game_invitees = ["miguel", "toofast", "murcitdev"]
        buy_in = 1000
        game_settings = {
            "benchmark": "sharpe_ratio",
            "buy_in": buy_in,
            "duration": game_duration,
            "game_mode": "multi_player",
            "n_rebuys": 0,  # this is just for test consistency -- rebuys are switched off for now
            "invitees": game_invitees,
            "side_bets_perc": 50,
            "side_bets_period": "weekly",
            "title": "stupified northcutt",
            "invite_window": DEFAULT_INVITE_OPEN_WINDOW,
            "stakes": "monopoly"
        }
        res = self.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token},
                                         verify=False, json=game_settings)
        current_time = time.time()
        self.assertEqual(res.status_code, 200)

        # inspect subsequent DB entries
        games_entry = query_to_dict("SELECT * FROM games WHERE title = %s", game_settings["title"])[0]
        game_id = games_entry["id"]
        status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s;", game_id)[0]

        # games table tests
        for field in games_entry.values():  # make sure that we're test-writing all fields
            self.assertIsNotNone(field)

        self.assertEqual(game_settings["buy_in"], games_entry["buy_in"])
        self.assertEqual(game_settings["duration"], games_entry["duration"])
        self.assertEqual(game_settings["game_mode"], games_entry["game_mode"])
        self.assertEqual(game_settings["benchmark"], games_entry["benchmark"])
        self.assertEqual(game_settings["side_bets_perc"], games_entry["side_bets_perc"])
        self.assertEqual(game_settings["side_bets_period"], games_entry["side_bets_period"])
        self.assertEqual(game_settings["title"], games_entry["title"])
        self.assertEqual(user_id, games_entry["creator_id"])
        # Quick note: this test is non-determinstic: it could fail to do API server performance issues, which would be
        # something worth looking at
        window = games_entry["invite_window"] - current_time
        self.assertLess(window - DEFAULT_INVITE_OPEN_WINDOW * SECONDS_IN_A_DAY, 1)

        # game_status table tests
        for field in status_entry.values():  # make sure that we're test-writing all fields
            self.assertIsNotNone(field)
        self.assertEqual(status_entry["game_id"], game_id)
        self.assertEqual(status_entry["status"], "pending")
        # Same as note above about performance issue
        time_diff = abs((status_entry["timestamp"] - current_time))
        self.assertLess(time_diff, 1)
        invited_users = json.loads(status_entry["users"])
        invitees = tuple(game_settings["invitees"] + [user_name])
        with self.engine.connect() as conn:
            res = conn.execute(f"""
                SELECT id FROM users WHERE username IN ({",".join(['%s'] * len(invitees))});
            """, invitees)
        lookup_invitee_ids = [x[0] for x in res]
        self.assertEqual(set(lookup_invitee_ids), set(invited_users))

        # murcitdev and toofast will accept, miguel will decline
        miguel_token = self.make_test_token_from_email("mike@example.test")
        toofast_token = self.make_test_token_from_email("eddie@example.test")
        murcitdev_token = self.make_test_token_from_email("eli@example.test")
        self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": murcitdev_token},
                                   json={"game_id": game_id, "decision": "joined"}, verify=False)
        self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": toofast_token},
                                   json={"game_id": game_id, "decision": "joined"}, verify=False)
        self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": miguel_token},
                                   json={"game_id": game_id, "decision": "declined"}, verify=False)

        # since all players have responded to the game invite it should have kicked off automatically. Check that the
        # three players who are participating have the starting balances that we expect and that  initializations for
        # (a) game leaderboard, (b) current balances, (c) open orders, (d) balances chart, and (e) the field chart all
        # look good.
        res = self.requests_session.post(f"{HOST_URL}/get_leaderboard", json={"game_id": game_id},
                                         cookies={"session_token": session_token})
        self.assertEqual(res.json()["days_left"], game_duration - 1)
        self.assertEqual(set([x["username"] for x in res.json()["records"]]), {"murcitdev", "toofast", "cheetos"})
        sql = """
            SELECT *
            FROM game_balances
            WHERE game_id = %s
            AND balance_type = 'virtual_cash'
        """
        with self.engine.connect() as conn:
            player_cash_balances = pd.read_sql(sql, conn, params=[game_id])
        self.assertEqual(player_cash_balances.shape, (3, 8))
        self.assertTrue(all([x == DEFAULT_VIRTUAL_CASH for x in player_cash_balances["balance"].to_list()]))

        side_bar_stats = s3_cache.unpack_s3_json(f"{game_id}/{LEADERBOARD_PREFIX}")
        self.assertEqual(len(side_bar_stats["records"]), 3)
        self.assertTrue(all([x["cash_balance"] == DEFAULT_VIRTUAL_CASH for x in side_bar_stats["records"]]))
        self.assertEqual(side_bar_stats["days_left"], game_duration - 1)

        current_balances_keys = [x for x in s3_cache.keys() if CURRENT_BALANCES_PREFIX in x]
        self.assertEqual(len(current_balances_keys), 3)
        init_balances_entry = s3_cache.unpack_s3_json(current_balances_keys[0])
        self.assertEqual(init_balances_entry["data"], [])
        self.assertEqual(len(init_balances_entry["headers"]), 8)

        open_orders_keys = [x for x in s3_cache.keys() if PENDING_ORDERS_PREFIX in x]
        self.assertEqual(len(open_orders_keys), 3)
        init_open_orders_entry = s3_cache.unpack_s3_json(open_orders_keys[0])
        init_fulfilled_orders_entry = s3_cache.unpack_s3_json(open_orders_keys[0])
        self.assertEqual(init_open_orders_entry["data"], [])
        self.assertEqual(init_fulfilled_orders_entry["data"], [])
        self.assertEqual(len(init_open_orders_entry["headers"]), 9)

        serialize_and_pack_winners_table(game_id)
        payouts_table = s3_cache.unpack_s3_json(f"{game_id}/{PAYOUTS_PREFIX}")
        side_bet_payouts = [entry for entry in payouts_table["data"] if entry["Type"] == "Sidebet"]
        self.assertEqual(len(side_bet_payouts), game_duration // 7)
        # len(invitees) - 1 because one of the players declines the game
        # TODO: Cleanup rounding issues in payout handling to make this more precise
        self.assertTrue(sum([x["Payout"] for x in payouts_table["data"]]) - (len(invitees) - 1) * buy_in < 1)

        # we'll test our ability to leave a game
        res = self.requests_session.post(f"{HOST_URL}/leave_game", json={"game_id": game_id},
                                         cookies={"session_token": session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        trigger_dag("update_game_dag", wait_for_complete=True, game_id=game_id)

        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": session_token},
                                         verify=False)
        self.assertEqual(res.status_code, 200)
        user_landing_info = res.json()
        self.assertNotIn(game_id, [x["game_id"] for x in user_landing_info["game_info"]])

        res = self.requests_session.post(f"{HOST_URL}/game_info", cookies={"session_token": session_token},
                                         json={"game_id": game_id}, verify=False)
        self.assertEqual(res.status_code, 200)
        play_game_info = res.json()
        self.assertNotIn(user_id, [x["id"] for x in play_game_info["leaderboard"]])

        # if all users leave a game, we expect that game to be inactive
        res = self.requests_session.post(f"{HOST_URL}/leave_game", json={"game_id": game_id},
                                         cookies={"session_token": toofast_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/leave_game", json={"game_id": game_id},
                                         cookies={"session_token": murcitdev_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        game_status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s ORDER BY id DESC LIMIT 0, 1;",
                                          game_id)[0]
        self.assertEqual(game_status_entry["status"], "expired")
        self.assertEqual(json.loads(game_status_entry["users"]), [])

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
        self.assertEqual(set([x["username"] for x in res.json()["platform_invites"]]),
                         {"cheetos", "toofast", "miguel", "murcitdev"})
        self.assertEqual(set([x["status"] for x in res.json()["platform_invites"]]),
                         {"joined", "invited", "invited", "invited"})

        res = self.requests_session.post(f"{HOST_URL}/respond_to_game_invite",
                                         json={"game_id": game_id, "decision": "joined"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/get_pending_game_info", json={"game_id": game_id},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        for user_entry in res.json()["platform_invites"]:
            if user_entry["username"] in ["murcitdev", "cheetos"]:
                self.assertEqual(user_entry["status"], "joined")
            else:
                self.assertEqual(user_entry["status"], "invited")

    def test_create_single_player_game(self):
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        game_duration = 365
        game_settings = {
            "duration": game_duration,
            "game_mode": "single_player",
            "title": "jugando solo",
            "benchmark": "return_ratio"
        }
        res = self.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token},
                                         verify=False, json=game_settings)
        self.assertEqual(res.status_code, 200)


class TestPlayGame(BaseTestCase):

    def test_play_game(self):
        """Use the canonical game #3 to interact with the game play API
        """
        user_id = 1
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        game_id = 3
        serialize_and_pack_order_details(game_id, user_id)
        stock_pick = "JETS"
        order_quantity = 25
        market_price, _ = fetch_price(stock_pick)
        order_ticket = {
            "user_id": user_id,
            "game_id": game_id,
            "symbol": stock_pick,
            "order_type": "limit",
            "stop_limit_price": 0,  # we want to be 100% sure that that this order doesn't automatically clear
            "quantity_type": "Shares",
            "market_price": market_price,
            "amount": order_quantity,
            "buy_or_sell": "buy",
            "time_in_force": "until_cancelled"
        }
        res = self.requests_session.post(f"{HOST_URL}/place_order", cookies={"session_token": session_token},
                                         verify=False, json=order_ticket)
        self.assertEqual(res.status_code, 200)

        # these assets update in real time
        self.assertIsNotNone(s3_cache.get(f"{game_id}/{user_id}/{PENDING_ORDERS_PREFIX}"))
        self.assertIsNotNone(s3_cache.get(f"{game_id}/{user_id}/{FULFILLED_ORDER_PREFIX}"))
        self.assertIsNotNone(s3_cache.get(f"{game_id}/{user_id}/{CURRENT_BALANCES_PREFIX}"))

        trigger_dag("update_game_dag", wait_for_complete=True, game_id=game_id)

        with self.engine.connect() as conn:
            last_order = conn.execute("""
                SELECT symbol FROM orders
                ORDER BY id DESC LIMIT 0, 1;
                """).fetchone()[0]
        self.assertEqual(last_order, stock_pick)

        res = self.requests_session.post(f"{HOST_URL}/get_pending_orders_table",
                                         cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)
        stocks_in_table_response = [x["Symbol"] for x in res.json()["data"]]
        self.assertIn(stock_pick, stocks_in_table_response)

        balances_chart = s3_cache.get(f"{game_id}/{user_id}/{BALANCES_CHART_PREFIX}")
        while balances_chart is None:
            balances_chart = s3_cache.get(f"{game_id}/{user_id}/{BALANCES_CHART_PREFIX}")

        res = self.requests_session.post(f"{HOST_URL}/get_balances_chart", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)
        expected_current_balances_series = {'AMZN', 'Cash', 'LYFT', 'NVDA', 'SPXU', 'TSLA'}
        returned_current_balances_series = set([x['label'] for x in res.json()["datasets"]])
        self.assertEqual(expected_current_balances_series, returned_current_balances_series)

        # check a different user's balance information
        df = make_user_balances_chart_data(game_id, 3)
        serialize_and_pack_balances_chart(df, game_id, 3)
        res = self.requests_session.post(f"{HOST_URL}/get_balances_chart", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id, "username": "toofast"})
        self.assertEqual(res.status_code, 200)
        expected_current_balances_series = {'NVDA', 'Cash', 'NKE'}
        returned_current_balances_series = set([x['label'] for x in res.json()["datasets"]])
        self.assertEqual(expected_current_balances_series, returned_current_balances_series)

        # place a couple different types of invalid orders to make sure that we're getting what we expect back
        stock_pick = "AMZN"
        market_price, _ = fetch_price(stock_pick)

        # can't buy a billion dollars of Amazon
        order_ticket = {
            "user_id": user_id,
            "game_id": game_id,
            "symbol": stock_pick,
            "order_type": "limit",
            "stop_limit_price": 1_000,  # we want to be 100% sure that that this order doesn't automatically clear
            "quantity_type": "USD",
            "market_price": market_price,
            "amount": 1_000_000_000,
            "buy_or_sell": "buy",
            "time_in_force": "until_cancelled"
        }
        res = self.requests_session.post(f"{HOST_URL}/place_order", cookies={"session_token": session_token},
                                         verify=False, json=order_ticket)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, str(InsufficientFunds()))

        # also can't sell a million shares that we don't own
        order_ticket = {
            "user_id": user_id,
            "game_id": game_id,
            "symbol": stock_pick,
            "order_type": "market",
            "stop_limit_price": 0,  # we want to be 100% sure that that this order doesn't automatically clear
            "quantity_type": "Shares",
            "market_price": market_price,
            "amount": 1_000_000,
            "buy_or_sell": "sell",
            "time_in_force": "until_cancelled"
        }
        res = self.requests_session.post(f"{HOST_URL}/place_order", cookies={"session_token": session_token},
                                         verify=False, json=order_ticket)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, str(InsufficientHoldings()))

        # Trigger the exception for a limit order that's effectively a market order
        order_ticket = {
            "user_id": user_id,
            "game_id": game_id,
            "symbol": stock_pick,
            "order_type": "limit",
            "stop_limit_price": 5_000,  # we want to be 100% sure that that this order doesn't automatically clear
            "quantity_type": "Shares",
            "market_price": market_price,
            "amount": 1,
            "buy_or_sell": "buy",
            "time_in_force": "until_cancelled"
        }
        res = self.requests_session.post(f"{HOST_URL}/place_order", cookies={"session_token": session_token},
                                         verify=False, json=order_ticket)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.text, str(LimitError()))

        # cancel the last order that we placed successfully and verify that this updated the order details table
        with self.engine.connect() as conn:
            order_id = conn.execute("SELECT id FROM main.orders WHERE symbol = 'JETS';").fetchone()[0]
        res = self.requests_session.post(f"{HOST_URL}/cancel_order", cookies={"session_token": session_token},
                                         verify=False, json={"order_id": order_id, "game_id": game_id})
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/get_pending_orders_table",
                                         cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)
        stocks_in_table_response = [x["Symbol"] for x in res.json()["data"]]
        self.assertNotIn("JETS", stocks_in_table_response)

        res = self.requests_session.post(f"{HOST_URL}/get_current_balances_table",
                                         cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)

        res = self.requests_session.post(f"{HOST_URL}/get_current_balances_table",
                                         cookies={"session_token": session_token}, verify=False,
                                         json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)

        # this just test that last close is at least producing something -- the backgroun test data isn't setup to
        # produce meaningful results, yet.
        nvda_entry = [x["Change since last close"] for x in res.json()["data"] if x["Symbol"] == "NVDA"][0]
        self.assertEqual(nvda_entry, "0.00%")

        # check fulfilled orders. these should just match the order that we have for the test user in the mock DB
        res = self.requests_session.post(f"{HOST_URL}/get_fulfilled_orders_table",
                                         cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)

        self.assertIn("color", res.json()["data"][0])
        self.assertEqual(set([x["Symbol"] for x in res.json()["data"]]), {"AMZN", "TSLA", "LYFT", "SPXU", "NVDA"})
        self.assertEqual(len(res.json()["data"]), 6)  # because we have a buy and a sell order for AMZN

        res = self.requests_session.post(f"{HOST_URL}/get_transactions_table", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)

        transactions = query_to_dict("SELECT * FROM game_balances WHERE game_id = %s AND user_id = %s", game_id,
                                     user_id)
        self.assertEqual(len(res.json()), len(transactions))


class TestGetGameStats(BaseTestCase):

    def test_leaderboard(self):
        game_id = 3
        calculate_and_pack_game_metrics(game_id)
        compile_and_pack_player_leaderboard(game_id)

        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        res = self.requests_session.post(f"{HOST_URL}/get_leaderboard", cookies={"session_token": session_token},
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
        compile_and_pack_player_leaderboard(game_id)

        res = self.requests_session.post(f"{HOST_URL}/game_info", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": game_id})
        self.assertEqual(res.status_code, 200)

        db_dict = query_to_dict("SELECT * FROM games WHERE id = %s", game_id)[0]
        for k, v in res.json().items():
            if k in ["creator_username", "game_mode", "benchmark", "game_status", "user_status", "end_time",
                     "start_time", "benchmark_formatted", "leaderboard", "is_host", "creator_profile_pic",
                     "stakes_formatted"]:
                continue
            self.assertEqual(db_dict[k], v)

        self.assertEqual(res.json()["user_status"], "joined")
        self.assertEqual(res.json()["game_status"], "active")
        self.assertEqual(res.json()["creator_username"], "cheetos")
        self.assertEqual(res.json()["creator_username"], "cheetos")
        self.assertEqual(res.json()["benchmark_formatted"], "RETURN RATIO")


class TestFriendManagement(BaseTestCase):

    def test_friend_management(self):
        """Integration test of the API's ability to interface with the celery functions tested in
        test_celery_tasks.TestFriendManagement
        """
        test_username = "cheetos"
        test_friend_email = "test_dummy_email@example.com"
        dummy_username = "dummy2"
        test_user_session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        dummy_user_session_token = self.make_test_token_from_email("dummy2@example.test")
        jack_session_token = self.make_test_token_from_email("jack@black.pearl")

        # look at our list of test user's friends
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friends",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        expected_friends = set(['toofast', 'miguel'] + [f"minion{x}" for x in range(1, 31)])
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
        res = self.requests_session.post(f"{HOST_URL}/invite_users_by_email",
                                         json={"friend_emails": [test_friend_email]},
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
        res = self.requests_session.post(f"{HOST_URL}/game_defaults", json={"game_mode": "multi_player"},
                                         cookies={"session_token": test_user_session_token}, verify=False)
        expected_available_invites = set(['toofast', 'miguel', "murcitdev"] + [f"minion{x}" for x in range(1, 31)])
        self.assertEqual(set(res.json()["available_invitees"]), expected_available_invites)

        # finally, confirm that the new friends list looks good
        res = self.requests_session.post(f"{HOST_URL}/get_list_of_friends",
                                         cookies={"session_token": test_user_session_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        expected_friends = set(['toofast', 'miguel', "murcitdev"] + [f"minion{x}" for x in range(1, 31)])
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
        self.assertEqual(len(res.json()["game_info"]), 5)
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
        for game_entry in res.json()["game_info"]:
            self.assertEqual(game_entry["invite_status"], "joined")

    def test_home_first_landing(self):
        """Simulate a world where we have users and friends, but no games. We'll recreate a game from the create_game
        test. Rhis functionality is already tested. Want to do a bit testing of the order placing functionality via the
        API and how that impacts the database.
        """
        #
        s3_cache.flushall()
        reset_db()
        populate_table("users")
        populate_table("symbols")
        populate_table("friends")

        user_id = 1
        user_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        username = "cheetos"

        res = self.requests_session.post(f"{HOST_URL}/home", cookies={"session_token": user_token}, verify=False)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], Config.TEST_CASE_EMAIL)
        self.assertEqual(data["game_info"], [])
        self.assertEqual(data["id"], user_id)
        self.assertEqual(data["username"], username)

        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        game_duration = 365
        game_invitees = ["miguel", "toofast", "murcitdev"]
        game_settings = {
            "benchmark": "sharpe_ratio",
            "buy_in": 1000,
            "duration": game_duration,
            "game_mode": "multi_player",
            "n_rebuys": 3,
            "invitees": game_invitees,
            "side_bets_perc": 50,
            "side_bets_period": "weekly",
            "title": "stupified northcutt",
            "invite_window": DEFAULT_INVITE_OPEN_WINDOW
        }
        self.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token}, verify=False,
                                   json=game_settings)

        miguel_token = self.make_test_token_from_email("mike@example.test")
        toofast_token = self.make_test_token_from_email("eddie@example.test")
        murcitdev_token = self.make_test_token_from_email("eli@example.test")
        self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": murcitdev_token},
                                   json={"game_id": 1, "decision": "joined"}, verify=False)
        self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": toofast_token},
                                   json={"game_id": 1, "decision": "joined"}, verify=False)
        self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": miguel_token},
                                   json={"game_id": 1, "decision": "declined"}, verify=False)

        # verify that starting cash balances work as expected
        res = self.requests_session.post(f"{HOST_URL}/get_cash_balances", cookies={"session_token": session_token},
                                         verify=False, json={"game_id": 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["cash_balance"], USD_FORMAT.format(DEFAULT_VIRTUAL_CASH))
        self.assertEqual(res.json()["buying_power"], USD_FORMAT.format(DEFAULT_VIRTUAL_CASH))

        # confirm that a blank-slate buy order makes it in without any hiccups
        order_ticket = {
            "user_id": 1,
            "game_id": 1,
            "symbol": "TSLA",
            "order_type": "market",
            "quantity_type": "Shares",
            "market_price": 1_000,
            "amount": 1,
            "buy_or_sell": "buy",
            "time_in_force": "day"
        }
        res = self.requests_session.post(f"{HOST_URL}/place_order", cookies={"session_token": session_token},
                                         verify=False, json=order_ticket)
        self.assertEqual(res.status_code, 200)

        with self.engine.connect() as conn:
            orders = pd.read_sql("SELECT * FROM main.orders", conn)
            order_status = pd.read_sql("SELECT * FROM main.order_status", conn)

        self.assertEqual(orders.shape, (1, 9))
        self.assertGreaterEqual(order_status.shape[0], 1)
        self.assertEqual(order_status.iloc[0]["status"], "pending")


class TestPriceFetching(BaseTestCase):

    def test_api_price_fetching(self):
        reset_db()
        populate_table("users")

        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        res = self.requests_session.post(f"{HOST_URL}/fetch_price", cookies={"session_token": session_token},
                                         json={"symbol": "TSLA"}, verify=False)
        self.assertEqual(res.status_code, 200)

        self.assertNotIn("GMT", res.json()["last_updated"])
        self.assertIn("EST", res.json()["last_updated"])

        # we only expect a database entry during trading hours
        if during_trading_day():
            while "TSLA" not in s3_cache.keys():
                continue

            with self.engine.connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM main.prices;").fetchone()[0]

            self.assertIn("TSLA", s3_cache.keys())  # we expect to see a cached price entry no matter
            self.assertEqual(count, 1)
        else:
            with self.engine.connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM main.prices;").fetchone()[0]

            self.assertNotIn("TSLA", s3_cache.keys())
            self.assertEqual(count, 0)
