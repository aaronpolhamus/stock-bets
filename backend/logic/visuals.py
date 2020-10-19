"""Logic for rendering visual asset data and returning to frontend
"""
import json
import time
from datetime import datetime as dt
from typing import List, Union

import numpy as np
import pandas as pd
from pandas import DateOffset
from backend.logic.base import (
    get_time_defaults,
    get_active_balances,
    get_trading_calendar,
    get_all_game_usernames,
    get_game_info,
    get_order_details,
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
    make_historical_balances_and_prices_table,
    get_current_game_cash_balance,
    get_game_start_and_end,
    get_usernames,
    posix_to_datetime,
    STARTING_VIRTUAL_CASH,
    get_active_game_user_ids,
    get_index_portfolio_value_data,
    TIMEZONE,
    get_end_of_last_trading_day,
    SECONDS_IN_A_DAY,
    get_price_histories,
    add_bookends,
    RESAMPLING_INTERVAL,
    filter_for_trade_time,
    append_price_data_to_balance_histories,
    datetime_to_posix
)
from backend.logic.metrics import (
    STARTING_RETURN_RATIO,
    STARTING_SHARPE_RATIO,
    calculate_metrics,
    portfolio_return_ratio,
    portfolio_sharpe_ratio,
    RISK_FREE_RATE_DEFAULT,
    log_winners,
    get_overall_payout,
    get_winners_meta_data,
    get_sidebet_payout,
    get_expected_sidebets_payout_dates,
    USD_FORMAT,
    get_user_portfolio_value,
    get_index_portfolio_value
)
from backend.logic.schemas import (
    order_performance_schema,
    balances_chart_schema,
    portfolio_comps_schema,
    order_details_schema,
    apply_validation
)
from backend.logic.stock_data import TRACKED_INDEXES
from backend.logic.stock_data import get_most_recent_prices
from backend.tasks import s3_cache
from backend.tasks.redis import rds
from backend.database.db import engine
from backend.database.helpers import query_to_dict

# Exceptions
# ----------


class BadOrderMerge(Exception):

    def __str__(self):
        return "The merge of balance-prices history on orders failed. Check for either redundant or missing orders"


# -------------------------------- #
# Prefixes for redis caching layer #
# -------------------------------- #

CURRENT_BALANCES_PREFIX = "current_balances"
LEADERBOARD_PREFIX = "leaderboard"
PENDING_ORDERS_PREFIX = "pending_orders"
FULFILLED_ORDER_PREFIX = "fulfilled_orders"
FIELD_CHART_PREFIX = "field_chart"
BALANCES_CHART_PREFIX = "balances_chart"
ORDER_PERF_CHART_PREFIX = "order_performance_chart"
PAYOUTS_PREFIX = "payouts"
RETURN_RATIO_PREFIX = "return_ratio"
SHARPE_RATIO_PREFIX = "sharpe_ratio"
PLAYER_RANK_PREFIX = "player_rank"
THREE_MONTH_RETURN_PREFIX = "three_month_return"
PUBLIC_LEADERBOARD_PREFIX = "public_leaderboard"

# -------------- #
# Chart settings #
# -------------- #

CHART_INTERPOLATION_SETTING = True  # see https://www.chartjs.org/docs/latest/charts/line.html#cubicinterpolationmode
BORDER_WIDTH_SETTING = 2  # see https://www.chartjs.org/docs/latest/charts/line.html#line-styling
NA_TEXT_SYMBOL = "--"
NA_NUMERIC_VAL = -99
N_PLOT_POINTS = 150
DATE_LABEL_FORMAT = "%b %-d, %-H:%M"

# -------------- #
# Table settings #
# -------------- #

FULFILLED_ORDER_MAPPINGS = {
    "symbol": "Symbol",
    "timestamp": "Cleared on",
    "quantity": "Quantity",
    "clear_price": "Clear price",
    "basis": "Basis",
    "fifo_balance": "Balance (FIFO)",
    "realized_pl": "Realized P&L",
    "realized_pl_percent": "Realized P&L (%)",
    "unrealized_pl": "Unrealized P&L",
    "unrealized_pl_percent": "Unrealized P&L (%)",
    "Market price": "Market price",
    "as of": "as of"
}

PENDING_ORDER_MAPPINGS = {
    "symbol": "Symbol",
    "timestamp_pending": "Placed on",
    "buy_or_sell": "Buy/Sell",
    "quantity": "Quantity",
    "order_type": "Order type",
    "time_in_force": "Time in force",
    "price": "Order price",
    "Market price": "Market price",
    "as of": "as of"}

PORTFOLIO_DETAIL_MAPPINGS = {
    "symbol": "Symbol",
    "balance": "Balance",
    "clear_price": "Last order price",
    "price": "Market price",
    "timestamp": "Updated at",
    "Value": "Value",
    "Portfolio %": "Portfolio %",
    "Change since last close": "Change since last close"}

# ------ #
# Colors #
# ------ #
"""Colors are organized sequentially with three different grouping. We'll assign user colors in order, starting with the
first one, and working our way through the list"""
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


def get_game_users(game_id: int):
    usernames = get_all_game_usernames(game_id)
    if check_single_player_mode(game_id):
        index_names = query_to_dict("SELECT `name` FROM index_metadata")
        usernames += [x["name"] for x in index_names]
    return usernames


def assign_colors(inventory: List):
    """We break this out as a separate function because we need the leaderboard and the field charts to share the same
    color mappings"""
    inventory.sort()  # ensures that the passed-in order doesn't matter for color mappings
    colors = palette_generator(len(inventory))
    return {item: color for item, color in zip(inventory, colors)}

# ----- #
# Lists #
# ----- #


