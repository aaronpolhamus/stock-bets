"""Base business logic that can be shared between multiple modules. This is mainly here to help us avoid circular
as we build out the logic library.
"""
import calendar
import sys
import time
from datetime import datetime as dt, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import pandas as pd
from pandas.tseries.offsets import DateOffset
import pandas_market_calendars as mcal
import pytz
import requests
from backend.config import Config
from backend.tasks.redis import rds
from backend.database.db import engine
from backend.database.helpers import query_to_dict


# -------- #
# Defaults #
# -------- #


DEFAULT_VIRTUAL_CASH = 1_000_000  # USD
IEX_BASE_SANBOX_URL = "https://sandbox.iexapis.com/"
IEX_BASE_PROD_URL = "https://cloud.iexapis.com/"

# -------------------------------- #
# Managing time and trad schedules #
# -------------------------------- #
TIMEZONE = 'America/New_York'
PRICE_CACHING_INTERVAL = 60  # The n-second interval for writing updated price values to the DB
nyse = mcal.get_calendar('NYSE')

# ----------------------------------------------------------------------------------------------------------------- $
# Time handlers. Pro tip: This is a _sensitive_ part of the code base in terms of testing. Times need to be mocked, #
# and those mocks need to be redirected if this code goes elsewhere, so move with care and test often               #
# ----------------------------------------------------------------------------------------------------------------- #


def datetime_to_posix(localized_date):
    return calendar.timegm(localized_date.utctimetuple())


def get_schedule_start_and_end(schedule):
    return [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]


def posix_to_datetime(ts, divide_by=1, timezone=TIMEZONE):
    utc_dt = dt.utcfromtimestamp(ts / divide_by).replace(tzinfo=pytz.utc)
    tz = pytz.timezone(timezone)
    return utc_dt.astimezone(tz)


def get_end_of_last_trading_day():
    current_day = posix_to_datetime(time.time())
    schedule = nyse.schedule(current_day, current_day)
    while schedule.empty:
        current_day -= timedelta(days=1)
        schedule = nyse.schedule(current_day, current_day)
    _, end_day = get_schedule_start_and_end(schedule)
    return end_day


def during_trading_day():
    posix_time = time.time()
    nyc_time = posix_to_datetime(posix_time)
    schedule = nyse.schedule(nyc_time, nyc_time)
    if schedule.empty:
        return False
    start_day, end_day = get_schedule_start_and_end(schedule)
    return start_day <= posix_time < end_day


def get_next_trading_day_schedule(current_day: dt):
    """For day orders we need to know when the next trading day happens if the order is placed after hours.
    """
    schedule = nyse.schedule(current_day, current_day)
    while schedule.empty:
        current_day += timedelta(days=1)
        schedule = nyse.schedule(current_day, current_day)
    return schedule


def make_date_offset(side_bets_period):
    """date offset calculator for when working with sidebets
    """
    assert side_bets_period in ["weekly", "monthly"]
    offset = DateOffset(days=7)
    if side_bets_period == "monthly":
        offset = DateOffset(months=1)
    return offset


def n_sidebets_in_game(game_start: float, game_end: float, offset: DateOffset):
    game_start = posix_to_datetime(game_start)
    game_end = posix_to_datetime(game_end)
    count = 0
    t = game_start + offset
    while t <= game_end:
        count += 1
        t += offset
    return count

# ------------ #
# Game-related #
# ------------ #


def get_current_game_status(game_id: int):
    with engine.connect() as conn:
        status = conn.execute("""
            SELECT gs.status
            FROM game_status gs
            INNER JOIN
            (SELECT game_id, max(id) as max_id
              FROM game_status
              GROUP BY game_id) grouped_gs
            ON
              gs.id = grouped_gs.max_id
            WHERE gs.game_id = %s;
        """, game_id).fetchone()[0]
    return status


def get_game_start_time(game_id: int):
    with engine.connect() as conn:
        start = conn.execute("""
            SELECT timestamp FROM game_status
            WHERE game_id = %s AND status = 'active'
        """, game_id).fetchone()
    if start:
        return start[0]
    return None


