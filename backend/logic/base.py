"""Base business logic that can be shared between multiple modules. This is mainly here to help us avoid circular
as we build out the logic library.
"""
import calendar
import json
import time
from datetime import datetime as dt, timedelta
from typing import List

import pandas as pd
import pandas_market_calendars as mcal
import pytz
from backend.database.db import db_session, db_metadata
from backend.database.helpers import orm_rows_to_dict
from backend.tasks.redis import rds

# -------------------------------- #
# Managing time and trad schedules #
# -------------------------------- #
TIMEZONE = 'America/New_York'
PRICE_CACHING_INTERVAL = 60  # The n-second interval for writing updated price values to the DB
nyse = mcal.get_calendar('NYSE')


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

# ------------ #
# Game-related #
# ------------ #

DEFAULT_VIRTUAL_CASH = 1_000_000  # USD


def get_all_game_users(game_id):
    with db_session.connection() as conn:
        result = conn.execute(
            """
            SELECT DISTINCT user_id 
            FROM game_invites WHERE 
                game_id = %s AND
                status = 'joined';""", game_id)
        db_session.remove()
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
    with db_session.connection() as conn:
        result = conn.execute(sql_query, (user_id, game_id)).fetchone()[0]
        db_session.remove()
    return result


def get_game_end_date(game_id: int):
    with db_session.connection() as conn:
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
        db_session.remove()
    return start_time + duration * 24 * 60 * 60

# --------- #
# User info #
# --------- #


def get_user_information(user_id):
    users = db_metadata.tables["users"]
    row = db_session.query(users).filter(users.c.id == user_id)
    return orm_rows_to_dict(row)


def get_user_id(username: str):
    with db_session.connection() as conn:
        user_id = conn.execute("""
        SELECT id FROM users WHERE username = %s
        """, username).fetchone()[0]
        db_session.remove()
    return user_id


def get_username(user_id: int):
    with db_session.connection() as conn:
        username = conn.execute("""
        SELECT username FROM users WHERE id = %s
        """, int(user_id)).fetchone()[0]
        db_session.remove()
    return username


def get_profile_pic(user_id: int):
    with db_session.connection() as conn:
        username = conn.execute("""
        SELECT profile_pic FROM users WHERE id = %s
        """, int(user_id)).fetchone()[0]
        db_session.remove()
    return username

# --------------- #
# Data processing #
# --------------- #


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
    max_time_val = make_bookend_time()
    symbols = balances["symbol"].unique()
    for symbol in symbols:
        row = balances[balances["symbol"] == symbol].tail(1)
        if row.iloc[0]["balance"] > 0:
            row["timestamp"] = max_time_val
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
    balances = pd.read_sql(sql, db_session.connection(), params=[game_id, user_id])
    balances.loc[balances["balance_type"] == "virtual_cash", "symbol"] = "Cash"
    balances = add_bookends(balances)
    return balances


def make_balances_and_prices_table(game_id: int, user_id: int) -> pd.DataFrame:
    balances = get_user_balance_history(game_id, user_id)
    df = append_price_data_to_balances(balances)
    return filter_for_trade_time(df)


def get_price_histories(symbols):
    sql = f"""
        SELECT timestamp, price, symbol FROM prices
        WHERE symbol IN ({','.join(['%s'] * len(symbols))})
    """
    return pd.read_sql(sql, db_session.connection(), params=symbols)


def get_most_recent_prices(symbols):
    sql = f"""
        SELECT p.symbol, p.price, p.timestamp
        FROM prices p
        INNER JOIN (
        SELECT symbol, max(id) as max_id
          FROM prices
          GROUP BY symbol) max_price
        ON p.id = max_price.max_id
        WHERE p.symbol IN ({','.join(['%s'] * len(symbols))})
    """
    return pd.read_sql(sql, db_session.connection(), params=symbols)


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
    return pd.read_sql(sql, db_session.connection(), params=[game_id, user_id])


def get_portfolio_value(game_id: int, user_id: int) -> float:
    balances = get_active_balances(game_id, user_id)
    symbols = balances["symbol"].unique()
    prices = get_most_recent_prices(symbols)
    df = balances[["symbol", "balance"]].merge(prices, how="left", on="symbol")
    df["value"] = df["balance"] * df["price"]
    return df["value"].sum()


def resample_balances(symbol_subset):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({"balance": "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{PRICE_CACHING_INTERVAL}S").asfreq().ffill()


def append_price_data_to_balances(balances_df: pd.DataFrame) -> pd.DataFrame:
    symbols = balances_df["symbol"].unique()
    price_df = get_price_histories(symbols)
    price_df["timestamp"] = price_df["timestamp"].apply(lambda x: posix_to_datetime(x))

    resampled_balances = balances_df.groupby("symbol").apply(resample_balances)
    resampled_balances = resampled_balances.reset_index().rename(columns={"level_1": "timestamp"})
    price_subsets = []
    for symbol in symbols:
        balance_subset = resampled_balances[resampled_balances["symbol"] == symbol]
        prices_subset = price_df[price_df["symbol"] == symbol]
        del prices_subset["symbol"]
        price_subsets.append(pd.merge_asof(balance_subset, prices_subset, on="timestamp", direction="nearest"))
    df = pd.concat(price_subsets, axis=0)
    df.loc[df["symbol"] == "Cash", "price"] = 1
    df["value"] = df["balance"] * df["price"]
    return df


def filter_for_trade_time(df: pd.DataFrame) -> pd.DataFrame:
    """Because we just resampled at a fine-grained interval in append_price_data_to_balances we've introduced a
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

# ---------- #
# Statistics #
# ---------- #


def make_stat_entry(user_id: int, total_return: float = 1, sharpe_ratio: float = 1, stocks_held: List[str] = None,
                    cash_balance: float = DEFAULT_VIRTUAL_CASH, portfolio_value: float = DEFAULT_VIRTUAL_CASH):
    if stocks_held is None:
        stocks_held = list()

    entry = get_user_information(user_id)
    entry["total_return"] = total_return
    entry["sharpe_ratio"] = sharpe_ratio
    entry["stocks_held"] = stocks_held
    entry["cash_balance"] = cash_balance
    entry["portfolio_value"] = portfolio_value
    return entry


def _days_left(game_id: int):
    seconds_left = get_game_end_date(game_id) - time.time()
    return int(seconds_left / (24 * 60 * 60))


def make_side_bar_output(game_id: int, user_stats: list):
    return dict(days_left=_days_left(game_id), records=user_stats)


def init_sidebar_stats(game_id: int):
    user_ids = get_all_game_users(game_id)
    records = []
    for user_id in user_ids:
        records.append(make_stat_entry(user_id))
    output = make_side_bar_output(game_id, records)
    rds.set(f"sidebar_stats_{game_id}", json.dumps(output))
