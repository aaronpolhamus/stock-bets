import json
from datetime import timedelta
from unittest.mock import patch

from backend.database.fixtures.make_historical_price_data import make_stock_data_records
from backend.database.helpers import add_row
from backend.logic.base import (
    get_all_game_users_ids,
    get_schedule_start_and_end,
    nyse,
    posix_to_datetime
)
from backend.logic.winners import calculate_and_pack_game_metrics
from backend.logic.visuals import (
    make_chart_json,
    compile_and_pack_player_leaderboard,
    make_the_field_charts,
    serialize_and_pack_order_details,
    serialize_and_pack_portfolio_details,
    serialize_and_pack_order_performance_chart,
    serialize_and_pack_winners_table
)
from backend.bi.report_logic import (
    serialize_and_pack_games_per_user_chart,
    make_games_per_user_data,
    ORDERS_PER_ACTIVE_USER_PREFIX
)
from backend.tasks.redis import rds
from config import Config

SECONDS_IN_A_DAY = 60 * 60 * 24
price_records, index_records = make_stock_data_records()
simulation_start_time = min([record["timestamp"] for record in price_records])
simulation_end_time = max([record["timestamp"] for record in price_records])


def get_beginning_of_next_trading_day(ref_time):
    current_day = posix_to_datetime(ref_time)
    schedule = nyse.schedule(current_day, current_day)
    while schedule.empty:
        current_day += timedelta(days=1)
        schedule = nyse.schedule(current_day, current_day)
    start_day, _ = get_schedule_start_and_end(schedule)
    return start_day


def get_stock_start_price(symbol, records=price_records, order_time=simulation_start_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][0]
    return stock_record["price"]


def get_stock_finish_price(symbol, records=price_records, order_time=simulation_end_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][-1]
    return stock_record["price"]


def refresh_table(table_name):
    mock_entry = MOCK_DATA.get(table_name)
    for entry in mock_entry:
        add_row(table_name, **entry)


