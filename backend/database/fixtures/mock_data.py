from datetime import datetime as dt

from backend.database.helpers import retrieve_meta_data, reset_db
from config import Config
from sqlalchemy import create_engine

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
metadata = retrieve_meta_data()

# The test case user needs to be a live gmail acccount. Eventually we'll need to make this a heavily-restricted
# demo@stockbets.io account that anyone can use, but this is good for now.
DUMMY_USER_EMAIL = "dummy@example.test"

# Mocked data: These are listed in order so that we can tear down and build up while respecting foreign key constraints
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
        {"title": "gentleman's game", "mode": "return_weighted", "duration": 180, "buy_in": 50, "n_rebuys": 3,
         "benchmark": "return_ratio", "side_bets_perc": 50, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": 1589368380.0},
        {"title": "test user excluded", "mode": "winner_takes_all", "duration": 60, "buy_in": 20, "n_rebuys": 100,
         "benchmark": "return_ratio", "side_bets_perc": 25, "side_bets_period": "monthly", "creator_id": 5,
         "invite_window": 1580630520.0}
    ],

    "game_status": [
        {"game_id": 1, "status": "pending", "timestamp": 1589195580.0, "users": [1, 3, 4]},
        {"game_id": 2, "status": "pending", "timestamp": 1589368260.0, "users": [1, 4]},
        {"game_id": 3, "status": "pending", "timestamp": 1589281860.0, "users": [1, 3, 4, 5]},
        {"game_id": 3, "status": "active", "timestamp": 1589368260.0, "users": [1, 3, 4, 5]},
        {"game_id": 4, "status": "pending", "timestamp": 1589281860.0, "users": [3, 4, 5]},
        {"game_id": 4, "status": "active", "timestamp": 1589368260.0, "users": [3, 4, 5]}
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
