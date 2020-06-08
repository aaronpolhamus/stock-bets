"""Logic for rendering visual asset data and returning to frontend
"""
import json
import time

import pandas as pd
from backend.database.db import db_session
from backend.logic.base import (
    make_balances_and_prices_table,
    get_current_game_cash_balance,
    get_most_recent_prices,
    get_active_balances,
    get_username,
    get_profile_pic,
    get_portfolio_value,
    get_game_end_date
)
from backend.logic.games import get_all_game_users
from backend.logic.stock_data import (
    posix_to_datetime
)
from backend.tasks.redis import rds

N_PLOT_POINTS = 25
DATE_LABEL_FORMAT = "%b %-d, %-H:%-M"


# ------------------ #
# Time series charts #
# ------------------ #


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
    df = make_balances_and_prices_table(game_id, user_id)
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


def serialize_and_pack_balances_chart(df: pd.DataFrame, game_id: int, user_id: int):
    """Serialize a pandas dataframe to the appropriate json format and then "pack" it to redis
    """
    chart_json = []
    symbols = df["symbol"].unique()
    for symbol in symbols:
        entry = dict(id=symbol)
        subset = df[df["symbol"] == symbol]
        entry["data"] = serialize_pandas_rows_to_json(subset, x="label", y="value")
        chart_json.append(entry)
    rds.set(f"balances_chart_{game_id}_{user_id}", json.dumps(chart_json))


def serialize_and_pack_portfolio_comps_chart(df: pd.DataFrame, game_id: int):
    chart_json = []
    user_ids = df["id"].unique()
    for user_id in user_ids:
        username = get_username(user_id)
        entry = dict(id=username)
        subset = df[df["id"] == user_id]
        entry["data"] = serialize_pandas_rows_to_json(subset, x="label", y="value")
        chart_json.append(entry)
    rds.set(f"field_chart_{game_id}", json.dumps(chart_json))


def aggregate_portfolio_value(df: pd.DataFrame):
    """Tally aggregated portfolio value for "the field" chart
    """
    last_entry_df = df.groupby(["symbol", "t_index"], as_index=False)[["timestamp", "value"]].aggregate(
        {"timestamp": "last", "value": "last"})
    return last_entry_df.groupby("t_index", as_index=False)[["timestamp", "value"]].aggregate(
        {"timestamp": "first", "value": "sum"})


def aggregate_all_portfolios(portfolios_dict: dict) -> pd.DataFrame:
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
    user_ids = get_all_game_users(db_session, game_id)
    portfolio_values = {}
    for user_id in user_ids:
        df = make_balances_chart_data(game_id, user_id)
        portfolio_values[user_id] = aggregate_portfolio_value(df)
        serialize_and_pack_balances_chart(df, game_id, user_id)
    aggregated_df = aggregate_all_portfolios(portfolio_values)
    serialize_and_pack_portfolio_comps_chart(aggregated_df, game_id)


# -------------------------- #
# Orders and balances tables #
# -------------------------- #
def format_posix_times(sr: pd.Series) -> pd.Series:
    sr = sr.apply(lambda x: posix_to_datetime(x))
    return sr.apply(lambda x: x.strftime(DATE_LABEL_FORMAT))


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
    column_mappings = {"symbol": "Symbol", "buy_or_sell": "Buy/Sell", "quantity": "Quantity", "price": "Price",
                       "order_type": "Order type", "time_in_force": "Time in force", "timestamp": "Placed on"}
    open_orders.rename(columns=column_mappings, inplace=True)
    out_dict = dict(
        data=open_orders.to_dict(orient="records"),
        headers=list(column_mappings.values())
    )
    rds.set(f"open_orders_{game_id}_{user_id}", json.dumps(out_dict))


def serialize_and_pack_current_balances(game_id: int, user_id: int):
    balances = get_active_balances(game_id, user_id)
    symbols = balances["symbol"].unique()
    prices = get_most_recent_prices(symbols)
    df = balances.groupby("symbol", as_index=False).aggregate({"balance": "last", "clear_price": "last"})
    df = df.merge(prices, on="symbol", how="left")
    df["timestamp"] = format_posix_times(df["timestamp"])
    column_mappings = {"symbol": "Symbol", "balance": "Balance", "clear_price": "Last order price", "price": "Last price", "timestamp": "Updated at"}
    df.rename(columns=column_mappings, inplace=True)
    out_dict = dict(
        data=df.to_dict(orient="records"),
        headers=list(column_mappings.values())
    )
    rds.set(f"current_balances_{game_id}_{user_id}", json.dumps(out_dict))


# ----- #
# Lists #
# ----- #

def compile_and_pack_player_sidebar_stats(game_id: int):
    user_ids = get_all_game_users(db_session, game_id)
    records = []
    for user_id in user_ids:
        balances = get_active_balances(game_id, user_id)
        stocks_held = list(balances["symbol"].unique())
        cash_balance = get_current_game_cash_balance(user_id, game_id)
        record = dict(
            user_id=user_id,
            username=get_username(user_id),
            profile_pic=get_profile_pic(user_id),
            total_return=rds.get(f"total_return_{game_id}_{user_id}"),
            sharpe_ratio=rds.get(f"sharpe_ratio_{game_id}_{user_id}"),
            stocks_held=stocks_held,
            cash_balance=cash_balance,
            portfolio_value=get_portfolio_value(game_id, user_id)
        )
        records.append(record)

    seconds_left = get_game_end_date(game_id) - time.time()
    output = dict(
        days_left=int(seconds_left / (24 * 60 * 60)),
        records=records
    )
    rds.set(f"sidebar_stats_{game_id}", json.dumps(output))
