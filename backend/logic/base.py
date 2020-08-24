"""Base business logic that can be shared between multiple modules. This is mainly here to help us avoid circular
as we build out the logic library.
"""
import calendar
import json
import sys
import time
from datetime import datetime as dt, timedelta
from re import sub
from typing import List, Union

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import pytz
import requests
from backend.config import Config
from backend.database.db import engine
from backend.database.helpers import (
    query_to_dict,
    add_row,
    read_table_cache,
    write_table_cache
)
from backend.logic.schemas import (
    apply_validation,
    balances_and_prices_table_schema
)
from backend.tasks.redis import (
    rds,
    redis_cache,
    DEFAULT_CACHE_EXPIRATION
)
from pandas.tseries.offsets import DateOffset
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tasks import s3_cache

USD_FORMAT = "${:,.2f}"

# -------- #
# Defaults #
# -------- #

TRACKED_INDEXES = ["^IXIC", "^GSPC", "^DJI"]
DEFAULT_VIRTUAL_CASH = 1_000_000  # USD
IEX_BASE_SANBOX_URL = "https://sandbox.iexapis.com/"
IEX_BASE_PROD_URL = "https://cloud.iexapis.com/"

# --------------------------------- #
# Managing time and trade schedules #
# --------------------------------- #
SECONDS_IN_A_DAY = 60 * 60 * 24
TIMEZONE = 'America/New_York'
RESAMPLING_INTERVAL = 5  # resampling interval in minutes when building series of balances and prices
nyse = mcal.get_calendar('NYSE')
pd.options.mode.chained_assignment = None


def standardize_email(email: str):
    return email.lower().replace(".", "")


def get_user_ids_from_passed_emails(invited_user_emails: List[str]) -> List[int]:
    standardized_emails = [standardize_email(x) for x in invited_user_emails]
    with engine.connect() as conn:
        res = conn.execute(f"""
            SELECT id FROM users WHERE LOWER(REPLACE(email, '.', '')) 
            IN ({','.join(['%s'] * len(standardized_emails))})""", standardized_emails).fetchall()
    if res:
        return [x[0] for x in res]
    return []


# ----------------------------------------------------------------------------------------------------------------- $
# Time handlers. Pro tip: This is a _sensitive_ part of the code base in terms of testing. Times need to be mocked, #
# and those mocks need to be redirected if this code goes elsewhere, so move with care and test often               #
# ----------------------------------------------------------------------------------------------------------------- #


