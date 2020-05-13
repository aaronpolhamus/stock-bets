from datetime import datetime as dt, timedelta
from functools import wraps

import jwt
import pandas as pd
import requests
from backend.database.db import db
from backend.database.helpers import retrieve_meta_data
from backend.logic.games import (
    make_random_game_title,
    DEFAULT_GAME_MODE,
    GAME_MODES,
    DEFAULT_GAME_DURATION,
    DEFAULT_BUYIN,
    DEFAULT_REBUYS,
    DEFAULT_BENCHMARK,
    DEFAULT_SIDEBET_PERCENT,
    DEFAULT_SIDEBET_PERIOD,
    SIDE_BET_PERIODS,
    BENCHMARKS,
    DEFAULT_INVITE_OPEN_WINDOW)
from config import Config
from flask import Blueprint, request, make_response, jsonify
from sqlalchemy import select

routes = Blueprint("routes", __name__)

# Error messages
# --------------
TOKEN_ID_MISSING_MSG = "This request is missing the 'tokenId' field -- are you a hacker?"
GOOGLE_OAUTH_ERROR_MSG = "tokenId from Google OAuth failed verification -- are you a hacker?"
INVALID_SIGNATURE_ERROR_MSG = "Couldn't decode session token -- are you a hacker?"
LOGIN_ERROR_MSG = "Login to receive valid session_token"
SESSION_EXP_ERROR_MSG = "You session token expired -- log back in"
MISSING_USERNAME_ERROR_MSG = "Didn't find 'username' in request body"
USERNAME_TAKE_ERROR_MSG = "This username is taken. Try another one?"
GAME_CREATED_MSG = "Game created! "
INVALID_OAUTH_PROVIDER_MSG = "Not a valid OAuth provider"
MISSING_OAUTH_PROVIDER_MSG = "Please specify the provider in the requests body"


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def create_jwt(email, user_id, username, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "user_id": user_id, "username": username,
               "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm=Config.JWT_ENCODE_ALGORITHM).decode("utf-8")


def get_invitee_list(username):
    """This is an unsustainable way to do this, but it works for now. If this app goes anywhere we will either have to
    stream values from the API, or introduce some kind of a friends feature
    """
    with db.engine.connect() as conn:
        invitees = conn.execute("SELECT username FROM users WHERE username != %s;", username).fetchall()
    return [invitee[0] for invitee in invitees]


def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            return make_response(LOGIN_ERROR_MSG, 401)
        try:
            jwt.decode(session_token, Config.SECRET_KEY)
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            resp = make_response(SESSION_EXP_ERROR_MSG, 401)
        except jwt.InvalidSignatureError:
            resp = make_response(INVALID_SIGNATURE_ERROR_MSG, 401)
        return resp

    return decorated


@routes.route("/api/login", methods=["POST"])
def register_user():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API. token_id comes from response.tokenId where the
    response is the returned value from the React-Google-Login component.
    """
    # from flask import current_app

    provider = request.json.get("provider")
    assert provider in ["google", "facebook", "twitter"], make_response(INVALID_OAUTH_PROVIDER_MSG, 401)

    if provider == "google":
        token_id = request.json.get("tokenId")
        if token_id is None:
            return make_response(TOKEN_ID_MISSING_MSG, 401)

        response = verify_google_oauth(token_id)
        if response.status_code == 200:
            resource_uuid = request.json.get("googleId")
            decoded_json = response.json()
            with db.engine.connect() as conn:
                user = conn.execute("SELECT * FROM users WHERE resource_uuid = %s", resource_uuid).fetchone()
                create_user_entry = {
                    "name": decoded_json["given_name"],
                    "email": decoded_json["email"],
                    "profile_pic": decoded_json["picture"],
                    "username": None,
                    "created_at": dt.now(),
                    "provider": provider,
                    "resource_uuid": resource_uuid
                }
        else:
            return make_response(GOOGLE_OAUTH_ERROR_MSG, response.status_code)

    if provider == "facebook":
        resource_uuid = "test"

    if provider == "twitter":
        resource_uuid = "test"

    with db.engine.connect() as conn:
        if user is None:
            metadata = retrieve_meta_data()
            users = metadata.tables["users"]
            conn.execute(users.insert(), create_user_entry)

        user_id, email, username = conn.execute("SELECT id, email, username FROM users WHERE resource_uuid = %s",
                                                resource_uuid).fetchone()
        session_token = create_jwt(email, user_id, username)
        resp = make_response()
        resp.set_cookie("session_token", session_token, httponly=True)
        return resp


@routes.route("/api/home", methods=["POST"])
@authenticate
def index():
    """Return some basic information about the user's profile, games, and bets in order to
    populate the landing page"""
    decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_id = decocded_session_token["user_id"]
    with db.engine.connect() as conn:
        user_info = conn.execute("SELECT * FROM users WHERE id = %s", user_id).fetchone()

    # Retrieve open invites and active games
    # TODO: There's a cleaner way to do this with the sqlalchemy ORM, I think
    game_info_query = """
        SELECT g.id, g.title, gs.status
        FROM games g
          INNER JOIN game_status gs
            ON g.id = gs.game_id
          INNER JOIN (
              SELECT game_id, MAX(timestamp) timestamp
            FROM game_status
            GROUP BY game_id
          ) tmp ON tmp.game_id = gs.game_id AND
                    tmp.timestamp = gs.timestamp
          WHERE
            JSON_CONTAINS(gs.users, %s) AND
            gs.status IN ('pending', 'active');
    """
    with db.engine.connect() as conn:
        game_info_df = pd.read_sql(game_info_query, conn, params=str(user_id))
    game_info_resp = game_info_df.to_dict(orient="records")

    resp = jsonify(
        {"name": user_info[1],
         "email": user_info[2],
         "profile_pic": user_info[3],
         "username": user_info[4],
         "game_info": game_info_resp})
    return resp


@routes.route("/api/logout", methods=["POST"])
@authenticate
def logout():
    """Log user out of the backend by blowing away their session token
    """
    resp = make_response()
    resp.set_cookie("session_token", "", httponly=True, expires=0)
    return resp


@routes.route("/api/set_username", methods=["POST"])
@authenticate
def set_username():
    """Invoke to set a user's username during welcome and subsequently when they want to change it
    """
    decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_id = decocded_session_token["user_id"]
    user_email = decocded_session_token["email"]
    candidate_username = request.json["username"]
    if candidate_username is None:
        make_response(MISSING_USERNAME_ERROR_MSG, 400)

    with db.engine.connect() as conn:
        matches = conn.execute("SELECT name FROM users WHERE username = %s", candidate_username).fetchone()
        if matches is None:
            conn.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
            user_id, username = conn.execute("SELECT id, username FROM users WHERE email = %s", user_email).fetchone()
            session_token = create_jwt(user_email, user_id, username)
            resp = make_response()
            resp.set_cookie("session_token", session_token, httponly=True)
            return resp

    return make_response(USERNAME_TAKE_ERROR_MSG, 400)


@routes.route("/api/game_defaults", methods=["POST"])
@authenticate
def game_defaults():
    """Returns information to the MakeGame form that contains the defaults and optional values that it needs
    to render fields correctly
    """
    decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    username = decocded_session_token["username"]
    default_title = make_random_game_title()  # TODO: Enforce uniqueness at some point here
    available_invitees = get_invitee_list(username)
    resp = {
        "title": default_title,
        "mode": DEFAULT_GAME_MODE,
        "game_modes": GAME_MODES,
        "duration": DEFAULT_GAME_DURATION,
        "buy_in": DEFAULT_BUYIN,
        "n_rebuys": DEFAULT_REBUYS,
        "benchmark": DEFAULT_BENCHMARK,
        "side_bets_perc": DEFAULT_SIDEBET_PERCENT,
        "side_bets_period": DEFAULT_SIDEBET_PERIOD,
        "sidebet_periods": SIDE_BET_PERIODS,
        "benchmarks": BENCHMARKS,
        "available_invitees": available_invitees
    }
    return jsonify(resp)


@routes.route("/api/create_game", methods=["POST"])
@authenticate
def create_game():
    # setup
    decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_id = decocded_session_token["user_id"]
    metadata = retrieve_meta_data()
    game = metadata.tables["games"]
    game_status = metadata.tables["game_status"]
    users = metadata.tables["users"]

    # update game table
    opened_at = dt.utcnow()
    game_settings = request.json
    game_settings["creator_id"] = user_id
    # this may become configurable at some point via the UI -- for now it's hard-coded
    game_settings["invite_window"] = opened_at + timedelta(hours=DEFAULT_INVITE_OPEN_WINDOW)
    with db.engine.connect() as conn:
        result = conn.execute(game.insert(), game_settings)
        # Update game status table
        game_id = result.inserted_primary_key[0]
        invitees = tuple(game_settings["invitees"])
        invitee_ids = conn.execute(select([users.c.id], users.c.username.in_(invitees))).fetchall()
        user_ids = [x[0] for x in invitee_ids]
        user_ids.append(user_id)
        status_entry = {"game_id": game_id, "status": "pending", "timestamp": opened_at, "users": user_ids}
        conn.execute(game_status.insert(), status_entry)

    return make_response(GAME_CREATED_MSG, 200)


@routes.route("/api/play_game_landing", methods=["POST"])
@authenticate
def game_info():
    # decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    # user_id = decocded_session_token["user_id"]
    game_id = request.json["game_id"]
    with db.engine.connect() as conn:
        title = conn.execute("SELECT title FROM games WHERE id = %s", game_id).fetchone()[0]

    resp = {
        "title": title,

    }
    return jsonify(resp)


@routes.route("/api/place_order", methods=["POST"])
@authenticate
def place_order():
    pass
