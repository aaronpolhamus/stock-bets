from redis import Redis

from backend.config import Config

rds = Redis(Config.REDIS_HOST, decode_responses=True, charset="utf-8")