@redis_cache.cache(namespace="get_trading_calendar", ttl=DEFAULT_CACHE_EXPIRATION)
def get_trading_calendar(start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    """In order to speed up functions related to the trading calendar we'll wrap nyse in a redis-cached function.
    Important use note: to get the benefit of caching, don't passed in time/tz information -- convert datetime-like
    arguments with datetime.date()
    """
    return nyse.schedule(start_date, end_date)


def datetime_to_posix(localized_date: dt) -> float:
    return calendar.timegm(localized_date.utctimetuple())


def get_schedule_start_and_end(schedule) -> List[float]:
    return [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]


def posix_to_datetime(ts: float, divide_by: int = 1, timezone=TIMEZONE) -> dt:
    utc_dt = dt.utcfromtimestamp(ts / divide_by).replace(tzinfo=pytz.utc)
    tz = pytz.timezone(timezone)
    return utc_dt.astimezone(tz)


def get_end_of_last_trading_day(ref_time: float = None) -> float:
    """Note, if any trading happens during this day this will return the end of the current day
    """
    if ref_time is None:
        ref_time = time.time()
    ref_date = posix_to_datetime(ref_time).date()
    schedule = get_trading_calendar(ref_date, ref_date)
    while schedule.empty:
        ref_date -= timedelta(days=1)
        schedule = get_trading_calendar(ref_date, ref_date)
    _, end_day = get_schedule_start_and_end(schedule)
    return end_day


def during_trading_day(posix_time: float = None) -> bool:
    if posix_time is None:
        posix_time = time.time()
    ref_date = posix_to_datetime(posix_time).date()
    schedule = get_trading_calendar(ref_date, ref_date)
    if schedule.empty:
        return False
    start_day, end_day = get_schedule_start_and_end(schedule)
    return start_day <= posix_time < end_day


def get_next_trading_day_schedule(reference_day: dt):
    """For day orders we need to know when the next trading day happens if the order is placed after hours. Note that
    if we are inside of trading hours this will return the schedule for the current day
    """
    reference_day = reference_day.date()
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


def get_time_defaults(game_id: int, start_time: float = None, end_time: float = None):
    """There are several places in the code that deal with time where we optionally set a time window as [game_start,
    present_time], depending on whether the user has passed those values in manually. This code wraps that operation.
    """
    if start_time is None:
        start_time, _ = get_game_start_and_end(game_id)

    if end_time is None:
        end_time = time.time()

    return start_time, end_time


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


def get_game_info(game_id: int):
    info = query_to_dict("SELECT * FROM games WHERE id = %s;", game_id)[0]
    creator_id = info["creator_id"]
    info["creator_username"] = get_usernames([creator_id])[0]
    info["creator_profile_pic"] = query_to_dict("SELECT * FROM users WHERE id = %s", creator_id)[0]["profile_pic"]
    info["benchmark_formatted"] = info["benchmark"].upper().replace("_", " ")
    info["stakes_formatted"] = USD_FORMAT.format(info["buy_in"]) if info["stakes"] == 'real' else "Just for fun"
    info["game_status"] = get_current_game_status(game_id)
    info["start_time"] = info["end_time"] = None
    if info["game_status"] in ["active", "finished"]:
        info["start_time"], info["end_time"] = get_game_start_and_end(game_id)
    return info


def get_active_game_user_ids(game_id: int):
    with engine.connect() as conn:
        result = conn.execute("""
            SELECT users FROM game_status 
            WHERE game_id = %s AND status = 'active'
            ORDER BY id DESC LIMIT 0, 1;""", game_id).fetchone()[0]
    return json.loads(result)


def get_current_game_cash_balance(user_id: int, game_id: int):
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
            # it's OK for there to be no data for these columns when there is no fulfilled order data, but we do need
            # them present
            pivot_df[column] = np.nan
    return pivot_df


def get_order_details(game_id: int, user_id: int, start_time: float = None, end_time: float = None):
    """Retrieves order and fulfillment information for all orders for a game/user that have not been either cancelled
    or expired
    """
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
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
        WHERE game_id = %s AND user_id = %s AND relevant_orders.timestamp >= %s AND relevant_orders.timestamp <= %s;
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=[game_id, user_id, start_time, end_time])
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

    # pending market orders are implicitly after-hours transactions
    tab = df[(df["order_type"] == "market")]
    if not tab.empty:
        tab["value"] = tab["price"] * df["quantity"]
        open_value += tab["value"].sum()

    return open_value


def get_game_start_and_end(game_id: int):
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
    return start_time, start_time + duration * 24 * 60 * 60


def get_all_game_usernames(game_id: int):
    user_ids = get_active_game_user_ids(game_id)
    return get_usernames(user_ids)


# --------- #
# User info #
# --------- #


def get_user_information(user_id):
    return query_to_dict("SELECT * FROM users WHERE id = %s", user_id)[0]


def get_user_ids(usernames: List[str]) -> List[int]:
    with engine.connect() as conn:
        res = conn.execute(f"""
            SELECT id FROM users WHERE username in ({",".join(['%s'] * len(usernames))});
        """, usernames).fetchall()
    return [x[0] for x in res]