# Mocked data: These are listed in order so that we can tear down and build up while respecting foreign key constraints
MOCK_DATA = {
    "users": [
        {"name": Config.TEST_CASE_NAME, "email": Config.TEST_CASE_EMAIL,
         "profile_pic": "https://i.imgur.com/P5LO9v4.png",
         "username": "cheetos", "created_at": 1588307605.0, "provider": "google",
         "resource_uuid": Config.TEST_CASE_UUID},
        {"name": "dummy", "email": "dummy@example.test",
         "profile_pic": "https://cadena100-cdnmed.agilecontent.com/resources/jpg/8/2/1546649423628.jpg",
         "username": None, "created_at": 1588702321.0, "provider": "google", "resource_uuid": "efg456"},
        {"name": "Eddie", "email": "eddie@example.test",
         "profile_pic": "https://animalark.org/wp-content/uploads/2016/03/181Cheetahs12.jpg", "username": "toofast",
         "created_at": 1588307928.0, "provider": "twitter", "resource_uuid": "hij789"},
        {"name": "Mike", "email": "mike@example.test",
         "profile_pic": "https://gitedumoulinavent.com/wp-content/uploads/pexels-photo-1230302.jpeg",
         "username": "miguel", "created_at": 1588308080.0, "provider": "facebook",
         "resource_uuid": "klm101"},
        {"name": "Eli", "email": "eli@example.test",
         "profile_pic": "https://nationalpostcom.files.wordpress.com/2018/11/gettyimages-1067958662.jpg",
         "username": "murcitdev", "created_at": 1588308406.0, "provider": "google",
         "resource_uuid": "nop112"},
        {"name": "dummy2", "email": "dummy2@example.test",
         "profile_pic": "https://cadena100-cdnmed.agilecontent.com/resources/jpg/8/2/1546649423628.jpg",
         "username": "dummy2", "created_at": 1588308407.0, "provider": "google", "resource_uuid": "qrs131"},
        {"name": "jack sparrow", "email": "jack@black.pearl",
         "profile_pic": "https://i2.wp.com/www.californiaherald.com/wp-content/uploads/2020/03/jack-sparrow.jpg",
         "username": "jack", "created_at": 1591562299, "provider": "google", "resource_uuid": "tuv415"},
        {"name": "johnnie walker", "email": "johnnie@walker.com",
         "profile_pic": "https://www.brandemia.org/sites/default/files/sites/default/files/johnnie_walker_nuevo_logo.png",
         "username": "johnnie", "created_at": 1591562299, "provider": "google", "resource_uuid": "tuv415"},
        {"name": "jadis", "email": "jadis@rick.lives",
         "profile_pic": "https://vignette.wikia.nocookie.net/villains/images/7/78/Season_eight_jadis.png",
         "username": "jadis", "created_at": 1591562299, "provider": "google", "resource_uuid": "wxy617"},
    ],

    "games": [
        {"title": "fervent swartz", "game_mode": "multi_player", "duration": 365, "buy_in": 100, "n_rebuys": 2,
         "benchmark": "sharpe_ratio", "side_bets_perc": 50, "side_bets_period": "monthly", "creator_id": 4,
         "invite_window": 1589368380.0},
        {"title": "max aggression", "game_mode": "multi_player", "duration": 1, "buy_in": 100_000, "n_rebuys": 0,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 3,
         "invite_window": 1589368380.0},
        {"title": "test game", "game_mode": "multi_player", "duration": 14, "buy_in": 100, "n_rebuys": 3,
         "benchmark": "return_ratio", "side_bets_perc": 50, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": 1589368380.0},
        {"title": "test user excluded", "game_mode": "multi_player", "duration": 60, "buy_in": 20, "n_rebuys": 100,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0},
        {"title": "valiant roset", "game_mode": "multi_player", "duration": 60, "buy_in": 20, "n_rebuys": 100,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0}
    ],
    "game_status": [
        {"game_id": 1, "status": "pending", "timestamp": 1589195580.0, "users": [1, 3, 4, 5]},
        {"game_id": 2, "status": "pending", "timestamp": 1589368260.0, "users": [1, 3]},
        {"game_id": 3, "status": "pending", "timestamp": simulation_start_time, "users": [1, 3, 4]},
        {"game_id": 3, "status": "active", "timestamp": simulation_start_time, "users": [1, 3, 4]},
        {"game_id": 4, "status": "pending", "timestamp": simulation_start_time, "users": [3, 4, 5]},
        {"game_id": 4, "status": "active", "timestamp": simulation_start_time, "users": [3, 4, 5]},
        {"game_id": 5, "status": "pending", "timestamp": 1589368260.0, "users": [1, 3, 4, 5]}
    ],
    "game_invites": [
        {"game_id": 1, "user_id": 4, "status": "joined", "timestamp": 1589195580.0},
        {"game_id": 1, "user_id": 1, "status": "invited", "timestamp": 1589195580.0},
        {"game_id": 1, "user_id": 3, "status": "invited", "timestamp": 1589195580.0},
        {"game_id": 1, "user_id": 5, "status": "invited", "timestamp": 1589195580.0},
        {"game_id": 2, "user_id": 3, "status": "joined", "timestamp": 1589368260.0},
        {"game_id": 2, "user_id": 1, "status": "invited", "timestamp": 1589368260.0},
        {"game_id": 3, "user_id": 1, "status": "joined", "timestamp": simulation_start_time},
        {"game_id": 3, "user_id": 3, "status": "invited", "timestamp": simulation_start_time},
        {"game_id": 3, "user_id": 4, "status": "invited", "timestamp": simulation_start_time},
        {"game_id": 3, "user_id": 3, "status": "joined", "timestamp": simulation_start_time},
        {"game_id": 3, "user_id": 4, "status": "joined", "timestamp": simulation_start_time},
        {"game_id": 4, "user_id": 5, "status": "joined", "timestamp": 1589281860.0},
        {"game_id": 4, "user_id": 3, "status": "invited", "timestamp": 1589281860.0},
        {"game_id": 4, "user_id": 4, "status": "invited", "timestamp": 1589281860.0},
        {"game_id": 4, "user_id": 3, "status": "joined", "timestamp": 1589368260.0},
        {"game_id": 4, "user_id": 4, "status": "declined", "timestamp": 1589368260.0},
        {"game_id": 1, "user_id": 1, "status": "declined", "timestamp": 1590363478.0},
        {"game_id": 1, "user_id": 3, "status": "joined", "timestamp": 1590363478.0},
        {"game_id": 2, "user_id": 1, "status": "declined", "timestamp": 1589368260.0},
        {"game_id": 5, "user_id": 5, "status": "joined", "timestamp": 1589368260.0},
        {"game_id": 5, "user_id": 1, "status": "invited", "timestamp": 1589368260.0},
        {"game_id": 5, "user_id": 3, "status": "invited", "timestamp": 1589368260.0},
        {"game_id": 5, "user_id": 4, "status": "invited", "timestamp": 1589368260.0},
    ],
    "symbols": [
        {"symbol": "MSFT", "name": "MICROSOFT"},
        {"symbol": "AAPL", "name": "APPLE"},
        {"symbol": "AMZN", "name": "AMAZON"},
        {"symbol": "GOOG", "name": "ALPHABET CLASS C"},
        {"symbol": "GOOGL", "name": "ALPHABET CLASS A"},
        {"symbol": "FB", "name": "FACEBOOK"},
        {"symbol": "BRK.B", "name": "BERKSHIRE HATHAWAY CLASS B"},
        {"symbol": "JNJ", "name": "JNJ"},
        {"symbol": "V", "name": "VISA"},
        {"symbol": "PG", "name": "PROCTOR AND GAMBLE"},
        {"symbol": "JPM", "name": "JP MORGAN"},
        {"symbol": "UNH", "name": "UNITED HEALTH"},
        {"symbol": "MA", "name": "MASTERCARD"},
        {"symbol": "INTC", "name": "INTEL"},
        {"symbol": "VZ", "name": "VERIZON"},
        {"symbol": "HD", "name": "HOME DEPOT"},
        {"symbol": "T", "name": "AT&T"},
        {"symbol": "PFE", "name": "PFIZER"},
        {"symbol": "MRK", "name": "MERCK"},
        {"symbol": "PEP", "name": "PEPSICO"},
        {"symbol": "TSLA", "name": "TESLA"},
        {"symbol": "LYFT", "name": "LYFT"},
        {"symbol": "SPXU", "name": "SPY PROSHARES ISHORT 3X"},
        {"symbol": "MELI", "name": "MERCADO LIBRE"},
        {"symbol": "NVDA", "name": "NVIDIA"},
        {"symbol": "NKE", "name": "NIKE"},
    ],
    "prices": price_records,
    "indexes": index_records,
    "orders": [
        # game 3, user id #1
        {"user_id": 1, "game_id": 3, "symbol": "AMZN", "buy_or_sell": "buy", "quantity": 10,
         "price": get_stock_start_price("AMZN"), "order_type": "market", "time_in_force": "day"},  # 1
        {"user_id": 1, "game_id": 3, "symbol": "TSLA", "buy_or_sell": "buy", "quantity": 35,
         "price": get_stock_start_price("TSLA"), "order_type": "market", "time_in_force": "day"},  # 2
        {"user_id": 1, "game_id": 3, "symbol": "LYFT", "buy_or_sell": "buy", "quantity": 700,
         "price": get_stock_start_price("LYFT"), "order_type": "market", "time_in_force": "day"},  # 3
        {"user_id": 1, "game_id": 3, "symbol": "SPXU", "buy_or_sell": "buy", "quantity": 1200,
         "price": get_stock_start_price("SPXU"), "order_type": "market", "time_in_force": "day"},  # 4

        # game 3, user id #3
        {"user_id": 3, "game_id": 3, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 130,
         "price": get_stock_start_price("NVDA"), "order_type": "market", "time_in_force": "day"},  # 5
        {"user_id": 3, "game_id": 3, "symbol": "NKE", "buy_or_sell": "buy", "quantity": 400,
         "price": get_stock_start_price("NKE"), "order_type": "market", "time_in_force": "day"},  # 6

        # game 3, user id #4
        {"user_id": 4, "game_id": 3, "symbol": "MELI", "buy_or_sell": "buy", "quantity": 107,
         "price": get_stock_start_price("MELI"), "order_type": "market", "time_in_force": "day"},  # 7

        # game 3, user id #1, follow-on orders
        {"user_id": 1, "game_id": 3, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 8,
         "price": get_stock_start_price("NVDA") * 1.05, "order_type": "stop", "time_in_force": "until_cancelled"},  # 8
        {"user_id": 1, "game_id": 3, "symbol": "MELI", "buy_or_sell": "buy", "quantity": 2,
         "price": get_stock_finish_price("MELI") * 0.9, "order_type": "limit", "time_in_force": "until_cancelled"},  # 9
        {"user_id": 1, "game_id": 3, "symbol": "SPXU", "buy_or_sell": "sell", "quantity": 300,
         "price": get_stock_finish_price("SPXU") * 0.75, "order_type": "stop", "time_in_force": "until_cancelled"},
        # 10
        {"user_id": 1, "game_id": 3, "symbol": "AMZN", "buy_or_sell": "sell", "quantity": 4,
         "price": get_stock_finish_price("AMZN"), "order_type": "market", "time_in_force": "day"},  # 11

        # game 4, user id #5
        {"user_id": 5, "game_id": 4, "symbol": "BABA", "buy_or_sell": "buy", "quantity": 3,
         "price": 201.72, "order_type": "market", "time_in_force": "day"},  # 12
        # game 4, user id #4
        {"user_id": 4, "game_id": 4, "symbol": "SQQQ", "buy_or_sell": "buy", "quantity": 3_128,
         "price": 7.99, "order_type": "market", "time_in_force": "day"},  # 13
        {"user_id": 4, "game_id": 4, "symbol": "SPXU", "buy_or_sell": "buy", "quantity": 2_131,
         "price": 11.73, "order_type": "market", "time_in_force": "day"},  # 14
    ],
    "order_status": [
        {"order_id": 1, "timestamp": simulation_start_time, "status": "pending"},  # 1
        {"order_id": 1, "timestamp": simulation_start_time, "status": "fulfilled",  # 2
         "clear_price": get_stock_start_price("AMZN")},
        {"order_id": 2, "timestamp": simulation_start_time, "status": "pending"},  # 3
        {"order_id": 2, "timestamp": simulation_start_time, "status": "fulfilled",  # 4
         "clear_price": get_stock_start_price("TSLA")},
        {"order_id": 3, "timestamp": simulation_start_time, "status": "pending"},  # 5
        {"order_id": 3, "timestamp": simulation_start_time, "status": "fulfilled",  # 6
         "clear_price": get_stock_start_price("LYFT")},
        {"order_id": 4, "timestamp": simulation_start_time, "status": "pending"},  # 7
        {"order_id": 4, "timestamp": simulation_start_time, "status": "fulfilled",  # 8
         "clear_price": get_stock_start_price("SPXU")},
        {"order_id": 5, "timestamp": simulation_start_time, "status": "pending"},  # 9
        {"order_id": 5, "timestamp": simulation_start_time, "status": "fulfilled",  # 10
         "clear_price": get_stock_start_price("NVDA")},
        {"order_id": 6, "timestamp": simulation_start_time, "status": "pending"},  # 11
        {"order_id": 6, "timestamp": simulation_start_time, "status": "fulfilled",  # 12
         "clear_price": get_stock_start_price("NKE")},
        {"order_id": 7, "timestamp": simulation_start_time, "status": "pending"},  # 13
        {"order_id": 7, "timestamp": simulation_start_time, "status": "fulfilled",  # 14
         "clear_price": get_stock_start_price("MELI")},
        {"order_id": 8, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 15
        {"order_id": 8, "timestamp": get_beginning_of_next_trading_day(simulation_start_time + SECONDS_IN_A_DAY),
         "status": "fulfilled", "clear_price": get_stock_start_price("NVDA") * 1.05},  # 16
        {"order_id": 9, "timestamp": simulation_end_time, "status": "pending", "clear_price": None},  # 17
        {"order_id": 10, "timestamp": simulation_end_time, "status": "pending", "clear_price": None},  # 18
        {"order_id": 11, "timestamp": simulation_end_time, "status": "pending"},  # 19
        {"order_id": 11, "timestamp": simulation_end_time, "status": "fulfilled",  # 20
         "clear_price": get_stock_finish_price("AMZN")},
        {"order_id": 12, "timestamp": simulation_start_time, "status": "pending"},  # 21
        {"order_id": 12, "timestamp": simulation_start_time, "status": "fulfilled"},  # 22
        {"order_id": 13, "timestamp": 1592572846.5938, "status": "pending"},  # 23
        {"order_id": 14, "timestamp": 1592572846.5938, "status": "pending"},  # 24
    ],
    "game_balances": [
        # Game 3, user id #1
        {"user_id": 1, "game_id": 3, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 2, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 100_000 - get_stock_start_price("AMZN") * 10, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 2, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 10, "symbol": "AMZN"},

        {"user_id": 1, "game_id": 3, "order_status_id": 4, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash",
         "balance": 100_000 - get_stock_start_price("AMZN") * 10 - get_stock_start_price("TSLA") * 35, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 4, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 35, "symbol": "TSLA"},

        {"user_id": 1, "game_id": 3, "order_status_id": 6, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash",
         "balance": 100_000 - get_stock_start_price("AMZN") * 10 - get_stock_start_price(
             "TSLA") * 35 - get_stock_start_price("LYFT") * 700, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 6, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 700, "symbol": "LYFT"},

        {"user_id": 1, "game_id": 3, "order_status_id": 8, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash",
         "balance": 100_000 - get_stock_start_price("AMZN") * 10 - get_stock_start_price(
             "TSLA") * 35 - get_stock_start_price("LYFT") * 700 - get_stock_start_price("SPXU") * 1200, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 8, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 1200, "symbol": "SPXU"},

        # Game 3, user id #3
        {"user_id": 3, "game_id": 3, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 10, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 52679.10716, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 10, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 130, "symbol": "NVDA"},
        {"user_id": 3, "game_id": 3, "order_status_id": 12, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 14130.324760000003, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 12, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 400, "symbol": "NKE"},

        # Game 3, user id #4
        {"user_id": 4, "game_id": 3, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 4, "game_id": 3, "order_status_id": 14, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 8130.831265999994, "symbol": None},
        {"user_id": 4, "game_id": 3, "order_status_id": 14, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 107, "symbol": "MELI"},

        # Game 3, user id #1, subsequent plays
        {"user_id": 1, "game_id": 3, "order_status_id": 16,
         "timestamp": get_beginning_of_next_trading_day(simulation_start_time + SECONDS_IN_A_DAY),
         "balance_type": "virtual_cash",
         "balance": 100_000 - get_stock_start_price("AMZN") * 10 - get_stock_start_price(
             "TSLA") * 35 - get_stock_start_price("LYFT") * 700 - get_stock_start_price(
             "SPXU") * 1200 - get_stock_start_price("NVDA") * 1.05 * 8, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 16,
         "timestamp": get_beginning_of_next_trading_day(simulation_start_time + SECONDS_IN_A_DAY),
         "balance_type": "virtual_stock", "balance": 8, "symbol": "NVDA"},

        {"user_id": 1, "game_id": 3, "order_status_id": 20, "timestamp": simulation_end_time,
         "balance_type": "virtual_cash",
         "balance": 100_000 - get_stock_start_price("AMZN") * 10 - get_stock_start_price(
             "TSLA") * 35 - get_stock_start_price("LYFT") * 700 - get_stock_start_price(
             "SPXU") * 1200 - get_stock_start_price("NVDA") * 1.05 * 8 + get_stock_finish_price("AMZN") * 4,
         "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 20, "timestamp": simulation_end_time,
         "balance_type": "virtual_stock", "balance": 6, "symbol": "AMZN"},

        # Game 4, setup
        {"user_id": 5, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": 13, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 99798.28, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": 13, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 1, "symbol": "BABA"},
        {"user_id": 3, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 1_000_000, "symbol": None},
        {"user_id": 4, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 1_000_000, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": 1_000_000, "symbol": None},
    ],
    "friends": [
        {"requester_id": 1, "invited_id": 3, "status": "invited", "timestamp": 1589758324},
        {"requester_id": 1, "invited_id": 3, "status": "accepted", "timestamp": 1590363091},
        {"requester_id": 1, "invited_id": 4, "status": "invited", "timestamp": 1589758324},
        {"requester_id": 1, "invited_id": 4, "status": "accepted", "timestamp": 1590363091},
        {"requester_id": 5, "invited_id": 1, "status": "invited", "timestamp": 1589758324},
        {"requester_id": 3, "invited_id": 4, "status": "invited", "timestamp": 1589758324},
        {"requester_id": 3, "invited_id": 4, "status": "accepted", "timestamp": 1590363091},
        {"requester_id": 3, "invited_id": 5, "status": "invited", "timestamp": 1589758324},
        {"requester_id": 3, "invited_id": 5, "status": "accepted", "timestamp": 1590363091},
        {"requester_id": 5, "invited_id": 4, "status": "invited", "timestamp": 1589758324},
        {"requester_id": 5, "invited_id": 4, "status": "accepted", "timestamp": 1590363091},
        {"requester_id": 1, "invited_id": 7, "status": "invited", "timestamp": 1591561793},
    ]
}


def make_mock_data():
    table_names = MOCK_DATA.keys()
    for table in table_names:
        refresh_table(table)


def make_redis_mocks():
    game_id = 3
    with patch("backend.logic.base.time") as mock_base_time:
        mock_base_time.time.return_value = simulation_end_time

        # performance metrics
        calculate_and_pack_game_metrics(game_id)

        # leaderboard
        compile_and_pack_player_leaderboard(game_id)

        # the field and balance charts
        make_the_field_charts(game_id)

        # tables and performance breakout charts
        user_ids = get_all_game_users_ids(game_id)
        for user_id in user_ids:
            # game/user-level assets
            serialize_and_pack_order_details(game_id, user_id)
            serialize_and_pack_portfolio_details(game_id, user_id)
            serialize_and_pack_order_performance_chart(game_id, user_id)

        # winners/payouts table
        serialize_and_pack_winners_table(game_id)

    # key metrics for the admin panel
    serialize_and_pack_games_per_user_chart()
    # TODO: This is a quick hack to get the admin panel working in dev. Fix at some point
    df = make_games_per_user_data()
    chart_json = make_chart_json(df, "cohort", "percentage", "game_count")
    rds.set(f"{ORDERS_PER_ACTIVE_USER_PREFIX}", json.dumps(chart_json))


if __name__ == '__main__':
    make_mock_data()