def _days_left(game_id: int):
    _, end = get_game_start_and_end(game_id)
    seconds_left = end - time.time()
    return seconds_left // SECONDS_IN_A_DAY


def make_stat_entry(color: str, cash_balance: Union[float, None], portfolio_value: float, stocks_held: List[str],
                    return_ratio: float = None, sharpe_ratio: float = None):
    if return_ratio is None:
        return_ratio = STARTING_RETURN_RATIO

    if sharpe_ratio is None:
        sharpe_ratio = STARTING_SHARPE_RATIO

    return_ratio = float(return_ratio)
    sharpe_ratio = float(sharpe_ratio)

    return dict(
        return_ratio=return_ratio,
        sharpe_ratio=sharpe_ratio,
        stocks_held=stocks_held,
        cash_balance=cash_balance,
        portfolio_value=portfolio_value,
        color=color
    )


def get_user_information(user_id: int):
    sql = "SELECT id, name, email, profile_pic, username, created_at FROM users WHERE id = %s"
    info = query_to_dict(sql, user_id)[0]
    info["rating"] = float(rds.get(f"{PLAYER_RANK_PREFIX}_{user_id}"))
    info["three_month_return"] = float(rds.get(f"{THREE_MONTH_RETURN_PREFIX}_{user_id}"))
    return info


def compile_and_pack_player_leaderboard(game_id: int, start_time: float = None, end_time: float = None):
    user_ids = get_active_game_user_ids(game_id)
    usernames = get_game_users(game_id)
    user_colors = assign_colors(usernames)
    records = []
    for user_id in user_ids:
        user_info = get_user_information(user_id)  # this is where username and profile pic get added in
        cash_balance = get_current_game_cash_balance(user_id, game_id)
        balances = get_active_balances(game_id, user_id)
        stocks_held = list(balances["symbol"].unique())
        portfolio_value = get_user_portfolio_value(game_id, user_id)
        stat_info = make_stat_entry(color=user_colors[user_info["username"]],
                                    cash_balance=cash_balance,
                                    portfolio_value=portfolio_value,
                                    stocks_held=stocks_held,
                                    return_ratio=rds.get(f"{RETURN_RATIO_PREFIX}_{game_id}_{user_id}"),
                                    sharpe_ratio=rds.get(f"{SHARPE_RATIO_PREFIX}_{game_id}_{user_id}"))
        records.append({**user_info, **stat_info})

    if check_single_player_mode(game_id):
        for index in TRACKED_INDEXES:
            index_info = query_to_dict("""
                SELECT name as username, avatar AS profile_pic 
                FROM index_metadata WHERE symbol = %s""", index)[0]
            portfolio_value = get_index_portfolio_value(game_id, index, start_time, end_time)
            stat_info = make_stat_entry(color=user_colors[index_info["username"]],
                                        cash_balance=None,
                                        portfolio_value=portfolio_value,
                                        stocks_held=[],
                                        return_ratio=rds.get(f"{RETURN_RATIO_PREFIX}_{game_id}_{index}"),
                                        sharpe_ratio=rds.get(f"{SHARPE_RATIO_PREFIX}_{game_id}_{index}"))
            records.append({**index_info, **stat_info})

    benchmark = get_game_info(game_id)["benchmark"]  # get game benchmark and use it to sort leaderboard
    records = sorted(records, key=lambda x: -x[benchmark])
    output = dict(days_left=_days_left(game_id), records=records)
    s3_cache.set(f"{game_id}/{LEADERBOARD_PREFIX}", json.dumps(output))


# ------------------ #
# Time series charts #
# ------------------ #


def format_posix_time(ts: float):
    if np.isnan(ts):
        return ts
    dtime = posix_to_datetime(ts)
    return dtime.strftime(DATE_LABEL_FORMAT)


def downsample_time_series(sr: pd.Series, n: int):
    """if at some point in the future we want to remove downsampling for high chart resolution all that's required is
    to convert the passed in series to a list with sr.to_list()
    """
    if sr.nunique() < n:
        n = sr.nunique()
    return pd.cut(sr, n, right=True, labels=False, include_lowest=False).to_list()


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

    start_time = timestamp_sr.min().date()
    end_time = timestamp_sr.max().date()
    trade_times_df = get_trading_calendar(start_time, end_time)
    # when this happens it means that the game is young enough that we don't yet have any observations that occured
    # during trading hours. In this case we won't worry about filtering our trading hours -- we'll just assign  an index
    # on the times available
    if trade_times_df.empty or trade_times_df.iloc[-1]["market_close"] <= start_time:
        return pd.cut(timestamp_sr, N_PLOT_POINTS, right=True, labels=False, include_lowest=False).to_list()

    df = timestamp_sr.to_frame()
    df["anchor_time"] = timestamp_sr.min()
    df["time_diff"] = (df["timestamp"] - df["anchor_time"]).dt.total_seconds()
    df.set_index("timestamp", inplace=True)
    df.index = df.index.to_period("D")
    del df["anchor_time"]

    trade_times_df["last_close"] = trade_times_df["market_close"].shift(1)
    trade_times_df["non_trading_seconds"] = (
            trade_times_df["market_open"] - trade_times_df["last_close"]).dt.total_seconds().fillna(0)
    trade_times_df["adjustment"] = trade_times_df["non_trading_seconds"].cumsum()
    trade_times_df.set_index("market_open", inplace=True)
    trade_times_df.index = trade_times_df.index.to_period("D")
    adjustment_df = trade_times_df["adjustment"]

    tt_df = df.join(adjustment_df)
    tt_df["trade_time"] = tt_df["time_diff"] - tt_df["adjustment"]
    return downsample_time_series(tt_df["trade_time"], N_PLOT_POINTS)


