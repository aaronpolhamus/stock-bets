"""Logic for rendering visual asset data and returning to frontend
"""
import json
import time
from datetime import datetime as dt
from typing import List

import numpy as np
import pandas as pd
from backend.database.db import engine
from backend.database.helpers import query_to_dict
from backend.logic.base import (
    add_bookends,
    fetch_price,
    make_date_offset,
    n_sidebets_in_game,
    get_order_details,
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
    DEFAULT_VIRTUAL_CASH,
    RESAMPLING_INTERVAL
)
from backend.tasks.redis import rds, unpack_redis_json
# -------------------------------- #
# Prefixes for redis caching layer #
# -------------------------------- #
from logic.base import get_active_balances, get_payouts_meta_data

CURRENT_BALANCES_PREFIX = "current_balances"
SIDEBAR_STATS_PREFIX = "sidebar_stats"
ORDER_DETAILS_PREFIX = "open_orders"
FIELD_CHART_PREFIX = "field_chart"
BALANCES_CHART_PREFIX = "balances_chart"
ORDER_PERF_CHART_PREFIX = "order_performance_chart"
PAYOUTS_PREFIX = "payouts"

# -------------- #
# Chart settings #
# -------------- #

CHART_INTERPOLATION_SETTING = True  # see https://www.chartjs.org/docs/latest/charts/line.html#cubicinterpolationmode
BORDER_WIDTH_SETTING = 2  # see https://www.chartjs.org/docs/latest/charts/line.html#line-styling
NA_TEXT_SYMBOL = "--"
N_PLOT_POINTS = 30
USD_FORMAT = "${:,.2f}"
PCT_FORMAT = "{0:.2%}"
DATE_LABEL_FORMAT = "%b %-d, %-H:%M"
RETURN_TIME_FORMAT = "%a, %-d %b %Y %H:%M:%S EST"

# -------------- #
# Table settings #
# -------------- #

ORDER_DETAIL_MAPPINGS = {"order_id": "order_id",
                         "symbol": "Symbol",
                         "status": "Status",
                         "timestamp_pending": "Placed on",
                         "timestamp_fulfilled": "Cleared on",
                         "buy_or_sell": "Buy/Sell",
                         "quantity": "Quantity",
                         "order_type": "Order type",
                         "time_in_force": "Time in force",
                         "price": "Order price",
                         "clear_price_fulfilled": "Clear price",
                         "Market price": "Market price",
                         "as of": "as of",
                         "Hypothetical % return": "Hypothetical % return"}

PORTFOLIO_DETAIL_MAPPINGS = {
    "symbol": "Symbol",
    "balance": "Balance",
    "clear_price": "Last order price",
    "price": "Market price",
    "timestamp": "Updated at",
    "Value": "Value",
    "Portfolio %": "Portfolio %"}

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
    hex_codes = []
    i = 0
    # recycle color palette if we've maxed it out -- there's definitely a more compact way to do this
    for _ in range(n):
        hex_codes.append(HEX_COLOR_PALETTE[i])
        i += 1
        if i == len(HEX_COLOR_PALETTE):
            i = 0
    rgb_codes = [hex_to_rgb(x) for x in hex_codes]
    return [f"rgba({r}, {g}, {b}, 1)" for r, g, b in rgb_codes]


# --------------- #
# Dynamic display #
# --------------- #


def format_time_for_response(timestamp: dt) -> str:
    return_time = posix_to_datetime(timestamp).replace(tzinfo=None)
    return f"{return_time.strftime(format=RETURN_TIME_FORMAT)}"


def percent_formatter(val):
    return val if np.isnan(val) else PCT_FORMAT.format(val)


# ------------------ #
# Time series charts #
# ------------------ #


def format_posix_time(ts):
    if np.isnan(ts):
        return ts
    dtime = posix_to_datetime(ts)
    return dtime.strftime(DATE_LABEL_FORMAT)


