from sqlalchemy import create_engine

from backend.tasks.celery import celery
from backend.config import Config
from backend.logic.stock_data import get_symbols_table, fetch_iex_price


@celery.task(name="tasks.async_update_symbols", bind=True, default_retry_delay=10)
def update_symbols_table(self):
    try:
        symbols_table = get_symbols_table()
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        print("writing to db...")
        with engine.connect() as conn:
            conn.execute("TRUNCATE TABLE symbols;")
            symbols_table.to_sql("symbols", conn, if_exists="append", index=False)
    except Exception as exc:
        raise self.retry(exc=exc)


def async_update_symbols():
    update_symbols_table.delay()


@celery.task(name="tasks.async_fetch_price")
def fetch_price(symbol):
    """For now this is just a silly wrapping step that allows us to decorate the external function into our celery tasks
    inventory. Lots of room to add future nuance here around different data providers, cache look-ups, etc.
    """
    return fetch_iex_price(symbol)


def async_fetch_price(symbol):
    return fetch_price.delay(symbol)