def add_time_labels(df: pd.DataFrame, time_col: dt = "timestamp") -> pd.DataFrame:
    df.sort_values(time_col, inplace=True)
    df["t_index"] = trade_time_index(df[time_col])
    labels = df.groupby("t_index", as_index=False)[time_col].max().rename(columns={time_col: "label"})
    df = df.merge(labels, how="inner", on="t_index")
    df["label"] = df["label"].apply(lambda x: datetime_to_posix(x)).astype(float)
    return df


def make_user_balances_chart_data(game_id: int, user_id: int, start_time: float = None,
                                  end_time: float = None) -> pd.DataFrame:
    df = make_historical_balances_and_prices_table(game_id, user_id, start_time, end_time)
    if df.empty:  # this should only happen outside of trading hours
        df["label"] = None  # for downstream compliance with schema validation
        return df
    df = add_time_labels(df)
    df = df.groupby(["symbol", "t_index"], as_index=False).aggregate(
        {"label": "last", "value": "last", "timestamp": "last"})
    return df[~df["value"].isnull()]  # necessary for when merge_asof didn't find a balance-price match


def serialize_pandas_rows_to_dataset(df: pd.DataFrame, dataset_label: str, dataset_color: str, labels: List[str],
                                     data_column: str, label_column: str):
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


def make_chart_json(df: pd.DataFrame, series_var: str, data_var: str, labels_var: str = "label",
                    colors: List[str] = None, interpolate: bool = True) -> dict:
    """
    :param df: A data with columns corresponding to each of the required variables
    :param series_var: What is the column that defines a unique data set entry?
    :param labels_var: What is the column that defines the x-axis?
    :param data_var: What is the column that defines the y-axis
    :param colors: A passed-in array if you want to override the default color scheme
    :param interpolate: flag controlling whether to implement missing data interpolation
    :return: A json-serializable chart dictionary

    Target schema is:
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
    """
    if interpolate:
        # if the sampling interval is fine-grained enough we may have missing values. interpolate those here
        def _interpolate(mini_df):
            mini_df[data_var] = mini_df[data_var].interpolate(method='akima')
            return mini_df

        df = df.groupby(series_var).apply(lambda x: _interpolate(x))

    labels = list(df[labels_var].unique())
    datasets = []
    series = df[series_var].unique()
    if colors is None:
        colors = palette_generator(len(series))
    for series_entry, color in zip(series, colors):
        subset = df[df[series_var] == series_entry]
        entry = serialize_pandas_rows_to_dataset(subset, series_entry, color, labels, data_var, labels_var)
        datasets.append(entry)
    return dict(labels=labels, datasets=datasets)


def make_null_chart(null_label: str):
    """Null chart function for when a game has just barely gotten going / has started after hours and there's no data.
    For now this function is a bit unnecessary, but the idea here is to be really explicit about what's happening so
    that we can add other attributes later if need be.
    """
    schedule = get_next_trading_day_schedule(dt.utcnow())
    start, end = [posix_to_datetime(x) for x in get_schedule_start_and_end(schedule)]
    labels = [datetime_to_posix(t) for t in pd.date_range(start, end, N_PLOT_POINTS)]
    data = [STARTING_VIRTUAL_CASH for _ in labels]
    return dict(labels=labels,
                datasets=[
                    dict(label=null_label, data=data, borderColor=NULL_RGBA, backgroundColor=NULL_RGBA, fill=False)])


def serialize_and_pack_balances_chart(df: pd.DataFrame, game_id: int, user_id: int):
    chart_json = make_null_chart("Cash")
    if df.shape[0] > 1:  # a dataframe with a single row means that this user just got started and is only holding cash
        df.sort_values("timestamp", inplace=True)
        apply_validation(df, balances_chart_schema)
        chart_json = make_chart_json(df, "symbol", "value")
    s3_cache.set(f"{game_id}/{user_id}/{BALANCES_CHART_PREFIX}", json.dumps(chart_json))


def serialize_and_pack_portfolio_comps_chart(df: pd.DataFrame, game_id: int):
    usernames = get_game_users(game_id)
    user_colors = assign_colors(usernames)
    datasets = []
    if df["username"].nunique() == df.shape[0]:
        # if our portfolio dataframe only has as many rows as there are users in the game, this means that we've just
        # started the game, and can post a null chart to the field
        for username, color in user_colors.items():
            null_chart = make_null_chart(username)
            datasets.append(null_chart["datasets"][0])
        labels = null_chart["labels"]
        chart_json = dict(labels=list(labels), datasets=datasets)
    else:
        colors = []
        for username in df["username"].unique():
            colors.append(user_colors[username])
        chart_json = make_chart_json(df, "username", "value", colors=colors)

    leaderboard = s3_cache.unpack_s3_json(f"{game_id}/{LEADERBOARD_PREFIX}")
    chart_json["leaderboard"] = leaderboard["records"]
    s3_cache.set(f"{game_id}/{FIELD_CHART_PREFIX}", json.dumps(chart_json))


def aggregate_portfolio_value(df: pd.DataFrame):
    """Tally aggregated portfolio value for "the field" chart
    """
    if df.empty:
        return df

    last_entry_df = df.groupby(["symbol", "t_index"], as_index=False)[["label", "value", "timestamp"]].aggregate(
        {"label": "last", "value": "last", "timestamp": "last"})
    return last_entry_df.groupby("t_index", as_index=False)[["label", "value", "timestamp"]].aggregate(
        {"label": "first", "value": "sum", "timestamp": "first"})


