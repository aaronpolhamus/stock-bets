"""This is a "master" integration test designed to test a full user story from first login, to adding friends,
creating a game, and placing and fulfilling orders. It's designed to be expanded upon as we add additional functionality
to the platform.

A few important things about this test:
1) In order to test real-time order fulfillment this should be run with the IEX_API_PRODUCTION env var set to True and
  during trading hours.
2) This test isn't meant to be run automatically as part of the regular testing suite, but as a form of detailed,
  manual QC
3) Eventually we'll want to bake this into Cypress or some other frontend testing framework. For now, each call to the
  API server is blocked with with an input() confirmation, allowing you to keep the frontend open and see the impact of
  different user actions.
"""
from backend.config import Config
from backend.database.fixtures.mock_data import refresh_table
from backend.database.helpers import reset_db
from backend.tasks.redis import rds
from backend.tests import BaseTestCase
from backend.tests.test_api import HOST_URL

if __name__ == '__main__':
    btc = BaseTestCase()
    btc.setUp()
    reset_db()
    rds.flushall()
    refresh_table("users")

    # setup user tokens
    user_token = btc.make_test_token_from_email(Config.TEST_CASE_EMAIL)
    username = "cheetos"
    miguel_token = btc.make_test_token_from_email("mike@example.test")
    toofast_token = btc.make_test_token_from_email("eddie@example.test")
    jack_token = btc.make_test_token_from_email("jack@black.pearl")
    jadis_token = btc.make_test_token_from_email("jadis@rick.lives")
    johnnie_token = btc.make_test_token_from_email("johnnie@walker.com")

    value = input("""
    Check out the play game screen. It should be blank. Hit 'c' to add all friends automatically,  otherwise head to 
    localhost:3000 to add friends manually. Be sure to add miguel, toofast, jack, jadis, and johnnie, or the test will 
    break. When you're done, come back and hit "enter" to continue.
    """)
    if value == "c":
        btc.requests_session.post(f"{HOST_URL}/send_friend_request", json={"friend_invitee": "toofast"},
                                  cookies={"session_token": user_token}, verify=False)
        btc.requests_session.post(f"{HOST_URL}/send_friend_request", json={"friend_invitee": "miguel"},
                                  cookies={"session_token": user_token}, verify=False)
        btc.requests_session.post(f"{HOST_URL}/send_friend_request", json={"friend_invitee": "johnnie"},
                                  cookies={"session_token": user_token}, verify=False)
        btc.requests_session.post(f"{HOST_URL}/send_friend_request", json={"friend_invitee": "jack"},
                                  cookies={"session_token": user_token}, verify=False)
        btc.requests_session.post(f"{HOST_URL}/send_friend_request", json={"friend_invitee": "jadis"},
                                  cookies={"session_token": user_token}, verify=False)

    input("""
    If you try to re-add the same people, you should see "invite sent" next to each of their names. Go ahead and hit any
    key for jadis and jack to accept your invites. johnnie is going to reject you, but whatever. If you refresh the 
    page, you should now have them in your friend list:
    """)
    btc.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                              json={"requester_username": username, "decision": "accepted"},
                              cookies={"session_token": miguel_token}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                              json={"requester_username": username, "decision": "accepted"},
                              cookies={"session_token": toofast_token}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                              json={"requester_username": username, "decision": "declined"},
                              cookies={"session_token": johnnie_token}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                              json={"requester_username": username, "decision": "accepted"},
                              cookies={"session_token": jadis_token}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_friend_request",
                              json={"requester_username": username, "decision": "accepted"},
                              cookies={"session_token": jack_token}, verify=False)

    # we're done here. go ahead and tear it all down
    btc.tearDown()
