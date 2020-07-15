"""Logic for calculating and dispering payouts between invitees
"""
from datetime import datetime as dt, timedelta

import pandas as pd
import numpy as np
from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import (
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
    during_trading_day,
    get_all_game_users_ids,
    get_payouts_meta_data,
    n_sidebets_in_game,
    posix_to_datetime,
    datetime_to_posix,
    make_historical_balances_and_prices_table
)
from backend.tasks.redis import rds
from backend.logic.visuals import (
    STARTING_SHARPE_RATIO,
    get_expected_sidebets_payout_dates
)

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


def portfolio_value_by_day(game_id: int, user_id: int, start_date: dt, end_date: dt) -> pd.DataFrame:
    df = get_data_and_clip_time(game_id, user_id, start_date, end_date)
    df = df.groupby(["symbol", "timestamp"], as_index=False)["value"].agg("last")
    return df.groupby("timestamp", as_index=False)["value"].sum()


def porfolio_return_ratio(df: pd.DataFrame):
    start_val = df.iloc[0]["value"]
    end_val = df.iloc[-1]["value"]
    return 100 * (end_val - start_val) / start_val


def portfolio_sharpe_ratio(df: pd.DataFrame, rf: float):
    # TODO: risk-free rate may need to vary in time at some point
    df["returns"] = (df["value"] - df.iloc[0]["value"]) / df.iloc[0]["value"]
    value = (df["returns"].mean() - rf) / df["returns"].std()
    if np.isnan(value):
        # When a user has not trade and is in cash only, the calculation above produces np.nan. We need to be on the
        # lookout for any other situations that might cause this to happen other than this one
        return STARTING_SHARPE_RATIO
    return value


def calculate_metrics(game_id: int, user_id: int, start_date: dt = None, end_date: dt = None,
                      rf: float = RISK_FREE_RATE_DEFAULT):
    df = portfolio_value_by_day(game_id, user_id, start_date, end_date)
    return_ratio = porfolio_return_ratio(df)
    sharpe_ratio = portfolio_sharpe_ratio(df, rf)
    return return_ratio, sharpe_ratio


def calculate_and_pack_metrics(game_id, user_id, start_date=None, end_date=None):
    return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, start_date, end_date)
    if start_date is None and end_date is None:
        return_ratio_label = f"return_ratio_{game_id}_{user_id}"
        sharpe_ratio_label = f"sharpe_ratio_{game_id}_{user_id}"
    else:
        return_ratio_label = f"return_ratio_{game_id}_{user_id}_{start_date}-{end_date}"
        sharpe_ratio_label = f"sharpe_ratio_{game_id}_{user_id}_{start_date}-{end_date}"
    rds.set(return_ratio_label, return_ratio)
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


def get_winner(game_id: int, start_time: float, end_time: float, benchmark: str):
    assert benchmark in ["return_ratio", "sharpe_ratio"]
    start_date = posix_to_datetime(start_time)
    end_date = posix_to_datetime(end_time)
    ids_and_scores = []

    user_ids = get_all_game_users_ids(game_id)
    for user_id in user_ids:
        return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, start_date, end_date)
        metric = return_ratio
        if benchmark == "sharpe_ratio":
            metric = sharpe_ratio
        ids_and_scores.append((user_id, metric))

    max_score = max([x[1] for x in ids_and_scores])
    return [x for x in ids_and_scores if x[1] == max_score][0]  # TODO: handle ties (mathematically unlikely)


def get_payouts_to_date(game_id: int):
    with engine.connect() as conn:
        total_payouts = conn.execute("SELECT SUM(payout) FROM winners WHERE game_id = %s", game_id).fetchone()[0]
    return total_payouts


def check_if_payout_time(current_time: float, payout_time: float) -> bool:
    if current_time >= payout_time:
        return True

    if during_trading_day():
        return False

    next_day_schedule = get_next_trading_day_schedule(posix_to_datetime(current_time) + timedelta(days=1))
    next_trade_day_start, _ = get_schedule_start_and_end(next_day_schedule)
    if next_trade_day_start > payout_time:
        return True

    return False


def log_winners(game_id: int, current_time: float):
    update_performed = False
    pot_size, game_start_time, game_end_time, offset, side_bets_perc, benchmark = get_payouts_meta_data(game_id)
    game_start_posix = datetime_to_posix(game_start_time)
    game_end_posix = datetime_to_posix(game_end_time)

    # what are the expected sidebet payouts?
    expected_sidebet_dates = get_expected_sidebets_payout_dates(game_start_time, game_end_time, side_bets_perc, offset)

    # If we have sidebets to monitor, see if we have a winner
    if side_bets_perc:
        last_interval_end = get_last_sidebet_payout(game_id)
        if not last_interval_end:
            last_interval_end = game_start_posix
        last_interval_dt = posix_to_datetime(last_interval_end)
        payout_time = datetime_to_posix(last_interval_dt + offset)
        if check_if_payout_time(current_time, payout_time):
            curr_time_dt = posix_to_datetime(current_time)
            curr_interval_end = [date for date in expected_sidebet_dates if last_interval_dt < date <= curr_time_dt][0]
            curr_interval_posix = datetime_to_posix(curr_interval_end)
            winner_id, score = get_winner(game_id, last_interval_end, curr_interval_posix, benchmark)
            n_sidebets = n_sidebets_in_game(game_start_posix, game_end_posix, offset)
            payout = round(pot_size * (side_bets_perc / 100) / n_sidebets, 2)
            add_row("winners", game_id=game_id, winner_id=winner_id, score=float(score), timestamp=current_time,
                    payout=payout, type="sidebet", benchmark=benchmark, end_time=curr_interval_posix,
                    start_time=last_interval_end)
            update_performed = True

    # if we've reached the end of our game, pay out the winner and mark the game as completed
    if current_time >= game_end_posix:
        payout = pot_size * (1 - side_bets_perc / 100)
        winner_id, score = get_winner(game_id, game_start_posix, game_end_posix, benchmark)
        add_row("winners", game_id=game_id, winner_id=winner_id, benchmark=benchmark, score=float(score),
                start_time=game_start_posix, end_time=game_end_posix, payout=payout, type="overall",
                timestamp=current_time)
        update_performed = True

        # the game's over! we've completed our stockbets journey for this round, and it's time to mark the game as
        # completed
        user_ids = get_all_game_users_ids(game_id)
        add_row("game_status", game_id=game_id, status="finished", users=user_ids, timestamp=current_time)

    return update_performed
