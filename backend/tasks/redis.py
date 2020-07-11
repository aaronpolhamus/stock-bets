import json
from redis import Redis
from redlock import Redlock

from backend.config import Config

TASK_LOCK_MSG = "Task execution skipped -- another task already has the lock"

rds = Redis(Config.REDIS_HOST, decode_responses=True, charset="utf-8")
dlm = Redlock([{"host": Config.REDIS_HOST}])


def task_lock(function=None, key="", timeout=None):
    """Enforce only one celery task at a time. timeout is in milliseconds"""
    def _dec(run_func):
        def _caller(*args, **kwargs):
            ret_value = TASK_LOCK_MSG
            lock = dlm.lock(key, timeout)
            if lock:
                ret_value = run_func(*args, **kwargs)
                dlm.unlock(lock)
            return ret_value
        return _caller

    return _dec(function) if function is not None else _dec


def unpack_redis_json(key: str):
    result = rds.get(key)
    if result is not None:
        return json.loads(result)
