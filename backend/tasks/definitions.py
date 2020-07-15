import time

from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import (
    during_trading_day,
    get_all_game_users_ids,
    get_cache_price,
    set_cache_price
)
from backend.logic.games import (
    get_all_open_orders,
    process_order,
    get_open_game_invite_ids,
    get_active_game_ids,
    service_open_game
)
from backend.logic.winners import (
    calculate_and_pack_metrics,
    log_winners
)
from logic.base import (
    SeleniumDriverError,
    get_symbols_table,
    fetch_price,
    get_all_active_symbols,
)
from backend.logic.visuals import (
    serialize_and_pack_order_performance_chart,
    serialize_and_pack_winners_table,
    compile_and_pack_player_leaderboard,
    serialize_and_pack_order_details,
    make_the_field_charts,
    serialize_and_pack_portfolio_details,
)
from backend.tasks.celery import (
    celery,
    BaseTask
)
from backend.bi.report_logic import (
    serialize_and_pack_games_per_user_chart,
    serialize_and_pack_orders_per_active_user
)
from backend.tasks.redis import task_lock

PROCESS_ORDERS_LOCK_KEY = "process_all_open_orders"
PROCESS_ORDERS_LOCK_TIMEOUT = 60 * 15 * 1000

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


@celery.task(name="async_service_open_games", bind=True, base=BaseTask)
def async_service_open_games(self):
    open_game_ids = get_open_game_invite_ids()
    for game_id in open_game_ids:
        async_service_one_open_game.delay(game_id)


@celery.task(name="async_service_one_open_game", bind=True, base=BaseTask)
def async_service_one_open_game(self, game_id):
    service_open_game(game_id)

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
@task_lock(key=PROCESS_ORDERS_LOCK_KEY, timeout=PROCESS_ORDERS_LOCK_TIMEOUT)
def async_process_all_open_orders(self):
    """Scheduled to update all orders across all games throughout the trading day
    """
    open_orders = get_all_open_orders()
    for order_id, _ in open_orders.items():
        process_order(order_id)


# ------------- #
# Visual assets #
# ------------- #
"""async_update_game gets a little bit dense, but its logic is actually pretty straightforward:
1) Update the overall game metrics for each player
2) Based on those metrics, update the leaderboard 
3) Now the we have a leaderboard, calculate the field and balances charts. We'll send these along with the leaderboard
4) For each player, update their orders and balances table, and then update their order performance chart
5) Finally, check for winners and update the winners table if there are any
"""


@celery.task(name="async_update_all_games", bind=True, base=BaseTask)
def async_update_all_games(self):
    open_game_ids = get_active_game_ids()
    for game_id in open_game_ids:
        async_update_game_data.delay(game_id)


@celery.task(name="async_update_game_data", bind=True, base=BaseTask)
def async_update_game_data(self, game_id):
    user_ids = get_all_game_users_ids(game_id)
    for user_id in user_ids:
        # calculate overall standings
        calculate_and_pack_metrics(game_id, user_id)

    # leaderboard
    compile_and_pack_player_leaderboard(game_id)

    # the field and balance charts
    make_the_field_charts(game_id)

    # tables and performance breakout charts
    for user_id in user_ids:
        # game/user-level assets
        serialize_and_pack_order_details(game_id, user_id)
        serialize_and_pack_portfolio_details(game_id, user_id)
        serialize_and_pack_order_performance_chart(game_id, user_id)

    # winners/payouts table
    update_performed = log_winners(game_id, time.time())
    if update_performed:
        serialize_and_pack_winners_table(game_id)


# ----------- #
# Key metrics #
# ----------- #
@celery.task(name="async_calculate_metrics", bind=True, base=BaseTask)
def async_calculate_metrics(self):
    serialize_and_pack_games_per_user_chart()
    serialize_and_pack_orders_per_active_user()
