from datetime import datetime as dt

from sqlalchemy import create_engine
from backend.database.helpers import retrieve_meta_data, reset_db
from config import Config


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
metadata = retrieve_meta_data()

# The test case user needs to be a live gmail acccount. Eventually we'll need to make this a heavily-restricted
# demo@stockbets.io account that anyone can use, but this is good for now.
TEST_CASE_USER = "aaron@stockbets.io"

# Mocked data: These are listed in order so that we can tear down and build up while respecting foreign key constraints
MOCK_DATA = {
    "users": [
        {"name": "Aaron", "email": TEST_CASE_USER, "profile_pic": "https://i.imgur.com/P5LO9v4.png",
         "username": "cheetos", "created_at": dt(2020, 4, 30, 23, 33, 25)},
        {"name": "dummy", "email": "dummy@example.test",
         "profile_pic": "https://cadena100-cdnmed.agilecontent.com/resources/jpg/8/2/1546649423628.jpg",
         "username": None, "created_at": dt(2020, 5, 5, 13, 12, 1)},
        {"name": "Eddie", "email": "eddie@example.test",
         "profile_pic": "https://animalark.org/wp-content/uploads/2016/03/181Cheetahs12.jpg", "username": "toofast",
         "created_at": dt(2020, 4, 30, 23, 38, 48)},
        {"name": "Mike", "email": "mike@example.test",
         "profile_pic": "https://gitedumoulinavent.com/wp-content/uploads/pexels-photo-1230302.jpeg",
         "username": "miguel", "created_at": dt(2020, 4, 30, 23, 41, 20)},
        {"name": "Eli", "email": "eli@example.test",
         "profile_pic": "https://nationalpostcom.files.wordpress.com/2018/11/gettyimages-1067958662.jpg",
         "username": "murcitdev", "created_at": dt(2020, 4, 30, 23, 46, 46)}
    ],
    "games": [
        {"title": "fervent swartz", "mode": "consolation_prize", "duration": 365, "buy_in": 100, "n_rebuys": 2,
         "benchmark": "sharpe_ratio", "side_bets_perc": 50, "side_bets_period": "monthly", "creator_id": 4,
         "invite_window": dt(2020, 5, 13, 6, 13)},
        {"title": "max aggression", "mode": "winner_takes_all", "duration": 1, "buy_in": 100_000, "n_rebuys": 0,
         "benchmark": "sharpe_ratio", "side_bets_perc": 0, "side_bets_period": "weekly", "creator_id": 3,
         "invite_window": dt(2020, 5, 13, 6, 13)},
        {"title": "gentleman's game", "mode": "return_weighted", "duration": 180, "buy_in": 50, "n_rebuys": 3,
         "benchmark": "return_ratio", "side_bets_perc": 50, "side_bets_period": "weekly", "creator_id": 1,
         "invite_window": dt(2020, 5, 13, 6, 13)}
    ],

    "game_status": [
        {"game_id": 1, "status": "pending", "updated_at": dt(2020, 5, 11, 6, 13), "users": [1, 3, 4]},
        {"game_id": 2, "status": "pending", "updated_at": dt(2020, 5, 13, 6, 11), "users": [1, 4]},
        {"game_id": 2, "status": "pending", "updated_at": dt(2020, 5, 13, 6, 11), "users": [1, 3, 4, 5]}
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
