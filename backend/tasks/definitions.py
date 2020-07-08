import time

from backend.database.db import engine
from backend.database.helpers import (
    add_row
)
from backend.logic.base import (
    during_trading_day,
    get_user_id,
    get_all_game_users,
    get_cache_price,
    set_cache_price
)
from backend.logic.friends import (
    suggest_friends,
    get_user_details_from_ids,
    get_friend_ids,
    get_friend_invite_ids
)
from backend.logic.games import (
    get_user_invite_statuses_for_pending_game,
    get_all_open_orders,
    process_order,
    get_open_game_invite_ids,
    get_active_game_ids,
    respond_to_invite,
    service_open_game,
    start_game_if_all_invites_responded,
    get_user_invite_status_for_game
)
from backend.logic.payouts import (
    calculate_and_pack_metrics,
    log_winners
)
from logic.base import (
    SeleniumDriverError,
    get_symbols_table,
    fetch_price,
    get_all_active_symbols,
    get_game_info
)
from backend.logic.visuals import (
    update_order_details_table,
    serialize_and_pack_order_performance_chart,
    serialize_and_pack_winners_table,
    compile_and_pack_player_sidebar_stats,
    serialize_and_pack_order_details,
    make_balances_chart_data,
    serialize_and_pack_balances_chart,
    make_the_field_charts,
    serialize_and_pack_portfolio_details,
)
from backend.tasks.celery import (
    celery,
    BaseTask
)
from backend.tasks.redis import task_lock

# -------------------------- #
# Price fetching and caching #
# -------------------------- #


@celery.task(name="async_cache_price", bind=True, base=BaseTask)
def async_cache_price(self, symbol: str, price: float, last_updated: float):
    """We'll store the last-updated price of each monitored stock in redis. In the short-term this will save us some
    unnecessary data API call.
    """
    cache_price, cache_time = get_cache_price(symbol)
    if cache_price is not None and cache_time == last_updated:
        return

    if during_trading_day():
        add_row("prices", symbol=symbol, price=price, timestamp=last_updated)
        set_cache_price(symbol, price, last_updated)


@celery.task(name="async_fetch_and_cache_prices", bind=True, base=BaseTask)
def async_fetch_and_cache_prices(self, symbol):
    price, timestamp = fetch_price(symbol)
    async_cache_price.delay(symbol, price, timestamp)


@celery.task(name="async_fetch_active_symbol_prices", bind=True, base=BaseTask)
def async_fetch_active_symbol_prices(self):
    active_symbols = get_all_active_symbols()
    for symbol in active_symbols:
        async_fetch_and_cache_prices.delay(symbol)

# --------------- #
# Game management #
# --------------- #


@celery.task(name="async_get_user_invite_statuses_for_pending_game", bind=True, base=BaseTask)
def async_get_user_invite_statuses_for_pending_game(self, game_id):
    return get_user_invite_statuses_for_pending_game(game_id)


@celery.task(name="async_respond_to_game_invite", bind=True, base=BaseTask)
def async_respond_to_game_invite(self, game_id, user_id, status):
    assert status in ["joined", "declined"]
    response_time = time.time()
    respond_to_invite(game_id, user_id, status, response_time)
    # Check to see if we everyone has either joined or declined and whether we can start the game early
    start_game_if_all_invites_responded(game_id)


@celery.task(name="async_service_open_games", bind=True, base=BaseTask)
def async_service_open_games(self):
    open_game_ids = get_open_game_invite_ids()
    for game_id in open_game_ids:
        async_service_one_open_game.delay(game_id)


@celery.task(name="async_service_one_open_game", bind=True, base=BaseTask)
def async_service_one_open_game(self, game_id):
    service_open_game(game_id)


@celery.task(name="async_get_game_info", bind=True, base=BaseTask)
def async_get_game_info(self, game_id, user_id):
    game_info = get_game_info(game_id)
    game_info["user_status"] = get_user_invite_status_for_game(game_id, user_id)
    return game_info

# ---------------- #
# Order management #
# ---------------- #


@celery.task(name="async_update_symbols_table", bind=True, default_retry_delay=10, base=BaseTask)
def async_update_symbols_table(self, n_rows=None):
    symbols_table = get_symbols_table(n_rows)
    if symbols_table.empty:
        raise SeleniumDriverError

    print("writing to db...")
    with engine.connect() as conn:
        conn.execute("TRUNCATE TABLE symbols;")

    with engine.connect() as conn:
        symbols_table.to_sql("symbols", conn, if_exists="append", index=False)


@celery.task(name="async_process_all_open_orders", bind=True, base=BaseTask)
@task_lock(key="process_all_open_orders", timeout=60 * 5)
def async_process_all_open_orders(self):
    """Scheduled to update all orders across all games throughout the trading day
    """
    open_orders = get_all_open_orders()
    for order_id, _ in open_orders.items():
        process_order(order_id)


@celery.task(name="async_update_order_details_table", bind=True, base=BaseTask)
def async_update_order_details_table(self, game_id, user_id, order_id, action):
    update_order_details_table(game_id, user_id, order_id, action)


# ------- #
# Friends #
# ------- #


@celery.task(name="async_invite_friend", bind=True, base=BaseTask)
def async_invite_friend(self, requester_id, invited_username):
    """Since the user is sending the request, we'll know their user ID via their web token. We don't post this
    information to the frontend for other users, though, so we'll look up their ID based on username
    """
    invited_id = get_user_id(invited_username)
    add_row("friends", requester_id=requester_id, invited_id=invited_id, status="invited", timestamp=time.time())


