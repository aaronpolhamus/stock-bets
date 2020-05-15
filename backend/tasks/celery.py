from celery import Celery

from backend.config import Config

celery = Celery('tasks',
                broker=Config.CELERY_BROKER_URL,
                backend=Config.CELERY_RESULTS_BACKEND)
