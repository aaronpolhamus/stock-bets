import celery
from celery.schedules import crontab

from backend.database.db import db_session
from backend.logic.stock_data import TIMEZONE
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
    }
}


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the database is closed on task completion. Every
    task that interacts with the DB should use this class as a base"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()