@celery.task(name="async_respond_to_friend_invite", bind=True, base=BaseTask)
def async_respond_to_friend_invite(self, requester_username, invited_id, decision):
    """Since the user is responding to the request, we'll know their user ID via their web token. We don't post this
    information to the frontend for other users, though, so we'll look up the request ID based on the username
    """
    requester_id = get_user_id(requester_username)
    add_row("friends", requester_id=requester_id, invited_id=invited_id, status=decision, timestamp=time.time())


@celery.task(name="async_get_friends_details", bind=True, base=BaseTask)
def async_get_friends_details(self, user_id):
    friend_ids = get_friend_ids(user_id)
    return get_user_details_from_ids(friend_ids)


@celery.task(name="async_suggest_friends", bind=True, base=BaseTask)
def async_suggest_friends(self, user_id, text):
    return suggest_friends(user_id, text)


@celery.task(name="async_get_friend_invites", bind=True, base=BaseTask)
def async_get_friend_invites(self, user_id):
    invite_ids = get_friend_invite_ids(user_id)
    if not invite_ids:
        return []
    details = get_user_details_from_ids(invite_ids)
    return [x["username"] for x in details]


# ------------- #
# Visual assets #
# ------------- #
"""This gets a little bit dense. async_serialize_order_details and async_serialize_current_balances run at the game-user
level, and are light, fast tasks that update users' orders and balances tables. async_update_play_game_visuals starts 
both of these tasks for every user in every open game. It also runs tasks for async_make_the_field_charts, a more
expensive task that serializes balance histories for all user positions in all open games and, based on that data, 
creates a "the field" chart for portfolio level comps. 

In addition to being run by async_update_play_game_visuals, these tasks are also run when calling the place_order
endpoint in order to have user data be as dynamic and responsive as possible:
* async_serialize_order_details
* async_serialize_current_balances
* async_serialize_balances_chart
"""


@celery.task(name="async_serialize_order_details", bind=True, base=BaseTask)
def async_serialize_order_details(self, game_id, user_id):
    serialize_and_pack_order_details(game_id, user_id)


@celery.task(name="async_serialize_current_balances", bind=True, base=BaseTask)
def async_serialize_current_balances(self, game_id, user_id):
    serialize_and_pack_portfolio_details(game_id, user_id)


@celery.task(name="async_serialize_balances_chart", bind=True, base=BaseTask)
def async_serialize_balances_chart(self, game_id, user_id):
    df = make_balances_chart_data(game_id, user_id)
    serialize_and_pack_balances_chart(df, game_id, user_id)


@celery.task(name="async_make_the_field_charts", bind=True, base=BaseTask)
def async_make_the_field_charts(self, game_id):
    make_the_field_charts(game_id)


@celery.task(name="async_make_order_performance_chart", bind=True, base=BaseTask)
def async_make_order_performance_chart(self, game_id, user_id):
    serialize_and_pack_order_performance_chart(game_id, user_id)


@celery.task(name="async_update_play_game_visuals", bind=True, base=BaseTask)
def async_update_play_game_visuals(self):
    open_game_ids = get_active_game_ids()
    for game_id in open_game_ids:
        # game-level assets
        async_make_the_field_charts.delay(game_id)
        async_serialize_and_pack_winners_table.delay(game_id)
        async_compile_player_sidebar_stats.delay(game_id)
        user_ids = get_all_game_users(game_id)
        for user_id in user_ids:
            # game/user-level assets
            async_serialize_order_details.delay(game_id, user_id)
            async_serialize_current_balances.delay(game_id, user_id)
            async_make_order_performance_chart.delay(game_id, user_id)

# ---------------------- #
# Player stat production #
# ---------------------- #


@celery.task(name="async_calculate_metrics", bind=True, base=BaseTask)
def async_calculate_game_metrics(self, game_id, user_id, start_date=None, end_date=None):
    calculate_and_pack_metrics(game_id, user_id, start_date, end_date)


@celery.task(name="async_compile_player_sidebar_stats", bind=True, base=BaseTask)
def async_compile_player_sidebar_stats(self, game_id):
    compile_and_pack_player_sidebar_stats(game_id)


@celery.task(name="async_update_player_stats", bind=True, base=BaseTask)
def async_update_player_stats(self):
    """This task calculates game-level metrics for all players in all games, caching those metrics to redis
    """
    active_game_ids = get_active_game_ids()
    for game_id in active_game_ids:
        async_compile_player_sidebar_stats.delay(game_id)
        user_ids = get_all_game_users(game_id)
        for user_id in user_ids:
            async_calculate_game_metrics.delay(game_id, user_id)


@celery.task(name="async_serialize_and_pack_winners_table", bind=True, base=BaseTask)
def async_serialize_and_pack_winners_table(self, game_id):
    serialize_and_pack_winners_table(game_id)


@celery.task(name="async_calculate_winner", bind=True, base=BaseTask)
def async_calculate_winner(self, game_id):
    log_winners(game_id)


@celery.task(name="async_calculate_winners", bind=True, base=BaseTask)
def async_calculate_winners(self):
    open_game_ids = get_active_game_ids()
    for game_id in open_game_ids:
        async_calculate_winner.delay(game_id)
