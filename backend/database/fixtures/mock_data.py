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
}

if __name__ == '__main__':
    table_names = metadata.tables.keys()
    for table in table_names:
        # first flush all data from all tables
        table_api = metadata.tables[table]
        conn.execute(table_api.delete())

        # then fill in mock data
        mock_entry = MOCK_DATA.get(table)
        if mock_entry:
            conn.execute(table_api.insert(), mock_entry)
