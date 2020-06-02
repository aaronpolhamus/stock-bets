"""Logic for rendering visual asset data and returning to frontend
"""
import json
import time

import pandas as pd
from backend.database.db import db_session
from backend.logic.games import get_all_game_users
from backend.logic.stock_data import (
    PRICE_CACHING_INTERVAL,
    posix_to_datetime,
    get_end_of_last_trading_day,
    get_schedule_start_and_end,
    nyse
)
from backend.tasks.redis import rds

N_PLOT_POINTS = 100
DATE_LABEL_FORMAT = "%b %-d, %-H:%-M"
N_TIMESTAMP_LABELS = 20  # We control axis formatting backend-side


# ------------------ #
# Time series charts #
# ------------------ #

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


def get_prices(symbols):
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


def resample_balances(symbol_subset):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({"balance": "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{PRICE_CACHING_INTERVAL}S").asfreq().ffill()


def append_price_data_to_balances(balances_df: pd.DataFrame) -> pd.DataFrame:
    symbols = balances_df["symbol"].unique()
    price_df = get_prices(symbols)
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


def _interpolate_values(df):
    df["value"] = df["value"].interpolate(method="akima")
    return df.reset_index(drop=True)


def reformat_for_plotting(df: pd.DataFrame) -> pd.DataFrame:
    """Get position values, add a t_index or plotting, and down-sample for easier client-side rendering
    """
    df["value"] = df["balance"] * df["price"]
    df = df.groupby("symbol", as_index=False).apply(lambda subset: _interpolate_values(subset)).reset_index(drop=True)
    df["t_index"] = pd.cut(df["timestamp"], N_PLOT_POINTS * 4, right=True, labels=False)
    df["t_index"] = df["t_index"].rank(method="dense")
    return df.groupby(["symbol", "t_index"], as_index=False).aggregate({"value": "last", "timestamp": "last"})


def make_balances_chart_data(game_id: int, user_id: int) -> pd.DataFrame:
    balances = get_user_balance_history(game_id, user_id)
    df = append_price_data_to_balances(balances)
    df = filter_for_trade_time(df)
    df = reformat_for_plotting(df)
    return df


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
        with db_session.connection() as conn:
            username = conn.execute("""
            SELECT username FROM users WHERE id = %s
            """, int(user_id)).fetchone()[0]
            db_session.remove()
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
        # Before serializing, but after storing in the portfolio values array, reformat the time data
        df["label"] = df["timestamp"].apply(lambda x: x.strftime(DATE_LABEL_FORMAT))
        serialize_and_pack_balances_chart(df, game_id, user_id)
    aggregated_df = aggregate_all_portfolios(portfolio_values)
    serialize_and_pack_portfolio_comps_chart(aggregated_df, game_id)


# -------------------------- #
# Orders and balances tables #
# -------------------------- #
def format_posix_times(sr: pd.Series) -> pd.Series:
    sr = sr.apply(lambda x: posix_to_datetime(x))
    return sr.apply(lambda x: x.strftime(DATE_LABEL_FORMAT))


def serialize_and_pack_orders_open_orders(game_id: int, user_id: int):
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
    open_orders = pd.read_sql(query, db_session.connection(), params=[game_id, user_id])
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
    sql = """
        SELECT symbol, balance, balance_type, clear_price, timestamp
        FROM game_balances g
        INNER JOIN (
          SELECT id, clear_price
          FROM order_status WHERE
          status = 'fulfilled'
        ) os
        ON g.order_status_id = os.id
        WHERE
          game_id = %s AND
          user_id = %s AND
          symbol IS NOT NULL;
        """
    balances = pd.read_sql(sql, db_session.connection(), params=[game_id, user_id])
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
