from sqlalchemy import create_engine

from backend.tasks.celery import celery
from backend.tasks.redis import r
from backend.config import Config
from backend.logic.stock_data import get_symbols_table, fetch_iex_price, during_trading_day


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


@celery.task(name="tasks.async_cache_price")
def cache_price(symbol: str, price: float, last_updated: float):
    """We'll store the last-updated price of each monitored stock in redis. In the short-term this will save us some
    unnecessary data API call.
    """
    r.set(symbol, f"{price}_{last_updated}")


def async_cache_price(symbol: str, price: float, last_updated: float):
    cache_price.delay(symbol, price, last_updated)


@celery.task(name="tasks.async_suggest_symbol")
def fetch_symbol(text):
    to_match = f"{text.upper()}%"
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    suggest_query = """
        SELECT * FROM symbols
        WHERE symbol LIKE %s OR name LIKE %s LIMIT 20;;
    """

    with engine.connect() as conn:
        symbol_suggestions = conn.execute(suggest_query, (to_match, to_match))

    return [{"symbol": entry[1], "label": f"{entry[1]} ({entry[2]})"} for entry in symbol_suggestions]


def async_fetch_symbol(text):
    return fetch_symbol.delay(text)


if __name__ == '__main__':
    async_update_symbols()
