import base64
from contextlib import contextmanager
import json
import pickle as pkl
import uuid

from backend.config import Config
from redis import StrictRedis
from redis_cache import RedisCache
from redlock import Redlock

rds = StrictRedis(Config.REDIS_HOST, decode_responses=True, charset="utf-8")
rds_cache = StrictRedis(Config.REDIS_HOST, decode_responses=False, charset="utf-8")
redis_cache = RedisCache(redis_client=rds_cache, prefix="rc", serializer=pkl.dumps, deserializer=pkl.loads)
dlm = Redlock([{"host": Config.REDIS_HOST}])

TASK_LOCK_MSG = "Task execution skipped -- another task already has the lock"
DEFAULT_ASSET_EXPIRATION = 8 * 24 * 60 * 60  # by default keep cached values around for 8 days
DEFAULT_CACHE_EXPIRATION = 1 * 24 * 60 * 60  # we can keep cached values around for a shorter period of time

REMOVE_ONLY_IF_OWNER_SCRIPT = """
if redis.call("get",KEYS[1]) == ARGV[1] then
    return redis.call("del",KEYS[1])
else
    return 0
end
"""


@contextmanager
def redis_lock(lock_name, expires=60):
    # https://breadcrumbscollector.tech/what-is-celery-beat-and-how-to-use-it-part-2-patterns-and-caveats/
    random_value = str(uuid.uuid4())
    lock_acquired = bool(
        rds.set(lock_name, random_value, ex=expires, nx=True)
    )
    print(f'Lock acquired? {lock_name} for {expires} - {lock_acquired}')

    yield lock_acquired

    if lock_acquired:
        # if lock was acquired, then try to release it BUT ONLY if we are the owner
        # (i.e. value inside is identical to what we put there originally)
        rds.eval(REMOVE_ONLY_IF_OWNER_SCRIPT, 1, lock_name, random_value)
        print(f'Lock {lock_name} released!')


def argument_signature(*args, **kwargs):
    arg_list = [str(x) for x in args]
    kwarg_list = [f"{str(k)}:{str(v)}" for k, v in kwargs.items()]
    return base64.b64encode(f"{'_'.join(arg_list)}-{'_'.join(kwarg_list)}".encode()).decode()


def task_lock(func=None, main_key="", timeout=None):
    def _dec(run_func):
        def _caller(*args, **kwargs):
            with redis_lock(f"{main_key}_{argument_signature(*args, **kwargs)}", timeout) as acquired:
                if not acquired:
                    return TASK_LOCK_MSG
                return run_func(*args, **kwargs)
        return _caller
    return _dec(func) if func is not None else _dec


def unpack_redis_json(key: str):
    result = rds.get(key)
    if result is not None:
        return json.loads(result)
