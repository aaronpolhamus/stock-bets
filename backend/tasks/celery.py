import celery
from backend.database.db import db_session

from backend.config import Config

celery = celery.Celery('tasks',
                       broker=Config.CELERY_BROKER_URL,
                       backend=Config.CELERY_RESULTS_BACKEND,
                       include=['tasks.definitions'])


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()
