"""mock_data.py is our test data factory. running it for ever test is expensive, so we use it at the very beginning of
test runner to construct a .sql data dump that we can quickly scan into the DB.
"""
import json
from datetime import timedelta
from io import BytesIO
from sqlalchemy import MetaData
from unittest.mock import patch

from backend.bi.report_logic import (
    serialize_and_pack_games_per_user_chart,
    make_games_per_user_data,
    ORDERS_PER_ACTIVE_USER_PREFIX
)
from backend.config import Config
from backend.database.db import engine
from backend.database.fixtures.make_historical_price_data import make_stock_data_records
from backend.database.helpers import (
    add_row,
    aws_client
)
from backend.logic.base import (
    STARTING_VIRTUAL_CASH,
    SECONDS_IN_A_DAY,
    get_schedule_start_and_end,
    get_trading_calendar,
    posix_to_datetime
)
from backend.logic.games import (
    init_game_assets,
    DEFAULT_INVITE_OPEN_WINDOW
)
from backend.logic.visuals import (
    make_chart_json,
    serialize_and_pack_rankings,
    TRACKED_INDEXES
)
from backend.tasks import s3_cache
from backend.logic.metrics import STARTING_ELO_SCORE

price_records, index_records = make_stock_data_records()
simulation_start_time = min([record["timestamp"] for record in price_records])
simulation_end_time = max([record["timestamp"] for record in price_records])


def get_beginning_of_next_trading_day(ref_time):
    ref_day = posix_to_datetime(ref_time).date()
    schedule = get_trading_calendar(ref_day, ref_day)
    while schedule.empty:
        ref_day += timedelta(days=1)
        schedule = get_trading_calendar(ref_day, ref_day)
    start_day, _ = get_schedule_start_and_end(schedule)
    return start_day


def get_stock_start_price(symbol, records=price_records, order_time=simulation_start_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][0]
    return stock_record["price"]


def get_stock_finish_price(symbol, records=price_records, order_time=simulation_end_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][-1]
    return stock_record["price"]