def trade_time_index(timestamp_sr: pd.Series) -> List:
    """this function solves the problem of how to create a continuous, linear index across a bunch of purchases and
    sales happening at different times across trade days. Simply trying to get the timestamp for a fixed number of bins
    results in the algorithm creating bins for "non-event" times on weekend and between trading hours. This algorithm
    create a "trade time index" that maps scalar time index values dependably to corresponding datetimes.

    Note that the passed-in timestamp series must be sorted, meaning that the dataframe from the outer environment must
    be sorted in orders for this to work.
    """
    ls = timestamp_sr.to_list()
    assert all(ls[i] <= ls[i + 1] for i in range(len(ls) - 1))  # enforces that timestamps are strictly sorted

    anchor_time = last_time = timestamp_sr.min()
    adjustment = 0  # the adjustment differences out the seconds attributable to "no event" space
    trade_time_array = []
    for t in timestamp_sr.to_list():
        # if we crossed a boundary between days, increase the adjustment factor to account for the "no event" space
        if t.day is not last_time.day:
            current_schedule = get_next_trading_day_schedule(t)
            current_start, _ = get_schedule_start_and_end(current_schedule)
            last_schedule = get_next_trading_day_schedule(last_time)
            _, last_end = get_schedule_start_and_end(last_schedule)
            adjustment += current_start - last_end

        trade_seconds = (t - anchor_time).total_seconds() - adjustment
        trade_time_array.append(trade_seconds)
        last_time = t

    return pd.cut(pd.Series(trade_time_array), N_PLOT_POINTS, right=True, labels=False, include_lowest=False).to_list()


def build_labels(df: pd.DataFrame, time_col="timestamp") -> pd.DataFrame:
    df.sort_values(time_col, inplace=True)
    df["t_index"] = trade_time_index(df[time_col])
    labels = df.groupby("t_index", as_index=False)[time_col].max().rename(columns={time_col: "label"})
    labels["label"] = labels["label"].apply(lambda x: x.strftime(DATE_LABEL_FORMAT))
    return df.merge(labels, how="inner", on="t_index")


def make_balances_chart_data(game_id: int, user_id: int) -> pd.DataFrame:
    df = make_historical_balances_and_prices_table(game_id, user_id)
    if df.empty:  # this should only happen outside of trading hours
        return df
    df = build_labels(df)
    return df.groupby(["symbol", "t_index"], as_index=False).aggregate(
        {"label": "last", "value": "last", "timestamp": "last"})


def serialize_pandas_rows_to_dataset(df: pd.DataFrame, dataset_label: str, dataset_color: str, labels: List[str],
                                     data_column: str, label_column: str = "label"):
    """The serializer requires a list of "global" labels that it can use to decide when to make null assignments, along
    with an identification of the column that contains the data mapping. We also pass in a label and color for the
    dataset
    """
    dataset = dict(label=dataset_label, borderColor=dataset_color, backgroundColor=dataset_color, fill=False,
                   cubicInterpolationMode=CHART_INTERPOLATION_SETTING, borderWidth=BORDER_WIDTH_SETTING)
    data = []
    for label in labels:
        row = df[df[label_column] == label]
        assert row.shape[0] <= 1
        if row.empty:
            data.append(None)
            continue
        data.append(row.iloc[0][data_column])
    dataset["data"] = data
    return dataset


def make_null_chart(null_label: str):
    """Null chart function for when a game has just barely gotten going / has started after hours and there's no data.
    For now this function is a bit unnecessary, but the idea here is to be really explicit about what's happening so
    that we can add other attributes later if need be.
    """
    schedule = get_next_trading_day_schedule(dt.utcnow())
    start, end = [posix_to_datetime(x) for x in get_schedule_start_and_end(schedule)]
    labels = [t.strftime(DATE_LABEL_FORMAT) for t in pd.date_range(start, end, N_PLOT_POINTS)]
    data = [DEFAULT_VIRTUAL_CASH for _ in labels]
    return dict(labels=labels,
                datasets=[
                    dict(label=null_label, data=data, borderColor=NULL_RGBA, backgroundColor=NULL_RGBA, fill=False)])


