from redis import Redis

from backend.config import Config

r = Redis(Config.REDIS_HOST)