def get_usernames(user_ids: List[int]) -> Union[str, List[str]]:
    """If a single user_id is passed the function will return a single username. If an array is passed, it will
    return an array of names
    """
    with engine.connect() as conn:
        usernames = conn.execute(f"""
        SELECT username FROM users WHERE id IN ({', '.join(['%s'] * len(user_ids))})
        """, user_ids).fetchall()
    return [x[0] for x in usernames]


# --------------- #
# Data processing #
# --------------- #


def get_price_histories(symbols: List, min_time: float, max_time: float):
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


def resample_values(symbol_subset, value_col="balance"):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({value_col: "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{RESAMPLING_INTERVAL}T").last().ffill()


def append_price_data_to_balance_histories(balances_df: pd.DataFrame) -> pd.DataFrame:
    # Resample balances over the desired time interval within each symbol
    resampled_balances = balances_df.groupby("symbol").apply(resample_values)
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
    # if we only observe cash in the balances, that means the game has only just kicked off or they haven't ordered.
    if set(df["symbol"].unique()) == {'Cash'}:
        min_time = df["timestamp"].min()
        max_time = df["timestamp"].max()
        trade_days_df = get_trading_calendar(min_time, max_time)
        if trade_days_df.empty:
            return df

        # this bit of logic checks whether any trading hours have happened, if if the user hasn't ordered
        trade_days_df = trade_days_df[
            (trade_days_df["market_close"] >= min_time) & (trade_days_df["market_open"] <= max_time)]
        if trade_days_df.empty:
            return df

    days = df["timestamp"].dt.normalize().unique()
    schedule_df = get_trading_calendar(min(days).date(), max(days).date())
    schedule_df['start'] = schedule_df['market_open'].apply(datetime_to_posix)
    schedule_df['end'] = schedule_df['market_close'].apply(datetime_to_posix)
    df['timestamp_utc'] = df['timestamp'].dt.tz_convert("UTC")
    df['timestamp_epoch'] = df['timestamp_utc'].astype('int64') // 1e9
    df["mask"] = False
    for start, end in zip(schedule_df['start'], schedule_df['end']):
        df["mask"] = df["mask"] | mask_time_creator(df, start, end)
    df = df[df["mask"]]
    return df.drop(["timestamp_utc", "timestamp_epoch", "mask"], axis=1)


def make_bookend_time(max_time_val: float = None):
    if max_time_val is None:
        max_time_val = time.time()

    end_of_last_trade_day = get_end_of_last_trading_day(max_time_val)
    if max_time_val > end_of_last_trade_day:
        max_time_val = end_of_last_trade_day
    return max_time_val


def add_bookends(balances: pd.DataFrame, group_var: str = "symbol", condition_var: str = "balance",
                 time_var: str = "timestamp", end_time: float = None) -> pd.DataFrame:
    """If the final balance entry that we have for a position is not 0, then we'll extend that position out
    until the current date.

    :param balances: a pandas dataframe with a valid group_var, condition_var, and time_var
    :param group_var: what is the grouping unit that the bookend time is being added to?
    :param condition_var: We only add bookends when there is still a non-zero quantity for the final observation. Which
      column defines that rule?
    :param time_var: the posix time column that contains time information
    :param end_time: reference time for bookend. defaults to present time if passed in as None
    """
    bookend_time = make_bookend_time(end_time)
    last_entry_df = balances.groupby(group_var, as_index=False).last()
    to_append = last_entry_df[(last_entry_df[condition_var] > 0) & (last_entry_df[time_var] < bookend_time)]
    to_append[time_var] = bookend_time
    return pd.concat([balances, to_append]).reset_index(drop=True)


def get_user_balance_history(game_id: int, user_id: int, start_time: float, end_time: float) -> pd.DataFrame:
    """Extracts a running record of a user's balances through time.
    """
    sql = """
            SELECT timestamp, balance_type, symbol, balance FROM game_balances
            WHERE
              game_id = %s AND
              user_id = %s AND
              timestamp >= %s AND
              timestamp <= %s
            ORDER BY id;            
        """
    with engine.connect() as conn:
        balances = pd.read_sql(sql, conn, params=[game_id, user_id, start_time, end_time])
    balances.loc[balances["balance_type"] == "virtual_cash", "symbol"] = "Cash"
    balances.drop("balance_type", inplace=True, axis=1)
    return balances


def handle_balances_cache(game_id: int, user_id: int, start_time: float = None, end_time: float = None):
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    cached_df = read_table_cache("balances_and_prices_cache", start_time, end_time, game_id=game_id, user_id=user_id)
    cached_df.drop(["game_id", "user_id"], axis=1, inplace=True)
    cache_end = 0
    if not cached_df.empty:
        cache_end = float(cached_df["timestamp"].max())

    balances_df = get_user_balance_history(game_id, user_id, cache_end, end_time)
    if not balances_df.empty:
        balances_df = balances_df[balances_df["timestamp"] > cache_end]
        prepend_df = cached_df.loc[
            cached_df["timestamp"] == cached_df["timestamp"].max(), ["symbol", "timestamp", "balance"]]
        balances_df = pd.concat([prepend_df, balances_df])

    return balances_df, cached_df, cache_end


def make_historical_balances_and_prices_table(game_id: int, user_id: int, start_time: float = None,
                                              end_time: float = None) -> pd.DataFrame:
    """This is a very important function that aggregates user balance and price information and is used both for
    plotting and calculating winners. It's the reason the 7 functions above exist.

    start_time and end_time control the window that the function will construct a merged series of running balances
    and price for. if left as None, respective, they will default to the game start and the current time

    the end_time argument determines the reference date for calculating the "bookends" of the running balances series.
    if this is passed as its default value, None, it will use the present time as the bookend reference. being able to
    control this value explicitly lets us "freeze time" when running DAG tests.

    another quick note about this function -- while you can technical pass in any start_time, the internal logic here
    requires prior knowledge of past balances to run properly, othwerwise you'll likely end up ignoring users' past
    purchases. for the best outcome, generally leave the start_time default behavior alone, unless working in a
    testing env where you need to "freeze" time to the test fixture window.
    """
    balances_df, cached_df, cache_end = handle_balances_cache(game_id, user_id, start_time, end_time)
    if balances_df.empty:  # this means that there's nothing new to add -- no need for the logic below
        balances_df = add_bookends(cached_df, end_time=end_time)
    else:
        balances_df = add_bookends(balances_df, end_time=end_time)
    update_df = append_price_data_to_balance_histories(balances_df)  # price appends + resampling happen here
    update_df = filter_for_trade_time(update_df)
    apply_validation(update_df, balances_and_prices_table_schema, strict=True)
    cached_df["timestamp"] = cached_df["timestamp"].apply(lambda x: posix_to_datetime(x))
    df = pd.concat([cached_df, update_df], axis=0)
    df["timestamp"] = pd.to_datetime(df["timestamp"])  # this ensure datetime dtype for when cached_df is empty
    df = df[~df.duplicated(["symbol", "timestamp"])]
    if not update_df.empty:
        cache_update = df[df["timestamp"] > posix_to_datetime(cache_end)]
        cache_update["timestamp"] = cache_update["timestamp"].apply(lambda x: datetime_to_posix(x))
        write_table_cache("balances_and_prices_cache", cache_update, game_id=game_id, user_id=user_id)
    return df.reset_index(drop=True).sort_values(["timestamp", "symbol"])


# ------------------------------------- #
# Price and stock data harvesting tools #
# ------------------------------------- #


class SeleniumDriverError(Exception):

    def __str__(self):
        return "It looks like the selenium web driver failed to instantiate properly"


def currency_string_to_float(money_string):
    if type(money_string) == str:
        return float(sub(r'[^\d.]', '', money_string))
    return money_string


def get_web_driver():
    print("starting selenium web driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)


def extract_row_data(row):
    list_entry = dict()
    split_entry = row.text.split(" ")
    list_entry["symbol"] = split_entry[0]
    list_entry["name"] = " ".join(split_entry[2:])
    return list_entry


def get_symbols_table(n_rows=None, timeout=20):
    driver = get_web_driver()
    driver.get(Config.SYMBOLS_TABLE_URL)
    table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
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


def get_index_value(symbol, timeout=120):
    quote_url = f"{Config.YAHOO_FINANCE_URL}/quote/{symbol}"
    driver = get_web_driver()
    driver.get(quote_url)
    header = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="quote-header-info"]/div[3]/div/div/span[1]')))
    return currency_string_to_float(header.text)


def update_index_value(symbol):
    value = get_index_value(symbol)
    if during_trading_day():
        add_row("indexes", symbol=symbol, value=value, timestamp=time.time())
        return True

    # a bit of logic to get the close of day price
    with engine.connect() as conn:
        max_time = conn.execute("SELECT MAX(timestamp) FROM indexes WHERE symbol = %s;", symbol).fetchone()[0]
        if max_time is None:
            max_time = 0

    ref_day = time.time()
    eod = get_end_of_last_trading_day(ref_day)
    while eod > ref_day:
        ref_day -= SECONDS_IN_A_DAY
        eod = get_end_of_last_trading_day(ref_day)

    if max_time < eod <= time.time():
        add_row("indexes", symbol=symbol, value=value, timestamp=eod)
        return True

    return False


def get_cache_price(symbol):
    data = s3_cache.get(symbol)
    if data is None:
        return None, None
    return [float(x) for x in data.split("_")]


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


def check_single_player_mode(game_id: int) -> bool:
    with engine.connect() as conn:
        game_mode = conn.execute("SELECT game_mode FROM games WHERE id = %s", game_id).fetchone()
    if not game_mode:
        return False
    return game_mode[0] == "single_player"


# Methods for handling indexes in single-player mode
# --------------------------------------------------


def get_index_reference(game_id: int, symbol: str) -> float:
    ref_time, _ = get_game_start_and_end(game_id)
    with engine.connect() as conn:
        ref_val = conn.execute("""
            SELECT value FROM indexes 
            WHERE symbol = %s AND timestamp <= %s
            ORDER BY id DESC LIMIT 0, 1;""", symbol, ref_time).fetchone()
    if not ref_val:
        return 1
    return ref_val[0]


def make_index_start_time(game_start: float) -> float:
    if during_trading_day(game_start):
        return game_start

    schedule = get_next_trading_day_schedule(posix_to_datetime(game_start))
    trade_start, _ = get_schedule_start_and_end(schedule)
    if game_start > trade_start:
        schedule = get_next_trading_day_schedule(posix_to_datetime(game_start))
        trade_start, _ = get_schedule_start_and_end(schedule)
        return trade_start
    return trade_start


def get_index_portfolio_value_data(game_id: int, symbol: str, start_time: float = None,
                                   end_time: float = None) -> pd.DataFrame:
    """In single-player mode a player competes against the indexes. This function just normalizes a dataframe of index
    values by the starting value for when the game began
    """
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    base_value = get_index_reference(game_id, symbol)

    with engine.connect() as conn:
        df = pd.read_sql("""
            SELECT symbol as username, timestamp, value FROM indexes 
            WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s;""", conn, params=[symbol, start_time, end_time])

    # normalizes index to the same starting scale as the user
    df["value"] = DEFAULT_VIRTUAL_CASH * df["value"] / base_value

    # index data will always lag single-player game starts, esp off-hours. we'll add an initial row here to handle this
    trade_start = make_index_start_time(start_time)
    return pd.concat([pd.DataFrame(dict(username=[symbol], timestamp=[trade_start], value=[DEFAULT_VIRTUAL_CASH])), df])
