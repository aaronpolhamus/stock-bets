import base64
import json
import pickle as pkl

from backend.config import Config
from redis import Redis
from redis_cache import RedisCache
from redlock import Redlock

TASK_LOCK_MSG = "Task execution skipped -- another task already has the lock"
DEFAULT_ASSET_EXPIRATION = 8 * 24 * 60 * 60  # by default keep cached values around for 8 days
DEFAULT_CACHE_EXPIRATION = 1 * 24 * 60 * 60  # we can keep cached values around for a shorter period of time

rds = Redis(Config.REDIS_HOST, decode_responses=True, charset="utf-8")
rds_cache = Redis(Config.REDIS_HOST, decode_responses=False, charset="utf-8")
redis_cache = RedisCache(redis_client=rds_cache, prefix="rc", serializer=pkl.dumps, deserializer=pkl.loads)
dlm = Redlock([{"host": Config.REDIS_HOST}])


def argument_signature(*args, **kwargs):
    arg_list = [str(x) for x in args]
    kwarg_list = [f"{str(k)}:{str(v)}" for k, v in kwargs.items()]
    return base64.b64encode(f"{'_'.join(arg_list)}-{'_'.join(kwarg_list)}".encode()).decode()


def task_lock(function=None, key="", timeout=None):
    """Enforce only one celery task at a time. timeout is in milliseconds"""

    def _dec(run_func):
        def _caller(*args, **kwargs):
            ret_value = TASK_LOCK_MSG
            signature = argument_signature(*args, **kwargs)
            lock = dlm.lock(signature, timeout)
            print(f"lock: {lock} -- signature: {signature}")
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
