import json
from redis import Redis

from backend.config import Config

rds = Redis(Config.REDIS_HOST, decode_responses=True, charset="utf-8")


def unpack_redis_json(key: str):
    result = rds.get(key)
    if result is not None:
        return json.loads(result)
