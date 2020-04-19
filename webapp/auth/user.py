from flask_login import UserMixin

from database.db import db


class User(UserMixin):
    def __init__(self, name, email, profile_pic, username):
        self.name = name
        self.email = email
        self.username = username
        self.profile_pic = profile_pic

    @property
    def id(self):
        return db.engine.execute("SELECT id FROM users WHERE email = %s;", self.email).fetchone()[0]

    @staticmethod
    def get(_id):
        user = db.engine.execute("SELECT * FROM users WHERE id = %s", _id).fetchone()
        if not user:
            return None

        user = User(name=user[1], email=user[2], profile_pic=user[3], username=user[4])
        return user

    @staticmethod
    def create(name, email, username, profile_pic):
        db.engine.execute(
            "INSERT INTO users (name, email, username, profile_pic)"
            "VALUES (%s, %s, %s, %s)",
            (name, email, username, profile_pic),
        )

    @staticmethod
    def test():
        return db.engine.execute("SELECT * FROM users WHERE id = 1;").fetchone()