def serialize_and_pack_balances_chart(df: pd.DataFrame, game_id: int, user_id: int):
    """Serialize a pandas dataframe to the appropriate json format and then "pack" it to redis. The dataframe is the
    result of calling make_balances_chart_data. Target schema is:
    data = {
        labels = [ ... ],
        datasets = [
            {
             "label": "<symbol>",
             "data": [x1, x2, ..., xn],
             "borderColor: "rgba(r, g, b, a)"
            },
            ...
        ]
    }

    Labels can have values of None for where we do want to have a tick, but not a label so as to avoid overcrowding.
    Similarly, the data array for each dataset should have None values corresponding to where no data is observed for a
    given label.
    """
    chart_json = make_null_chart("Cash")
    if not df.empty:
        df.sort_values("timestamp", inplace=True)
        labels = df["label"].unique()
        datasets = []
        symbols = df["symbol"].unique()
        colors = palette_generator(len(symbols))
        for symbol, color in zip(symbols, colors):
            subset = df[df["symbol"] == symbol]
            entry = serialize_pandas_rows_to_dataset(subset, symbol, color, labels, "value")
            datasets.append(entry)
        chart_json = dict(labels=list(labels), datasets=datasets)
    rds.set(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}", json.dumps(chart_json))


def serialize_and_pack_portfolio_comps_chart(df: pd.DataFrame, game_id: int):
    """This shares the same schema with the balances chart. See doc string for serialize_and_pack_balances_chart
    """
    user_ids = get_all_game_users(game_id)
    datasets = []
    colors = palette_generator(len(user_ids))
    if df.empty:
        for i, user_id in enumerate(user_ids):
            username = get_username(user_id)
            null_chart = make_null_chart(username)
            datasets.append(null_chart["datasets"][0])
        labels = null_chart["labels"]
    else:
        labels = df["label"].unique()
        for user_id, color in zip(user_ids, colors):
            username = get_username(user_id)
            subset = df[df["id"] == user_id]
            entry = serialize_pandas_rows_to_dataset(subset, username, color, labels, "value")
            datasets.append(entry)

    chart_json = dict(labels=list(labels), datasets=datasets)
    rds.set(f"{FIELD_CHART_PREFIX}_{game_id}", json.dumps(chart_json))


def aggregate_portfolio_value(df: pd.DataFrame):
    """Tally aggregated portfolio value for "the field" chart
    """
    if df.empty:
        return df

    last_entry_df = df.groupby(["symbol", "t_index"], as_index=False)[["label", "value", "timestamp"]].aggregate(
        {"label": "last", "value": "last", "timestamp": "last"})
    return last_entry_df.groupby("t_index", as_index=False)[["label", "value", "timestamp"]].aggregate(
        {"label": "first", "value": "sum", "timestamp": "first"})


def aggregate_all_portfolios(portfolios_dict: dict) -> pd.DataFrame:
    if all([df.empty for k, df in portfolios_dict.items()]):
        return list(portfolios_dict.values())[0]

    ls = []
    for _id, df in portfolios_dict.items():
        df["id"] = _id
        ls.append(df)
    df = pd.concat(ls)
    del df["label"]  # delete the old labels, since we'll be re-assigning them based on the merged data here
    df = build_labels(df)
    df.sort_values("timestamp", inplace=True)
    return df.groupby(["id", "t_index"], as_index=False)[["label", "value"]].agg("last")


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


