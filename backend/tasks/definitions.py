import time

from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import (
    TRACKED_INDEXES,
    during_trading_day,
    get_cache_price,
    set_cache_price,
    SeleniumDriverError,
    get_symbols_table,
    fetch_price,
    get_all_active_symbols,
    update_index_value
)
from backend.logic.games import (
    get_all_open_orders,
    process_order,
    get_open_game_ids_past_window,
    get_game_ids_by_status,
    service_open_game,
    expire_finished_game
)
from backend.tasks.celery import (
    celery,
    BaseTask
)
from backend.bi.report_logic import (
    serialize_and_pack_games_per_user_chart,
    serialize_and_pack_orders_per_active_user
)
from backend.tasks.redis import (
    redis_lock,
    TASK_LOCK_MSG
)
from backend.tasks.airflow import trigger_dag

TASK_LOCK_TEST_SLEEP = 1
CACHE_PRICE_LOCK_TIMEOUT = 60 * 5
PROCESS_ORDERS_LOCK_TIMEOUT = 60 * 5
UPDATE_GAME_DATA_TIMEOUT = 60 * 15

# -------------------------- #
# Price fetching and caching #
# -------------------------- #


@celery.task(name="async_cache_price", bind=True, base=BaseTask)
def async_cache_price(self, symbol: str, price: float, last_updated: float):
    # TODO: Turn this is into a wrapped function!
    with redis_lock(f"{symbol}_{price}_{last_updated}", CACHE_PRICE_LOCK_TIMEOUT) as acquired:
        if not acquired:
            return TASK_LOCK_MSG

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


@celery.task(name="async_update_index_value", bind=True, base=BaseTask)
def async_update_index_value(self, index):
    update_index_value(index)


@celery.task(name="async_update_all_index_values", bind=True, base=BaseTask)
def async_update_all_index_values(self):
    for index in TRACKED_INDEXES:
        async_update_index_value.delay(index)

# --------------- #
# Game management #
# --------------- #


@celery.task(name="async_service_open_games", bind=True, base=BaseTask)
def async_service_open_games(self):
    open_game_ids = get_open_game_ids_past_window()
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

    with engine.connect() as conn:
        conn.execute("TRUNCATE TABLE symbols;")

    with engine.connect() as conn:
        symbols_table.to_sql("symbols", conn, if_exists="append", index=False)


@celery.task(name="async_process_all_orders_in_game", bind=True, base=BaseTask)
def async_process_all_orders_in_game(self, game_id: int):
    with redis_lock(f"process_all_orders_{game_id}", PROCESS_ORDERS_LOCK_TIMEOUT) as acquired:
        if not acquired:
            return TASK_LOCK_MSG

        open_orders = get_all_open_orders(game_id)
        for order_id, _ in open_orders.items():
            process_order(order_id)


@celery.task(name="async_process_all_open_orders", bind=True, base=BaseTask)
def async_process_all_open_orders(self):
    """Scheduled to update all orders across all games throughout the trading day
    """
    active_ids = get_game_ids_by_status()
    for game_id in active_ids:
        async_process_all_orders_in_game.delay(game_id)


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
    active_ids = get_game_ids_by_status()
    for game_id in active_ids:
        async_update_game_data.delay(game_id)

    finished_ids = get_game_ids_by_status("finished")
    for game_id in finished_ids:
        expire_finished_game(game_id)


@celery.task(name="async_update_game_data", bind=True, base=BaseTask)
def async_update_game_data(self, game_id, start_time=None, end_time=None):
    with redis_lock(f"update_game_data{game_id}", UPDATE_GAME_DATA_TIMEOUT) as acquired:
        if not acquired:
            return TASK_LOCK_MSG
        trigger_dag("update_game_dag", game_id=game_id, start_time=start_time, end_time=end_time)

# ----------- #
# Key metrics #
# ----------- #


@celery.task(name="async_calculate_key_metrics", bind=True, base=BaseTask)
def async_calculate_key_metrics(self):
    serialize_and_pack_games_per_user_chart()
    serialize_and_pack_orders_per_active_user()

# ------- #
# Testing #
# ------- #


@celery.task(name="async_test_task_lock", bind=True, base=BaseTask)
def async_test_task_lock(self, game_id):
    with redis_lock(f"async_test_task_lock{game_id}", UPDATE_GAME_DATA_TIMEOUT) as acquired:
        if not acquired:
            return TASK_LOCK_MSG
        time.sleep(TASK_LOCK_TEST_SLEEP)
