from backend.database.helpers import query_to_dict
from backend.tests import BaseTestCase
from backend.config import Config

HOST_URL = 'https://localhost:5000/api'


class TestPayments(BaseTestCase):

    def test_game_startup(self):
        user_id = 1
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)
        miguel_token = self.make_test_token_from_email("mike@example.test")
        toofast_token = self.make_test_token_from_email("eddie@example.test")

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
            uuid='abc123',
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
            uuid='cde456',
            amount=buy_in,
            currency='USD'
        )
        res = self.requests_session.post(f"{HOST_URL}/process_payment", cookies={"session_token": session_token},
                                         verify=False, json=payment_payload)
        self.assertEqual(res.status_code, 200)

        game_payment_entries = query_to_dict("SELECT * FROM payments WHERE game_id = %s", game_id)
        self.assertEqual(len(game_payment_entries), 2)
        self.assertEqual(set([x['type'] for x in game_payment_entries]), {'start', 'join'})

        # test refunds for cancelled games
        # miguel changes his mind and cancels -- he gets a refund

        # toofast declines the game, canceling it -- the host gets a refund

    def test_game_payouts(self):
        session_token = self.make_test_token_from_email(Config.TEST_CASE_EMAIL)

        # test sidebet winner

        # test overall winner
        pass
