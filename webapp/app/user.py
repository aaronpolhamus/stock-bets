from flask_login import UserMixin

from db.manager import db


class User(UserMixin):
    def __init__(self, name, email, username, profile_pic):
        self.name = name
        self.email = email
        self.username = username
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return None

        user = User(name=user[0], email=user[1], username=user[2], profile_pic=user[3])
        return user

    @staticmethod
    def create(name, email, username, profile_pic):
        db.execute(
            "INSERT INTO users (name, email, username, profile_pic)"
            "VALUES (?, ?, ?, ?)",
            (name, email, username, profile_pic),
        )
        db.commit()
