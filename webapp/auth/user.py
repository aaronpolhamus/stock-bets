from flask_login import UserMixin

from database.db import db


class User(UserMixin):
    def __init__(self, name, email, username, profile_pic):
        self.name = name
        self.email = email
        self.username = username
        self.profile_pic = profile_pic

    @property
    def id(self):
        return db.engine.execute("SELECT id FROM users WHERE email = %s;", self.email).fetchone()

    @staticmethod
    def get(user_email):
        user = db.engine.execute("SELECT * FROM users WHERE email = %s", user_email).fetchone()
        if not user:
            return None

        user = User(name=user[0], email=user[1], username=user[2], profile_pic=user[3])
        return user

    @staticmethod
    def create(name, email, username, profile_pic):
        db.engine.execute(
            "INSERT INTO users (name, email, username, profile_pic)"
            "VALUES (%s, %s, %s, %s)",
            (name, email, username, profile_pic),
        )
