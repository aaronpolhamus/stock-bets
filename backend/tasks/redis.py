import json
from redis import Redis

from backend.config import Config

TASK_LOCK_MSG = "Task execution skipped -- another task already has the lock"

rds = Redis(Config.REDIS_HOST, decode_responses=True, charset="utf-8")


def task_lock(function=None, key="", timeout=None):
    """Enforce only one celery task at a time."""

    def _dec(run_func):

        def _caller(*args, **kwargs):
            ret_value = TASK_LOCK_MSG
            have_lock = False
            lock = rds.lock(key, timeout=timeout)
            try:
                have_lock = lock.acquire(blocking=False)
                if have_lock:
                    ret_value = run_func(*args, **kwargs)
            finally:
                if have_lock:
                    lock.release()

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec


def unpack_redis_json(key: str):
    result = rds.get(key)
    if result is not None:
        return json.loads(result)
