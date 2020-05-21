import json

from backend.database.helpers import retrieve_meta_data, reset_db
from config import Config
from sqlalchemy import create_engine

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
metadata = retrieve_meta_data(engine)

with open("./database/fixtures/caches/price_records.json") as json_file:
    price_records = json.load(json_file)

market_order_time = min([record["timestamp"] for record in price_records])
close_of_simulation_time = max([record["timestamp"] for record in price_records])
seconds_in_a_day = 60 * 60 * 24


def get_stock_start_price(symbol, records=price_records, order_time=market_order_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][0]
    return stock_record["price"]


def get_stock_finish_price(symbol, records=price_records, order_time=close_of_simulation_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][-1]
    return stock_record["price"]


# Mocked data: These are listed in order so that we can tear down and build up while respecting foreign key constraints
DUMMY_USER_EMAIL = "dummy@example.test"
MOCK_DATA = {
    "users": [
        {"name": "test_user", "email": Config.TEST_CASE_EMAIL, "profile_pic": "https://i.imgur.com/P5LO9v4.png",
         "username": "cheetos", "created_at": 1588307605.0, "provider": "google",
         "resource_uuid": Config.TEST_CASE_UUID},
        {"name": "dummy", "email": DUMMY_USER_EMAIL,
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
         "resource_uuid": "nop112"}
    ],
    "games": [
        {"title": "fervent swartz", "mode": "consolation_prize", "duration": 365, "buy_in": 100, "n_rebuys": 2,
         "benchmark": "sharpe_ratio", "side_bets_perc": 50, "side_bets_period": "monthly", "creator_id": 4,
         "invite_window": 1589368380.0},
        {"title": "max aggression", "mode": "winner_takes_all", "duration": 1, "buy_in": 100_000, "n_rebuys": 0,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 3,
         "invite_window": 1589368380.0},
        {"title": "gentleman's game", "mode": "return_weighted", "duration": 14, "buy_in": 100, "n_rebuys": 3,
         "benchmark": "return_ratio", "side_bets_perc": 50, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": 1589368380.0},
        {"title": "test user excluded", "mode": "winner_takes_all", "duration": 60, "buy_in": 20, "n_rebuys": 100,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0}
    ],
    "game_status": [
        {"game_id": 1, "status": "pending", "timestamp": 1589195580.0, "users": [1, 3, 4]},
        {"game_id": 2, "status": "pending", "timestamp": 1589368260.0, "users": [1, 4]},
        {"game_id": 3, "status": "pending", "timestamp": 1589281860.0, "users": [1, 3, 4]},
        {"game_id": 3, "status": "active", "timestamp": 1589368260.0, "users": [1, 3, 4]},
        {"game_id": 4, "status": "pending", "timestamp": 1589281860.0, "users": [3, 4, 5]},
        {"game_id": 4, "status": "active", "timestamp": 1589368260.0, "users": [3, 4, 5]}
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
        {"user_id": 1, "game_id": 3, "symbol": "AMZN", "buy_or_sell": "buy", "quantity": 5,
         "price": get_stock_start_price("AMZN"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "TSLA", "buy_or_sell": "buy", "quantity": 15,
         "price": get_stock_start_price("TSLA"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "LYFT", "buy_or_sell": "buy", "quantity": 350,
         "price": get_stock_start_price("LYFT"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "SPXU", "buy_or_sell": "buy", "quantity": 600,
         "price": get_stock_start_price("SPXU"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 3, "game_id": 3, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 70,
         "price": get_stock_start_price("NVDA"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 3, "game_id": 3, "symbol": "NKE", "buy_or_sell": "buy", "quantity": 235,
         "price": get_stock_start_price("NKE"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 4, "game_id": 3, "symbol": "MELI", "buy_or_sell": "buy", "quantity": 60,
         "price": get_stock_start_price("MELI"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 5,
         "price": get_stock_start_price("NVDA") * 1.05, "order_type": "stop", "time_in_force": "until_cancelled"},
        {"user_id": 1, "game_id": 3, "symbol": "MELI", "buy_or_sell": "buy", "quantity": 100,
         "price": get_stock_finish_price("MELI") * 0.9, "order_type": "limit", "time_in_force": "until_cancelled"},
        {"user_id": 1, "game_id": 3, "symbol": "SPXU", "buy_or_sell": "sell", "quantity": 300,
         "price": get_stock_finish_price("SPXU") * 0.75, "order_type": "stop", "time_in_force": "until_cancelled"},
    ],
    "order_status": [
        {"order_id": 1, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("AMZN")},
        {"order_id": 2, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("TSLA")},
        {"order_id": 3, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("LYFT")},
        {"order_id": 4, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("SPXU")},
        {"order_id": 5, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("NVDA")},
        {"order_id": 6, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("NKE")},
        {"order_id": 7, "timestamp": market_order_time, "status": "fulfilled",
         "clear_price": get_stock_start_price("MELI")},
        {"order_id": 8, "timestamp": market_order_time, "status": "pending", "clear_price": None},
        {"order_id": 8, "timestamp": market_order_time + seconds_in_a_day, "status": "fulfilled",
         "clear_price": get_stock_start_price("NVDA") * 1.05},
        {"order_id": 9, "timestamp": close_of_simulation_time, "status": "pending", "clear_price": None},
        {"order_id": 10, "timestamp": close_of_simulation_time, "status": "pending", "clear_price": None}
    ],
    "game_balances": [
        {"user_id": 1, "game_id": 3, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 1, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 88180.87446, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 1, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 5, "symbol": "AMZN"},
        {"user_id": 1, "game_id": 3, "order_status_id": 2, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 75914.79993000001, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 2, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 15, "symbol": "TSLA"},
        {"user_id": 1, "game_id": 3, "order_status_id": 3, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 65808.40223, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 3, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 350, "symbol": "LYFT"},
        {"user_id": 1, "game_id": 3, "order_status_id": 4, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 56105.78903000001, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 4, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 600, "symbol": "SPXU"},
        {"user_id": 3, "game_id": 3, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 5, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 77913.94531, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 5, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 70, "symbol": "NVDA"},
        {"user_id": 3, "game_id": 3, "order_status_id": 6, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 57495.573395, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 6, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 235, "symbol": "NKE"},
        {"user_id": 4, "game_id": 3, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 4, "game_id": 3, "order_status_id": 7, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 53985.8575, "symbol": None},
        {"user_id": 4, "game_id": 3, "order_status_id": 7, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 60, "symbol": "MELI"},
        {"user_id": 1, "game_id": 3, "order_status_id": 9, "timestamp": market_order_time + seconds_in_a_day,
         "balance_type": "virtual_cash", "balance": 54405.28330175001, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 9, "timestamp": market_order_time + seconds_in_a_day,
         "balance_type": "virtual_stock", "balance": 5, "symbol": "NVDA"},
    ]
}


def make_mock_data():
    # reset the database for each test class in order to maintain consistency of auto-incremented IDs
    reset_db()

    table_names = MOCK_DATA.keys()
    for table in table_names:
        # first flush all data from all tables
        table_meta = metadata.tables[table]
        conn.execute(table_meta.delete())

        # then fill in mock data
        mock_entry = MOCK_DATA.get(table)
        if mock_entry:
            conn.execute(table_meta.insert(), mock_entry)


if __name__ == '__main__':
    make_mock_data()