def make_order_performance_table(game_id: int, user_id: int):
    # get historical order details
    order_df = get_order_details(game_id, user_id)
    order_df = order_df[(order_df["status"] == "fulfilled") & (order_df["buy_or_sell"] == "buy")]
    if order_df.empty:
        return order_df

    # add a label that uniquely identifies a purchase order
    order_df["order_label"] = order_df["symbol"] + order_df["timestamp_fulfilled"].astype(str)
    order_df = order_df[["symbol", "quantity", "clear_price_fulfilled", "timestamp_fulfilled", "order_label"]]
    order_df["order_label"] = order_df["timestamp_fulfilled"].apply(lambda x: format_posix_time(x))
    order_df["order_label"] = order_df["symbol"] + "/" + order_df["quantity"].astype(str) + " @ " + order_df[
        "clear_price_fulfilled"].apply(lambda x: number_to_currency(x)) + "/" + order_df["order_label"]

    # add bookend times and resample
    order_df = add_bookends(order_df, group_var="order_label", condition_var="quantity", time_var="timestamp_fulfilled")
    order_df["timestamp_fulfilled"] = order_df["timestamp_fulfilled"].apply(lambda x: posix_to_datetime(x))
    order_df.set_index("timestamp_fulfilled", inplace=True)
    order_df = order_df.groupby("order_label", as_index=False).resample(f"{RESAMPLING_INTERVAL}T").last().ffill()
    order_df = order_df.reset_index()
    del order_df["level_0"]

    # we'll now ensure that resampled orders are properly sorte and compute cumulative purchases
    order_df.sort_values(["symbol", "timestamp_fulfilled", "order_label"], inplace=True)
    tmp_array = []
    for symbol in order_df["symbol"].unique():
        cum_buys = 0
        symbol_subset = order_df[order_df["symbol"] == symbol]
        for order_label in symbol_subset["order_label"].unique():
            order_subset = symbol_subset[symbol_subset["order_label"] == order_label]
            cum_buys += order_subset.iloc[0]["quantity"]
            order_subset["cum_buys"] = cum_buys
            tmp_array.append(order_subset)
    order_df = pd.concat(tmp_array)

    # get historical balances and prices
    bp_df = make_historical_balances_and_prices_table(game_id, user_id)

    def _make_cumulative_sales(subset):
        sales_diffs = subset["balance"].diff(1).fillna(0)
        sales_diffs[sales_diffs > 0] = 0
        subset["cum_sales"] = sales_diffs.abs().cumsum()
        return subset.reset_index(drop=True)

    bp_df = bp_df.groupby("symbol", as_index=False).apply(_make_cumulative_sales).reset_index(drop=True)

    # merge running balance  information with order history
    slices = []
    for order_label in order_df["order_label"].unique():
        order_subset = order_df[order_df["order_label"] == order_label]
        bp_subset = bp_df[bp_df["symbol"] == order_subset.iloc[0]["symbol"]]
        del bp_subset["symbol"]
        right_cols = ["timestamp", "price", "cum_sales"]
        df_slice = pd.merge_asof(order_subset, bp_subset[right_cols], left_on="timestamp_fulfilled",
                                 right_on="timestamp", direction="nearest")

        # a bit of kludgy logic to make sure that we also get the sale data point included in the return series
        mask = (df_slice["cum_buys"] >= df_slice["cum_sales"]).to_list()
        true_index = list(np.where(mask)[0])
        if true_index[-1] < df_slice.shape[0] - 1:
            true_index.append(true_index[-1] + 1)

        df_slice = df_slice.iloc[true_index]
        slices.append(df_slice)

    df = pd.concat(slices)
    df["return"] = ((df["price"] / df["clear_price_fulfilled"] - 1) * 100).apply(lambda x: round(x, 2))
    return df


def serialize_and_pack_order_performance_chart(game_id: int, user_id: int):
    order_perf = make_order_performance_table(game_id, user_id)
    if order_perf.empty:
        chart_json = make_null_chart("Waiting for orders...")
    else:
        order_perf = build_labels(order_perf)
        order_perf = order_perf.groupby(["order_label", "t_index"], as_index=False)[
            ["label", "return", "timestamp"]].last()
        order_perf.sort_values("t_index", inplace=True)
        chart_labels = list(order_perf["label"].unique())
        order_labels = order_perf["order_label"].unique()
        colors = palette_generator(len(order_labels))
        datasets = []
        for order_label, color in zip(order_labels, colors):
            subset = order_perf[order_perf["order_label"] == order_label]
            datasets.append(serialize_pandas_rows_to_dataset(subset, order_label, color, chart_labels, "return"))
        chart_json = dict(labels=chart_labels, datasets=datasets)
    rds.set(f"{ORDER_PERF_CHART_PREFIX}_{game_id}_{user_id}", json.dumps(chart_json))


# ------ #
# Tables #
# ------ #


def number_to_currency(val):
    if np.isnan(val):
        return val
    return USD_FORMAT.format(val)