def relabel_aggregated_portfolios(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    del df["label"]  # delete the old labels, since we'll be re-assigning them based on the merged data here
    df = add_time_labels(df)
    df.sort_values("timestamp", inplace=True)
    return df.groupby(["username", "label"], as_index=False)[["value", "timestamp"]].agg("last")


def make_the_field_charts(game_id: int, start_time: float = None, end_time: float = None):
    """This function wraps a loop that produces the balances chart for each user and the field chart for the game. This
    will run every time a user places and order, and periodically as prices are collected
    """
    user_ids = get_active_game_user_ids(game_id)
    portfolios = []
    portfolio_table_keys = list(portfolio_comps_schema.keys())
    for user_id in user_ids:
        df = make_user_balances_chart_data(game_id, user_id, start_time, end_time)
        serialize_and_pack_balances_chart(df, game_id, user_id)
        portfolio = aggregate_portfolio_value(df)
        portfolio["username"] = get_usernames([user_id])[0]
        apply_validation(portfolio, portfolio_comps_schema)
        portfolios.append(portfolio[portfolio_table_keys])

    # add index data
    if check_single_player_mode(game_id):
        for index in TRACKED_INDEXES:
            df = get_index_portfolio_value_data(game_id, index, start_time, end_time)
            df["timestamp"] = df["timestamp"].apply(lambda x: posix_to_datetime(x))
            df = add_time_labels(df)
            df = df.groupby("t_index", as_index=False).agg(
                {"username": "last", "label": "last", "value": "last", "timestamp": "last"})
            apply_validation(df, portfolio_comps_schema)
            portfolios.append(df[portfolio_table_keys])

    portfolios_df = pd.concat(portfolios)
    relabelled_df = relabel_aggregated_portfolios(portfolios_df)
    relabelled_df.sort_values("timestamp", inplace=True)
    serialize_and_pack_portfolio_comps_chart(relabelled_df, game_id)


# ------ #
# Orders #
# ------ #


def make_order_labels(order_df: pd.DataFrame) -> pd.DataFrame:
    apply_validation(order_df, order_details_schema)
    order_df["order_label"] = pd.DatetimeIndex(pd.to_datetime(order_df['timestamp_fulfilled'], unit='s')).tz_localize(
        'UTC').tz_convert(TIMEZONE)
    order_df['order_label'] = order_df['order_label'].dt.strftime(DATE_LABEL_FORMAT)
    order_df["order_label"] = order_df["symbol"] + "/" + order_df["quantity"].astype(str) + " @ " + order_df[
        "clear_price_fulfilled"].map(USD_FORMAT.format) + "/" + order_df["order_label"]

    # check for cases where different orders have the same labels. in these cases add an [n]
    mask = order_df[["order_label", "buy_or_sell"]].duplicated(keep=False)
    if mask.any():

        def _index_duplicate_labels(dup_subset):
            new_labels = []
            dup_subset = dup_subset.reset_index(drop=True)
            for i, row in dup_subset.iterrows():
                label_elements = row["order_label"].split("/")
                label_elements[1] += f" [{i + 1}]"
                new_labels.append("/".join(label_elements))
            dup_subset["order_label"] = new_labels
            return dup_subset

        dup_order_df = order_df[mask]
        dup_order_df = dup_order_df.groupby("order_label").apply(_index_duplicate_labels).reset_index(drop=True)
        order_df = pd.concat([dup_order_df, order_df[~mask]])

    return order_df


def get_game_balances(game_id: int, user_id: int, start_time: float = None, end_time: float = None):
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    with engine.connect() as conn:
        return pd.read_sql("""
          SELECT timestamp, symbol, balance, transaction_type, order_status_id, stock_split_id FROM game_balances
          WHERE game_id = %s AND user_id = %s AND balance_type = 'virtual_stock' AND timestamp >= %s AND timestamp <= %s
          ORDER BY symbol, id;""", conn, params=[game_id, user_id, start_time, end_time])


def make_order_performance_table(game_id: int, user_id: int, start_time: float = None, end_time: float = None):
    """the order performance table provides the basis for the order performance chart and the order performance table
    in the UI. it looks at each purchase order as a separate entity, and then iterates over subsequent sale and stock
    split events to iteratively 'unwind' the P&L associated with that buy order. the function handles multiple buy
    orders for the same stock by considering the buy order events and the split/sale events to each be their own queue.
    as the function iterates over the buy orders it "consumes" split/sell events from the queue. the sales event portion
    of the queue is unique to each stock symbol -- this part of the queue is built at the outermost loop, and sales
    events are "consumed" and removed from the queue as the function iterates over the different buy events. stock
    splits, on the other hand can apply to multiple buy orders and aren't dropped from the queue in the same way that
    sales events are. this portion of the queue is therefore reconstructed for each buy order iteration before being
    blended with the remaining sales events in the queue. """
    # get historical order details
    order_df = get_order_details(game_id, user_id, start_time, end_time)
    order_df = order_df[(order_df["status"] == "fulfilled") & (order_df["symbol"] != "Cash")]
    if order_df.empty:
        return order_df
    order_df = make_order_labels(order_df)
    order_details_columns = ["symbol", "order_id", "order_status_id", "order_label", "buy_or_sell", "quantity",
                             "clear_price_fulfilled", "timestamp_fulfilled"]
    orders = order_df[order_details_columns]
    balances = get_game_balances(game_id, user_id, start_time, end_time)
    df = balances.merge(orders, on=["symbol", "order_status_id"], how="left")

    buys_df = df[df["buy_or_sell"] == "buy"]
    sales_df = df[df["transaction_type"] == "stock_sale"]
    splits_df = df[df["transaction_type"] == "stock_split"]
    performance_records = []
    for symbol in df["symbol"].unique():
        # look up price ranged need to calculating unrealized p&l for split events
        min_time = float(df[df["symbol"] == symbol]["timestamp"].min())
        max_time = time.time()
        price_df = get_price_histories([symbol], min_time, max_time)

        # iterate over buy and sales queues
        buys_subset = buys_df[buys_df["symbol"] == symbol]
        sales_queue = sales_df[sales_df["symbol"] == symbol].to_dict(orient="records")
        for _, buy_order in buys_subset.iterrows():
            order_label = buy_order["order_label"]
            buy_quantity = buy_order["quantity"]
            clear_price = buy_order["clear_price_fulfilled"]
            basis = buy_quantity * clear_price
            performance_records.append(dict(
                symbol=symbol,
                order_id=buy_order["order_id"],
                order_label=order_label,
                basis=basis,
                quantity=buy_quantity,
                clear_price=clear_price,
                event_type="buy",
                fifo_balance=buy_quantity,
                timestamp=buy_order["timestamp_fulfilled"],
                realized_pl=0,
                unrealized_pl=0,
                total_pct_sold=0
            ))

            # instantiate variable for balances and sold percentages
            fifo_balance = buy_order["quantity"]
            total_pct_sold = 0

            # reconstruct the events queue with splits refreshed each time
            mask = (splits_df["symbol"] == symbol) & (splits_df["timestamp"] >= buy_order["timestamp"])
            splits_queue = splits_df[mask].to_dict(orient="records")
            events_queue = splits_queue + sales_queue
            events_queue = sorted(events_queue, key=lambda k: k['timestamp'])
            while fifo_balance > 0 and len(events_queue) > 0:
                event = events_queue[0]  # 'consume' events from the queue as we unwind P&L
                if event["transaction_type"] == "stock_split":
                    split_entry = query_to_dict("SELECT * FROM stock_splits WHERE id = %s", event["stock_split_id"])[0]
                    fifo_balance *= split_entry["numerator"] / split_entry["denominator"]
                    price = price_df[price_df["timestamp"] >= event["timestamp"]].iloc[0]["price"]
                    performance_records.append(dict(
                        symbol=symbol,
                        order_label=order_label,
                        order_id=None,
                        basis=basis,
                        quantity=None,
                        clear_price=None,
                        event_type="split",
                        fifo_balance=fifo_balance,
                        timestamp=split_entry["exec_date"],
                        realized_pl=0,
                        unrealized_pl=fifo_balance * price - (1 - total_pct_sold) * basis,
                        total_pct_sold=total_pct_sold
                    ))
                    events_queue.pop(0)

                if event["transaction_type"] == "stock_sale":
                    sale_price = event["clear_price_fulfilled"]
                    quantity_sold = order_amount = event["quantity"]
                    if fifo_balance - quantity_sold < 0:
                        quantity_sold = fifo_balance

                    event["quantity"] -= quantity_sold
                    assert not event["quantity"] < 0
                    if event["quantity"] == 0:
                        sales_queue.pop(0)
                    events_queue.pop(0)
                    sale_pct = (1 - total_pct_sold) * quantity_sold / fifo_balance
                    total_pct_sold += sale_pct
                    fifo_balance -= quantity_sold
                    performance_records.append(dict(
                        symbol=symbol,
                        order_label=order_label,
                        order_id=event["order_id"],
                        basis=basis,
                        quantity=order_amount,
                        clear_price=sale_price,
                        event_type="sell",
                        fifo_balance=fifo_balance,
                        timestamp=event["timestamp_fulfilled"],
                        realized_pl=quantity_sold * sale_price - sale_pct * basis,
                        unrealized_pl=fifo_balance * sale_price - (1 - total_pct_sold) * basis,
                        total_pct_sold=total_pct_sold
                    ))
    return pd.DataFrame(performance_records)


def serialize_and_pack_order_performance_chart(df: pd.DataFrame, game_id: int, user_id: int):
    if df.empty:
        chart_json = make_null_chart("Waiting for orders...")
    else:
        apply_validation(df, order_performance_schema, True)
        plot_df = add_bookends(df, group_var="order_label", condition_var="fifo_balance")
        plot_df["cum_pl"] = plot_df.groupby("order_label")["realized_pl"].cumsum()
        plot_df["timestamp"] = plot_df["timestamp"].apply(lambda x: posix_to_datetime(x))
        plot_df.set_index("timestamp", inplace=True)
        plot_df = plot_df.groupby("order_label", as_index=False).resample(f"{RESAMPLING_INTERVAL}T").last().ffill()
        plot_df = plot_df.reset_index(level=1)
        plot_df = filter_for_trade_time(plot_df)
        plot_df = append_price_data_to_balance_histories(plot_df)
        plot_df.sort_values(["order_label", "timestamp"], inplace=True)
        plot_df = add_time_labels(plot_df)
        plot_df = plot_df.groupby(["order_label", "t_index"], as_index=False).agg("last")
        plot_df["label"] = plot_df["timestamp"].apply(lambda x: datetime_to_posix(x)).astype(float)
        plot_df.sort_values("timestamp", inplace=True)
        plot_df["total_pl"] = plot_df["cum_pl"] + plot_df["fifo_balance"] * plot_df["price"] - (
                1 - plot_df["total_pct_sold"]) * plot_df["basis"]
        plot_df["return"] = 100 * plot_df["total_pl"] / plot_df["basis"]
        label_colors = assign_colors(plot_df["order_label"].unique())
        plot_df["color"] = plot_df["order_label"].apply(lambda x: label_colors.get(x))
        chart_json = make_chart_json(plot_df, "order_label", "return", "label", colors=plot_df["color"].unique())
    s3_cache.set(f"{game_id}/{user_id}/{ORDER_PERF_CHART_PREFIX}", json.dumps(chart_json))


def no_fulfilled_orders_table(game_id: int, user_id: int):
    init_fufilled_json = dict(data=[], headers=list(FULFILLED_ORDER_MAPPINGS.values()))
    s3_cache.set(f"{game_id}/{user_id}/{FULFILLED_ORDER_PREFIX}", json.dumps(init_fufilled_json))


def add_fulfilled_order_entry(game_id: int, user_id: int, order_id: int):
    """Add a fulfilled order to the fulfilled orders table without rebuilding the entire asset"""
    order_status_entry = query_to_dict("""
        SELECT * FROM order_status WHERE order_id = %s ORDER BY id DESC LIMIT 0, 1""", order_id)[0]
    if order_status_entry["status"] == "fulfilled":
        order_entry = query_to_dict("SELECT * FROM orders WHERE id = %s;", order_id)[0]
        symbol = order_entry['symbol']
        timestamp = order_status_entry["timestamp"]
        clear_price = order_status_entry["clear_price"]
        quantity = order_entry["quantity"]
        order_label = f"{symbol}/{int(quantity)} @ {USD_FORMAT.format(clear_price)}/{format_posix_time(timestamp)}"
        buy_or_sell = order_entry["buy_or_sell"]
        new_entry = {
            "order_label": order_label,
            "event_type": buy_or_sell,
            "Symbol": symbol,
            "Cleared on": timestamp,
            "Quantity": quantity,
            "Clear price": clear_price,
            "Basis": quantity * clear_price if buy_or_sell == "buy" else NA_TEXT_SYMBOL,
            "Balance (FIFO)": quantity if buy_or_sell == "buy" else NA_NUMERIC_VAL,
            "Realized P&L": quantity if buy_or_sell == "buy" else NA_NUMERIC_VAL,
            "Unrealized P&L": quantity if buy_or_sell == "buy" else NA_NUMERIC_VAL,
            "Market price": quantity if buy_or_sell == "buy" else NA_NUMERIC_VAL,
            "as of": quantity if buy_or_sell == "buy" else NA_NUMERIC_VAL,
            "color": quantity if buy_or_sell == "buy" else NA_NUMERIC_VAL
        }
        assert set(FULFILLED_ORDER_MAPPINGS.values()) - set(new_entry.keys()) == set()
        fulfilled_order_table = s3_cache.unpack_s3_json(f"{game_id}/{user_id}/{FULFILLED_ORDER_PREFIX}")
        fulfilled_order_table["data"] = [new_entry] + fulfilled_order_table["data"]
        s3_cache.set(f"{game_id}/{user_id}/{FULFILLED_ORDER_PREFIX}", json.dumps(fulfilled_order_table))


def serialize_and_pack_order_performance_table(df: pd.DataFrame, game_id: int, user_id: int):
    if df.empty:
        no_fulfilled_orders_table(game_id, user_id)
        return
    apply_validation(df, order_performance_schema, True)
    agg_rules = {"symbol": "first", "quantity": "first", "clear_price": "first", "timestamp": "first",
                 "fifo_balance": "last", "basis": "first", "realized_pl": "sum", "unrealized_pl": "last",
                 "total_pct_sold": "last", "event_type": "first"}
    tab = df.groupby("order_label", as_index=False).agg(agg_rules)
    recent_prices = get_most_recent_prices(tab["symbol"].unique())
    recent_prices.rename(columns={"price": "Market price", "timestamp": "as of"}, inplace=True)
    tab = tab.merge(recent_prices, how="left")
    tab.sort_values(["order_label", "timestamp"], inplace=True)
    label_colors = assign_colors(tab["order_label"].to_list())
    tab["unrealized_pl"] = tab["fifo_balance"] * tab["Market price"] - (1 - tab["total_pct_sold"]) * tab["basis"]
    del tab["total_pct_sold"]
    tab["color"] = tab["order_label"].apply(lambda x: label_colors.get(x))
    # tack on sold orders
    sold_columns = ["symbol", "timestamp", "quantity", "clear_price", "basis", "event_type"]
    sold_df = df.loc[df["event_type"] == "sell", sold_columns]
    sold_df["basis"] = -1 * sold_df["basis"]
    tab = pd.concat([tab, sold_df], axis=0)
    tab.sort_values("timestamp", inplace=True)
    tab["realized_pl_percent"] = tab["realized_pl"] / tab["basis"]
    tab["unrealized_pl_percent"] = tab["unrealized_pl"] / tab["basis"]
    tab.rename(columns=FULFILLED_ORDER_MAPPINGS, inplace=True)
    tab.fillna(NA_NUMERIC_VAL, inplace=True)
    fulfilled_order_table = dict(data=tab.to_dict(orient="records"), headers=list(FULFILLED_ORDER_MAPPINGS.values()))
    s3_cache.set(f"{game_id}/{user_id}/{FULFILLED_ORDER_PREFIX}", json.dumps(fulfilled_order_table))


def serialize_and_pack_order_performance_assets(game_id: int, user_id: int, start_time: float = None,
                                                end_time: float = None):
    df = make_order_performance_table(game_id, user_id, start_time, end_time)
    serialize_and_pack_order_performance_chart(df, game_id, user_id)
    serialize_and_pack_order_performance_table(df, game_id, user_id)

# ------ #
# Tables #
# ------ #


def add_market_prices_to_order_details(df):
    recent_prices = get_most_recent_prices(df["symbol"].unique())
    recent_prices.rename(columns={"price": "Market price", "timestamp": "as of"}, inplace=True)
    return df.merge(recent_prices, how="left")


def no_pending_orders_table(game_id: int, user_id: int):
    init_pending_json = dict(data=[], headers=list(PENDING_ORDER_MAPPINGS.values()))
    s3_cache.set(f"{game_id}/{user_id}/{PENDING_ORDERS_PREFIX}", json.dumps(init_pending_json))


def serialize_and_pack_pending_orders(game_id: int, user_id: int):
    df = get_order_details(game_id, user_id)
    df = df[df["status"] == "pending"]
    if df.empty:
        no_pending_orders_table(game_id, user_id)
        return
    df["time_in_force"] = df["time_in_force"].apply(lambda x: "Day" if x == "day" else "Until cancelled")
    df = add_market_prices_to_order_details(df)
    df.fillna(NA_TEXT_SYMBOL, inplace=True)
    mapped_columns_to_drop = ["clear_price_fulfilled", "timestamp_fulfilled"]
    df = df.drop(mapped_columns_to_drop, axis=1)
    df = df.rename(columns=PENDING_ORDER_MAPPINGS)
    df = df[df["status"] == "pending"]
    pending_order_records = dict(data=df.to_dict(orient="records"), headers=list(PENDING_ORDER_MAPPINGS.values()))
    s3_cache.set(f"{game_id}/{user_id}/{PENDING_ORDERS_PREFIX}", json.dumps(pending_order_records))


def removing_pending_order(game_id: int, user_id: int, order_id: int):
    fn = f"{game_id}/{user_id}/{PENDING_ORDERS_PREFIX}"
    order_json = s3_cache.unpack_s3_json(fn)
    order_json["data"] = [entry for entry in order_json["data"] if entry["order_id"] != order_id]
    s3_cache.set(fn, json.dumps(order_json))


def get_last_close_prices(symbols: List):
    current_time = time.time()
    end_time = get_end_of_last_trading_day(current_time - SECONDS_IN_A_DAY)
    sql = f"""
    SELECT p.symbol, p.price as close_price
    FROM prices p
    INNER JOIN (
    SELECT symbol, max(id) as max_id
      FROM prices
      WHERE symbol IN ({', '.join(["%s"] * len(symbols))}) AND timestamp <= %s
      GROUP BY symbol) max_price
    ON p.id = max_price.max_id;"""
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=list(symbols) + [end_time])


