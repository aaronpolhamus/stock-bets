import time

from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import (
    during_trading_day,
    get_all_active_symbols
)
from logic.stock_data import (
    update_index_value,
    get_cache_price,
    fetch_price,
    set_cache_price,
    TRACKED_INDEXES,
    get_game_ids_by_status,
)
from backend.logic.games import (
    get_all_open_orders,
    process_order,
    get_open_game_ids_past_window,
    service_open_game
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
from backend.tasks.airflow import start_dag

TASK_LOCK_TEST_SLEEP = 1
CACHE_PRICE_LOCK_TIMEOUT = 60 * 5
PROCESS_ORDERS_LOCK_TIMEOUT = 60 * 5
CACHE_PRICE_TIMEOUT = 60 * 15


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


@celery.task(name="async_scrape_stock_data", bind=True, base=BaseTask)
def async_scrape_stock_data(self):
    start_dag("stock_data_dag")

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


@celery.task(name="async_process_all_orders_in_game", bind=True, base=BaseTask)
@task_lock(main_key="async_process_all_orders_in_game", timeout=PROCESS_ORDERS_LOCK_TIMEOUT)
def async_process_all_orders_in_game(self, game_id: int):
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
def async_update_all_games(self):
    active_ids = get_game_ids_by_status()
    for game_id in active_ids:
        async_update_game_data.delay(game_id)


@celery.task(name="async_update_game_data", bind=True, base=BaseTask)
def async_update_game_data(self, game_id, start_time=None, end_time=None):
    start_dag("update_game_dag", game_id=game_id, start_time=start_time, end_time=end_time)

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
