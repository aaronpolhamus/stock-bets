"""Logic for calculating and dispering payouts between invitees
"""
import time
from datetime import datetime as dt
from typing import List

import numpy as np
import pandas as pd
from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import (
    n_sidebets_in_game,
    make_date_offset,
    get_all_game_users,
    posix_to_datetime,
    datetime_to_posix,
    get_game_info,
    make_historical_balances_and_prices_table
)
from backend.tasks.redis import rds

RISK_FREE_RATE_DEFAULT = 0


# ------------------------------------ #
# Base methods for calculating metrics #
# ------------------------------------ #


def get_data_and_clip_time(game_id: int, user_id: int, start_date: dt = None, end_date: dt = None) -> pd.DataFrame:
    df = make_historical_balances_and_prices_table(game_id, user_id)
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
    return 100 * (end_val - start_val) / start_val


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


# ------------------- #
# Winners and payouts #
# ------------------- #


def get_last_sidebet_payout(game_id: int):
    # when was the last time that a payout was made/that the game was started?
    with engine.connect() as conn:
        last_payout_date = conn.execute("""
            SELECT timestamp FROM winners
            WHERE game_id = %s AND type = 'sidebet'
            ORDER BY timestamp DESC LIMIT 0, 1
        """, game_id).fetchone()
    if last_payout_date:
        return last_payout_date[0]
    return None


def get_winner(game_id: int, start_time: float, end_time: float, user_ids: List[int], benchmark: str):
    assert benchmark in ["RETURN RATIO", "SHARPE RATIO"]
    start_date = posix_to_datetime(start_time)
    end_date = posix_to_datetime(end_time)
    ids_and_scores = []
    for user_id in user_ids:
        return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, start_date, end_date)
        metric = return_ratio
        if benchmark == "SHARPE RATIO":
            metric = sharpe_ratio
        ids_and_scores.append((user_id, metric))

    max_score = max([x[1] for x in ids_and_scores])
    return [x for x in ids_and_scores if x[1] == max_score][0]  # TODO: handle ties (mathematically unlikely)


def get_payouts_to_date(game_id: int):
    with engine.connect() as conn:
        total_payouts = conn.execute("SELECT SUM(payout) FROM winners WHERE game_id = %s", game_id).fetchone()[0]
    return total_payouts


def log_winners(game_id: int):
    current_time = time.time()
    game_info = get_game_info(game_id)
    game_start_time = game_info["start_time"]
    game_end_time = game_info["end_time"]
    benchmark = game_info["benchmark"]
    side_bets_perc = game_info.get("side_bets_perc")
    if side_bets_perc is None:
        side_bets_perc = 0
    side_bets_period = game_info.get("side_bets_period")
    player_ids = get_all_game_users(game_id)
    n_players = len(player_ids)
    pot_size = n_players * game_info["buy_in"]

    # If we have sidebets to monitor, see if we have a winner
    if side_bets_perc:
        last_interval_end = get_last_sidebet_payout(game_id)
        if not last_interval_end:
            last_interval_end = game_start_time
        offset = make_date_offset(side_bets_period)
        payout_time = datetime_to_posix(posix_to_datetime(last_interval_end) + offset)
        if current_time >= payout_time:
            winner_id, score = get_winner(game_id, last_interval_end, current_time, player_ids, game_info["benchmark"])
            score = float(score)
            n_sidebets = n_sidebets_in_game(game_start_time, game_end_time, offset)
            payout = round(pot_size * (side_bets_perc / 100) / n_sidebets, 2)
            add_row("winners", game_id=game_id, winner_id=winner_id, score=score, timestamp=current_time, payout=payout,
                    type="sidebet")

    # if we've reached the end of our game, pay out the winner and mark the game as completed
    if current_time >= game_end_time:
        payout = pot_size * (1 - side_bets_perc / 100)
        winner_id, score = get_winner(game_id, game_start_time, game_end_time, player_ids, benchmark)
        add_row("winners", game_id=game_id, winner_id=winner_id, score=float(score), timestamp=current_time,
                payout=payout, type="overall")
