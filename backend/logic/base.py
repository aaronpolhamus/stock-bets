"""Base business logic that can be shared between multiple modules. This is mainly here to help us avoid circular
as we build out the logic library.
"""
import calendar
import json
import time
from datetime import datetime as dt, timedelta
from typing import List, Union

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import pytz
from backend.database.db import engine
from backend.database.helpers import query_to_dict
from backend.logic.schemas import (
    apply_validation,
    balances_and_prices_table_schema
)
from backend.tasks.redis import (
    redis_cache,
    DEFAULT_CACHE_EXPIRATION
)
from pandas.tseries.offsets import DateOffset

# -------- #
# Defaults #
# -------- #

STARTING_VIRTUAL_CASH = 1_000_000  # USD
SECONDS_IN_A_DAY = 60 * 60 * 24
TIMEZONE = 'America/New_York'
END_OF_TRADE_HOUR = 16
RESAMPLING_INTERVAL = 5  # resampling interval in minutes when building series of balances and prices

# --------------------------------- #
# Managing time and trade schedules #
# --------------------------------- #

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


def get_end_of_next_trading_day(ref_time: float = None) -> float:
    """Note: if the ref_time is before the end of the current trading day this function will return the end of
    trading hours on that day"""
    if ref_time is None:
        ref_time = time.time()

    ref_datetime = posix_to_datetime(ref_time)
    ref_date = ref_datetime.date()  # a bit redundant, but makes efficient use of cached schedule lookups
    schedule = get_trading_calendar(ref_date, ref_date)
    if not schedule.empty and ref_datetime.hour <= END_OF_TRADE_HOUR:
        _, end_time = get_schedule_start_and_end(schedule)
        return end_time

    ref_date += timedelta(days=1)
    schedule = get_trading_calendar(ref_date, ref_date)
    while schedule.empty:
        ref_date += timedelta(days=1)
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
    """For day orders we need to know when the next trading day happens if the order is placed after hours. Note that if
    off-hours on a trading day, this will return the current trading day schedule anyhow.
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
    game_start, game_end = get_game_start_and_end(game_id)
    if start_time is None:
        start_time = game_start

    if end_time is None:
        current_time = time.time()
        end_time = current_time if current_time < game_end else game_end

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
        ["order_id", "order_status_id", "symbol", "buy_or_sell", "quantity", "order_type", "time_in_force", "price"])
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
            relevant_orders.order_status_id,
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
          SELECT os_full.id,
                 os_full.timestamp,
                 os_full.order_id,
                 os_full.clear_price,
                 os_full.status,
                 os_relevant.order_status_id
          FROM order_status os_full
          INNER JOIN (
            SELECT os.order_id, grouped_os.max_id as order_status_id
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
        WHERE game_id = %s AND user_id = %s AND relevant_orders.timestamp >= %s AND relevant_orders.timestamp <= %s;"""

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


def duration_for_end_of_trade_day(opened_at: float, day_duration: int) -> float:
    naive_end = opened_at + day_duration * SECONDS_IN_A_DAY
    end_of_trade_time = get_end_of_next_trading_day(naive_end)
    return end_of_trade_time - opened_at


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
    return start_time, start_time + duration_for_end_of_trade_day(start_time, duration)


def get_all_game_usernames(game_id: int):
    user_ids = get_active_game_user_ids(game_id)
    return get_usernames(user_ids)


