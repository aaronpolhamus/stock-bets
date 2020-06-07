from datetime import timedelta

from backend.database.fixtures.make_historical_price_data import make_stock_data_records
from backend.database.helpers import retrieve_meta_data, reset_db
from backend.logic.stock_data import (
    get_schedule_start_and_end,
    nyse,
    posix_to_datetime,
)
from backend.tasks.definitions import (
    async_update_play_game_visuals,
    async_update_player_stats,
    async_compile_player_sidebar_stats
)
from config import Config
from sqlalchemy import create_engine

SECONDS_IN_A_DAY = 60 * 60 * 24

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
metadata = retrieve_meta_data(engine)

price_records = make_stock_data_records()
market_order_time = min([record["timestamp"] for record in price_records])
close_of_simulation_time = max([record["timestamp"] for record in price_records])


def get_beginning_of_next_trading_day(ref_time):
    current_day = posix_to_datetime(ref_time)
    schedule = nyse.schedule(current_day, current_day)
    while schedule.empty:
        current_day += timedelta(days=1)
        schedule = nyse.schedule(current_day, current_day)
    start_day, _ = get_schedule_start_and_end(schedule)
    return start_day


def get_stock_start_price(symbol, records=price_records, order_time=market_order_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][0]
    return stock_record["price"]


def get_stock_finish_price(symbol, records=price_records, order_time=close_of_simulation_time):
    stock_record = [item for item in records if item["symbol"] == symbol and item["timestamp"] == order_time][-1]
    return stock_record["price"]