def get_game_info(game_id: int):
    sql_query = "SELECT * FROM games WHERE id = %s;"
    info = query_to_dict(sql_query, game_id)
    info["creator_username"] = get_username(info["creator_id"])
    info["mode"] = info["mode"].upper().replace("_", " ")
    info["benchmark"] = info["benchmark"].upper().replace("_", " ")
    info["game_status"] = get_current_game_status(game_id)
    start_time = get_game_start_time(game_id)
    info["start_time"] = start_time
    info["end_time"] = None
    if start_time:
        info["end_time"] = start_time + info["duration"] * 60 * 60 * 24
    return info


def get_all_game_users(game_id):
    with engine.connect() as conn:
        result = conn.execute(
            """
            SELECT DISTINCT user_id 
            FROM game_invites WHERE 
                game_id = %s AND
                status = 'joined';""", game_id)
    return [x[0] for x in result]


def get_current_game_cash_balance(user_id, game_id):
    """Get the user's current virtual cash balance for a given game. Expects a valid database connection for query
    execution to be passed in from the outside
    """

    sql_query = """
        SELECT balance
        FROM game_balances gb
        INNER JOIN
        (SELECT user_id, game_id, balance_type, max(id) as max_id
          FROM game_balances
          WHERE
            user_id = %s AND
            game_id = %s AND
            balance_type = 'virtual_cash'
          GROUP BY game_id, balance_type, user_id) grouped_gb
        ON
          gb.id = grouped_gb.max_id;    
    """
    with engine.connect() as conn:
        result = conn.execute(sql_query, (user_id, game_id)).fetchone()[0]
    return result


def get_open_orders(game_id: int, user_id: int):
    # this kinda feels like we'd be better off just handling two pandas tables...
    query = """
        SELECT symbol, buy_or_sell, quantity, price, order_type, time_in_force, open_orders.timestamp
        FROM orders o
        INNER JOIN (
          SELECT os_start.timestamp, os_start.order_id
          FROM order_status os_start
          INNER JOIN (
            SELECT id, os.order_id, os.timestamp
            FROM order_status os
                   INNER JOIN
                 (SELECT order_id, max(id) as max_id
                  FROM order_status
                  GROUP BY order_id) grouped_os
                 ON
                   os.id = grouped_os.max_id
            WHERE os.status = 'pending'
          ) os_pending
          ON os_pending.id = os_start.id
        ) open_orders
        ON open_orders.order_id = o.id
        WHERE game_id = %s and user_id = %s;
    """
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params=[game_id, user_id])


def get_pending_buy_order_value(user_id, game_id):
    open_value = 0
    df = get_open_orders(game_id, user_id)
    tab = df[(df["order_type"].isin(["limit", "stop"])) & (df["buy_or_sell"] == "buy")]
    if not tab.empty:
        tab["value"] = tab["price"] * tab["quantity"]
        open_value += tab["value"].sum()

    tab = df[(df["order_type"] == "market") & (df["buy_or_sell"] == "buy")]
    if not tab.empty:
        for _, row in tab.iterrows():
            price, _ = fetch_iex_price(row["symbol"])
            open_value += price * row["quantity"]

    return open_value


def get_game_end_date(game_id: int):
    with engine.connect() as conn:
        start_time, duration = conn.execute("""
            SELECT timestamp as start_time, duration
            FROM games g
            INNER JOIN (
              SELECT game_id, timestamp
              FROM game_status
              WHERE status = 'active'
            ) gs
            ON gs.game_id = g.id
            WHERE gs.game_id = %s;
        """, game_id).fetchone()
    return start_time + duration * 24 * 60 * 60

# --------- #
# User info #
# --------- #


def get_user_information(user_id):
    return query_to_dict("SELECT * FROM users WHERE id = %s", user_id)


