"""Logic for rendering visual asset data and returning to frontend
"""
import time
from typing import List

import pandas as pd
from backend.database.db import db_session
from backend.logic.stock_data import (
    PRICE_CACHING_INTERVAL,
    posix_to_datetime,
    get_end_of_last_trading_day
)


def get_all_game_users(session: db_session, game_id: int) -> List[int]:
    with session.connection() as conn:
        result = conn.execute(
            """
            SELECT DISTINCT user_id 
            FROM game_invites WHERE 
                game_id = %s AND
                status = 'joined';""", game_id)
        session.remove()
    return [x[0] for x in result]


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


def get_user_balance_history(game_id: int, user_id: str) -> pd.DataFrame:
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


def resample_balances(symbol_subset):
    # first, take the last balance entry from each timestamp
    df = symbol_subset.groupby(["timestamp"]).aggregate({"balance": "last"})
    df.index = [posix_to_datetime(x) for x in df.index]
    return df.resample(f"{PRICE_CACHING_INTERVAL}S").asfreq().ffill()


def append_price_data_to_balances(db_session: db_session, balances_df: pd.DataFrame) -> pd.DataFrame:
    symbols = balances_df["symbol"].unique()
    sql = f"""
        SELECT timestamp, price, symbol FROM prices
        WHERE symbol IN ({','.join(['%s']*len(symbols))})
    """
    price_df = pd.read_sql(sql, db_session.connection(), params=symbols)
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


def prepare_plot_data(df: pd.DataFrame) -> pd.DataFrame:
    df["value"] = df["balance"] * df["price"]
    df["t_index"] = df["timestamp"].rank(method="dense")
    return df


def build_portfolio_comps(db_session: db_session, game_id) -> pd.DataFrame:
    pass