# Mocked data: These are listed in order so that we can tear down and build up while respecting foreign key constraints
pics_ep = f"{Config.AWS_PUBLIC_ENDPOINT}/{Config.AWS_PUBLIC_BUCKET_NAME}/profile_pics"
USER_DATA = [
    {"name": Config.TEST_CASE_NAME, "email": Config.TEST_CASE_EMAIL, "profile_pic": f"{pics_ep}/test_user.png",
     "username": "cheetos", "created_at": 1588307605.0, "provider": "google",
     "resource_uuid": Config.TEST_CASE_UUID},
    {"name": "dummy", "email": "dummy@example.test", "profile_pic": f"{pics_ep}/dummy.jpg", "username": None,
     "created_at": 1588702321.0, "provider": "google", "resource_uuid": "efg456"},
    {"name": "Eddie", "email": "eddie@example.test", "profile_pic": f"{pics_ep}/toofast.jpg", "username": "toofast",
     "created_at": 1588307928.0, "provider": "twitter", "resource_uuid": "hij789"},
    {"name": "Mike", "email": "mike@example.test", "profile_pic": f"{pics_ep}/miguel.jpg", "username": "miguel",
     "created_at": 1588308080.0, "provider": "facebook", "resource_uuid": "klm101"},
    {"name": "Eli", "email": "eli@example.test", "profile_pic": f"{pics_ep}/murcitdev.jpg", "username": "murcitdev",
     "created_at": 1588308406.0, "provider": "google", "resource_uuid": "nop112"},
    {"name": "dummy2", "email": "dummy2@example.test", "profile_pic": f"{pics_ep}/dummy.jpg", "username": "dummy2",
     "created_at": 1588308407.0, "provider": "google", "resource_uuid": "qrs131"},
    {"name": "jack sparrow", "email": "jack@black.pearl", "profile_pic": f"{pics_ep}/jack.jpg", "username": "jack",
     "created_at": 1591562299, "provider": "google", "resource_uuid": "tuv415"},
    {"name": "johnnie walker", "email": "johnnie@walker.com", "profile_pic": f"{pics_ep}/johnnie.png",
     "username": "johnnie", "created_at": 1591562299, "provider": "google", "resource_uuid": "tuv415"},
    {"name": "jadis", "email": "jadis@rick.lives", "profile_pic": f"{pics_ep}/jadis.png", "username": "jadis",
     "created_at": 1591562299, "provider": "google", "resource_uuid": "wxy617"},
    {"name": "minion", "email": "minion1@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion1", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion2@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion2", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion3@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion3", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion4@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion4", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion5@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion5", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion6@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion6", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion7@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion7", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion8@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion8", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion9@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion9", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion10@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion10", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion11@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion11", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion12@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion12", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion13@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion13", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion14@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion14", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion15@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion15", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion16@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion16", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion17@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion17", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion18@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion18", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion19@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion19", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion20@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion20", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion21@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion21", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion22@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion22", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion23@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion23", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion24@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion24", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion25@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion25", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion26@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion26", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion27@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion27", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion28@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion28", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion29@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion29", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
    {"name": "minion", "email": "minion30@despicable.me", "profile_pic": f"{pics_ep}/minion.jpg",
     "username": "minion30", "created_at": simulation_start_time, "provider": "google", "resource_uuid": "-99"},
]


def _ratings_builder(user_data):
    rating = 1500
    adjustment = 30
    ratings_array = []
    for i, entry in enumerate(user_data):
        ratings_array.append(dict(
            user_id=i+1,
            index_symbol=None,
            game_id=None,
            rating=STARTING_ELO_SCORE,
            update_type="sign_up",
            timestamp=simulation_start_time
        ))
        ratings_array.append(dict(
            user_id=i+1,
            index_symbol=None,
            game_id=3,
            rating=rating,
            update_type="game_end",
            timestamp=simulation_end_time
        ))
        rating -= adjustment

    rating = 1230
    adjustment = 14
    for index in TRACKED_INDEXES:
        ratings_array.append(dict(
            user_id=None,
            index_symbol=index,
            game_id=None,
            rating=STARTING_ELO_SCORE,
            update_type="sign_up",
            timestamp=simulation_start_time
        ))
        ratings_array.append(dict(
            user_id=None,
            index_symbol=index,
            game_id=3,
            rating=rating,
            update_type="game_end",
            timestamp=simulation_end_time
        ))
        rating -= adjustment

    ratings_array.sort(key=lambda x: x["timestamp"])
    return ratings_array


MOCK_DATA = {
    "users": USER_DATA,
    "games": [
        {"title": "fervent swartz", "game_mode": "multi_player", "duration": 365, "buy_in": 100,
         "benchmark": "sharpe_ratio", "side_bets_perc": 50, "side_bets_period": "monthly", "creator_id": 4,
         "invite_window": 1589368380.0, "stakes": "monopoly"},  # 1
        {"title": "max aggression", "game_mode": "multi_player", "duration": 1, "buy_in": 100_000,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 3,
         "invite_window": 1589368380.0, "stakes": "monopoly"},  # 2
        {"title": "test game", "game_mode": "multi_player", "duration": 14, "buy_in": 100,
         "benchmark": "return_ratio", "side_bets_perc": 50, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": 1589368380.0, "stakes": "real"},  # 3
        {"title": "test user excluded", "game_mode": "multi_player", "duration": 60, "buy_in": 20,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0, "stakes": "real"},  # 4
        {"title": "valiant roset", "game_mode": "multi_player", "duration": 60, "buy_in": 20,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0, "stakes": "monopoly"},  # 5
        {"title": "finished game to show", "game_mode": "multi_player", "duration": 1, "buy_in": 10,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": simulation_start_time + DEFAULT_INVITE_OPEN_WINDOW * SECONDS_IN_A_DAY, "stakes": "monopoly"},
        # 6
        {"title": "finished game to hide", "game_mode": "multi_player", "duration": 1, "buy_in": 10,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": simulation_start_time - SECONDS_IN_A_DAY * (14 + DEFAULT_INVITE_OPEN_WINDOW),
         "stakes": "monopoly"},  # 7
        {"title": "single player test", "game_mode": "single_player", "duration": 90, "buy_in": None,
         "benchmark": "sharpe_ratio", "side_bets_perc": None, "side_bets_period": None, "creator_id": 1,
         "invite_window": None, "stakes": "monopoly"}  # 8
    ],
    "game_status": [
        {"game_id": 1, "status": "pending", "timestamp": 1589195580.0, "users": [1, 3, 4, 5]},
        {"game_id": 2, "status": "pending", "timestamp": 1589368260.0, "users": [1, 3]},
        {"game_id": 3, "status": "pending", "timestamp": simulation_start_time, "users": [1, 3, 4]},
        {"game_id": 3, "status": "active", "timestamp": simulation_start_time, "users": [1, 3, 4]},  # active
        {"game_id": 4, "status": "pending", "timestamp": simulation_start_time, "users": [3, 4, 5]},
        {"game_id": 4, "status": "active", "timestamp": simulation_start_time, "users": [3, 4, 5]},  # active
        {"game_id": 5, "status": "pending", "timestamp": 1589368260.0, "users": [1, 3, 4, 5]},
        {"game_id": 6, "status": "pending", "timestamp": simulation_start_time, "users": [1, 4]},
        {"game_id": 6, "status": "active", "timestamp": simulation_start_time, "users": [1, 4]},
        {"game_id": 6, "status": "finished", "timestamp": simulation_start_time + SECONDS_IN_A_DAY * 1 + 10,
         "users": [1, 4]},
        {"game_id": 7, "status": "pending", "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY,
         "users": [1, 4]},
        {"game_id": 7, "status": "active", "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY,
         "users": [1, 4]},
        {"game_id": 7, "status": "finished", "timestamp": simulation_start_time - 13 * SECONDS_IN_A_DAY,
         "users": [1, 4]},
        {"game_id": 8, "status": "pending", "timestamp": simulation_start_time, "users": [1]},
        {"game_id": 8, "status": "active", "timestamp": simulation_start_time, "users": [1]},
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
        {"game_id": 6, "user_id": 1, "status": "joined", "timestamp": simulation_start_time},
        {"game_id": 6, "user_id": 4, "status": "invited", "timestamp": simulation_start_time},
        {"game_id": 6, "user_id": 4, "status": "joined", "timestamp": simulation_start_time},
        {"game_id": 7, "user_id": 1, "status": "joined", "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY},
        {"game_id": 7, "user_id": 4, "status": "invited", "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY},
        {"game_id": 7, "user_id": 4, "status": "joined", "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY},
        {"game_id": 8, "user_id": 1, "status": "joined", "timestamp": simulation_start_time},
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

        # game 8, user id #1
        {"user_id": 1, "game_id": 8, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 713,
         "price": get_stock_start_price("NVDA"), "order_type": "market", "time_in_force": "day"},  # 15
        {"user_id": 1, "game_id": 8, "symbol": "NKE", "buy_or_sell": "buy", "quantity": 3136,
         "price": get_stock_start_price("NKE"), "order_type": "market", "time_in_force": "day"},  # 16
    ],
    "order_status": [
        {"order_id": 1, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 1
        {"order_id": 1, "timestamp": simulation_start_time, "status": "fulfilled",  # 2
         "clear_price": get_stock_start_price("AMZN")},
        {"order_id": 2, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 3
        {"order_id": 2, "timestamp": simulation_start_time, "status": "fulfilled",  # 4
         "clear_price": get_stock_start_price("TSLA")},
        {"order_id": 3, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 5
        {"order_id": 3, "timestamp": simulation_start_time, "status": "fulfilled",  # 6
         "clear_price": get_stock_start_price("LYFT")},
        {"order_id": 4, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 7
        {"order_id": 4, "timestamp": simulation_start_time, "status": "fulfilled",  # 8
         "clear_price": get_stock_start_price("SPXU")},
        {"order_id": 5, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 9
        {"order_id": 5, "timestamp": simulation_start_time, "status": "fulfilled",  # 10
         "clear_price": get_stock_start_price("NVDA")},
        {"order_id": 6, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 11
        {"order_id": 6, "timestamp": simulation_start_time, "status": "fulfilled",  # 12
         "clear_price": get_stock_start_price("NKE")},
        {"order_id": 7, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 13
        {"order_id": 7, "timestamp": simulation_start_time, "status": "fulfilled",  # 14
         "clear_price": get_stock_start_price("MELI")},
        {"order_id": 8, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 15
        {"order_id": 8, "timestamp": get_beginning_of_next_trading_day(simulation_start_time + SECONDS_IN_A_DAY),
         "status": "fulfilled", "clear_price": get_stock_start_price("NVDA") * 1.05},  # 16
        {"order_id": 9, "timestamp": simulation_end_time, "status": "pending", "clear_price": None},  # 17
        {"order_id": 10, "timestamp": simulation_end_time, "status": "pending", "clear_price": None},  # 18
        {"order_id": 11, "timestamp": simulation_end_time, "status": "pending", "clear_price": None},  # 19
        {"order_id": 11, "timestamp": simulation_end_time, "status": "fulfilled",  # 20
         "clear_price": get_stock_finish_price("AMZN")},
        {"order_id": 12, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 21
        {"order_id": 12, "timestamp": simulation_start_time, "status": "fulfilled", "clear_price": 1_000},  # 22
        {"order_id": 13, "timestamp": 1592572846.5938, "status": "pending", "clear_price": None},  # 23
        {"order_id": 14, "timestamp": 1592572846.5938, "status": "pending", "clear_price": None},  # 24
        {"order_id": 15, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 25
        {"order_id": 15, "timestamp": simulation_start_time, "status": "fulfilled",  # 26
         "clear_price": get_stock_start_price("NVDA")},
        {"order_id": 16, "timestamp": simulation_start_time, "status": "pending", "clear_price": None},  # 27
        {"order_id": 16, "timestamp": simulation_start_time, "status": "fulfilled",  # 28
         "clear_price": get_stock_start_price("NKE")}
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
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": 13, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": 13, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 1, "symbol": "BABA"},
        {"user_id": 3, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 4, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},

        # Game 6, setup
        {"user_id": 1, "game_id": 6, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 4, "game_id": 6, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},

        # Game 7, setup
        {"user_id": 1, "game_id": 7, "order_status_id": None,
         "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY, "balance_type": "virtual_cash",
         "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 4, "game_id": 7, "order_status_id": None,
         "timestamp": simulation_start_time - 14 * SECONDS_IN_A_DAY, "balance_type": "virtual_cash",
         "balance": STARTING_VIRTUAL_CASH, "symbol": None},

        # Game 8, setup and orders
        {"user_id": 1, "game_id": 8, "order_status_id": None, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH, "symbol": None},
        {"user_id": 1, "game_id": 8, "order_status_id": 26, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash", "balance": STARTING_VIRTUAL_CASH - get_stock_start_price("NVDA") * 713,
         "symbol": None},
        {"user_id": 1, "game_id": 8, "order_status_id": 26, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 713, "symbol": "NVDA"},
        {"user_id": 1, "game_id": 8, "order_status_id": 28, "timestamp": simulation_start_time,
         "balance_type": "virtual_cash",
         "balance": STARTING_VIRTUAL_CASH - get_stock_start_price("NVDA") * 713 - get_stock_start_price("NKE") * 3136,
         "symbol": None},
        {"user_id": 1, "game_id": 8, "order_status_id": 28, "timestamp": simulation_start_time,
         "balance_type": "virtual_stock", "balance": 3136, "symbol": "NKE"},

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
        {"requester_id": 10, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 10, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 11, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 11, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 12, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 12, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 13, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 13, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 14, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 14, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 15, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 15, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 16, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 16, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 17, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 17, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 18, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 18, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 19, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 19, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 20, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 20, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 21, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 21, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 22, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 22, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 23, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 23, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 24, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 24, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 25, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 25, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 26, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 26, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 27, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 27, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 28, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 28, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 29, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 29, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 30, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 30, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 31, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 31, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 32, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 32, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 33, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 33, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 34, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 34, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 35, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 35, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 36, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 36, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 37, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 37, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 38, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 38, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time},
        {"requester_id": 39, "invited_id": 1, "status": "invited", "timestamp": simulation_start_time},
        {"requester_id": 39, "invited_id": 1, "status": "accepted", "timestamp": simulation_start_time}
    ],
    "payment_profiles": [
        {"user_id": 1, "processor": "paypal", "uuid": Config.PAYPAL_TEST_USER_ID, "payer_email": Config.TEST_CASE_EMAIL,
         "timestamp": simulation_start_time},
        {"user_id": 3, "processor": "paypal", "uuid": Config.PAYPAL_TEST_USER_ID, "payer_email": "eddie@example.test",
         "timestamp": simulation_start_time},
        {"user_id": 4, "processor": "paypal", "uuid": Config.PAYPAL_TEST_USER_ID, "payer_email": "mike@example.test",
         "timestamp": simulation_start_time}
    ],
    "index_metadata": [
        {"symbol": "^IXIC", "start_date": simulation_start_time, "avatar": f"{pics_ep}/nasdaq.png", "name": "NASDAQ"},
        {"symbol": "^DJI", "start_date": simulation_start_time, "avatar": f"{pics_ep}/dji.png", "name": "Dow Jones"},
        {"symbol": "^GSPC", "start_date": simulation_start_time, "avatar": f"{pics_ep}/s_and_p.png", "name": "S&P 500"}
    ],
    "indexes": index_records,
    "stockbets_rating": _ratings_builder(USER_DATA)
}


def populate_table(table_name):
    db_metadata = MetaData(bind=engine)
    db_metadata.reflect()
    with engine.connect() as conn:
        table_meta = db_metadata.tables[table_name]
        conn.execute(table_meta.insert(), MOCK_DATA[table_name])


def make_db_mocks():
    table_names = MOCK_DATA.keys()
    db_metadata = MetaData(bind=engine)
    db_metadata.reflect()
    for table in table_names:
        if MOCK_DATA.get(table) and table != 'users':
            populate_table(table)
        if table == 'users':
            for user in MOCK_DATA.get(table):
                add_row("users", name=user["name"], email=user["email"], profile_pic=user["profile_pic"],
                        username=user["username"], created_at=user["created_at"], provider=user["provider"],
                        password=None, resource_uuid=user["resource_uuid"])


def make_s3_mocks():

    def _local_pic_to_bucket(filepath: str, key: str):
        s3 = aws_client()
        with open(filepath, "rb") as image:
            f = image.read()
            pic = bytearray(f)
            out_img = BytesIO(pic)
            out_img.seek(0)
            s3.put_object(Body=out_img, Bucket=Config.AWS_PUBLIC_BUCKET_NAME, Key=key, ACL="public-read")

    table = 'users'
    for user_entry in MOCK_DATA[table]:
        pic_name = user_entry['profile_pic'].split('/')[-1]
        key = f"profile_pics/{pic_name}"
        _local_pic_to_bucket(f"database/fixtures/assets/{pic_name}", key)
        if user_entry["name"] == "minion":
            break  # we only need to run this once for minion -- they all share the same profile pic

    table = "index_metadata"
    for index_entry in MOCK_DATA[table]:
        key = f"profile_pics/{index_entry['avatar'].split('/')[-1]}"
        _local_pic_to_bucket(f"database/fixtures/assets/{index_entry['symbol']}.png", key)


def make_redis_mocks():

    @patch("backend.logic.base.STARTING_VIRTUAL_CASH", 100_000)
    def _game_3_mock():
        init_game_assets(3)

    _game_3_mock()

    game_ids = [6, 7, 8]
    for game_id in game_ids:
        init_game_assets(game_id)

    serialize_and_pack_rankings()
    serialize_and_pack_games_per_user_chart()

    # TODO: This is a quick hack to get the admin panel working in dev. Fix at some point
    df = make_games_per_user_data()
    chart_json = make_chart_json(df, "cohort", "percentage", "game_count")
    s3_cache.set(f"{ORDERS_PER_ACTIVE_USER_PREFIX}", json.dumps(chart_json))


if __name__ == '__main__':
    make_db_mocks()
