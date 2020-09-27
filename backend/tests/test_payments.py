from freezegun import freeze_time
import time

from backend.logic.base import (
    SECONDS_IN_A_DAY,
    posix_to_datetime
)
from backend.logic.metrics import log_winners
from backend.database.helpers import query_to_dict
from backend.database.fixtures.mock_data import simulation_start_time
from backend.tests import BaseTestCase
from backend.config import Config

HOST_URL = 'https://localhost:5000/api'


class TestPayments(BaseTestCase):

    def test_game_startup(self):
        user_id = 1
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        miguel_token = self.make_test_token_from_email("mike@example.test")

        # in the frontend flow once a user has sent payment to start a game we first create that game, then link a
        # starting payment entry to it in the payments table. We'll also create a payment profile if we don't have
        # one for the user, yet, and will update the existing payment profile entry if it has changed
        buy_in = 1_000
        game_duration = 7
        game_invitees = ["miguel", "toofast"]
        game_title = "real $$$$"
        game_settings = dict(
            benchmark="sharpe_ratio",
            buy_in=buy_in,
            duration=game_duration,
            game_mode="multi_player",
            n_rebuys=0,
            invitees=game_invitees,
            title=game_title,
            invite_window=2,
            stakes="real"
        )
        res = self.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token},
                                         verify=False, json=game_settings)
        self.assertEqual(res.status_code, 200)
        game_id = res.json()["game_id"]

        # the next thing that happens is a payment call to kick off the game
        payer_email = "canbedifferent@example.com"
        payment_payload = dict(
            game_id=game_id,
            processor='paypal',
            type='start',
            payer_email=payer_email,
            uuid=Config.PAYPAL_TEST_USER_ID,
            amount=buy_in,
            currency='USD'
        )
        # we don't have a payment profile with this email in the test DB -- after we process the payment, we should
        # have a new one
        payment_profile = query_to_dict("SELECT * FROM payment_profiles WHERE payer_email = %s", payer_email)
        self.assertTrue(len(payment_profile) == 0)
        res = self.requests_session.post(f"{HOST_URL}/process_payment", cookies={"session_token": session_token},
                                         verify=False, json=payment_payload)
        self.assertEqual(res.status_code, 200)
        payment_profile = query_to_dict("SELECT * FROM payment_profiles WHERE payer_email = %s", payer_email)
        self.assertTrue(len(payment_profile) == 1)

        game_entry = query_to_dict("SELECT * FROM games WHERE title = %s AND creator_id = %s", game_title, user_id)[0]
        payment_entry = query_to_dict("SELECT * FROM payments WHERE user_id = %s ORDER BY id DESC LIMIT 1;", user_id)[0]
        self.assertEqual(game_entry["buy_in"], payment_entry["amount"])
        self.assertEqual(game_entry["creator_id"], payment_entry["user_id"])

        # test join game flow
        res = self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": miguel_token},
                                         verify=False, json={"game_id": game_id, "decision": "joined"})
        self.assertEqual(res.status_code, 200)

        payment_payload = dict(
            game_id=game_id,
            processor='paypal',
            type='join',
            payer_email="anotherdifferentemail@example.com",
            uuid=Config.PAYPAL_TEST_USER_ID,
            amount=buy_in,
            currency='USD'
        )
        res = self.requests_session.post(f"{HOST_URL}/process_payment", cookies={"session_token": session_token},
                                         verify=False, json=payment_payload)
        self.assertEqual(res.status_code, 200)

        game_payment_entries = query_to_dict("SELECT * FROM payments WHERE game_id = %s", game_id)
        self.assertEqual(len(game_payment_entries), 2)
        self.assertEqual(set([x['type'] for x in game_payment_entries]), {'start', 'join'})
        [self.assertEqual(x["direction"], "inflow") for x in game_payment_entries]

    def test_start_game_refund(self):
        # same situation as above, except here miguel will decline, the game will expire, and we will refund the host
        user_id = 1
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        miguel_token = self.make_test_token_from_email("mike@example.test")

        # in the frontend flow once a user has sent payment to start a game we first create that game, then link a
        # starting payment entry to it in the payments table. We'll also create a payment profile if we don't have
        # one for the user, yet, and will update the existing payment profile entry if it has changed
        buy_in = 1_000
        game_duration = 7
        game_invitees = ["miguel"]
        game_title = "real $$$$"
        game_settings = dict(
            benchmark="sharpe_ratio",
            buy_in=buy_in,
            duration=game_duration,
            game_mode="multi_player",
            n_rebuys=0,
            invitees=game_invitees,
            title=game_title,
            invite_window=2,
            stakes="real"
        )
        res = self.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": session_token},
                                         verify=False, json=game_settings)
        self.assertEqual(res.status_code, 200)
        game_id = res.json()["game_id"]

        # the next thing that happens is a payment call to kick off the game
        payer_email = "canbedifferent@example.com"
        payment_payload = dict(
            game_id=game_id,
            processor='paypal',
            type='start',
            payer_email=payer_email,
            uuid=Config.PAYPAL_TEST_USER_ID,
            amount=buy_in,
            currency='USD'
        )
        # we don't have a payment profile with this email in the test DB -- after we process the payment, we should
        # have a new one
        payment_profile = query_to_dict("SELECT * FROM payment_profiles WHERE payer_email = %s", payer_email)
        self.assertTrue(len(payment_profile) == 0)
        res = self.requests_session.post(f"{HOST_URL}/process_payment", cookies={"session_token": session_token},
                                         verify=False, json=payment_payload)
        self.assertEqual(res.status_code, 200)

        # user will decline to join, and we'll expect to see a capital outflow because of this
        game_payment_entries = query_to_dict("SELECT * FROM payments WHERE game_id = %s", game_id)
        self.assertEqual(len(game_payment_entries), 1)
        res = self.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": miguel_token},
                                         verify=False, json={"game_id": game_id, "decision": "declined"})
        self.assertEqual(res.status_code, 200)

        game_payment_entries = query_to_dict("SELECT * FROM payments WHERE game_id = %s", game_id)
        self.assertEqual(len(game_payment_entries), 2)
        self.assertEqual(set([x["type"] for x in game_payment_entries]), {"start", "refund"})
        for entry in game_payment_entries:
            self.assertEqual(entry["user_id"], user_id)
            self.assertEqual(entry["amount"], buy_in)
            if entry["type"] == "start":
                self.assertEqual(entry["direction"], "inflow")
            if entry["type"] == "refund":
                self.assertEqual(entry["direction"], "outflow")

    def test_game_payouts(self):
        # simulate a progression through the canonical game. after the first week we should send out a sidebet
        # payment to the winner. Once the game is concluded we should send out both the second sidebet payment and the
        # overall payment
        game_id = 3

        # after week 1
        with freeze_time(posix_to_datetime(simulation_start_time + SECONDS_IN_A_DAY * 7 + 1)):
            log_winners(game_id, time.time())
            last_win_entry = query_to_dict("SELECT * FROM winners ORDER BY id DESC LIMIT 1")[0]
            last_payment_entry = query_to_dict("SELECT * FROM payments ORDER BY id DESC LIMIT 1")[0]
            self.assertEqual(last_payment_entry["user_id"], last_win_entry["winner_id"])
            self.assertEqual(last_payment_entry["amount"], last_win_entry["payout"])
            self.assertEqual(last_payment_entry["winner_table_id"], last_win_entry["id"])
            self.assertEqual(last_payment_entry["type"], "sidebet")
            self.assertEqual(last_payment_entry["direction"], "outflow")

        # after week 2
        with freeze_time(posix_to_datetime(simulation_start_time + SECONDS_IN_A_DAY * 20 + 1)):
            log_winners(game_id, time.time())
            win_entries = query_to_dict("SELECT * FROM winners ORDER BY ID DESC;")
            self.assertEqual(len(win_entries), 3)
            overall_win_entry = win_entries[0]
            sidebet_win_entry = win_entries[1]
            last_payment_entries = query_to_dict("SELECT * FROM payments ORDER BY id DESC LIMIT 2")
            self.assertEqual(set(x["type"] for x in last_payment_entries), {"sidebet", "overall"})
            overall_payment_entry = last_payment_entries[0]
            sidebet_payment_entry = last_payment_entries[1]

            self.assertEqual(sidebet_payment_entry["user_id"], sidebet_win_entry["winner_id"])
            self.assertEqual(sidebet_payment_entry["amount"], sidebet_win_entry["payout"])
            self.assertEqual(sidebet_payment_entry["winner_table_id"], sidebet_win_entry["id"])
            self.assertEqual(sidebet_payment_entry["type"], "sidebet")
            self.assertEqual(sidebet_payment_entry["direction"], "outflow")

            self.assertEqual(overall_payment_entry["user_id"], overall_win_entry["winner_id"])
            self.assertEqual(overall_payment_entry["amount"], overall_win_entry["payout"])
            self.assertEqual(overall_payment_entry["winner_table_id"], overall_win_entry["id"])
            self.assertEqual(overall_payment_entry["type"], "overall")
            self.assertEqual(overall_payment_entry["direction"], "outflow")
