"""Logic for rendering visual asset data and returning to frontend
"""
import json
import time
from datetime import datetime as dt
from typing import List

import pandas as pd
import seaborn as sns
from backend.database.db import engine
from backend.logic.base import (
    make_date_offset,
    n_sidebets_in_game,
    get_game_info,
    get_open_orders,
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
    get_all_game_users,
    make_historical_balances_and_prices_table,
    get_current_game_cash_balance,
    get_user_information,
    get_game_end_date,
    get_username,
    posix_to_datetime,
    datetime_to_posix,
    DEFAULT_VIRTUAL_CASH
)
from backend.tasks.redis import rds

# -------------- #
# Chart settings #
# -------------- #

N_PLOT_POINTS = 25
USD_FORMAT = "${:,.2f}"
DATE_LABEL_FORMAT = "%b %-d, %-H:%M"
RETURN_TIME_FORMAT = "%a, %-d %b %Y %H:%M:%S EST"

# ------ #
# Colors #
# ------ #
"""Colors are organized sequentially with three different grouping. We'll assign user colors in order, starting with the
first one, and working our way through the list
"""
HEX_COLOR_PALETTE = [
    "#453B85",  # group 1
    "#FFAF75",
    "#FF4B4B",
    "#287B95",
    "#FF778F",
    "#7F7192",
    "#473232",
    "#8C80A1",  # group 2
    "#FCC698",
    "#FC8A7E",
    "#7BA7AB",
    "#FCA4A7",
    "#AFA1A9",
    "#8D7B6F",
    "#4B495B",  # group 3
    "#AA6E68",
    "#AA324F",
    "#02837B",
    "#A05E7C",
    "#903E88",
    "#3C2340"]

NULL_RGBA = "rgba(0, 0, 0, 0)"  # transparent plot elements


