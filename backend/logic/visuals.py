"""Logic for rendering visual asset data and returning to frontend
"""
import json
import time
from typing import List

import pandas as pd
from backend.database.db import db_session
from backend.logic.base import (
    get_all_game_users,
    make_historical_balances_and_prices_table,
    get_current_game_cash_balance,
    get_user_information,
    get_game_end_date,
    get_username,
    posix_to_datetime,
    DEFAULT_VIRTUAL_CASH
)
from backend.tasks.redis import rds

# -------------- #
# Chart settings #
# -------------- #
N_PLOT_POINTS = 25
DATE_LABEL_FORMAT = "%b %-d, %-H:%M"

# -------------------------------- #
# Prefixes for redis caching layer #
# -------------------------------- #
CURRENT_BALANCES_PREFIX = "current_balances"
SIDEBAR_STATS_PREFIX = "sidebar_stats"
OPEN_ORDERS_PREFIX = "open_orders"
FIELD_CHART_PREFIX = "field_chart"
BALANCES_CHART_PREFIX = "balances_chart"


# ------------------ #
# Time series charts #
# ------------------ #


def format_posix_times(sr: pd.Series) -> pd.Series:
    sr = sr.apply(lambda x: posix_to_datetime(x))
    return sr.apply(lambda x: x.strftime(DATE_LABEL_FORMAT))


def _interpolate_values(df):
    df["value"] = df["value"].interpolate(method="akima")
    return df.reset_index(drop=True)


def reformat_for_plotting(df: pd.DataFrame) -> pd.DataFrame:
    """Get position values, add a t_index or plotting, and down-sample for easier client-side rendering
    """
    df = df.groupby("symbol", as_index=False).apply(lambda subset: _interpolate_values(subset)).reset_index(drop=True)
    df["t_index"] = pd.cut(df["timestamp"], N_PLOT_POINTS * 4, right=True, labels=False)
    df["t_index"] = df["t_index"].rank(method="dense")
    df = df.groupby(["symbol", "t_index"], as_index=False).aggregate({"value": "last", "timestamp": "last"})
    df["label"] = df["timestamp"].apply(lambda x: x.strftime(DATE_LABEL_FORMAT))
    return df


def make_balances_chart_data(game_id: int, user_id: int) -> pd.DataFrame:
    df = make_historical_balances_and_prices_table(game_id, user_id)
    if df.empty:  # this should only happen when a game is just getting going and a user doesn't have any balances, yet
        return df
    return reformat_for_plotting(df)


def serialize_pandas_rows_to_json(df: pd.DataFrame, **kwargs):
    """The key for each kwarg is the corresponding react chart mapping that we're targeting. The value is the value
    of that data in the dataframe being parsed, e.g. y="value"
    """
    output_array = []
    for _, row in df.iterrows():
        entry = {}
        for k, v, in kwargs.items():
            entry[k] = row[v]
        output_array.append(entry)
    return output_array


def null_chart(null_label: str):
    """Null chart function for when a game has just barely gotten going / has started after hours and there's no data.
    For now this function is a bit unecessary, but the idea here is to be really explicit about what's happening so
    that we can add other attributes later if need be.
    """
    series = [{"x": _, "y": DEFAULT_VIRTUAL_CASH} for _ in range(N_PLOT_POINTS)]
    series[0]["y"] = 0
    return dict(id=null_label, data=series)


def serialize_and_pack_balances_chart(df: pd.DataFrame, game_id: int, user_id: int):
    """Serialize a pandas dataframe to the appropriate json format and then "pack" it to redis. The dataframe is the
    result of calling make_balances_chart_data
    """
    chart_json = null_chart("Cash")
    if not df.empty:
        chart_json = []
        symbols = df["symbol"].unique()
        for symbol in symbols:
            entry = dict(id=symbol)
            subset = df[df["symbol"] == symbol]
            entry["data"] = serialize_pandas_rows_to_json(subset, x="label", y="value")
            chart_json.append(entry)
    rds.set(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}", json.dumps(chart_json))


def serialize_and_pack_portfolio_comps_chart(df: pd.DataFrame, game_id: int):
    user_ids = get_all_game_users(game_id)
    chart_json = []
    for user_id in user_ids:
        username = get_username(user_id)
        if df.empty:
            entry = null_chart(username)
        else:
            entry = dict(id=username)
            subset = df[df["id"] == user_id]
            entry["data"] = serialize_pandas_rows_to_json(subset, x="label", y="value")
        chart_json.append(entry)
    rds.set(f"{FIELD_CHART_PREFIX}_{game_id}", json.dumps(chart_json))


def aggregate_portfolio_value(df: pd.DataFrame):
    """Tally aggregated portfolio value for "the field" chart
    """
    if df.empty:
        return df

    last_entry_df = df.groupby(["symbol", "t_index"], as_index=False)[["timestamp", "value"]].aggregate(
        {"timestamp": "last", "value": "last"})
    return last_entry_df.groupby("t_index", as_index=False)[["timestamp", "value"]].aggregate(
        {"timestamp": "first", "value": "sum"})