def serialize_and_pack_portfolio_details(game_id: int, user_id: int):
    out_dict = dict(data=[], headers=list(PORTFOLIO_DETAIL_MAPPINGS.values()))
    balances = get_active_balances(game_id, user_id)
    if balances.empty:
        s3_cache.set(f"{game_id}/{user_id}/{CURRENT_BALANCES_PREFIX}", json.dumps(out_dict))
        return
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    symbols = balances["symbol"].unique()
    prices = get_most_recent_prices(symbols)
    df = balances.groupby("symbol", as_index=False).aggregate({"balance": "last", "clear_price": "last"})
    df = df.merge(prices, on="symbol", how="left")
    df["Value"] = df["balance"] * df["price"]
    total_portfolio_value = df["Value"].sum() + cash_balance
    df["Portfolio %"] = (df["Value"] / total_portfolio_value)
    close_prices = get_last_close_prices(symbols)
    df = df.merge(close_prices, how="left")
    df["Change since last close"] = ((df["price"] - df["close_price"]) / df["close_price"])
    del df["close_price"]
    symbols_colors = assign_colors(symbols)
    df["color"] = df["symbol"].apply(lambda x: symbols_colors[x])
    df.rename(columns=PORTFOLIO_DETAIL_MAPPINGS, inplace=True)
    df.fillna(NA_TEXT_SYMBOL, inplace=True)
    records = df.to_dict(orient="records")
    out_dict["data"] = records
    s3_cache.set(f"{game_id}/{user_id}/{CURRENT_BALANCES_PREFIX}", json.dumps(out_dict))