# Mocked data: These are listed in order so that we can tear down and build up while respecting foreign key constraints
MOCK_DATA = {
    "users": [
        {"name": Config.TEST_CASE_NAME, "email": Config.TEST_CASE_EMAIL, "profile_pic": "https://i.imgur.com/P5LO9v4.png",
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
        {"name": "johnny walker", "email": "jack@black.pearl",
         "profile_pic": "https://www.brandemia.org/sites/default/files/sites/default/files/johnnie_walker_nuevo_logo.png",
         "username": "johnny", "created_at": 1591562299, "provider": "google", "resource_uuid": "tuv415"},
        {"name": "jadis", "email": "jadis@rick.lives",
         "profile_pic": "https://vignette.wikia.nocookie.net/villains/images/7/78/Season_eight_jadis.png",
         "username": "jadis", "created_at": 1591562299, "provider": "google", "resource_uuid": "wxy617"},
    ],

    "games": [
        {"title": "fervent swartz", "mode": "consolation_prize", "duration": 365, "buy_in": 100, "n_rebuys": 2,
         "benchmark": "sharpe_ratio", "side_bets_perc": 50, "side_bets_period": "monthly", "creator_id": 4,
         "invite_window": 1589368380.0},
        {"title": "max aggression", "mode": "winner_takes_all", "duration": 1, "buy_in": 100_000, "n_rebuys": 0,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 3,
         "invite_window": 1589368380.0},
        {"title": "test game", "mode": "return_weighted", "duration": 14, "buy_in": 100, "n_rebuys": 3,
         "benchmark": "return_ratio", "side_bets_perc": 50, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": 1589368380.0},
        {"title": "test user excluded", "mode": "winner_takes_all", "duration": 60, "buy_in": 20, "n_rebuys": 100,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0},
        {"title": "valiant roset", "mode": "winner_takes_all", "duration": 60, "buy_in": 20, "n_rebuys": 100,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0}
    ],
    "game_status": [
        {"game_id": 1, "status": "pending", "timestamp": 1589195580.0, "users": [1, 3, 4, 5]},
        {"game_id": 2, "status": "pending", "timestamp": 1589368260.0, "users": [1, 3]},
        {"game_id": 3, "status": "pending", "timestamp": 1589281860.0, "users": [1, 3, 4]},
        {"game_id": 3, "status": "active", "timestamp": 1589368260.0, "users": [1, 3, 4]},
        {"game_id": 4, "status": "pending", "timestamp": 1589281860.0, "users": [3, 4, 5]},
        {"game_id": 4, "status": "active", "timestamp": 1589368260.0, "users": [3, 4, 5]},
        {"game_id": 5, "status": "pending", "timestamp": 1589368260.0, "users": [1, 3, 4, 5]}
    ],
    "game_invites": [
        {"game_id": 1, "user_id": 4, "status": "joined", "timestamp": 1589195580.0},
        {"game_id": 1, "user_id": 1, "status": "invited", "timestamp": 1589195580.0},
        {"game_id": 1, "user_id": 3, "status": "invited", "timestamp": 1589195580.0},
        {"game_id": 1, "user_id": 5, "status": "invited", "timestamp": 1589195580.0},
        {"game_id": 2, "user_id": 3, "status": "joined", "timestamp": 1589368260.0},
        {"game_id": 2, "user_id": 1, "status": "invited", "timestamp": 1589368260.0},
        {"game_id": 3, "user_id": 1, "status": "joined", "timestamp": 1589281860.0},
        {"game_id": 3, "user_id": 3, "status": "invited", "timestamp": 1589281860.0},
        {"game_id": 3, "user_id": 4, "status": "invited", "timestamp": 1589281860.0},
        {"game_id": 3, "user_id": 3, "status": "joined", "timestamp": 1589368260.0},
        {"game_id": 3, "user_id": 4, "status": "joined", "timestamp": 1589368260.0},
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
    "orders": [
        # game 3, user id #1
        {"user_id": 1, "game_id": 3, "symbol": "AMZN", "buy_or_sell": "buy", "quantity": 10,
         "price": get_stock_start_price("AMZN"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "TSLA", "buy_or_sell": "buy", "quantity": 35,
         "price": get_stock_start_price("TSLA"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "LYFT", "buy_or_sell": "buy", "quantity": 700,
         "price": get_stock_start_price("LYFT"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 1, "game_id": 3, "symbol": "SPXU", "buy_or_sell": "buy", "quantity": 1200,
         "price": get_stock_start_price("SPXU"), "order_type": "market", "time_in_force": "day"},

        # game 3, user id #3
        {"user_id": 3, "game_id": 3, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 130,
         "price": get_stock_start_price("NVDA"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 3, "game_id": 3, "symbol": "NKE", "buy_or_sell": "buy", "quantity": 400,
         "price": get_stock_start_price("NKE"), "order_type": "market", "time_in_force": "day"},

        # game 3, user id #4
        {"user_id": 4, "game_id": 3, "symbol": "MELI", "buy_or_sell": "buy", "quantity": 107,
         "price": get_stock_start_price("MELI"), "order_type": "market", "time_in_force": "day"},

        # game 3, user id #1, follow-on orders
        {"user_id": 1, "game_id": 3, "symbol": "NVDA", "buy_or_sell": "buy", "quantity": 8,
         "price": get_stock_start_price("NVDA") * 1.05, "order_type": "stop", "time_in_force": "until_cancelled"},
        {"user_id": 1, "game_id": 3, "symbol": "MELI", "buy_or_sell": "buy", "quantity": 2,
         "price": get_stock_finish_price("MELI") * 0.9, "order_type": "limit", "time_in_force": "until_cancelled"},
        {"user_id": 1, "game_id": 3, "symbol": "SPXU", "buy_or_sell": "sell", "quantity": 300,
         "price": get_stock_finish_price("SPXU") * 0.75, "order_type": "stop", "time_in_force": "until_cancelled"},
        {"user_id": 1, "game_id": 3, "symbol": "AMZN", "buy_or_sell": "sell", "quantity": 4,
         "price": get_stock_finish_price("AMZN"), "order_type": "market", "time_in_force": "day"},
        {"user_id": 5, "game_id": 4, "symbol": "BABA", "buy_or_sell": "buy", "quantity": 3,
         "price": 201.72, "order_type": "market", "time_in_force": "day"},
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
        {"order_id": 8, "timestamp": get_beginning_of_next_trading_day(market_order_time + SECONDS_IN_A_DAY),
         "status": "fulfilled",
         "clear_price": get_stock_start_price("NVDA") * 1.05},
        {"order_id": 9, "timestamp": close_of_simulation_time, "status": "pending", "clear_price": None},
        {"order_id": 10, "timestamp": close_of_simulation_time, "status": "pending", "clear_price": None},
        {"order_id": 11, "timestamp": close_of_simulation_time, "status": "fulfilled",
         "clear_price": get_stock_finish_price("AMZN")},
        {"order_id": 12, "timestamp": close_of_simulation_time, "status": "fulfilled",
         "clear_price": 201.72}
    ],
    "game_balances": [
        # Game 3, user id #1
        {"user_id": 1, "game_id": 3, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 1, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 75489.31133, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 1, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 10, "symbol": "AMZN"},
        {"user_id": 1, "game_id": 3, "order_status_id": 2, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 46482.067084999995, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 2, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 35, "symbol": "TSLA"},
        {"user_id": 1, "game_id": 3, "order_status_id": 3, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 23562.491384999994, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 3, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 700, "symbol": "LYFT"},
        {"user_id": 1, "game_id": 3, "order_status_id": 4, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 7460.725784999993, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 4, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 1200, "symbol": "SPXU"},

        # Game 3, user id #3
        {"user_id": 3, "game_id": 3, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 5, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 52679.10716, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 5, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 130, "symbol": "NVDA"},
        {"user_id": 3, "game_id": 3, "order_status_id": 6, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 14130.324760000003, "symbol": None},
        {"user_id": 3, "game_id": 3, "order_status_id": 6, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 400, "symbol": "NKE"},

        # Game 3, user id #4
        {"user_id": 4, "game_id": 3, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 4, "game_id": 3, "order_status_id": 7, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 8130.831265999994, "symbol": None},
        {"user_id": 4, "game_id": 3, "order_status_id": 7, "timestamp": market_order_time,
         "balance_type": "virtual_stock", "balance": 107, "symbol": "MELI"},

        # Game 3, user id #1, subsequent plays
        {"user_id": 1, "game_id": 3, "order_status_id": 9,
         "timestamp": get_beginning_of_next_trading_day(market_order_time + SECONDS_IN_A_DAY),
         "balance_type": "virtual_cash", "balance": 4403.068093799993, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 9,
         "timestamp": get_beginning_of_next_trading_day(market_order_time + SECONDS_IN_A_DAY),
         "balance_type": "virtual_stock", "balance": 8, "symbol": "NVDA"},

        {"user_id": 1, "game_id": 3, "order_status_id": 12, "timestamp": close_of_simulation_time,
         "balance_type": "virtual_cash", "balance": 14037.019021799993, "symbol": None},
        {"user_id": 1, "game_id": 3, "order_status_id": 12, "timestamp": close_of_simulation_time,
         "balance_type": "virtual_stock", "balance": 6, "symbol": "AMZN"},
        {"user_id": 5, "game_id": 4, "order_status_id": None, "timestamp": market_order_time,
         "balance_type": "virtual_cash", "balance": 100_000, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": 13, "timestamp": close_of_simulation_time,
         "balance_type": "virtual_cash", "balance": 99798.28, "symbol": None},
        {"user_id": 5, "game_id": 4, "order_status_id": 13, "timestamp": close_of_simulation_time,
         "balance_type": "virtual_stock", "balance": 1, "symbol": "BABA"},
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
        {"requester_id": 1, "invited_id": 6, "status": "invited", "timestamp": 1591561793},
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


def make_redis_mocks():
    test_game_id = 3
    res = async_update_player_stats.delay()
    while not res.ready():
        continue
    async_compile_player_sidebar_stats.delay(test_game_id)
    async_update_play_game_visuals.delay()


if __name__ == '__main__':
    make_mock_data()