def hex_to_rgb(h):
    h = h.lstrip('#')
    hlen = len(h)
    return tuple(int(h[i:(i + hlen // 3)], 16) for i in range(0, hlen, hlen // 3))


def palette_generator(n):
    """For n distinct series, generate a unique color palette"""
    hex_codes = HEX_COLOR_PALETTE[:n]
    rgb_codes = [hex_to_rgb(x) for x in hex_codes]
    return [f"rgba({r}, {g}, {b}, 1)" for r, g, b in rgb_codes]


# -------------------------------- #
# Prefixes for redis caching layer #
# -------------------------------- #
CURRENT_BALANCES_PREFIX = "current_balances"
SIDEBAR_STATS_PREFIX = "sidebar_stats"
OPEN_ORDERS_PREFIX = "open_orders"
FIELD_CHART_PREFIX = "field_chart"
BALANCES_CHART_PREFIX = "balances_chart"
PAYOUTS_PREFIX = "payouts"

# --------------- #
# Dynamic display #
# --------------- #


def format_time_for_response(timestamp: dt) -> str:
    return_time = posix_to_datetime(timestamp).replace(tzinfo=None)
    return f"{return_time.strftime(format=RETURN_TIME_FORMAT)}"

# ------------------ #
# Time series charts #
# ------------------ #


def format_posix_times(sr: pd.Series) -> pd.Series:
    sr = sr.apply(lambda x: posix_to_datetime(x))
    return sr.apply(lambda x: x.strftime(DATE_LABEL_FORMAT))


def reformat_for_plotting(df: pd.DataFrame) -> pd.DataFrame:
    """Get position values, add a t_index or plotting, and down-sample for easier client-side rendering
    """
    df["t_index"] = pd.cut(df["timestamp"], N_PLOT_POINTS * 4, right=True, labels=False)
    df["t_index"] = df["t_index"].rank(method="dense")
    df = df.groupby(["symbol", "t_index"], as_index=False).aggregate({"value": "last", "timestamp": "last"})
    df["label"] = df["timestamp"].apply(lambda x: x.strftime(DATE_LABEL_FORMAT))
    return df


def make_balances_chart_data(game_id: int, user_id: int) -> pd.DataFrame:
    df = make_historical_balances_and_prices_table(game_id, user_id)
    if df.empty:  # this should only happen outside of trading hours
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


def null_chart_series(null_label: str):
    """Null chart function for when a game has just barely gotten going / has started after hours and there's no data.
    For now this function is a bit unnecessary, but the idea here is to be really explicit about what's happening so
    that we can add other attributes later if need be.
    """
    schedule = get_next_trading_day_schedule(dt.utcnow())
    start, end = [posix_to_datetime(x) for x in get_schedule_start_and_end(schedule)]
    series = [{"x": t.strftime(DATE_LABEL_FORMAT), "y": DEFAULT_VIRTUAL_CASH} for t in
              pd.date_range(start, end, N_PLOT_POINTS)]
    series[0]["y"] = 0
    return dict(id=null_label, data=series)


def serialize_and_pack_balances_chart(df: pd.DataFrame, game_id: int, user_id: int):
    """Serialize a pandas dataframe to the appropriate json format and then "pack" it to redis. The dataframe is the
    result of calling make_balances_chart_data
    """
    chart_json = dict(
        line_data=[null_chart_series("Cash")],
        colors=[NULL_RGBA]
    )
    if not df.empty:
        line_data = []
        symbols = df["symbol"].unique()
        for i, symbol in enumerate(symbols):
            entry = dict(id=symbol)
            subset = df[df["symbol"] == symbol]
            entry["data"] = serialize_pandas_rows_to_json(subset, x="label", y="value")
            line_data.append(entry)
        chart_json = dict(line_data=line_data, colors=palette_generator(len(symbols)))

    rds.set(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}", json.dumps(chart_json))


def serialize_and_pack_portfolio_comps_chart(df: pd.DataFrame, game_id: int):
    user_ids = get_all_game_users(game_id)
    line_data = []
    colors = []
    palette = palette_generator(len(user_ids))
    for i, user_id in enumerate(user_ids):
        username = get_username(user_id)
        if df.empty:
            entry = null_chart_series(username)
            color = NULL_RGBA
        else:
            entry = dict(id=username)
            subset = df[df["id"] == user_id]
            entry["data"] = serialize_pandas_rows_to_json(subset, x="label", y="value")
            color = palette[i]
        line_data.append(entry)
        colors.append(color)

    chart_json = dict(line_data=line_data, colors=colors)
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
    """This function wraps a loop that produces the balances chart for each user and the field chart for the game. This
    will run every time a user places and order, and periodically as prices are collected
    """
    user_ids = get_all_game_users(game_id)
    portfolio_values = {}
    for user_id in user_ids:
        df = make_balances_chart_data(game_id, user_id)
        serialize_and_pack_balances_chart(df, game_id, user_id)
        portfolio_values[user_id] = aggregate_portfolio_value(df)

    # when a game has just started during trading day no one will have placed an order. We'll do one more pass here to
    # see if this is the case, and if it is we'll make null chart assignments so that we can have an empty grid
    # until someone orders
    init_state = all([balances.shape[0] == 1 for _, balances in portfolio_values.items()])
    if init_state:
        blank_df = pd.DataFrame(columns=df.columns)
        for user_id in user_ids:
            serialize_and_pack_balances_chart(blank_df, game_id, user_id)
            portfolio_values[user_id] = aggregate_portfolio_value(blank_df)

    aggregated_df = aggregate_all_portfolios(portfolio_values)
    serialize_and_pack_portfolio_comps_chart(aggregated_df, game_id)

# ------ #
# Tables #
# ------ #


def number_columns_to_currency(df: pd.DataFrame, columns_to_format: List[str]):
    df[columns_to_format] = df[columns_to_format].applymap(lambda x: USD_FORMAT.format(x))
    return df


def serialize_and_pack_orders_open_orders(game_id: int, user_id: int):
    open_orders = get_open_orders(game_id, user_id)
    open_orders["timestamp"] = format_posix_times(open_orders["timestamp"])
    open_orders["time_in_force"] = open_orders["time_in_force"].apply(
        lambda x: "Day" if x == "day" else "Until cancelled")
    open_orders = number_columns_to_currency(open_orders, ["price"])
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
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=[game_id, user_id])


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
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=symbols)


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
        df = number_columns_to_currency(df, ["price", "clear_price"])
        df.rename(columns=column_mappings, inplace=True)
        out_dict["data"] = df.to_dict(orient="records")
    rds.set(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{user_id}", json.dumps(out_dict))


def get_expected_sidebets_payout_dates(start_time: dt, end_time: dt, side_bets_perc: float, offset):
    expected_sidebet_dates = []
    if side_bets_perc:
        payout_time = start_time + offset
        while payout_time <= end_time:
            expected_sidebet_dates.append(payout_time)
            payout_time += offset
    return expected_sidebet_dates


def serialize_and_pack_winners_table(game_id: int):
    # TODO: a lot of this can be consolidated with log_winners.
    game_info = get_game_info(game_id)
    player_ids = get_all_game_users(game_id)
    n_players = len(player_ids)
    pot_size = n_players * game_info["buy_in"]
    side_bets_perc = game_info.get("side_bets_perc")
    start_time = posix_to_datetime(game_info["start_time"])
    end_time = posix_to_datetime(game_info["end_time"])
    side_bets_period = game_info.get("side_bets_period")
    if side_bets_perc is None:
        side_bets_perc = 0

    # pull winners data from DB
    with engine.connect() as conn:
        winners_df = pd.read_sql("SELECT * FROM winners WHERE game_id = %s", conn, params=[game_id])
    game_finished = False
    if winners_df.empty:
        last_observed_win = start_time
    else:
        last_observed_win = posix_to_datetime(winners_df["timestamp"].max())
        if "overall" in winners_df["type"].to_list():
            game_finished = True

    data = []
    if side_bets_perc:
        offset = make_date_offset(side_bets_period)
        n_sidebets = n_sidebets_in_game(datetime_to_posix(start_time), datetime_to_posix(end_time), offset)
        payout = round(pot_size * (side_bets_perc / 100) / n_sidebets, 2)
        expected_sidebet_dates = get_expected_sidebets_payout_dates(start_time, end_time, side_bets_perc, offset)
        for _, row in winners_df.iterrows():
            if row["type"] == "sidebet":
                date = posix_to_datetime(row["timestamp"]).strftime(DATE_LABEL_FORMAT)
                winner = get_username(row["winner_id"])
                data.append({"Date": date, "Winner": winner, "Payout": payout, "Type": "Sidebet"})

        dates_to_fill_in = [x for x in expected_sidebet_dates if x > last_observed_win]
        for payout_date in dates_to_fill_in:
            data.append(
                {"Date": payout_date.strftime(DATE_LABEL_FORMAT), "Winner": "???", "Payout": payout, "Type": "Sidebet"})

    payout = pot_size * (1 - side_bets_perc / 100)
    if not game_finished:
        final_entry = {"Date": end_time.strftime(DATE_LABEL_FORMAT), "Winner": "???", "Payout": payout,
                       "Type": "Overall"}
    else:
        date = posix_to_datetime(winners_df["timestamp"].max()).strftime(DATE_LABEL_FORMAT)
        winner_id = winners_df.loc[winners_df["type"] == "overall", "winner_id"].iloc[0]
        winner = get_username(winner_id)
        final_entry = {"Date": date, "Winner": winner, "Payout": payout, "Type": "Overall"}

    data.append(final_entry)
    out_dict = dict(data=data, headers=list(data[0].keys()))
    rds.set(f"{PAYOUTS_PREFIX}_{game_id}", json.dumps(out_dict))

# ----- #
# Lists #
# ----- #


def _days_left(game_id: int):
    seconds_left = get_game_end_date(game_id) - time.time()
    return int(seconds_left / (24 * 60 * 60))


def make_side_bar_output(game_id: int, user_stats: list):
    return dict(days_left=_days_left(game_id), records=user_stats)


def get_portfolio_value(game_id: int, user_id: int) -> float:
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    balances = get_active_balances(game_id, user_id)
    symbols = balances["symbol"].unique()
    if len(symbols) == 0:
        return cash_balance
    prices = get_most_recent_prices(symbols)
    df = balances[["symbol", "balance"]].merge(prices, how="left", on="symbol")
    df["value"] = df["balance"] * df["price"]
    return df["value"].sum() + cash_balance


def make_stat_entry(user_id: int, cash_balance: float, portfolio_value: float, stocks_held: List[str],
                    total_return: float = None, sharpe_ratio: float = None):
    if total_return is None:
        total_return = 100

    if sharpe_ratio is None:
        sharpe_ratio = 1

    entry = get_user_information(user_id)
    entry["total_return"] = total_return
    entry["sharpe_ratio"] = sharpe_ratio
    entry["stocks_held"] = stocks_held
    entry["cash_balance"] = cash_balance
    entry["portfolio_value"] = portfolio_value
    return entry


def compile_and_pack_player_sidebar_stats(game_id: int):
    user_ids = get_all_game_users(game_id)
    records = []
    for user_id in user_ids:
        cash_balance = get_current_game_cash_balance(user_id, game_id)
        balances = get_active_balances(game_id, user_id)
        stocks_held = list(balances["symbol"].unique())
        record = make_stat_entry(user_id=user_id,
                                 cash_balance=cash_balance,
                                 portfolio_value=get_portfolio_value(game_id, user_id),
                                 stocks_held=stocks_held,
                                 total_return=rds.get(f"total_return_{game_id}_{user_id}"),
                                 sharpe_ratio=rds.get(f"sharpe_ratio_{game_id}_{user_id}"))
        records.append(record)
    output = make_side_bar_output(game_id, records)
    rds.set(f"{SIDEBAR_STATS_PREFIX}_{game_id}", json.dumps(output))
