import os
from argparse import ArgumentParser

import pandas as pd
from backend.database.db import (
    db,
    engine
)
from backend.database.helpers import drop_all_tables
from backend.logic.base import (
    get_active_game_user_ids,
    get_game_start_and_end,
    SECONDS_IN_A_DAY
)

parser = ArgumentParser()
parser.add_argument("--game_id", type=int)
args = parser.parse_args()

if __name__ == '__main__':
    if os.getenv("ENV") == "prod":
        with engine.connect() as conn:
            user_ids = get_active_game_user_ids(args.game_id)
            min_time, max_time = get_game_start_and_end(args.game_id)

            games = pd.read_sql("SELECT * FROM games WHERE id = %s;", conn, params=[args.game_id])
            game_status = pd.read_sql("SELECT * FROM game_status WHERE game_id = %s;", conn, params=[args.game_id])
            game_balances = pd.read_sql(f"""
                SELECT * FROM game_balances 
                WHERE game_id = %s AND user_id IN ({", ".join(["%s"] * len(user_ids))});
                """, conn, params=[args.game_id] + list(user_ids))
            game_invites = pd.read_sql(f"""
                SELECT * FROM game_invites
                WHERE user_id IN ({", ".join(["%s"] * len(user_ids))}); 
            """, conn, params=user_ids)
            symbols = game_balances["symbol"].unique().tolist()
            orders = pd.read_sql(f"""
                SELECT * FROM orders 
                WHERE game_id = %s AND user_id IN ({", ".join(["%s"] * len(user_ids))})
                """, conn, params=[args.game_id] + list(user_ids))
            order_ids = orders["id"].unique().tolist()
            order_status = pd.read_sql(f"""
              SELECT * FROM order_status
              WHERE order_id IN ({",".join(["%s"] * len(order_ids))});""", conn, params=order_ids)
            splits = pd.read_sql(f"""
              SELECT * FROM stock_splits
              WHERE symbol IN ({",".join(["%s"] * len(symbols))});""", conn, params=symbols)
            prices = pd.read_sql(f"""
              SELECT * FROM prices
              WHERE symbol IN ({",".join(["%s"] * len(symbols))}) AND timestamp >= %s AND timestamp <= %s;""", conn,
                                 params=symbols + [min_time, max_time])
            indexes = pd.read_sql(f"SELECT * FROM indexes WHERE timestamp >= %s AND timestamp <= %s", conn,
                                  params=[min_time - 4 * SECONDS_IN_A_DAY, max_time])
            index_metadata = pd.read_sql("SELECT * FROM index_metadata;", conn)
            users = pd.read_sql(f"""
                SELECT id, name, email, profile_pic, username, created_at, provider FROM users 
                WHERE id IN ({", ".join(["%s"] * len(user_ids))});""", conn, params=user_ids)
            stockbets_rating = pd.read_sql(f"""
                SELECT id, sr.user_id, index_symbol, game_id, rating, update_type, timestamp FROM stockbets_rating sr
                INNER JOIN (
                    SELECT user_id, MIN(id) AS min_id
                    FROM stockbets_rating 
                    WHERE user_id IN ({", ".join(["%s"] * len(user_ids))})
                    GROUP BY user_id
                ) grouped_sr ON grouped_sr.min_id = sr.id;""", conn, params=user_ids)

        games.to_pickle("games.pkl")
        game_status.to_pickle("game_status.pkl")
        game_balances.to_pickle("game_balances.pkl")
        game_invites.to_pickle("game_invites.pkl")
        orders.to_pickle("orders.pkl")
        order_status.to_pickle("order_status.pkl")
        splits.to_pickle("splits.pkl")
        prices.to_pickle("prices.pkl")
        indexes.to_pickle("indexes.pkl")
        index_metadata.to_pickle("index_metadata.pkl")
        users.to_pickle("users.pkl")
        stockbets_rating.to_pickle("stockbets_rating.pkl")

    if os.getenv("ENV") == "dev":
        drop_all_tables()
        games = pd.read_pickle("games.pkl")
        game_status = pd.read_pickle("game_status.pkl")
        game_balances = pd.read_pickle("game_balances.pkl")
        game_invites = pd.read_pickle("game_invites.pkl")
        orders = pd.read_pickle("orders.pkl")
        order_status = pd.read_pickle("order_status.pkl")
        splits = pd.read_pickle("splits.pkl")
        prices = pd.read_pickle("prices.pkl")
        indexes = pd.read_pickle("indexes.pkl")
        indexe_metadata = pd.read_pickle("index_metadata.pkl")
        users = pd.read_pickle("users.pkl")
        stockbets_rating = pd.read_pickle("stockbets_rating.pkl")
        with engine.connect() as conn:
            games.to_sql("games", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            game_status.to_sql("game_status", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            game_balances.to_sql("game_balances", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            game_invites.to_sql("game_invites", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            orders.to_sql("orders", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            order_status.to_sql("order_status", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            splits.to_sql("stock_splits", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            prices.to_sql("prices", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            indexes.to_sql("indexes", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            indexe_metadata.to_sql("index_metadata", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            users.to_sql("users", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
            stockbets_rating.to_sql("stockbets_rating", conn, if_exists="replace", index=False, dtype={"id": db.Integer})
        os.system(f"rm -rf database/fixtures/canonical_games/game_id_{args.game_id}.sql")
        os.system(f"mysqldump -h db -uroot main > database/fixtures/canonical_games/game_id_{args.game_id}.sql")
