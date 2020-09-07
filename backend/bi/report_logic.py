import json
import pandas as pd
import time

from backend.database.db import engine
from backend.logic.base import posix_to_datetime
from backend.logic.visuals import make_chart_json
from backend.tasks import s3_cache

GAMES_PER_USER_PREFIX = "game_per_user"
ORDERS_PER_ACTIVE_USER_PREFIX = "orders_per_active_user"

# n games per user by cohort
# --------------------------


def inflate_game_status_rows(row):
    """This function takes the users entries for each game and turns each one into a row in a table"""
    ls = [dict(game_id=row.iloc[0]["game_id"], user_id=user_id) for user_id in row.iloc[0]["users"]]
    return pd.DataFrame(ls)


def make_games_per_user_data():

    # get user and game_status data
    with engine.connect() as conn:
        users = pd.read_sql("SELECT id, created_at FROM users;", conn)
        game_status = pd.read_sql("""
            SELECT game_id, status, users FROM game_status 
            WHERE status = 'active'""", conn)  # Note: this doesn't discriminate between active and finished games
        game_status["users"] = game_status["users"].apply(lambda x: json.loads(x))

    gs = game_status.groupby("game_id").apply(lambda row: inflate_game_status_rows(row)).reset_index(drop=True)
    counts = gs.groupby("user_id", as_index=False).count().rename(columns={"game_id": "game_count"})

    users["created_at"] = users["created_at"].apply(lambda x: posix_to_datetime(x))
    users["period"] = users["created_at"].dt.to_period("M")
    label_df = users.groupby("period", as_index=False)["id"].count()
    label_df["cohort"] = label_df["period"].astype(str) + " [" + label_df["id"].astype(str) + "]"
    users = users.merge(label_df[["period", "cohort"]])
    df = users.merge(counts, how="left", left_on="id", right_on="user_id").fillna(0)

    cohort_data_array = []
    for cohort in df["cohort"].unique():
        cohort_df = df[df["cohort"] == cohort]
        population = cohort_df.shape[0]
        for game_count in range(int(cohort_df["game_count"].max() + 1)):
            entry = dict(
                cohort=cohort,
                game_count=float(game_count),
                percentage=float((cohort_df["game_count"] >= game_count).sum() / population)
            )
            cohort_data_array.append(entry)

    return pd.DataFrame(cohort_data_array)


def serialize_and_pack_games_per_user_chart():
    df = make_games_per_user_data()
    chart_json = make_chart_json(df, "cohort", "percentage", "game_count")
    s3_cache.set(f"{GAMES_PER_USER_PREFIX}", json.dumps(chart_json))

# average trading volume per active user
# --------------------------------------


def expand_counts(subset):
    return subset.set_index("timestamp")["user_count"].resample("D").ffill().bfill()


def make_orders_per_active_user():
    # get total number of active users on a given day (in at least one active game, or in a live single player mode)
    with engine.connect() as conn:
        game_status = pd.read_sql("""
            SELECT game_id, users, timestamp
            FROM game_status WHERE status NOT IN ('expired', 'pending')""", conn)
        order_status = pd.read_sql("SELECT id, timestamp FROM order_status WHERE status = 'pending';", conn)

    game_status["timestamp"] = game_status["timestamp"].apply(lambda x: posix_to_datetime(x))
    game_status["users"] = game_status["users"].apply(lambda x: json.loads(x))
    game_status["user_count"] = game_status["users"].apply(lambda x: len(x))

    # get total number of active users per day
    complete_counts_array = []
    for game_id in game_status["game_id"].unique():
        game_subset = game_status[game_status["game_id"] == game_id]
        if game_subset.shape == 2:
            complete_counts_array += game_subset[["user_count", "timestamp"]].to_dict(orient="records")
            continue
        user_count = game_subset.iloc[0]["user_count"]
        original_entry = dict(user_count=user_count, timestamp=game_subset.iloc[0]["timestamp"], game_id=game_id)
        bookend = dict(user_count=user_count, timestamp=posix_to_datetime(time.time()), game_id=game_id)
        complete_counts_array += [original_entry, bookend]

    user_count_df = pd.DataFrame(complete_counts_array)
    expanded_df = user_count_df.groupby("game_id").apply(expand_counts)
    expanded_df.index = expanded_df.index.droplevel(0)
    daily_active_users = expanded_df.resample("D").sum()

    order_status["timestamp"] = order_status["timestamp"].apply(lambda x: posix_to_datetime(x))
    order_status.set_index("timestamp", inplace=True)
    order_totals = order_status.resample("D").count()

    df = pd.concat([daily_active_users, order_totals], axis=1)
    df["orders_per_users"] = df["id"] / df["user_count"]
    df.fillna(0, inplace=True)
    return df.reset_index()


def serialize_and_pack_orders_per_active_user():
    df = make_orders_per_active_user()
    df["series_label"] = "Orders per active user"
    chart_json = make_chart_json(df, "series_label", "orders_per_users", "timestamp")
    s3_cache.set(f"{ORDERS_PER_ACTIVE_USER_PREFIX}", json.dumps(chart_json))