def aggregate_all_portfolios(portfolios_dict: dict) -> pd.DataFrame:
    if all([df.empty for k, df in portfolios_dict.items()]):
        return list(portfolios_dict.values())[0]

    ls = []
    for _id, df in portfolios_dict.items():
        df["id"] = _id
        ls.append(df)
    df = pd.concat(ls)
    df["bin"] = pd.cut(df["timestamp"], N_PLOT_POINTS * 4, right=True, labels=False)
    df["bin"] = df["bin"].rank(method="dense")
    labels = df.groupby("bin", as_index=False)["timestamp"].max().rename(columns={"timestamp": "label"})
    labels["label"] = labels["label"].apply(lambda x: x.strftime(DATE_LABEL_FORMAT))
    df = df.merge(labels, how="inner", on="bin")
    return df.groupby(["id", "bin"], as_index=False).aggregate({"label": "last", "value": "last"})


def make_the_field_charts(game_id: int):
    """For each user in a game iterate through and make a chart that breaks out the value of their different positions
    """
    user_ids = get_all_game_users(game_id)
    portfolio_values = {}
    for user_id in user_ids:
        df = make_balances_chart_data(game_id, user_id)
        serialize_and_pack_balances_chart(df, game_id, user_id)
        portfolio_values[user_id] = aggregate_portfolio_value(df)
    aggregated_df = aggregate_all_portfolios(portfolio_values)
    serialize_and_pack_portfolio_comps_chart(aggregated_df, game_id)


# -------------------------- #
# Orders and balances tables #
# -------------------------- #

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
    return pd.read_sql(query, db_session.connection(), params=[game_id, user_id])


def serialize_and_pack_orders_open_orders(game_id: int, user_id: int):
    open_orders = get_open_orders(game_id, user_id)
    open_orders["timestamp"] = format_posix_times(open_orders["timestamp"])
    open_orders["time_in_force"] = open_orders["time_in_force"].apply(
        lambda x: "Day" if x == "day" else "Until cancelled")
    open_orders.loc[open_orders["order_type"] == "market", "price"] = " -- "
    column_mappings = {"symbol": "Symbol", "buy_or_sell": "Buy/Sell", "quantity": "Quantity", "price": "Price",
                       "order_type": "Order type", "time_in_force": "Time in force", "timestamp": "Placed on"}
    open_orders.rename(columns=column_mappings, inplace=True)
    out_dict = dict(data=open_orders.to_dict(orient="records"), headers=list(column_mappings.values()))
    rds.set(f"{OPEN_ORDERS_PREFIX}_{game_id}_{user_id}", json.dumps(out_dict))


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


def get_most_recent_prices(symbols):
    if len(symbols) == 0:
        return None
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


def serialize_and_pack_current_balances(game_id: int, user_id: int):
    column_mappings = {"symbol": "Symbol", "balance": "Balance", "clear_price": "Last order price",
                       "price": "Market price", "timestamp": "Updated at"}
    out_dict = dict(data=[], headers=list(column_mappings.values()))
    balances = get_active_balances(game_id, user_id)
    if not balances.empty:
        symbols = balances["symbol"].unique()
        prices = get_most_recent_prices(symbols)
        df = balances.groupby("symbol", as_index=False).aggregate({"balance": "last", "clear_price": "last"})
        df = df.merge(prices, on="symbol", how="left")
        df["timestamp"] = format_posix_times(df["timestamp"])
        df.rename(columns=column_mappings, inplace=True)
        out_dict["data"] = df.to_dict(orient="records")
    rds.set(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{user_id}", json.dumps(out_dict))


# ----- #
# Lists #
# ----- #
def make_stat_entry(user_id: int, total_return: float = 100, sharpe_ratio: float = 1, stocks_held: List[str] = None,
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


def get_portfolio_value(game_id: int, user_id: int) -> float:
    balances = get_active_balances(game_id, user_id)
    symbols = balances["symbol"].unique()
    prices = get_most_recent_prices(symbols)
    df = balances[["symbol", "balance"]].merge(prices, how="left", on="symbol")
    df["value"] = df["balance"] * df["price"]
    return df["value"].sum()


def compile_and_pack_player_sidebar_stats(game_id: int):
    user_ids = get_all_game_users(game_id)
    records = []
    for user_id in user_ids:
        balances = get_active_balances(game_id, user_id)
        record = make_stat_entry(user_id,
                                 cash_balance=get_current_game_cash_balance(user_id, game_id),
                                 stocks_held=list(balances["symbol"].unique()),
                                 total_return=rds.get(f"total_return_{game_id}_{user_id}"),
                                 sharpe_ratio=rds.get(f"sharpe_ratio_{game_id}_{user_id}"),
                                 portfolio_value=get_portfolio_value(game_id, user_id))
        records.append(record)
    output = make_side_bar_output(game_id, records)
    rds.set(f"{SIDEBAR_STATS_PREFIX}_{game_id}", json.dumps(output))

