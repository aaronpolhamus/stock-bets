"""Logic for calculating and dispering payouts between invitees
"""
from datetime import timedelta, datetime as dt
from typing import Union

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
    make_date_offset,
    get_current_game_cash_balance,
    get_active_balances,
    get_index_portfolio_value_data,
    STARTING_VIRTUAL_CASH
)
from backend.logic.payments import (
    send_paypal_payment,
    get_payment_profile_uuids,
    PERCENT_TO_USER
)
from backend.logic.stock_data import (
    TRACKED_INDEXES,
    get_most_recent_prices
)


# -------- #
# Defaults #
# -------- #

STARTING_SHARPE_RATIO = 0
STARTING_RETURN_RATIO = 0
RISK_FREE_RATE_DEFAULT = 0
USD_FORMAT = "${:,.2f}"
ELO_K_FACTOR = 32
STARTING_ELO_SCORE = 1_000


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

        if stakes == "real":
            pass  # TODO: uncomment when we're able to take real money
            # payment_profile = get_payment_profile_uuids([winner_id])[0]
            # send_paypal_payment(
            #     uuids=[payment_profile["uuid"]],
            #     amount=payout,
            #     payment_type="overall",
            #     email_subject=f"Congrats on winning the {game_info['title']}!",
            #     email_content=f"You were the overall winner of {game_info['title']}. Awesome work. Here's your payment of {USD_FORMAT.format(payout)}. Come back soon!",
            #     note_content="Keep on crushing it."
            # )
            # add_row("payments", user_id=winner_id, profile_id=payment_profile["id"], game_id=game_id,
            #         winner_table_id=winner_table_id, type=win_type, amount=payout, currency="USD",
            #         direction="outflow", timestamp=current_time)

    return update_performed

# Elo ranking equations. Based on wikipedia and this guy's GitHub: https://github.com/rshk/elo
# --------------------------------------------------------------------------------------------


def expected_elo(player_a: float, player_b: float):
    """
    Calculate expected score of A in a match against B
    :param player_a: Elo rating for player A
    :param player_b: Elo rating for player B
    """
    return 1 / (1 + 10 ** ((player_b - player_a) / 400))


def elo_update(old: float, expected: float, score: float, k: float = ELO_K_FACTOR):
    """
    Calculate the new Elo rating for a player
    :param old: The previous Elo rating
    :param expected: The expected score for this match
    :param score: The actual score for this match
    :param k: The k-factor for Elo
    """
    return old + k * (score - expected)


def get_rating_info(player_id: Union[int, str]):
    """if player_id is passed as an int get_rating will interpret it as a user_id. if passed as a string it will interpret
    it as a n index"""
    assert type(player_id) in [int, str]
    rating_column = "index_symbol" if type(player_id) == str else "user_id"
    return query_to_dict(f"""SELECT n_games, basis, total_return, rating FROM stockbets_rating 
                                WHERE {rating_column} = %s ORDER BY id DESC LIMIT 0, 1;""", player_id)[0]


def get_user_portfolio_value(game_id: int, user_id: int, cutoff_time: float = None) -> float:
    """This works slightly differently than the method currently used to generates the leaderboard and charts, which
    depends on the dataframe that make_historical_balances_and_prices_table produces, using pandas.merge_asof. this
    minor discrepancy could result in leaderboard orders in the game panel not precisely matching how they are
    calculated internally here."""
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    balances = get_active_balances(game_id, user_id)
    symbols = balances["symbol"].unique()
    if len(symbols) == 0:
        return cash_balance
    prices = get_most_recent_prices(symbols, cutoff_time)
    df = balances[["symbol", "balance"]].merge(prices, how="left", on="symbol")
    df["value"] = df["balance"] * df["price"]
    return df["value"].sum() + cash_balance


def get_index_portfolio_value(game_id: int, index: str, start_time: float = None, end_time: float = None):
    df = get_index_portfolio_value_data(game_id, index, start_time, end_time)
    if df.empty:
        return STARTING_VIRTUAL_CASH
    return df.iloc[-1]["value"]


def update_ratings(game_id: int):
    start, end = get_game_start_and_end(game_id)
    user_ids = get_active_game_user_ids(game_id)

    # construct the leaderboard, including indexes. use simple return for now
    scoreboard = {}
    for user_id in user_ids:
        ending_value = get_user_portfolio_value(game_id, user_id, end)
        scoreboard[user_id] = ending_value / STARTING_VIRTUAL_CASH - 1

    for index in TRACKED_INDEXES:
        scoreboard[index] = get_index_portfolio_value(game_id, index, start, end) / STARTING_VIRTUAL_CASH - 1

    # now that we have the scoreboard, iterate over its entries to construct and update DF
    update_array = []
    for player, player_return in scoreboard.items():
        other_players = {k: v for k, v in scoreboard.items() if k != player}
        for other_player, other_player_return in other_players.items():
            player_entry = get_rating_info(player)
            other_player_entry = get_rating_info(other_player)
            player_rating = player_entry["rating"]
            other_player_rating = other_player_entry["rating"]

            # fields for return
            total_return = player_entry["total_return"]
            n_games = player_entry["n_games"]

            score = 1 if player_return > other_player_return else 0
            if player_return == other_player_return:
                score = 0.5

            update_array.append(dict(
                player_id=player,
                player_rating=player_rating,
                expected=expected_elo(player_rating, other_player_rating),
                score=score,
                total_return=total_return,
                n_games=n_games
            ))

    update_df = pd.DataFrame(update_array)
    summary_df = update_df.groupby("player_id", as_index=False).agg({
        "player_rating": "first",
        "expected": "sum",
        "score": "sum",
        "total_return": "first",
        "n_games": "first"
    })
    for _, row in summary_df.iterrows():
        player_id = row["player_id"]
        new_rating = elo_update(row["player_rating"], row["expected"], row["score"])

        # update basis and return stats
        game_basis = STARTING_VIRTUAL_CASH
        game_return = scoreboard[player_id]
        add_row("stockbets_rating",
                user_id=int(player_id) if player_id in user_ids else None,
                index_symbol=player_id if player_id in TRACKED_INDEXES else None,
                game_id=game_id,
                basis=float(game_basis),
                total_return=float(game_return),
                n_games=int(row["n_games"] + 1),
                rating=float(new_rating),
                update_type="game_end",
                timestamp=end)