def number_columns_to_currency(df: pd.DataFrame, columns_to_format: List[str]):
    df[columns_to_format] = df[columns_to_format].applymap(lambda x: number_to_currency(x))
    return df


def add_market_prices_to_order_details(df):
    df["Market price"] = np.nan
    df["as of"] = np.nan
    for i, row in df.iterrows():
        # for now grab current market price data directly from price fetcher. In the future it will probably make more
        # sense to use a cache
        market_price, timestamp = fetch_price(row["symbol"])
        df.loc[i, "Market price"] = market_price
        df.loc[i, "as of"] = timestamp
    df["as of"] = df["as of"].apply(lambda x: format_posix_time(x))
    df["Hypothetical % return"] = df["Market price"] / df["clear_price_fulfilled"] - 1
    df["Hypothetical % return"] = df["Hypothetical % return"].apply(lambda x: percent_formatter(x))
    return df


def serialize_and_pack_order_details(game_id: int, user_id: int):
    df = get_order_details(game_id, user_id)
    df["timestamp_pending"] = df["timestamp_pending"].apply(lambda x: format_posix_time(x))
    df["timestamp_fulfilled"] = df["timestamp_fulfilled"].apply(lambda x: format_posix_time(x))
    df["time_in_force"] = df["time_in_force"].apply(lambda x: "Day" if x == "day" else "Until cancelled")
    df = add_market_prices_to_order_details(df)
    df.rename(columns=ORDER_DETAIL_MAPPINGS, inplace=True)
    df = number_columns_to_currency(df, ["Order price", "Clear price", "Market price"])
    df.fillna(NA_TEXT_SYMBOL, inplace=True)
    df = df[ORDER_DETAIL_MAPPINGS.values()]
    records = df.to_dict(orient="records")
    orders_json = dict(pending=[x for x in records if x["Status"] == "pending"],
                       fulfilled=[x for x in records if x["Status"] == "fulfilled"])
    out_dict = dict(orders=orders_json, headers=[x for x in list(df.columns) if x != "order_id"])
    rds.set(f"{ORDER_DETAILS_PREFIX}_{game_id}_{user_id}", json.dumps(out_dict))


def init_order_details(game_id: int, user_id: int):
    """Before we have any order information to log, make a blank entry to kick  off a game
    """
    headers = list(ORDER_DETAIL_MAPPINGS.values())
    rds.set(f"{ORDER_DETAILS_PREFIX}_{game_id}_{user_id}",
            json.dumps(dict(orders=dict(pending=[], fulfilled=[]), headers=headers)))


def update_order_details_table(game_id: int, user_id: int, order_id: int, action: str):
    assert action in ["add", "remove"]

    fn = f"{ORDER_DETAILS_PREFIX}_{game_id}_{user_id}"
    order_details = unpack_redis_json(fn)
    if action == "add":
        order_record = query_to_dict("SELECT * FROM orders WHERE id = %s", order_id)
        order_status_latest = query_to_dict(
            "SELECT * FROM order_status WHERE order_id = %s ORDER BY id DESC LIMIT 0, 1", order_id)
        order_status = order_status_latest["status"]
        order_status_placed = query_to_dict("SELECT * FROM order_status WHERE order_id = %s AND status = 'pending'",
                                            order_id)
        market_price, timestamp = fetch_price(order_record["symbol"])
        clear_price = order_status_latest["clear_price"]
        entry = {
            "order_id": order_id,
            "Symbol": order_record["symbol"],
            "Status": order_status,
            "Placed on": format_posix_time(order_status_placed["timestamp"]),
            "Cleared on": format_posix_time(
                order_status_latest["timestamp"]) if order_status == "fulfilled" else NA_TEXT_SYMBOL,
            "Buy/Sell": order_record["buy_or_sell"],
            "Quantity": order_record["quantity"],
            "Order type": order_record["order_type"],
            "Time in force": "Day" if order_record["time_in_force"] == "day" else "Until cancelled",
            "Order price": number_to_currency(order_record["price"]),
            "Clear price": NA_TEXT_SYMBOL if clear_price is None else number_to_currency(clear_price),
            "Market price": number_to_currency(market_price),
            "as of": format_posix_time(timestamp),
            "Hypothetical % return": NA_TEXT_SYMBOL
        }
        if clear_price is not None:
            entry["Hypothetical % return"]: percent_formatter(market_price / clear_price - 1)

        assert entry["Status"] in ["pending", "fulfilled"]
        order_details["orders"][entry["Status"]].append(entry)
        assert set(ORDER_DETAIL_MAPPINGS.values()) == set(entry.keys())

    if action == "remove":
        order_details["orders"]["pending"] = [entry for entry in order_details["orders"]["pending"] if
                                              entry["order_id"] != order_id]

    rds.set(fn, json.dumps(order_details))


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