def get_user_id(username: str):
    with engine.connect() as conn:
        user_id = conn.execute("""
        SELECT id FROM users WHERE username = %s
        """, username).fetchone()[0]
    return user_id


def get_username(user_id: int):
    with engine.connect() as conn:
        username = conn.execute("""
        SELECT username FROM users WHERE id = %s
        """, int(user_id)).fetchone()[0]
    return username

# --------------- #
# Data processing #
# --------------- #


def get_price_histories(symbols):
    sql = f"""
        SELECT timestamp, price, symbol FROM prices
        WHERE symbol IN ({','.join(['%s'] * len(symbols))})
    """
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=symbols)


def resample_balances(symbol_subset):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({"balance": "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{PRICE_CACHING_INTERVAL}S").last().ffill()


def append_price_data_to_balance_histories(balances_df: pd.DataFrame) -> pd.DataFrame:
    # Resample balances over the desired time interval within each symbol
    resampled_balances = balances_df.groupby("symbol").apply(resample_balances)
    resampled_balances = resampled_balances.reset_index().rename(columns={"level_1": "timestamp"})

    # Now add price data
    symbols = balances_df["symbol"].unique()
    price_df = get_price_histories(symbols)
    price_df["timestamp"] = price_df["timestamp"].apply(lambda x: posix_to_datetime(x))
    price_subsets = []
    for symbol in symbols:
        balance_subset = resampled_balances[resampled_balances["symbol"] == symbol]
        prices_subset = price_df[price_df["symbol"] == symbol]
        del prices_subset["symbol"]
        price_subsets.append(pd.merge_asof(balance_subset, prices_subset, on="timestamp", direction="nearest"))
    df = pd.concat(price_subsets, axis=0)

    # handle Cash and create a column for the value of each position in time
    df.loc[df["symbol"] == "Cash", "price"] = 1
    df["value"] = df["balance"] * df["price"]
    return df


def filter_for_trade_time(df: pd.DataFrame) -> pd.DataFrame:
    """Because we just resampled at a fine-grained interval in append_price_data_to_balance_histories we've introduced a
    lot of non-trading time to the series. We'll clean that out here.
    """
    days = df["timestamp"].apply(lambda x: x.replace(hour=12, minute=0)).unique()
    df["mask"] = False
    for day in days:
        schedule = nyse.schedule(day, day)
        if schedule.empty:
            continue
        posix_times = get_schedule_start_and_end(schedule)
        start, end = [posix_to_datetime(x) for x in posix_times]
        df["mask"] = df["mask"] | (df["timestamp"] >= start) & (df["timestamp"] <= end)
    return df[df["mask"]]


def make_bookend_time():
    close_of_last_trade_day = get_end_of_last_trading_day()
    max_time_val = time.time()
    if max_time_val > close_of_last_trade_day:
        max_time_val = close_of_last_trade_day
    return max_time_val


def add_bookends(balances: pd.DataFrame) -> pd.DataFrame:
    """If the final balance entry that we have for a position is not 0, then we'll extend that position out
    until the current date.
    """
    bookend_time = make_bookend_time()
    symbols = balances["symbol"].unique()
    for symbol in symbols:
        row = balances[balances["symbol"] == symbol].tail(1)
        if row.iloc[0]["balance"] > 0 and row.iloc[0]["timestamp"] < bookend_time:
            row["timestamp"] = bookend_time
            balances = balances.append([row], ignore_index=True)
    return balances


def get_user_balance_history(game_id: int, user_id: int) -> pd.DataFrame:
    """Extracts a running record of a user's balances through time.
    """
    sql = """
            SELECT timestamp, balance_type, symbol, balance FROM game_balances
            WHERE
              game_id = %s AND
              user_id = %s
            ORDER BY id;            
        """
    with engine.connect() as conn:
        balances = pd.read_sql(sql, conn, params=[game_id, user_id])
    balances.loc[balances["balance_type"] == "virtual_cash", "symbol"] = "Cash"
    balances = add_bookends(balances)
    return balances


def make_historical_balances_and_prices_table(game_id: int, user_id: int) -> pd.DataFrame:
    """This is a very important function that aggregates user balance and price information and is used both for
    plotting and calculating winners. It's the reason the 7 functions above exis
    """
    balance_history = get_user_balance_history(game_id, user_id)
    # if the user has never bought anything then her cash balance has never changed, simplifying the problem a bit...
    if (balance_history["symbol"].nunique() == 1) and (balance_history["symbol"].unique() == ["Cash"]):
        row = balance_history.iloc[0]
        row["timestamp"] = time.time()
        balance_history = balance_history.append([row], ignore_index=True)
        df = resample_balances(balance_history)
        df = df.reset_index().rename(columns={"index": "timestamp"})
        df["price"] = 1
        df["value"] = df["balance"] * df["price"]
        df = filter_for_trade_time(df)
        df["symbol"] = "Cash"
        return df

    # ...otherwise we'll append price data for the more detailed breakout
    df = append_price_data_to_balance_histories(balance_history)
    return filter_for_trade_time(df)


# Price and stock data harvesting tools
# -------------------------------------

class SeleniumDriverError(Exception):

    def __str__(self):
        return "It looks like the selenium web driver failed to instantiate properly"


def get_web_table_object(timeout=20):
    print("starting selenium web driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(Config.SYMBOLS_TABLE_URL)
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))