def make_payout_table_entry(start_date: dt, end_date: dt, winner: str, payout: float, type: str, benchmark: str = None,
                            score: float = None):
    if score is None:
        formatted_score = NA_TEXT_SYMBOL
    else:
        assert benchmark in ["return_ratio", "sharpe_ratio"]
        formatted_score = round(score, 3)

    return dict(
        Start=datetime_to_posix(start_date),
        End=datetime_to_posix(end_date),
        Winner=winner,
        Payout=payout,
        Type=type,
        Score=formatted_score
    )


def serialize_and_pack_winners_table(game_id: int):
    """this function serializes the winners data that has already been saved to DB and fills in any missing rows."""
    game_start, game_end, start_dt, end_dt, benchmark, side_bets_perc, stakes, offset = get_winners_meta_data(game_id)

    # pull winners data from DB
    with engine.connect() as conn:
        winners_df = pd.read_sql("SELECT * FROM winners WHERE game_id = %s ORDER BY id", conn, params=[game_id])

    # Where are we at in the current game?
    game_finished = False
    if winners_df.empty:
        last_observed_win = start_dt
    else:
        last_observed_win = posix_to_datetime(winners_df["timestamp"].max())
        if "overall" in winners_df["type"].to_list():
            game_finished = True

    data = []
    if side_bets_perc:
        payout = get_sidebet_payout(game_id, side_bets_perc, offset, stakes)
        expected_sidebet_dates = get_expected_sidebets_payout_dates(start_dt, end_dt, side_bets_perc, offset)
        for _, row in winners_df.iterrows():
            if row["type"] == "sidebet":
                winner = get_usernames([row["winner_id"]])
                data.append(
                    make_payout_table_entry(posix_to_datetime(row["start_time"]), posix_to_datetime(row["end_time"]),
                                            winner, payout, "Sidebet", benchmark, row["score"]))

        dates_to_fill_in = [x for x in expected_sidebet_dates if x > last_observed_win]
        last_date = last_observed_win
        for payout_date in dates_to_fill_in:
            data.append(make_payout_table_entry(last_date, payout_date, "???", payout, "Sidebet"))
            last_date = payout_date

    payout = get_overall_payout(game_id, side_bets_perc, stakes)
    if not game_finished:
        final_entry = make_payout_table_entry(start_dt, end_dt, "???", payout, "Overall")
    else:
        winner_row = winners_df.loc[winners_df["type"] == "overall"].iloc[0]
        winner = get_usernames([int(winner_row["winner_id"])])[0]
        final_entry = make_payout_table_entry(start_dt, end_dt, winner, payout, "Overall", benchmark,
                                              winner_row["score"])

    data.append(final_entry)
    out_dict = dict(data=data, headers=list(data[0].keys()))
    s3_cache.set(f"{game_id}/{PAYOUTS_PREFIX}", json.dumps(out_dict))


