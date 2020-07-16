import time
from datetime import datetime as dt, timedelta

import jwt
import requests
from backend.config import Config
from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.base import query_to_dict

WHITE_LIST = [
    "aaron@stockbets.io",
    "adamdominik24@gmail.com",
    "adrian@captec.io",
    "alexanderclapp@gmail.com",
    "andressierrasoler@gmail.com",
    "andrew.nobrega@gmail.com",
    "apolhamu@gmail.com",
    "benp2007@gmail.com",
    "benspener@gmail.com",
    "bethanydominik@gmail.com",
    "bkrohn@gmail.com",
    "caseyoswald@gmail.com",
    "charly@captec.io",
    "David.V.Imbert@gmail.com",
    "dannygins@gmail.com",
    "dud341@gmail.com",
    "eddiestrickler@gmail.com",
    "edgar@captec.io",
    "gtheckt@gmail.com",
    "gavarj@spu.edu",
    "GraysonBadgley@gmail.com",
    "gretchenguo@gmail.com",
    "guillermomrelliug@gmail.com",
    "gustavo@captec.io",
    "ianhrovatin@gmail.com",
    "jafet@captec.io",
    "jaime@rodas.mx",
    "jafetgonz@gmail.com",
    "jason.shaw.23@gmail.com",
    "jmz7vcom@gmail.com",
    "jsanchezcastillejos@gmail.com",
    "ken@escale.com.br",
    "kiefertravis@gmail.com",
    "landstromconsulting@gmail.com",
    "markpolhamus@gmail.com",
    "matheus@sat.ws",
    "matt@escale.com.br",
    "mcooper4040@gmail.com",
    "mjpcooper@gmail.com",
    "mpolovin@gmail.com",
    "miguel@stockbets.io",
    "miguel@ruidovisual.com",
    "pattycampam@gmail.com",
    "renny@wearefirstin.com",
    "rohitesh.dhawan@gmail.com",
    "ryanwillemsen@gmail.com",
    "seanwells074@gmail.com",
    "scott.michel.moore@gmail.com",
    "thebigmehtaphor@gmail.com",
    "thedanc@gmail.com",
    "timmybouley@gmail.com",
    "tommaso@mymoons.mx",
    "torygreen@gmail.com",
    "waverly.james92@gmail.com",
]


ADMIN_USERS = ["aaron@stockbets.io", "miguel@ruidovisual.com"]


class WhiteListException(Exception):

    def __init__(self, message="The product is still in it's early beta and we're whitelisting. You'll get on soon!"):
        super().__init__(message)


def standardize_email(email):
    prefix, suffix = email.lower().split("@")
    prefix = prefix.replace(".", "")
    return "@".join([prefix, suffix])


def check_against_whitelist(email):
    standardized_list = [standardize_email(x) for x in WHITE_LIST]
    if standardize_email(email) in standardized_list:
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


def register_user(user_entry):
    user = query_to_dict("SELECT * FROM users WHERE resource_uuid = %s", user_entry["resource_uuid"])
    if user is None:
        add_row("users", **user_entry)
        return

    # update an existing user's profile pic if it's changed
    if user_entry["profile_pic"] != user["profile_pic"]:
        with engine.connect() as conn:
            conn.execute("UPDATE users SET profile_pic = %s WHERE id = %s;", user["profile_pic"], user["id"])


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
