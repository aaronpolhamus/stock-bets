import celery
from celery.schedules import crontab

from backend.database.db import db_session
from backend.logic.stock_data import TIMEZONE, PRICE_CACHING_INTERVAL
from backend.config import Config

celery = celery.Celery('tasks',
                       broker=Config.CELERY_BROKER_URL,
                       backend=Config.CELERY_RESULTS_BACKEND,
                       include=['tasks.definitions'])

# Setup regularly scheduled events
celery.conf.timezone = TIMEZONE
celery.conf.beat_schedule = {
    "update_symbols": {
        "task": "async_update_symbols_table",
        "schedule": crontab(minute=0, hour=8)
    },
    "process_all_open_orders": {
        "task": "async_process_all_open_orders",
        "schedule": crontab(minute=f"*/{Config.OPEN_ORDER_PROCESS_RATE}")
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
        "schedule": crontab(minute=f"*/{Config.GAME_STATUS_UPDATE_RATE}")
    }
}


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the database is closed on task completion. Every
    task that interacts with the DB should use this class as a base"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()


def pause_return_until_subtask_completion(status_list, task_name, iteration_limit=10_000):
    """This function exists to support the case where a task spawns a bunch of subtasks, and we want to wait for the
    ready() command of the parent task to return True until all those subtasks have finished. It's kinda like a DAG.
    If you know of a more elegant way to do this please kill this function immediately ;)
    """
    n = 0
    while not all([x.ready() for x in status_list]):
        n += 1
        if n > iteration_limit:
            raise Exception(f"Not tasks spawned by {task_name} completed. Are celery and the DB in good shape?")
        continue
