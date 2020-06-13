import time

from backend.database.db import db_session
from backend.database.helpers import (
    represent_table,
    table_updater
)
from backend.logic.base import (
    PRICE_CACHING_INTERVAL,
    during_trading_day,
    get_user_id,
    get_user_information,
    get_current_game_cash_balance,
    get_all_game_users,
)
from backend.logic.friends import (
    suggest_friends,
    get_user_details_from_ids,
    get_friend_ids,
    get_friend_invite_ids
)
from backend.logic.games import (
    get_user_invite_statuses_for_pending_game,
    get_current_stock_holding,
    get_all_open_orders,
    place_order,
    get_order_ticket,
    process_order,
    get_game_info,
    get_order_expiration_status,
    get_open_game_invite_ids,
    get_active_game_ids,
    respond_to_invite,
    service_open_game,
    translate_usernames_to_ids,
    create_pending_game_status_entry,
    create_game_invites_entries,
    start_game_if_all_invites_responded,
    get_game_info_for_user,
    get_user_invite_status_for_game,
    DEFAULT_INVITE_OPEN_WINDOW
)
from backend.logic.payouts import (
    calculate_and_pack_metrics
)
from backend.logic.stock_data import (
    get_symbols_table,
    fetch_iex_price,
    get_all_active_symbols,
    SeleniumDriverError
)
from backend.logic.visuals import (
    compile_and_pack_player_sidebar_stats,
    serialize_and_pack_orders_open_orders,
    make_balances_chart_data,
    serialize_and_pack_balances_chart,
    make_the_field_charts,
    serialize_and_pack_current_balances,
)
from backend.tasks.celery import (
    celery,
    BaseTask,
    pause_return_until_subtask_completion
)
from backend.tasks.redis import rds


@celery.task(name="async_get_user_information", bind=True, base=BaseTask)
def async_get_user_information(self, user_id):
    return get_user_information(user_id)


# -------------------------- #
# Price fetching and caching #
# -------------------------- #

@celery.task(name="async_fetch_active_symbol_prices", bind=True, base=BaseTask)
def async_fetch_active_symbol_prices(self):
    active_symbols = get_all_active_symbols(db_session)
    for symbol in active_symbols:
        async_fetch_price.delay(symbol)


@celery.task(name="async_fetch_price", bind=True, base=BaseTask)
def async_fetch_price(self, symbol):
    """Whatever method is used to get a price, the return should always be a (price, timestamp) tuple.
    """
    price, timestamp = fetch_iex_price(symbol)
    async_cache_price.delay(symbol, price, timestamp)
    return price, timestamp


@celery.task(name="async_cache_price", bind=True, base=BaseTask)
def async_cache_price(self, symbol: str, price: float, last_updated: float):
    """We'll store the last-updated price of each monitored stock in redis. In the short-term this will save us some
    unnecessary data API call.
    """
    current_time = time.time()
    cache_value = rds.get(symbol)
    # If we have a cached value within the range of our price caching interval, don't story anything. This will help
    # avoid redundant entries in the DB
    if cache_value is not None:
        price, update_time = [float(x) for x in cache_value.split("_")]
        if current_time - update_time <= PRICE_CACHING_INTERVAL:
            return

    # Leave the cache alone if outside trade day. Use the final trade-day redis value for after-hours lookups
    rds.set(symbol, f"{price}_{last_updated}")
    if during_trading_day():
        prices = represent_table("prices")
        table_updater(prices, symbol=symbol, price=price, timestamp=last_updated)


# --------------- #
# Game management #
# --------------- #

@celery.task(name="async_get_user_invite_statuses_for_pending_game", bind=True, base=BaseTask)
def async_get_user_invite_statuses_for_pending_game(self, game_id):
    return get_user_invite_statuses_for_pending_game(game_id)


@celery.task(name="async_add_game", bind=True, base=BaseTask)
def async_add_game(self, creator_id, title, mode, duration, buy_in, n_rebuys, benchmark, side_bets_perc,
                   side_bets_period, invitees):
    opened_at = time.time()
    invite_window = opened_at + DEFAULT_INVITE_OPEN_WINDOW

    games = represent_table("games")
    result = table_updater(games,
                           creator_id=creator_id,
                           title=title,
                           mode=mode,
                           duration=duration,
                           buy_in=buy_in,
                           n_rebuys=n_rebuys,
                           benchmark=benchmark,
                           side_bets_perc=side_bets_perc,
                           side_bets_period=side_bets_period,
                           invite_window=invite_window)
    game_id = result.inserted_primary_key[0]
    invited_ids = translate_usernames_to_ids(tuple(invitees))
    user_ids = invited_ids + [creator_id]

    create_pending_game_status_entry(game_id, user_ids, opened_at)
    create_game_invites_entries(game_id, creator_id, user_ids, opened_at)


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
    status_list = []
    for game_id in open_game_ids:
        status_list.append(async_service_one_open_game.delay(game_id))
    pause_return_until_subtask_completion(status_list, "async_service_open_games")