# --------- #
# User info #
# --------- #


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
          timestamp >= %s AND timestamp <= %s ORDER BY symbol, timestamp;"""
    params_list = list(symbols) + [min_time, max_time]
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params_list)
    return df.sort_values("timestamp")


def resample_values(symbol_subset):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({"balance": "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{RESAMPLING_INTERVAL}T").last().ffill()


def append_price_data_to_balance_histories(df: pd.DataFrame) -> pd.DataFrame:
    """the timestamp should be datetime formatted"""
    # Resample balances over the desired time interval within each symbol
    min_time = datetime_to_posix(df["timestamp"].min())
    max_time = datetime_to_posix(df["timestamp"].max())
    # Now add price data
    symbols = df["symbol"].unique()
    price_df = get_price_histories(symbols, min_time, max_time)
    price_df["timestamp"] = price_df["timestamp"].apply(lambda x: posix_to_datetime(x))
    price_subsets = []
    for symbol in symbols:
        balance_subset = df[df["symbol"] == symbol]
        balance_subset.sort_values("timestamp", inplace=True)
        prices_subset = price_df[price_df["symbol"] == symbol]
        if prices_subset.empty and symbol == "Cash":
            # Special handling for cash
            balance_subset.loc[:, "price"] = 1
            price_subsets.append(balance_subset)
            continue
        del prices_subset["symbol"]
        price_subsets.append(pd.merge_asof(balance_subset, prices_subset, on="timestamp", direction="nearest"))
    return pd.concat(price_subsets, axis=0)


def mask_time_creator(df: pd.DataFrame, start: int, end: int) -> pd.Series:
    mask_up = df['timestamp_epoch'] >= start
    mask_down = df['timestamp_epoch'] <= end
    return mask_up & mask_down


def filter_for_trade_time(df: pd.DataFrame, group_var: str = "symbol", time_var: str = "timestamp") -> pd.DataFrame:
    """Because we just resampled at a fine-grained interval in append_price_data_to_balance_histories we've introduced a
    lot of non-trading time to the series. We'll clean that out here.
    """
    # if we only observe cash in the balances, that means the game has only just kicked off or they haven't ordered.
    if set(df[group_var].unique()) == {'Cash'}:
        min_time = df[time_var].min()
        max_time = df[time_var].max()
        trade_days_df = get_trading_calendar(min_time, max_time)
        if trade_days_df.empty:
            return df

        # this bit of logic checks whether any trading hours have happened, if if the user hasn't ordered
        trade_days_df = trade_days_df[
            (trade_days_df["market_close"] >= min_time) & (trade_days_df["market_open"] <= max_time)]
        if trade_days_df.empty:
            return df

    days = df[time_var].dt.normalize().unique()
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


def make_bookend_time(max_time_val: float = None) -> float:
    if max_time_val is None:
        max_time_val = time.time()

    end_of_last_trade_day = get_end_of_last_trading_day(max_time_val)
    if max_time_val > end_of_last_trade_day:
        max_time_val = end_of_last_trade_day
    return max_time_val


def add_bookends(df: pd.DataFrame, group_var: str = "symbol", condition_var: str = "balance",
                 time_var: str = "timestamp", end_time: float = None) -> pd.DataFrame:
    """If the final balance entry that we have for a position is not 0, then we'll extend that position out
    until the current date.

    :param df: a pandas dataframe with a valid group_var, condition_var, and time_var
    :param group_var: what is the grouping unit that the bookend time is being added to?
    :param condition_var: We only add bookends when there is still a non-zero quantity for the final observation. Which
      column defines that rule?
    :param time_var: the posix time column that contains time information
    :param end_time: reference time for bookend. defaults to present time if passed in as None
    """
    bookend_time = make_bookend_time(end_time)
    last_entry_df = df.groupby(group_var, as_index=False).last()
    to_append = last_entry_df[(last_entry_df[condition_var] > 0) & (last_entry_df[time_var] < bookend_time)]
    to_append[time_var] = bookend_time
    return pd.concat([df, to_append]).reset_index(drop=True)


def get_user_balance_history(game_id: int, user_id: int, start_time: float, end_time: float) -> pd.DataFrame:
    """Extracts a running record of a user's balances through time.
    """
    sql = """
            SELECT timestamp, balance_type, symbol, balance
            FROM game_balances
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


def make_historical_balances_and_prices_table(game_id: int, user_id: int, start_time: float = None,
                                              end_time: float = None) -> pd.DataFrame:
    """start_time and end_time control the window that the function will construct a merged series of running balances
    and prices. If left as None they will default to the game start and the current time.

    the end_time argument determines the reference date for calculating the "bookends" of the running balances series.
    if this is passed as its default value, None, it will use the present time as the bookend reference. being able to
    control this value explicitly lets us "freeze time" when running DAG tests.
    """
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    balances_df = get_user_balance_history(game_id, user_id, start_time, end_time)
    df = add_bookends(balances_df, end_time=end_time)
    df = df.groupby("symbol").apply(resample_values)
    df = df.reset_index().rename(columns={"level_1": "timestamp"})
    df = append_price_data_to_balance_histories(df)  # price appends + resampling happen here
    df.sort_values(["symbol", "timestamp"])
    df["value"] = df["balance"] * df["price"]
    df = filter_for_trade_time(df)
    df[["balance", "price", "value"]] = df[["balance", "price", "value"]].astype(float)
    apply_validation(df, balances_and_prices_table_schema, strict=True)
    return df.reset_index(drop=True).sort_values(["timestamp", "symbol"])

# ------------------------------------- #
# Price and stock data harvesting tools #
# ------------------------------------- #


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
        SELECT g.symbol, g.balance, g.timestamp, os.clear_price
        FROM order_status os
        RIGHT JOIN
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
        ) g
        ON g.order_status_id = os.id;"""
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=[game_id, user_id])

# -------------------------------------------------- #
# Methods for handling indexes in single-player mode #
# -------------------------------------------------- #


def get_index_reference(game_id: int, symbol: str) -> float:
    ref_time, _ = get_game_start_and_end(game_id)
    with engine.connect() as conn:
        ref_val = conn.execute("""
            SELECT value FROM indexes 
            WHERE symbol = %s AND timestamp <= %s
            ORDER BY id DESC LIMIT 0, 1;""", symbol, ref_time).fetchone()
    return ref_val[0]


def make_index_start_time(game_start: float) -> float:
    if during_trading_day(game_start):
        return game_start

    game_start_dt = posix_to_datetime(game_start)
    if game_start_dt.hour >= END_OF_TRADE_HOUR:
        game_start_dt += DateOffset(days=1)

    schedule = get_next_trading_day_schedule(game_start_dt)
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
            SELECT imd.username, timestamp, `value` FROM indexes
            INNER JOIN (
              SELECT symbol, `name` AS username FROM index_metadata
            ) imd ON imd.symbol = indexes.symbol
            WHERE indexes.symbol = %s AND timestamp >= %s AND timestamp <= %s;""",
                         conn, params=[symbol, start_time, end_time])

    # normalizes index to the same starting scale as the user
    df["value"] = STARTING_VIRTUAL_CASH * df["value"] / base_value

    # When a game kicks off, it will generally be that case that there won't be an index data point at exactly that
    # time. We solve this here, create a synthetic "anchor" data point that starts at the same time at the game
    trade_start = make_index_start_time(start_time)
    return pd.concat([pd.DataFrame(dict(username=[df.iloc[0]["username"]], timestamp=[trade_start],
                                        value=[STARTING_VIRTUAL_CASH])), df])