def extract_row_data(row):
    list_entry = dict()
    split_entry = row.text.split(" ")
    list_entry["symbol"] = split_entry[0]
    list_entry["name"] = " ".join(split_entry[2:])
    return list_entry


def get_symbols_table(n_rows=None):
    table = get_web_table_object()
    rows = table.find_elements_by_tag_name("tr")
    row_list = list()
    n = len(rows)
    print(f"extracting available {n} rows of symbols data...")
    for i, row in enumerate(rows):
        list_entry = extract_row_data(row)
        if list_entry["symbol"] == "Symbol":
            continue
        row_list.append(list_entry)
        sys.stdout.write(f"\r{i} / {n} rows")
        sys.stdout.flush()
        if n_rows and len(row_list) == n_rows:
            # just here for low-cost testing
            break

    return pd.DataFrame(row_list)


def fetch_iex_price(symbol):
    secret = Config.IEX_API_SECRET_SANDBOX if not Config.IEX_API_PRODUCTION else Config.IEX_API_SECRET_PROD
    base_url = IEX_BASE_SANBOX_URL if not Config.IEX_API_PRODUCTION else IEX_BASE_PROD_URL
    res = requests.get(f"{base_url}/stable/stock/{symbol}/quote?token={secret}")
    if res.status_code == 200:
        quote = res.json()
        timestamp = quote["latestUpdate"] / 1000
        price = quote["latestPrice"]
        if not Config.IEX_API_PRODUCTION:
            timestamp = time.time()
        return price, timestamp


def get_all_active_symbols():
    with engine.connect() as conn:
        result = conn.execute("""
        SELECT DISTINCT gb.symbol FROM
        game_balances gb
        INNER JOIN
          (SELECT DISTINCT game_id
          FROM game_status
          WHERE status = 'active') active_ids
        ON gb.game_id = active_ids.game_id
        WHERE gb.balance_type = 'virtual_stock';
        """)

    return [x[0] for x in result]


def fetch_price_cache(symbol):
    """This function checks whether a symbol has a current end-of-trading day cache. If it does, and a user is on the
    platform during non-trading hours, we can use this updated value. If there isn't a valid cache entry we'll return
    None and use that a trigger to pull data
    """
    posix_time = time.time()
    if not during_trading_day():
        if rds.exists(symbol):
            price, update_time = rds.get(symbol).split("_")
            update_time = float(update_time)
            seconds_delta = posix_time - update_time
            ny_update_time = posix_to_datetime(update_time)
            if seconds_delta < 16.5 * 60 * 60 and ny_update_time.hour == 15 and ny_update_time.minute >= 59:
                return float(price), update_time
    return None, None
