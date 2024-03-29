import celery
from celery.schedules import crontab
from pymysql.err import OperationalError as PyMySQLOpError
from sqlalchemy.exc import (
    OperationalError as SQLAOpError,
    InvalidRequestError,
    ProgrammingError
)
from sqlalchemy.exc import (
    ResourceClosedError,
    StatementError
)
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException
)

from backend.config import Config
from backend.logic.base import TIMEZONE
from backend.logic.stock_data import SeleniumDriverError

# task execution defaults
PRICE_CACHING_INTERVAL = 1  # The n-minute interval for caching prices to DB

# Sometimes tasks break when they have trouble communicating with an external resource. We'll have those errors and
# retry the tasks
RESULT_EXPIRE_TIME = 60 * 60 * 4  # keep tasks around for four hours
DEFAULT_RETRY_DELAY = 3  # (seconds)
MAX_RETRIES = 5
RETRY_INVENTORY = (
    PyMySQLOpError,
    SQLAOpError,
    ResourceClosedError,
    StatementError,
    InvalidRequestError,
    ProgrammingError,
    SeleniumDriverError,
    TimeoutException,
    NoSuchElementException
)


celery = celery.Celery('tasks',
                       broker=Config.CELERY_BROKER_URL,
                       backend=Config.CELERY_RESULTS_BACKEND,
                       include=['tasks.definitions'],
                       result_expires=RESULT_EXPIRE_TIME)


class BaseTask(celery.Task):
    abstract = True
    autoretry_for = RETRY_INVENTORY
    default_retry_delay = DEFAULT_RETRY_DELAY
    max_retries = MAX_RETRIES


# Setup regularly scheduled events
celery.conf.timezone = TIMEZONE
celery.conf.beat_schedule = {
    "scrape_stock_data": {
        "task": "async_scrape_stock_data",
        "schedule": crontab(minute=30, hour=7)
    },
    "process_all_open_orders": {
        "task": "async_process_all_open_orders",
        "schedule": crontab(minute=f"*/{Config.OPEN_ORDER_PROCESS_RATE}", hour="9-16", day_of_week="1-5")
    },
    "service_open_games": {
        "task": "async_service_open_games",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}")
    },
    "fetch_active_symbol_prices_first_30_mins": {
        "task": "async_fetch_active_symbol_prices",
        "schedule": crontab(minute=f"30-59/{Config.GAME_STATUS_UPDATE_RATE}", hour="9", day_of_week="1-5")
    },
    "fetch_active_symbol_prices": {
        "task": "async_fetch_active_symbol_prices",
        "schedule": crontab(minute=f"*/{PRICE_CACHING_INTERVAL}", hour="10-16", day_of_week="1-5")
    },
    # make sure that we have EOD_closing prices for all symbols
    "fetch_active_symbol_prices_eod": {
        "task": "async_fetch_active_symbol_prices",
        "schedule": crontab(minute="5", hour="16", day_of_week="1-5")
    },
    "update_index_values": {
        "task": "async_update_all_index_values",
        "schedule": crontab(minute=f"*/{PRICE_CACHING_INTERVAL}", hour="9-16", day_of_week="1-5")
    },
    "update_index_values_eod": {
        "task": "async_update_all_index_values",
        "schedule": crontab(minute="5", hour="16", day_of_week="1-5")
    },
    "update_all_games": {  # the early start "wakes up" the system, bringing enough workers online to power the app
        "task": "async_update_all_games",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}", hour="9-15", day_of_week="1-5")
    },
    # final EOD check 10 mins after close just to make sure that all statuses are fully updated
    "update_all_games_eod": {
        "task": "async_update_all_games",
        "schedule": crontab(minute="1", hour="16", day_of_week="1-5")
    },
    # we need to keep updating games on the weekend, but only twice a day for now
    "update_all_games_weekend": {
        "task": "async_update_all_games",
        "schedule": crontab(minute="0", hour="*/6", day_of_week="saturday,sunday")
    },
    "update_public_rankings": {
        "task": "async_update_public_rankings",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}", hour="9-16", day_of_week="1-5")
    },
    # we'll also refresh platform KPIs at the end of each day
    "calculate_metrics": {
        "task": "async_calculate_key_metrics",
        "schedule": crontab(minute="59", hour="23")
    },
    # clear the balances and prices cache every day
    "clear_balances_and_prices_cache": {
        "task": "async_clear_balances_and_prices_cache",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}", hour="9-15", day_of_week="1-5")
    }
}