@celery.task(name="async_service_one_open_game", bind=True, base=BaseTask)
def async_service_one_open_game(self, game_id):
    service_open_game(game_id)


@celery.task(name="async_get_game_info", bind=True, base=BaseTask)
def async_get_game_info(self, game_id, user_id):
    game_info = get_game_info(game_id)
    game_info["user_status"] = get_user_invite_status_for_game(game_id, user_id)
    return game_info


@celery.task(name="async_get_game_info_for_user", bind=True, base=BaseTask)
def async_get_game_info_for_user(self, user_id):
    return get_game_info_for_user(user_id)


# ---------------- #
# Order management #
# ---------------- #


@celery.task(name="async_suggest_symbols", base=BaseTask)
def async_suggest_symbols(text):
    with db_session.connection() as conn:
        to_match = f"{text.upper()}%"
        symbol_suggestions = conn.execute("""
            SELECT * FROM symbols
            WHERE symbol LIKE %s OR name LIKE %s LIMIT 20;""", (to_match, to_match))
        db_session.remove()

    return [{"symbol": entry[1], "label": f"{entry[1]} ({entry[2]})"} for entry in symbol_suggestions]


@celery.task(name="async_update_symbols_table", bind=True, default_retry_delay=10, base=BaseTask)
def async_update_symbols_table(self, n_rows=None):
    symbols_table = get_symbols_table(n_rows)
    if symbols_table.empty:
        raise SeleniumDriverError

    print("writing to db...")
    with db_session.connection() as conn:
        conn.execute("TRUNCATE TABLE symbols;")
        db_session.remove()

    with db_session.connection() as conn:
        symbols_table.to_sql("symbols", conn, if_exists="append", index=False)
        db_session.commit()


@celery.task(name="async_place_order", base=BaseTask)
def async_place_order(user_id, game_id, symbol, buy_or_sell, order_type, quantity_type, market_price, amount,
                      time_in_force, stop_limit_price=None):
    """Placing an order involves several layers of conditional logic: is this is a buy or sell order? Stop, limit, or
    market? Do we either have the adequate cash on hand, or enough of a position in the stock for this order to be
    valid? Here an order_ticket from the frontend--along with the user_id tacked on during the API call--gets decoded,
    checked for validity, and booked. Market orders are fulfilled in the same step. Stop/limit orders are monitored on
    an ongoing basis by the celery schedule and book as their requirements are satisfies
    """
    # extract relevant data
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    current_holding = get_current_stock_holding(user_id, game_id, symbol)
    place_order(user_id, game_id, symbol, buy_or_sell, cash_balance, current_holding, order_type, quantity_type,
                market_price, amount, time_in_force, stop_limit_price)


@celery.task(name="async_process_single_order", base=BaseTask)
def async_process_single_order(order_id):
    timestamp = time.time()
    if get_order_expiration_status(order_id):
        order_status = represent_table("order_status")
        table_updater(order_status, order_id=order_id, timestamp=timestamp, status="expired", clear_price=None)
        return

    order_ticket = get_order_ticket(order_id)
    symbol = order_ticket["symbol"]
    res = async_fetch_price.delay(symbol)
    while not res.ready():
        continue

    market_price, _ = res.results
    process_order(order_ticket["game_id"], order_ticket["user_id"], symbol, order_id, order_ticket["buy_or_sell"],
                  order_ticket["order_type"], order_ticket["price"], market_price, order_ticket["quantity"], timestamp)


@celery.task(name="async_process_all_open_orders", bind=True, base=BaseTask)
def async_process_all_open_orders(self):
    """Scheduled to update all orders across all games throughout the trading day
    """
    open_orders = get_all_open_orders()
    status_list = []
    for order_id, expiration in open_orders:
        status_list.append(async_process_single_order.delay(order_id))
    pause_return_until_subtask_completion(status_list, "async_process_all_open_orders")

