from __future__ import absolute_import
from celery import Celery

from backend.config import Config

app = Celery('tasks',
             broker=Config.CELERY_BROKER_URL,
             backend='rpc://',
             include=['tasks.definitions'])
