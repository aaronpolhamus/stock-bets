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
import json

from backend.config import Config
from backend.database.fixtures.mock_data import refresh_table
from backend.database.helpers import (
    reset_db,
    orm_rows_to_dict,
    represent_table
)
from backend.logic.friends import get_user_details_from_ids
from backend.logic.games import get_invite_list_by_status
from backend.tasks.redis import rds
from backend.tasks.definitions import (
    async_update_play_game_visuals,
    async_update_player_stats
)
from backend.tests import BaseTestCase
from backend.tests.test_api import HOST_URL


if __name__ == '__main__':
    btc = BaseTestCase()
    btc.setUp()
    reset_db()
    rds.flushall()
    refresh_table("users")
    refresh_table("symbols")

    # setup user tokens
    user_id = 1
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

    with btc.db_session.connection() as conn:
        friend_entries_count = conn.execute("SELECT COUNT(*) FROM friends;").fetchone()[0]
        assert friend_entries_count == 5
        btc.db_session.remove()

    input("""
    If you try to re-add the same people, you should see "invite sent" next to each of their names. Go ahead and hit any
    key for miguel, toofast, jadis and jack to accept your invites. johnnie is going to reject you, but whatever. If you
    refresh the page, you should now have them in your friend list:
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

    with btc.db_session.connection() as conn:
        friend_count = conn.execute("SELECT COUNT(*) FROM friends WHERE requester_id = %s AND status = 'accepted';",
                                    user_id).fetchone()[0]
        assert friend_count == 4
        btc.db_session.remove()

    # make sure that from johnnie's perspective he doesn't have any outstandnig friend invites left
    res = btc.requests_session.post(f"{HOST_URL}/get_list_of_friend_invites", cookies={"session_token": johnnie_token}, verify=False)
    assert len(res.json()) == 0

    game_settings = {
        "title": "test game",
        "mode": "winner_takes_all",
        "duration": 90,
        "buy_in": 100,
        "n_rebuys": 3,
        "benchmark": "sharpe_ratio",
        "side_bets_perc": 50,
        "side_bets_period": "weekly",
        "invitees": ["miguel", "toofast", "jadis", "jack"],
    }

    value = input(f"""
    Time to make a game! Hit 'c' to have the test runner do this for you, or make the game by hand, paying close
    attention to these settings: (come back and hit any key once you've submitted the game ticket)
    {game_settings}
    """)

    if value == "c":
        res = btc.requests_session.post(f"{HOST_URL}/create_game", cookies={"session_token": user_token}, verify=False,
                                        json=game_settings)

    games = represent_table("games")
    row = btc.db_session.query(games).filter(games.c.id == 1)
    game_entry = orm_rows_to_dict(row)
    for k, v in game_settings.items():
        if k == "invitees":
            continue
        assert game_entry[k] == v

    game_status = represent_table("game_status")
    row = btc.db_session.query(game_status).filter(game_status.c.game_id == 1)
    game_entry = orm_rows_to_dict(row)
    user_id_list = json.loads(game_entry["users"])
    details = get_user_details_from_ids(user_id_list)
    assert set([x["username"] for x in details]) == {"cheetos", "miguel", "toofast", "jack", "jadis"}
    btc.db_session.remove()

    input("""
    Great, we've got the game on the board. jadis, jack, and miguel are going to play, toofast is going to bow out of 
    this round. Hit any key to continue. 
    """)
    btc.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": jadis_token},
                              json={"game_id": 1, "decision": "joined"}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": jack_token},
                              json={"game_id": 1, "decision": "joined"}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": miguel_token},
                              json={"game_id": 1, "decision": "joined"}, verify=False)
    btc.requests_session.post(f"{HOST_URL}/respond_to_game_invite", cookies={"session_token": toofast_token},
                              json={"game_id": 1, "decision": "declined"}, verify=False)

    accepted_invite_user_ids = get_invite_list_by_status(1, "joined")
    details = get_user_details_from_ids(accepted_invite_user_ids)
    assert set([x["username"] for x in details]) == {"cheetos", "miguel", "jack", "jadis"}

    res = btc.requests_session.post(f"{HOST_URL}/get_open_orders_table", cookies={"session_token": user_token},
                                    json={"game_id": 1}, verify=False)
    open_orders_table_init = res.json()

    res = btc.requests_session.post(f"{HOST_URL}/get_current_balances_table", cookies={"session_token": user_token},
                                    json={"game_id": 1}, verify=False)
    balances_table_init = res.json()

    input("""
    When we invoke functions to update the global game state we shouldn't see any error or change prior to placing
    orders. Hit any key to continue
    """)
    async_update_play_game_visuals()
    async_update_player_stats()
    import ipdb;ipdb.set_trace()

    input("""
    We got a game! Time to put in our first order.
    """)
    btc.tearDown()