def check_single_player_mode(game_id: int) -> bool:
    with engine.connect() as conn:
        game_mode = conn.execute("SELECT game_mode FROM games WHERE id = %s", game_id).fetchone()
    if not game_mode:
        return False
    return game_mode[0] == "single_player"


def init_game_assets(game_id: int):
    calculate_and_pack_game_metrics(game_id)

    # leaderboard
    compile_and_pack_player_leaderboard(game_id)

    # the field and balance charts
    make_the_field_charts(game_id)

    # tables and performance breakout charts
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        # game/user-level assets
        serialize_and_pack_pending_orders(game_id, user_id)
        serialize_and_pack_order_performance_assets(game_id, user_id)
        serialize_and_pack_portfolio_details(game_id, user_id)

    if not check_single_player_mode(game_id):
        # winners/payouts table
        update_performed = log_winners(game_id, time.time())
        if update_performed:
            serialize_and_pack_winners_table(game_id)


def calculate_and_pack_game_metrics(game_id: int, start_time: float = None, end_time: float = None):
    for user_id in get_active_game_user_ids(game_id):
        return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, start_time, end_time)
        rds.set(f"{RETURN_RATIO_PREFIX}_{game_id}_{user_id}", return_ratio)
        rds.set(f"{SHARPE_RATIO_PREFIX}_{game_id}_{user_id}", sharpe_ratio)

    if check_single_player_mode(game_id):
        for index in TRACKED_INDEXES:
            df = get_index_portfolio_value_data(game_id, index, start_time, end_time)
            index_return_ratio = portfolio_return_ratio(df)
            index_sharpe_ratio = portfolio_sharpe_ratio(df, RISK_FREE_RATE_DEFAULT)
            rds.set(f"{RETURN_RATIO_PREFIX}_{game_id}_{index}", index_return_ratio)
            rds.set(f"{SHARPE_RATIO_PREFIX}_{game_id}_{index}", index_sharpe_ratio)

