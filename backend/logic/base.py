"""Base business logic that can be shared between multiple modules. This is mainly here to help us avoid circular
as we build out the logic library.
"""
import calendar
import sys
import time
from datetime import datetime as dt, timedelta
from typing import List

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import pytz
import requests
from backend.config import Config
from backend.database.helpers import query_to_dict
from backend.tasks.redis import rds, redis_cache
from database.db import engine
from pandas.tseries.offsets import DateOffset
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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
RESAMPLING_INTERVAL = 5  # resampling interval in minutes when building series of balances and prices
nyse = mcal.get_calendar('NYSE')
pd.options.mode.chained_assignment = None


# ----------------------------------------------------------------------------------------------------------------- $
# Time handlers. Pro tip: This is a _sensitive_ part of the code base in terms of testing. Times need to be mocked, #
# and those mocks need to be redirected if this code goes elsewhere, so move with care and test often               #
# ----------------------------------------------------------------------------------------------------------------- #

@redis_cache.cache()
def get_trading_calendar(start_date: dt, end_date: dt) -> pd.DataFrame:
    return nyse.schedule(start_date, end_date)


def datetime_to_posix(localized_date: dt) -> float:
    return calendar.timegm(localized_date.utctimetuple())


def get_schedule_start_and_end(schedule) -> List[float]:
    return [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]


def posix_to_datetime(ts: float, divide_by: int = 1, timezone=TIMEZONE) -> dt:
    utc_dt = dt.utcfromtimestamp(ts / divide_by).replace(tzinfo=pytz.utc)
    tz = pytz.timezone(timezone)
    return utc_dt.astimezone(tz)


def get_end_of_last_trading_day() -> float:
    """Note, if we're in the middle of a trading day, this will return the end of the current day
    """
    current_day = posix_to_datetime(time.time())
    schedule = get_trading_calendar(current_day, current_day)
    while schedule.empty:
        current_day -= timedelta(days=1)
        schedule = get_trading_calendar(current_day, current_day)
    _, end_day = get_schedule_start_and_end(schedule)
    return end_day


def during_trading_day() -> bool:
    posix_time = time.time()
    nyc_time = posix_to_datetime(posix_time)
    schedule = get_trading_calendar(nyc_time, nyc_time)
    if schedule.empty:
        return False
    start_day, end_day = get_schedule_start_and_end(schedule)
    return start_day <= posix_time < end_day


def get_next_trading_day_schedule(reference_day: dt):
    """For day orders we need to know when the next trading day happens if the order is placed after hours. Note that
    if we are inside of trading hours this will return the schedule for the current day
    """
    schedule = get_trading_calendar(reference_day, reference_day)
    while schedule.empty:
        reference_day += timedelta(days=1)
        schedule = get_trading_calendar(reference_day, reference_day)
    return schedule


def make_date_offset(side_bets_period):
    """date offset calculator for when working with sidebets
    """
    assert side_bets_period in ["weekly", "monthly"]
    offset = DateOffset(days=7)
    if side_bets_period == "monthly":
        offset = DateOffset(months=1)
    return offset


def n_sidebets_in_game(game_start: float, game_end: float, offset: DateOffset) -> int:
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
    info["benchmark_formatted"] = info["benchmark"].upper().replace("_", " ")
    info["game_status"] = get_current_game_status(game_id)
    start_time = get_game_start_time(game_id)
    info["start_time"] = start_time
    info["end_time"] = None
    if start_time:
        info["end_time"] = start_time + info["duration"] * 60 * 60 * 24
    return info


def get_all_game_users_ids(game_id):
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


def pivot_order_details(order_details: pd.DataFrame) -> pd.DataFrame:
    """The vast majority of orders in the order details table are redundant. The timestamp and clear price are not.
    We'll pivot this table to consolidate most of the information in a single row, while adding columns for timestamp,
    status, and clear_price.
    """
    pivot_df = order_details.set_index(
        ["order_id", "symbol", "buy_or_sell", "quantity", "order_type", "time_in_force", "price"])
    pivot_df = pivot_df.pivot(columns="status").reset_index()
    pivot_df.columns = ['_'.join(col).strip("_") for col in pivot_df.columns.values]
    if "clear_price_pending" in pivot_df.columns:
        del pivot_df["clear_price_pending"]
    expanded_columns = ["timestamp_pending", "timestamp_fulfilled", "clear_price_fulfilled"]
    for column in expanded_columns:
        if column not in pivot_df.columns:
            pivot_df[column] = np.nan  # it's OK for there to be no data for these columns, but we do need them present
    return pivot_df


