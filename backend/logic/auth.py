from datetime import datetime as dt, timedelta

import jwt
import requests
import time

from backend.database.db import db_session
from backend.database.helpers import (
    retrieve_meta_data
)
from backend.config import Config

WHITE_LIST = [
    "benspener@gmail.com",
    "eddie.strickler@gmail.com",
    "gavarj@spu.edu",
    "mpolovin@gmail.com",
    "matheus@sat.ws",
    "mpolovin@gmail.com",
    "pattycampam@gmail.com",
    "jmz7v.com@gmail.com",
    "gustavo@captec.io",
    "jaime@rodas.mx"
]


class WhiteListException(Exception):

    def __str__(self):
        return "The product is still in it's early beta and we're whitelisting. You'll get on soon!"


def check_against_whitelist(email):
    if email in WHITE_LIST:
        return
    raise WhiteListException


def create_jwt(email, user_id, username, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "user_id": user_id, "username": username,
               "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm=Config.JWT_ENCODE_ALGORITHM).decode("utf-8")


def decode_token(req, element="user_id"):
    """Parse user information from the HTTP token that comes with each authenticated request from the frontend
    """
    decoded_session_token = jwt.decode(req.cookies["session_token"], Config.SECRET_KEY)
    return decoded_session_token[element]


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def make_user_entry_from_google(oauth_data):
    token_id = oauth_data.get("tokenId")
    response = verify_google_oauth(token_id)
    if response.status_code == 200:
        resource_uuid = oauth_data.get("googleId")
        decoded_json = response.json()
        user_entry = dict(
            name=decoded_json["given_name"],
            email=decoded_json["email"],
            profile_pic=decoded_json["picture"],
            username=None,
            created_at=time.time(),
            provider="google",
            resource_uuid=resource_uuid
        )
        return user_entry, resource_uuid, 200
    return None, None, response.status_code


def verify_facebook_oauth(access_token):
    return requests.post(Config.FACEBOOK_VALIDATION_URL, data={"access_token": access_token})


def make_user_entry_from_facebook(oauth_data):
    access_token = oauth_data.get("accessToken")
    response = verify_facebook_oauth(access_token)
    if response.status_code == 200:
        resource_uuid = oauth_data.get("userID")
        user_entry = dict(
            name=oauth_data["name"],
            email=oauth_data["email"],
            profile_pic=oauth_data["picture"]["data"]["url"],
            username=None,
            created_at=time.time(),
            provider="facebook",
            resource_uuid=resource_uuid
            )
        return user_entry, resource_uuid, 200
    return None, None, response.status_code


def make_user_entry(user_entry, resource_uuid):
    with db_session.connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE resource_uuid = %s", resource_uuid).fetchone()
        db_session.remove()

    if user is None:
        metadata = retrieve_meta_data(db_session.connection())
        with db_session.connection() as conn:
            users = metadata.tables["users"]
            conn.execute(users.insert(), user_entry)
            db_session.remove()


def make_session_token_from_uuid(resource_uuid):
    with db_session.connection() as conn:
        user_id, email, username = conn.execute("SELECT id, email, username FROM users WHERE resource_uuid = %s",
                                                resource_uuid).fetchone()
        db_session.remove()
    return create_jwt(email, user_id, username)


def register_username_with_token(user_id, user_email, candidate_username):
    with db_session.connection() as conn:
        matches = conn.execute("SELECT id FROM users WHERE username = %s", candidate_username).fetchone()
        db_session.remove()

    if matches is None:
        with db_session.connection() as conn:
            conn.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
            db_session.commit()
        return create_jwt(user_email, user_id, candidate_username)

    return None