# ------- #
# Friends #
# ------- #


@celery.task(name="async_invite_friend", bind=True, base=BaseTask)
def async_invite_friend(self, requester_id, invited_username):
    """Since the user is sending the request, we'll know their user ID via their web token. We don't post this
    information to the frontend for other users, though, so we'll look up their ID based on username
    """
    invited_id = get_user_id(invited_username)
    friends = represent_table("friends")
    table_updater(friends, requester_id=requester_id, invited_id=invited_id, status="invited", timestamp=time.time())


@celery.task(name="async_respond_to_friend_invite", bind=True, base=BaseTask)
def async_respond_to_friend_invite(self, requester_username, invited_id, decision):
    """Since the user is responding to the request, we'll know their user ID via their web token. We don't post this
    information to the frontend for other users, though, so we'll look up the request ID based on the username
    """
    requester_id = get_user_id(requester_username)
    friends = represent_table("friends")
    table_updater(friends, requester_id=requester_id, invited_id=invited_id, status=decision, timestamp=time.time())


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
"""This gets a little bit dense. async_serialize_open_orders and async_serialize_current_balances run at the game-user
level, and are light, fast tasks that update users' orders and balances tables. async_update_play_game_visuals starts 
both of these tasks for every user in every open game. It also runs tasks for async_make_the_field_charts, a more
expensive task that serializes balance histories for all user positions in all open games and, based on that data, 
creates a "the field" chart for portfolio level comps. 

In addition to being run by async_update_play_game_visuals, these tasks are also run when calling the place_order
endpoint in order to have user data be as dynamic and responsive as possible:
* async_serialize_open_orders
* async_serialize_current_balances
* async_serialize_balances_chart
"""


@celery.task(name="async_serialize_open_orders", bind=True, base=BaseTask)
def async_serialize_open_orders(self, game_id, user_id):
    serialize_and_pack_orders_open_orders(game_id, user_id)


@celery.task(name="async_serialize_current_balances", bind=True, base=BaseTask)
def async_serialize_current_balances(self, game_id, user_id):
    serialize_and_pack_current_balances(game_id, user_id)


@celery.task(name="async_serialize_balances_chart", bind=True, base=BaseTask)
def async_serialize_balances_chart(self, game_id, user_id):
    df = make_balances_chart_data(game_id, user_id)
    serialize_and_pack_balances_chart(df, game_id, user_id)


@celery.task(name="async_make_the_field_charts", bind=True, base=BaseTask)
def async_make_the_field_charts(self, game_id):
    make_the_field_charts(game_id)


@celery.task(name="async_update_play_game_visuals", bind=True, base=BaseTask)
def async_update_play_game_visuals(self):
    open_game_ids = get_active_game_ids()
    task_results = []
    for game_id in open_game_ids:
        task_results.append(async_make_the_field_charts.delay(game_id))
        user_ids = get_all_game_users(game_id)
        for user_id in user_ids:
            task_results.append(async_serialize_open_orders.delay(game_id, user_id))
            task_results.append(async_serialize_current_balances.delay(game_id, user_id))
    pause_return_until_subtask_completion(task_results, "async_update_play_game_visuals")


# ---------------------- #
# Player stat production #
# ---------------------- #
@celery.task(name="async_calculate_metrics", bind=True, base=BaseTask)
def async_calculate_game_metrics(self, game_id, user_id, start_date=None, end_date=None):
    calculate_and_pack_metrics(game_id, user_id, start_date, end_date)


@celery.task(name="async_update_player_stats", bind=True, base=BaseTask)
def async_update_player_stats(self):
    """This task calculates game-level metrics for all players in all games, caching those metrics to redis
    """
    open_game_ids = get_active_game_ids()
    task_results = []
    for game_id in open_game_ids:
        user_ids = get_all_game_users(game_id)
        for user_id in user_ids:
            task_results.append(async_calculate_game_metrics.delay(game_id, user_id))
    pause_return_until_subtask_completion(task_results, "async_update_player_stats")


@celery.task(name="async_compile_player_stats", bind=True, base=BaseTask)
def async_compile_player_sidebar_stats(self, game_id):
    compile_and_pack_player_sidebar_stats(game_id)


@celery.task(name="async_get_player_cash_balance", bind=True, base=BaseTask)
def async_get_player_cash_balance(self, game_id, user_id):
    return get_current_game_cash_balance(user_id, game_id)
