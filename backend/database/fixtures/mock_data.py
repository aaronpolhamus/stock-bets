from datetime import datetime as dt

from config import Config
from sqlalchemy import create_engine, MetaData

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
metadata = MetaData()
metadata.reflect(engine)

# Mocked data for users:
MOCK_DATA = {
    "users": [
        {"name": "Aaron", "email": "aaron@example.test", "profile_pic": "https://i.imgur.com/P5LO9v4.png",
         "username": "huachinango", "created_at": dt(2020, 4, 30, 23, 33, 25)},
        {"name": "dummy", "email": "dummy@example.test", "profile_pic": None, "username": None, "created_at": dt(2020, 5, 5, 13, 12, 1)}
    ],
}


def make_mock_data():
    table_names = metadata.tables.keys()
    for table in table_names:
        # first flush all data from all tables
        table_api = metadata.tables[table]
        conn.execute(table_api.delete())

        # then fill in mock data
        mock_entry = MOCK_DATA.get(table)
        if mock_entry:
            conn.execute(table_api.insert(), mock_entry)


if __name__ == '__main__':
    make_mock_data()
