"""Logic for calculating and dispering payouts between invitees
"""
from datetime import timedelta, datetime as dt

import numpy as np
import pandas as pd
from pandas import DateOffset
from backend.database.db import engine
from backend.database.helpers import (
    add_row,
    query_to_dict
)
from backend.logic.base import (
    get_time_defaults,
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
    during_trading_day,
    get_game_start_and_end,
    datetime_to_posix,
    make_historical_balances_and_prices_table,
    get_game_info,
    get_active_game_user_ids,
    posix_to_datetime,
    make_date_offset
)
from backend.logic.payments import (
    send_paypal_payment,
    get_payment_profile_uuids,
    PERCENT_TO_USER
)

# -------- #
# Defaults #
# -------- #

STARTING_SHARPE_RATIO = 0
STARTING_RETURN_RATIO = 0
RISK_FREE_RATE_DEFAULT = 0
USD_FORMAT = "${:,.2f}"

# ------------------------------------ #
# Base methods for calculating metrics #
# ------------------------------------ #


def portfolio_value_by_day(game_id: int, user_id: int, start_time: float, end_time: float) -> pd.DataFrame:
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    df = make_historical_balances_and_prices_table(game_id, user_id)
    df = df[(df["timestamp"] >= posix_to_datetime(start_time)) & (df["timestamp"] <= posix_to_datetime(end_time))]
    df = df.groupby(["symbol", "timestamp"], as_index=False)["value"].agg("last")
    return df.groupby("timestamp", as_index=False)["value"].sum()


def portfolio_return_ratio(df: pd.DataFrame):
    if df.empty:
        return STARTING_RETURN_RATIO
    start_val = df.iloc[0]["value"]
    end_val = df.iloc[-1]["value"]
    return 100 * (end_val - start_val) / start_val


def portfolio_sharpe_ratio(df: pd.DataFrame, rf: float):
    if df.empty:
        return STARTING_SHARPE_RATIO
    df["returns"] = (df["value"] - df.iloc[0]["value"]) / df.iloc[0]["value"]
    value = (df["returns"].mean() - rf) / df["returns"].std()
    if np.isnan(value):
        # When a user has not trade and is in cash only, the calculation above produces np.nan. We need to be on the
        # lookout for any other situations that might cause this to happen other than this one
        return STARTING_SHARPE_RATIO
    return value


def calculate_metrics(game_id: int, user_id: int, start_time: float = None, end_time: float = None,
                      rf: float = RISK_FREE_RATE_DEFAULT):
    df = portfolio_value_by_day(game_id, user_id, start_time, end_time)
    return_ratio = portfolio_return_ratio(df)
    sharpe_ratio = portfolio_sharpe_ratio(df, rf)
    return return_ratio, sharpe_ratio


# ------------------- #
# Winners and payouts #
# ------------------- #


def get_last_sidebet_payout(game_id: int):
    # when was the last time that a payout was made/that the game was started?
    with engine.connect() as conn:
        last_payout_date = conn.execute("""
            SELECT end_time FROM winners
            WHERE game_id = %s AND type = 'sidebet'
            ORDER BY end_time DESC LIMIT 0, 1
        """, game_id).fetchone()
    if last_payout_date:
        return last_payout_date[0]
    return None


def get_winner(game_id: int, start_time: float, end_time: float, benchmark: str):
    assert benchmark in ["return_ratio", "sharpe_ratio"]
    ids_and_scores = []

    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        return_ratio, sharpe_ratio = calculate_metrics(game_id, user_id, start_time, end_time)
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

    if during_trading_day() and current_time < payout_time:
        return False

    next_day_schedule = get_next_trading_day_schedule(posix_to_datetime(current_time) + timedelta(days=1))
    next_trade_day_start, _ = get_schedule_start_and_end(next_day_schedule)
    if next_trade_day_start > payout_time:
        return True

    return False


def get_expected_sidebets_payout_dates(start_time: dt, end_time: dt, side_bets_perc: float, offset):
    expected_sidebet_dates = []
    if side_bets_perc:
        payout_time = start_time + offset
        while payout_time <= end_time:
            expected_sidebet_dates.append(payout_time)
            payout_time += offset
    return expected_sidebet_dates


def n_sidebets_in_game(game_start: float, game_end: float, offset: DateOffset) -> int:
    game_start = posix_to_datetime(game_start)
    game_end = posix_to_datetime(game_end)
    count = 0
    t = game_start + offset
    while t <= game_end:
        count += 1
        t += offset
    return count


def get_pot_size(game_id: int):
    game_info = get_game_info(game_id)
    player_ids = get_active_game_user_ids(game_id)
    n_players = len(player_ids)
    return n_players * game_info["buy_in"]


def adjust_for_commission(stakes: str):
    assert stakes in ["real", "monopoly"]
    adjustment = 1
    if stakes == "real":
        adjustment = PERCENT_TO_USER
    return adjustment


def get_overall_payout(game_id: int, side_bets_perc: float = None, stakes: str = "real"):
    if side_bets_perc is None:
        side_bets_perc = 0
    pot_size = get_pot_size(game_id)
    adjustment = adjust_for_commission(stakes)
    return pot_size * (1 - side_bets_perc / 100) * adjustment


