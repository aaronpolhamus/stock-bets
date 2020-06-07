"""Logic for calculating and dispering payouts between invitees
"""
from datetime import datetime as dt

import numpy as np
import pandas as pd

from backend.logic.base import make_balances_and_prices_table
from backend.tasks.redis import rds

RISK_FREE_RATE_DEFAULT = 0


def get_data_and_clip_time(game_id: int, user_id: int, start_date: dt = None, end_date: dt = None) -> pd.DataFrame:
    df = make_balances_and_prices_table(game_id, user_id)
    if start_date is None:
        start_date = df["timestamp"].min()

    if end_date is None:
        end_date = df["timestamp"].max()

    return df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]


def portfolio_value_by_day(game_id, user_id, start_date, end_date) -> pd.DataFrame:
    df = get_data_and_clip_time(game_id, user_id, start_date, end_date)
    df = df.groupby(["symbol", "timestamp"], as_index=False)["value"].agg("last")
    return df.groupby("timestamp", as_index=False)["value"].sum()


def porfolio_total_return(df: pd.DataFrame):
    start_val = df.iloc[0]["value"]
    end_val = df.iloc[-1]["value"]
    return (end_val - start_val) / start_val


def calculate_sharpe_ratio(returns: pd.Series, rf: float, days: int) -> float:
    volatility = returns.std() * np.sqrt(days)
    return (returns.mean() - rf) / volatility


def portfolio_sharpe_ratio(df: pd.DataFrame, rf: float) -> float:
    n_days = df["timestamp"].apply(lambda x: x.replace(hour=12, minute=0)).nunique()
    df["returns"] = df["value"] - df.iloc[0]["value"]
    return calculate_sharpe_ratio(df["returns"], rf, n_days)


def calculate_metrics(game_id: int, user_id: int, start_date: dt = None, end_date: dt = None,
                      rf: float = RISK_FREE_RATE_DEFAULT):
    df = portfolio_value_by_day(game_id, user_id, start_date, end_date)
    total_return = porfolio_total_return(df)
    sharpe_ratio = portfolio_sharpe_ratio(df, rf)
    return total_return, sharpe_ratio


def calculate_and_pack_metrics(game_id, user_id, start_date=None, end_date=None):
    total_return, sharpe_ratio = calculate_metrics(game_id, user_id, start_date, end_date)
    total_return_label = f"total_return_{game_id}_{user_id}_{start_date}-{end_date}"
    sharpe_ratio_label = f"sharpe_ratio_{game_id}_{user_id}_{start_date}-{end_date}"
    if start_date is None and end_date is None:
        total_return_label = f"total_return_{game_id}_{user_id}"
        sharpe_ratio_label = f"sharpe_ratio_{game_id}_{user_id}"
    rds.set(total_return_label, total_return)
    rds.set(sharpe_ratio_label, sharpe_ratio)