def serialize_and_pack_portfolio_details(game_id: int, user_id: int):
    out_dict = dict(data=[], headers=list(PORTFOLIO_DETAIL_MAPPINGS.values()))
    balances = get_active_balances(game_id, user_id)
    if not balances.empty:
        cash_balance = get_current_game_cash_balance(user_id, game_id)
        symbols = balances["symbol"].unique()
        prices = get_most_recent_prices(symbols)
        df = balances.groupby("symbol", as_index=False).aggregate({"balance": "last", "clear_price": "last"})
        df = df.merge(prices, on="symbol", how="left")
        df["timestamp"] = df["timestamp"].apply(lambda x: format_posix_time(x))
        df["Value"] = df["balance"] * df["price"]
        total_portfolio_value = df["Value"].sum() + cash_balance
        df["Portfolio %"] = (df["Value"] / total_portfolio_value).apply(lambda x: percent_formatter(x))
        df = number_columns_to_currency(df, ["price", "clear_price", "Value"])
        df.rename(columns=PORTFOLIO_DETAIL_MAPPINGS, inplace=True)
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


def make_payout_table_entry(start_date: dt, end_date: dt, winner: str, payout: float, type: str, benchmark: str = None,
                            score: float = None):
    if score is None:
        formatted_score = " -- "
    else:
        assert benchmark in ["return_ratio", "sharpe_ratio"]
        formatted_score = PCT_FORMAT.format(score / 100)
        if benchmark == "sharpe_ratio":
            formatted_score = round(score, 3)

    return dict(
        Start=start_date.strftime(DATE_LABEL_FORMAT),
        End=end_date.strftime(DATE_LABEL_FORMAT),
        Winner=winner,
        Payout=payout,
        Type=type,
        Score=formatted_score
    )


def serialize_and_pack_winners_table(game_id: int):
    pot_size, start_time, end_time, side_bets_period, side_bets_perc, benchmark = get_payouts_meta_data(game_id)

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
                winner = get_username(row["winner_id"])
                data.append(
                    make_payout_table_entry(posix_to_datetime(row["start_time"]), posix_to_datetime(row["end_time"]),
                                            winner, payout, "Sidebet", benchmark, row["score"]))

        dates_to_fill_in = [x for x in expected_sidebet_dates if x > last_observed_win]
        last_date = last_observed_win
        for payout_date in dates_to_fill_in:
            data.append(make_payout_table_entry(last_date, payout_date, "???", payout, "Sidebet"))
            last_date = payout_date

    payout = pot_size * (1 - side_bets_perc / 100)
    if not game_finished:
        final_entry = make_payout_table_entry(start_time, end_time, "???", payout, "Overall")
    else:
        winner_row = winners_df.loc[winners_df["type"] == "overall"].iloc[0]
        winner = get_username(winner_row["winner_id"])
        final_entry = make_payout_table_entry(start_time, end_time, winner, payout, "Overall", benchmark,
                                              winner_row["score"])

    data.append(final_entry)
    out_dict = dict(data=data, headers=list(data[0].keys()))
    rds.set(f"{PAYOUTS_PREFIX}_{game_id}", json.dumps(out_dict))


# ----- #
# Lists #
# ----- #


def _days_left(game_id: int):
    seconds_left = get_game_end_date(game_id) - time.time()
    return seconds_left // (24 * 60 * 60)


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
