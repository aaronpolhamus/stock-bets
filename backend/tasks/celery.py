import celery
from backend.config import Config
from backend.logic.base import (
    TIMEZONE,
    PRICE_CACHING_INTERVAL
)
from logic.base import SeleniumDriverError
from celery.schedules import crontab
from pymysql.err import OperationalError as PyMySQLOpError
from sqlalchemy.exc import OperationalError as SQLAOpError, InvalidRequestError, ProgrammingError
from sqlalchemy.exc import ResourceClosedError, StatementError

# Sometimes tasks break when they have trouble communicating with an external resource. We'll have those errors and
# retry the tasks
RESULT_EXPIRE_TIME = 60 * 60 * 4  # keep tasks around for four hours
DEFAULT_RETRY_DELAY = 3  # (seconds)
MAX_RETRIES = 10
RETRY_INVENTORY = (
    PyMySQLOpError,
    SQLAOpError,
    ResourceClosedError,
    StatementError,
    InvalidRequestError,
    ProgrammingError,
    SeleniumDriverError)


celery = celery.Celery('tasks',
                       broker=Config.CELERY_BROKER_URL,
                       backend=Config.CELERY_RESULTS_BACKEND,
                       include=['tasks.definitions'],
                       result_expires=RESULT_EXPIRE_TIME)

# Setup regularly scheduled events
celery.conf.timezone = TIMEZONE
celery.conf.beat_schedule = {
    "update_symbols": {
        "task": "async_update_symbols_table",
        "schedule": crontab(minute=0, hour=8)
    },
    "process_all_open_orders": {
        "task": "async_process_all_open_orders",
        "schedule": crontab(minute=f"*/{Config.OPEN_ORDER_PROCESS_RATE}", hour="9-16", day_of_week="1-5")
    },
    "service_open_games": {
        "task": "async_service_open_games",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}")
    },
    "fetch_active_symbol_prices": {
        "task": "async_fetch_active_symbol_prices",
        "schedule": crontab(minute=f"*/{PRICE_CACHING_INTERVAL}", hour="9-16", day_of_week="1-5")
    },
    "update_play_game_visuals": {
        "task": "async_update_play_game_visuals",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}", hour="9-16", day_of_week="1-5")
    },
    "update_player_stats": {
        "task": "async_update_player_stats",
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}", hour="9-16", day_of_week="1-5")
    }
}


class BaseTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the database is closed on task completion. Every
    task that interacts with the DB should use this class as a base"""
    abstract = True
    autoretry_for = RETRY_INVENTORY
    default_retry_delay = DEFAULT_RETRY_DELAY
    max_retries = MAX_RETRIES


def pause_return_until_subtask_completion(status_list, task_name, iteration_limit=10_000):
    # TODO: Migrate this logic to chords: https://docs.celeryproject.org/en/latest/userguide/canvas.html#chords
    """This function exists to support the case where a task spawns a bunch of subtasks, and we want to wait for the
    ready() command of the parent task to return True until all those subtasks have finished. It's kinda like a DAG.
    If you know of a more elegant way to do this please kill this function immediately ;)
    """
    n = 0
    while not all([x.ready() for x in status_list]):
        n += 1
        if n > iteration_limit:
            raise Exception(f"Tasks spawned by {task_name} not completed. Are celery and the DB in good shape?")
        continue