def get_order_details(game_id: int, user_id: int):
    """Retrieves order and fulfillment information for all orders for a game/user that have not been either cancelled
    or expired
    """
    query = """
        SELECT
            o.id as order_id, 
            relevant_orders.status,
            symbol, 
            relevant_orders.timestamp, 
            buy_or_sell, 
            quantity, 
            order_type,
            time_in_force,
            price,
            relevant_orders.clear_price 
        FROM orders o
        INNER JOIN (
          SELECT os_full.timestamp, os_full.order_id, os_full.clear_price, os_full.status
          FROM order_status os_full
          INNER JOIN (
            SELECT os.order_id
            FROM order_status os
              INNER JOIN
                 (SELECT order_id, max(id) as max_id
                  FROM order_status
                  GROUP BY order_id) grouped_os
                 ON
                   os.id = grouped_os.max_id
            WHERE os.status NOT IN ('cancelled', 'expired')
          ) os_relevant
          ON os_relevant.order_id = os_full.order_id
        ) relevant_orders
        ON relevant_orders.order_id = o.id
        WHERE game_id = %s and user_id = %s;
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=[game_id, user_id])
    df = pivot_order_details(df)
    df["status"] = "fulfilled"
    df.loc[df["timestamp_fulfilled"].isna(), "status"] = "pending"
    return df


def get_pending_buy_order_value(user_id, game_id):
    open_value = 0
    df = get_order_details(game_id, user_id)
    df = df[(df["status"] == "pending") & (df["buy_or_sell"] == "buy")]
    tab = df[(df["order_type"].isin(["limit", "stop"]))]
    if not tab.empty:
        tab["value"] = tab["price"] * tab["quantity"]
        open_value += tab["value"].sum()

    tab = df[(df["order_type"] == "market")]
    if not tab.empty:
        for _, row in tab.iterrows():
            price, _ = fetch_price(row["symbol"])
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


def get_price_histories(symbols: List[str], min_time: float, max_time: float):
    sql = f"""
        SELECT timestamp, price, symbol FROM prices
        WHERE 
          symbol IN ({','.join(['%s'] * len(symbols))}) AND 
          timestamp >= %s AND timestamp <= %s;
    """
    params_list = list(symbols) + [min_time, max_time]
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params_list)
    return df.sort_values("timestamp")


def resample_balances(symbol_subset):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({"balance": "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{RESAMPLING_INTERVAL}T").last().ffill()


def append_price_data_to_balance_histories(balances_df: pd.DataFrame) -> pd.DataFrame:
    # Resample balances over the desired time interval within each symbol
    resampled_balances = balances_df.groupby("symbol").apply(resample_balances)
    resampled_balances = resampled_balances.reset_index().rename(columns={"level_1": "timestamp"})
    min_time = datetime_to_posix(resampled_balances["timestamp"].min())
    max_time = datetime_to_posix(resampled_balances["timestamp"].max())
    # Now add price data
    symbols = balances_df["symbol"].unique()
    price_df = get_price_histories(symbols, min_time, max_time)
    price_df["timestamp"] = price_df["timestamp"].apply(lambda x: posix_to_datetime(x))
    price_subsets = []
    for symbol in symbols:
        balance_subset = resampled_balances[resampled_balances["symbol"] == symbol]
        prices_subset = price_df[price_df["symbol"] == symbol]
        if prices_subset.empty and symbol == "Cash":
            # Special handling for cash
            balance_subset.loc[:, "price"] = 1
            price_subsets.append(balance_subset)
            continue
        del prices_subset["symbol"]
        price_subsets.append(pd.merge_asof(balance_subset, prices_subset, on="timestamp", direction="nearest"))
    df = pd.concat(price_subsets, axis=0)
    df["value"] = df["balance"] * df["price"]
    return df


def mask_time_creator(df: pd.DataFrame, start: int, end: int) -> pd.Series:
    mask_up = df['timestamp_epoch'] >= start
    mask_down = df['timestamp_epoch'] <= end
    return mask_up & mask_down


def filter_for_trade_time(df: pd.DataFrame) -> pd.DataFrame:
    """Because we just resampled at a fine-grained interval in append_price_data_to_balance_histories we've introduced a
    lot of non-trading time to the series. We'll clean that out here.
    """
    days = df["timestamp"].dt.normalize().unique()
    schedule_df = get_trading_calendar(min(days), max(days))
    schedule_df['start'] = schedule_df['market_open'].apply(datetime_to_posix)
    schedule_df['end'] = schedule_df['market_close'].apply(datetime_to_posix)
    df['timestamp_utc'] = df['timestamp'].dt.tz_convert("UTC")
    df['timestamp_epoch'] = df['timestamp_utc'].astype('int64') // 1e9
    df["mask"] = False
    for start, end in zip(schedule_df['start'], schedule_df['end']):
        df["mask"] = df["mask"] | mask_time_creator(df, start, end)
    return df[df["mask"]]


def make_bookend_time():
    close_of_last_trade_day = get_end_of_last_trading_day()
    max_time_val = time.time()
    if max_time_val > close_of_last_trade_day:
        max_time_val = close_of_last_trade_day
    return max_time_val


def add_bookends(balances: pd.DataFrame, group_var: str = "symbol", condition_var: str = "balance",
                 time_var: str = "timestamp") -> pd.DataFrame:
    """If the final balance entry that we have for a position is not 0, then we'll extend that position out
    until the current date.

    :param balances: a pandas dataframe with a valid group_var, condition_var, and time_var
    :param group_var: what is the grouping unit that the bookend time is being added to?
    :param condition_var: We only add bookends when there is still a non-zero quantity for the final observation. Which
      column defines that rule?
    :param time_var: the posix time column that contains time information
    """
    bookend_time = make_bookend_time()
    last_entry_df = balances.groupby("symbol", as_index=False).last()
    to_append = last_entry_df[(last_entry_df[condition_var] > 0) & (last_entry_df[time_var] < bookend_time)]
    to_append[time_var] = bookend_time
    return pd.concat([balances, to_append]).reset_index(drop=True)


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
    return add_bookends(balances)


def make_historical_balances_and_prices_table(game_id: int, user_id: int) -> pd.DataFrame:
    """This is a very important function that aggregates user balance and price information and is used both for
    plotting and calculating winners. It's the reason the 7 functions above exist
    """
    balance_history = get_user_balance_history(game_id, user_id)
    # if the user has never bought anything then her cash balance has never changed, simplifying the problem a bit...
    if set(balance_history["symbol"].unique()) == {'Cash'}:
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


def fetch_price_iex(symbol):
    secret = Config.IEX_API_SECRET_SANDBOX if not Config.IEX_API_PRODUCTION else Config.IEX_API_SECRET_PROD
    base_url = IEX_BASE_SANBOX_URL if not Config.IEX_API_PRODUCTION else IEX_BASE_PROD_URL
    res = requests.get(f"{base_url}/stable/stock/{symbol}/quote?token={secret}")
    if res.status_code == 200:
        quote = res.json()
        timestamp = quote["latestUpdate"] / 1000
        if Config.IEX_API_PRODUCTION is False:
            timestamp = time.time()
        price = quote["latestPrice"]
        return price, timestamp


def fetch_price(symbol, provider="iex"):
    if provider == "iex":
        return fetch_price_iex(symbol)


def get_cache_price(symbol):
    data = rds.get(symbol)
    if data is None:
        return None, None
    return [float(x) for x in data.split("_")]


def set_cache_price(symbol, price, timestamp):
    rds.set(symbol, f"{price}_{timestamp}")


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


def get_active_balances(game_id: int, user_id: int):
    """It gets a bit messy, but this query also tacks on the price that the last order for a stock cleared at.
    """
    sql = """
        SELECT symbol, balance, os.timestamp, clear_price
        FROM order_status os
        INNER JOIN
        (
          SELECT gb.symbol, gb.balance, gb.balance_type, gb.timestamp, gb.order_status_id
          FROM game_balances gb
          INNER JOIN
          (SELECT symbol, user_id, game_id, balance_type, max(id) as max_id
            FROM game_balances
            WHERE
              game_id = %s AND
              user_id = %s AND
              balance_type = 'virtual_stock'
            GROUP BY symbol, game_id, balance_type, user_id) grouped_gb
          ON
            gb.id = grouped_gb.max_id
          WHERE balance > 0
        ) balances
        WHERE balances.order_status_id = os.id;
    """
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=[game_id, user_id])


def get_payouts_meta_data(game_id: int):
    game_info = get_game_info(game_id)
    player_ids = get_all_game_users_ids(game_id)
    n_players = len(player_ids)
    pot_size = n_players * game_info["buy_in"]
    side_bets_perc = game_info.get("side_bets_perc")
    start_time = posix_to_datetime(game_info["start_time"])
    end_time = posix_to_datetime(game_info["end_time"])
    side_bets_period = game_info.get("side_bets_period")
    if side_bets_perc is None:
        side_bets_perc = 0
    offset = make_date_offset(side_bets_period)
    return pot_size, start_time, end_time, offset, side_bets_perc, game_info["benchmark"]
