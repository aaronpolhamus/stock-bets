"""This script makes the canonical data for game_id_82.sql reproducible. In "prod" mode it will download all the
required production files to csv. In "dev" mode these local files will be uploaded to the DB and turned into a MySQL
to be used during testing. USE ANY SCRIPT WITH EXTREME CAUTION, AND ONLY AFTER CHECKING WITH A SENIOR TEAM MEMBER"""
from argparse import ArgumentParser
import os

import pandas as pd
from backend.database.db import engine
from backend.database.helpers import drop_all_tables
from backend.logic.base import get_active_game_user_ids, get_game_start_and_end

parser = ArgumentParser()
parser.add_argument("--game_id", type=int)
args = parser.parse_args()


if __name__ == '__main__':
    if os.getenv("ENV") == "prod":
        with engine.connect() as conn:
            users_ids = user_ids = get_active_game_user_ids(args.game_id)
            min_time, max_time = get_game_start_and_end(args.game_id)

            games = pd.read_sql("SELECT * FROM games WHERE id = %s;", conn, params=[args.game_id])
            game_status = pd.read_sql("SELECT * FROM game_status WHERE game_id = %s;", conn, params=[args.game_id])
            game_balances = pd.read_sql(f"""
                SELECT * FROM game_balances 
                WHERE game_id = %s AND user_id IN ({", ".join(["%s"] * len(user_ids))});
                """, conn, params=[args.game_id] + list(user_ids))

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
            games.to_pickle("games.pkl")
            game_status.to_pickle("game_status.pkl")
            game_balances.to_pickle("game_balances.pkl")
            orders.to_pickle("orders.pkl")
            order_status.to_pickle("order_status.pkl")
            splits.to_pickle("splits.pkl")
            prices.to_pickle("prices.pkl")

    if os.getenv("ENV") == "dev":
        drop_all_tables()
        games = pd.read_pickle("games.pkl")
        game_status = pd.read_pickle("game_status.pkl")
        game_balances = pd.read_pickle("game_balances.pkl")
        orders = pd.read_pickle("orders.pkl")
        order_status = pd.read_pickle("order_status.pkl")
        splits = pd.read_pickle("splits.pkl")
        prices = pd.read_pickle("prices.pkl")
        with engine.connect() as conn:
            games.to_sql("games", conn, if_exists="replace", index=False)
            game_status.to_sql("game_status", conn, if_exists="replace", index=False)
            game_balances.to_sql("game_balances", conn, if_exists="replace", index=False)
            orders.to_sql("orders", conn, if_exists="replace", index=False)
            order_status.to_sql("order_status", conn, if_exists="replace", index=False)
            splits.to_sql("stock_splits", conn, if_exists="replace", index=False)
            prices.to_sql("prices", conn, if_exists="replace", index=False)
        os.system(f"rm -rf database/fixtures/canonical_games/game_id_{args.game_id}.sql")
        os.system(f"mysqldump -h db -uroot main > database/fixtures/canonical_games/game_id_{args.game_id}.sql")