def get_sidebet_payout(game_id: int, side_bets_perc: float, offset: DateOffset, stakes: str = "real"):
    game_start, game_end = get_game_start_and_end(game_id)
    n_sidebets = n_sidebets_in_game(game_start, game_end, offset)
    adjustment = adjust_for_commission(stakes)
    pot_size = get_pot_size(game_id)
    return round(pot_size * (side_bets_perc / 100) / n_sidebets, 2) * adjustment


def get_winners_meta_data(game_id: int):
    game_info = query_to_dict("SELECT * FROM games WHERE id = %s", game_id)[0]
    side_bets_perc = game_info.get("side_bets_perc")
    benchmark = game_info["benchmark"]
    stakes = game_info["stakes"]
    game_start, game_end = get_game_start_and_end(game_id)
    offset = make_date_offset(game_info["side_bets_period"])
    start_dt = posix_to_datetime(game_start)
    end_dt = posix_to_datetime(game_end)
    return game_start, game_end, start_dt, end_dt, benchmark, side_bets_perc, stakes, offset


def log_winners(game_id: int, current_time: float):
    update_performed = False
    game_info = query_to_dict("SELECT * FROM games WHERE id = %s", game_id)[0]
    game_start, game_end, start_dt, end_dt, benchmark, side_bets_perc, stakes, offset = get_winners_meta_data(game_id)
    start_dt = posix_to_datetime(game_start)
    end_dt = posix_to_datetime(game_end)

    # If we have sidebets to monitor, see if we have a winner
    if side_bets_perc:
        last_interval_end = get_last_sidebet_payout(game_id)
        if not last_interval_end:
            last_interval_end = game_start
        last_interval_dt = posix_to_datetime(last_interval_end)
        payout_time = datetime_to_posix(last_interval_dt + offset)
        if check_if_payout_time(current_time, payout_time):
            win_type = "sidebet"
            curr_time_dt = posix_to_datetime(current_time)
            anchor_time = last_interval_dt + timedelta(days=1)
            expected_sidebet_dates = get_expected_sidebets_payout_dates(start_dt, end_dt, side_bets_perc, offset)
            curr_interval_end = [date for date in expected_sidebet_dates if anchor_time < date <= curr_time_dt][0]
            curr_interval_posix = datetime_to_posix(curr_interval_end)
            winner_id, score = get_winner(game_id, last_interval_end, curr_interval_posix, benchmark)
            payout = get_sidebet_payout(game_id, side_bets_perc, offset, stakes)
            winner_table_id = add_row("winners", game_id=game_id, winner_id=winner_id, score=float(score),
                                      timestamp=current_time, payout=payout, type=win_type, benchmark=benchmark,
                                      end_time=curr_interval_posix, start_time=last_interval_end)
            update_performed = True
            if stakes == "real":
                payment_profile = get_payment_profile_uuids([winner_id])[0]
                send_paypal_payment(
                    uuids=[payment_profile["uuid"]],
                    amount=payout,
                    payment_type="sidebet",
                    email_subject=f"Congrats on winning the {game_info['side_bets_period']} sidebet!",
                    email_content=f"You came out on top in {game_info['title']} this week. Here's your payment of {USD_FORMAT.format(payout)}",
                    note_content="Keep on crushing it."
                )
                add_row("payments", user_id=winner_id, profile_id=payment_profile["id"], game_id=game_id,
                        winner_table_id=winner_table_id, type=win_type, amount=payout, currency="USD",
                        direction="outflow", timestamp=current_time)

    # if we've reached the end of our game, pay out the winner and mark the game as completed
    if current_time >= game_end:
        win_type = "overall"
        payout = get_overall_payout(game_id, side_bets_perc, stakes)
        winner_id, score = get_winner(game_id, game_start, game_end, benchmark)
        winner_table_id = add_row("winners", game_id=game_id, winner_id=winner_id, benchmark=benchmark,
                                  score=float(score), start_time=game_start, end_time=game_end,
                                  payout=payout, type=win_type, timestamp=current_time)
        update_performed = True

        # the game's over! we've completed our stockbets journey for this round, and it's time to mark the game as
        # completed and payout the overall winner
        user_ids = get_active_game_user_ids(game_id)
        add_row("game_status", game_id=game_id, status="finished", users=user_ids, timestamp=current_time)

        if stakes == "real":
            payment_profile = get_payment_profile_uuids([winner_id])[0]
            send_paypal_payment(
                uuids=[payment_profile["uuid"]],
                amount=payout,
                payment_type="overall",
                email_subject=f"Congrats on winning the {game_info['title']}!",
                email_content=f"You were the overall winner of {game_info['title']}. Awesome work. Here's your payment of {USD_FORMAT.format(payout)}. Come back soon!",
                note_content="Keep on crushing it."
            )
            add_row("payments", user_id=winner_id, profile_id=payment_profile["id"], game_id=game_id,
                    winner_table_id=winner_table_id, type=win_type, amount=payout, currency="USD",
                    direction="outflow", timestamp=current_time)

    return update_performed
