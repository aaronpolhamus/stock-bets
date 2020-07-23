import time
from datetime import datetime as dt, timedelta

import jwt
import requests
from backend.config import Config
from backend.database.db import engine
from backend.database.helpers import add_row, query_to_dict
from backend.logic.friends import invite_friend, get_requester_ids_from_email
from backend.logic.base import standardize_email

ADMIN_USERS = ["aaron@stockbets.io", "miguel@ruidovisual.com"]


def get_user_data(uuid):
    with engine.connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE resource_uuid = %s", uuid).fetchone()
    return user


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


def make_user_entry_from_google(tokenId, googleId):
    response = verify_google_oauth(tokenId)
    if response.status_code == 200:
        resource_uuid = googleId
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
        return user_entry, resource_uuid, response.status_code
    return None, None, response.status_code


def verify_facebook_oauth(access_token):
    return requests.post(Config.FACEBOOK_VALIDATION_URL, data={"access_token": access_token})


def make_user_entry_from_facebook(accessToken, userID, name, email, picture):
    response = verify_facebook_oauth(accessToken)
    if response.status_code == 200:
        user_entry = dict(
            name=name,
            email=email,
            profile_pic=picture,
            username=None,
            created_at=time.time(),
            provider="facebook",
            resource_uuid=userID
        )
        return user_entry, userID, 200
    return None, None, response.status_code


def update_profile_pic(user_id: id, new_profile_pic: str, old_profile_pic: str):
    if new_profile_pic != old_profile_pic:
        with engine.connect() as conn:
            conn.execute("UPDATE users SET profile_pic = %s WHERE id = %s;", new_profile_pic, user_id)


def setup_new_user(inbound_entry: dict, uuid: str) -> int:
    add_row("users", **inbound_entry)
    db_entry = get_user_data(uuid)
    requester_friends_ids = get_requester_ids_from_email(db_entry['email'])
    for requester_id in requester_friends_ids:
        add_row("external_invites", requester_id=requester_id, invited_email=db_entry["email"], status="accepted",
                timestamp=time.time())
        invite_friend(requester_id, db_entry["id"])
    return db_entry


def get_pending_external_game_invites(invited_email: str):
    """Returns external game invites whose most recent status is 'invited'
    """
    return query_to_dict("""
        SELECT *
        FROM external_invites ex
        INNER JOIN
             (SELECT requester_id, game_id, MAX(id) as max_id
               FROM external_invites
               GROUP BY requester_id, game_id) grouped_ex
        ON ex.id = grouped_ex.max_id
        WHERE LOWER(REPLACE(ex.invited_email, '.', '')) = %s AND ex.status = 'invited';
    """, standardize_email(invited_email))


def register_user(inbound_entry):
    uuid = inbound_entry["resource_uuid"]
    db_entry = get_user_data(uuid)
    returning_user = False
    if db_entry is not None:
        # make any necessary update to the user's profile data
        update_profile_pic(db_entry["id"], inbound_entry["profile_pic"], db_entry["profile_pic"])
        returning_user = True

    # register first-time users
    if not returning_user:
        db_entry = setup_new_user(inbound_entry, uuid)

    # for both classes of user, check if there are any outstanding game invites to create invitations for
    external_game_invite_entries = get_pending_external_game_invites(inbound_entry["email"])
    with engine.connect() as conn:
        for entry in external_game_invite_entries:
            # is this user already invited to a game?
            result = conn.execute("SELECT * FROM game_invites WHERE game_id = %s AND user_id = %s", entry["game_id"],
                                  db_entry["user_id"]).fetchone()
            if not result:
                add_row("game_invites", game_id=entry["game_id"], user_id=db_entry["user_id"], status="invited",
                        timestamp=time.time())


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
