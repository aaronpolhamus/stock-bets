import time
from datetime import datetime as dt, timedelta

import jwt
import requests
from backend.config import Config
from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.friends import invite_friend, get_if_invited_by_email, update_email_invite_status

ADMIN_USERS = ["aaron@stockbets.io", "miguel@ruidovisual.com"]


def standardize_email(email):
    prefix, suffix = email.lower().split("@")
    prefix = prefix.replace(".", "")
    return "@".join([prefix, suffix])


def check_against_invited_users(email):
    with engine.connect() as conn:
        count, = conn.execute("SELECT count(*) FROM external_invites WHERE invited_email = %s", email).fetchone()
    if count > 0:
        return True
    return False


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


def get_user_data(uuid):
    with engine.connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE resource_uuid = %s", uuid).fetchone()
    return user


def register_user(user_entry):
    # TODO add friend request of the user that invited the user
    uuid = user_entry["resource_uuid"]
    user = get_user_data(uuid)
    if user is not None:
        return None
    add_row("users", **user_entry)
    user = get_user_data(uuid)
    requester_friend_id = get_if_invited_by_email(user['email'])
    if requester_friend_id is not None:
        update_email_invite_status(user['email'])
        invite_friend(requester_friend_id, user["id"])


def make_session_token_from_uuid(resource_uuid):
    with engine.connect() as conn:
        user_id, email, username = conn.execute("SELECT id, email, username FROM users WHERE resource_uuid = %s",
                                                resource_uuid).fetchone()
    return create_jwt(email, user_id, username)


def register_username_with_token(user_id, user_email, candidate_username):
    with engine.connect() as conn:
        matches = conn.execute("SELECT id FROM users WHERE username = %s", candidate_username).fetchone()

    if matches is None:
        with engine.connect() as conn:
            conn.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
        return create_jwt(user_email, user_id, candidate_username)

    return None