# ------------------ #
# Public leaderboard #
# ------------------ #


def update_player_rank(df: pd.DataFrame):
    for i, row in df.iterrows():
        if row["user_id"]:
            rds.set(f"{PLAYER_RANK_PREFIX}_{int(row['user_id'])}", row["rating"])
            rds.set(f"{THREE_MONTH_RETURN_PREFIX}_{int(row['user_id'])}", row["three_month_return"])


def serialize_and_pack_rankings():
    cutoff_time = datetime_to_posix(dt.utcnow() - DateOffset(months=3))
    with engine.connect() as conn:
        user_df = pd.read_sql("""
            SELECT user_id, rating, username, profile_pic, n_games, total_return, basis, sr.timestamp 
            FROM stockbets_rating sr
            INNER JOIN (
              SELECT game_id, MAX(id) AS max_id
              FROM game_status
              WHERE status = 'finished' AND timestamp >= %s
              GROUP BY game_id
            ) gs ON gs.game_id = sr.game_id
            INNER JOIN (
              SELECT id, username, profile_pic
              FROM users
            ) u ON u.id = sr.user_id
        """, conn, params=[cutoff_time])

        indexes_df = pd.read_sql("""
            SELECT user_id, rating, imd.username, imd.profile_pic, n_games, total_return, basis, sr.timestamp 
            FROM stockbets_rating sr
            INNER JOIN (
              SELECT game_id, MAX(id) AS max_id
              FROM game_status
              WHERE status = 'finished' AND timestamp >= %s
              GROUP BY game_id
            ) gs ON gs.game_id = sr.game_id
            INNER JOIN (
              SELECT symbol, `name` AS username, avatar AS profile_pic
              FROM index_metadata
            ) imd ON sr.index_symbol = imd.symbol
        """, conn, params=[cutoff_time])

    df = pd.concat([user_df, indexes_df])
    df["basis_times_return"] = df["total_return"] * df["basis"]
    total_basis_df = df.groupby("username", as_index=False)["basis"].sum().rename(columns={"basis": "total_basis"})
    df = df.merge(total_basis_df, on="username").sort_values(["username", "timestamp"])
    stats_df = df.groupby("username", as_index=False).agg({"user_id": "first", "rating": "last", "profile_pic": "first",
                                                           "n_games": "last", "basis_times_return": "sum",
                                                           "total_basis": "first"})
    stats_df["three_month_return"] = stats_df["basis_times_return"] / stats_df["total_basis"]
    del stats_df["basis_times_return"]
    del stats_df["total_basis"]
    stats_df.sort_values("rating", ascending=False, inplace=True)
    stats_df = stats_df.where(pd.notnull(stats_df), None)
    update_player_rank(stats_df)
    rds.set(PUBLIC_LEADERBOARD_PREFIX, json.dumps(stats_df.to_dict(orient="records")))
