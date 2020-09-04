"""This script makes the canonical data for splits_game.sql reproducible. In "prod" mode it will download all the
required production files to csv. In "dev" mode these local files will be uploaded to the DB and turned into a MySQL
to be used during testing. USE ANY SCRIPT WITH EXTREME CAUTION, AND ONLY AFTER CHECKING WITH A SENIOR TEAM MEMBER"""
import os

import pandas as pd
from backend.database.db import engine
from backend.database.helpers import drop_all_tables

GAME_ID = 82
USER_ID = 1
MIN_TIME = 1598484949.23366
MAX_TIME = 1599236587.77923

if __name__ == '__main__':
    if os.getenv("ENV") == "prod":
        with engine.connect() as conn:
            games = pd.read_sql("SELECT * FROM games WHERE id = %s;", conn, params=[GAME_ID])
            game_status = pd.read_sql("SELECT * FROM game_status WHERE game_id = %s;", conn, params=[GAME_ID])
            game_balances = pd.read_sql("SELECT * FROM game_balances WHERE game_id = %s AND user_id = %s;", conn,
                                        params=[GAME_ID, USER_ID])
            symbols = game_balances["symbol"].unique().tolist()
            orders = pd.read_sql("SELECT * FROM orders WHERE game_id = %s AND user_id = %s;", conn,
                                 params=[GAME_ID, USER_ID])
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
                                 params=symbols + [MIN_TIME, MAX_TIME])
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

        # patch in stock splits by hand for now
        game_balances["stock_split_id"] = None
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "MUTE"][
            "stock_split_id"] = 1
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "PASS"][
            "stock_split_id"] = 2
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "WEBS"][
            "stock_split_id"] = 3
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "LABD"][
            "stock_split_id"] = 4
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "DRIP"][
            "stock_split_id"] = 5
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "SOXS"][
            "stock_split_id"] = 6
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "AAPL"][
            "stock_split_id"] = 27
        game_balances[(game_balances["transaction_type"] == "stock_split") & (game_balances["symbol"]) == "TSLA"][
            "stock_split_id"] = 28
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
            splits.to_sql("splits", conn, if_exists="replace", index=False)
            prices.to_sql("prices", conn, if_exists="replace", index=False)
        os.system("rm -rf database/fixtures/canonical_games/splits_game.sql")
        os.system("mysqldump -h db -uroot main > database/fixtures/canonical_games/splits_game.sql")
