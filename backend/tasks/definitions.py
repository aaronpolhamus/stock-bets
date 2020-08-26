import time

from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import (
    during_trading_day,
    SeleniumDriverError,
    get_all_active_symbols
)
from logic.stock_data import (
    get_symbols_table,
    update_index_value,
    get_cache_price,
    fetch_price,
    set_cache_price,
    get_stock_splits,
    apply_stock_splits,
    TRACKED_INDEXES, get_game_ids_by_status)
from backend.logic.games import (
    get_all_open_orders,
    process_order,
    get_open_game_ids_past_window,
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
    TASK_LOCK_MSG,
    task_lock
)
from backend.tasks.airflow import trigger_dag

TASK_LOCK_TEST_SLEEP = 1
CACHE_PRICE_LOCK_TIMEOUT = 60 * 5
PROCESS_ORDERS_LOCK_TIMEOUT = 60 * 5
CACHE_PRICE_TIMEOUT = 60 * 15
UPDATE_GAME_TIMEOUT = 60 * 15

# -------------------------- #
# Price fetching and caching #
# -------------------------- #


@celery.task(name="async_cache_price", bind=True, base=BaseTask)
@task_lock(main_key="async_cache_price", timeout=CACHE_PRICE_TIMEOUT)
def async_cache_price(self, symbol: str, price: float, last_updated: float):
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


@celery.task(name="async_apply_stock_splits", bind=True, base=BaseTask)
def async_apply_stock_splits(self):
    splits = get_stock_splits()
    with engine.connect() as conn:
        splits.to_sql("stock_splits", conn, if_exists="append", index=False)
    apply_stock_splits(splits)


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


@celery.task(name="async_update_all_games", bind=True, base=BaseTask)
def async_update_all_games(self, start_time=None, end_time=None):
    active_ids = get_game_ids_by_status()
    for game_id in active_ids:
        trigger_dag("update_game_dag", game_id=game_id, start_time=start_time, end_time=end_time)

    finished_ids = get_game_ids_by_status("finished")
    for game_id in finished_ids:
        expire_finished_game(game_id)


# ----------- #
# Key metrics #
# ----------- #

@celery.task(name="async_calculate_key_metrics", bind=True, base=BaseTask)
def async_calculate_key_metrics(self):
    serialize_and_pack_games_per_user_chart()
    serialize_and_pack_orders_per_active_user()


# ----------- #
# Maintenance #
# ----------- #

@celery.task(name="async_clear_balances_and_prices_cache", bind=True, base=BaseTask)
def async_clear_balances_and_prices_cache(self):
    with engine.connect() as conn:
        conn.execute("TRUNCATE balances_and_prices_cache;")


# ------- #
# Testing #
# ------- #

@celery.task(name="async_test_task_lock", bind=True, base=BaseTask)
@task_lock(main_key="async_test_task_lock", timeout=CACHE_PRICE_TIMEOUT)
def async_test_task_lock(self, game_id):
    print(f"processing game_id {game_id}")
    time.sleep(TASK_LOCK_TEST_SLEEP)
