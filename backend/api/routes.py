from datetime import datetime as dt, timedelta
from functools import wraps

import jwt
import pytz
import requests
from backend.database.db import db
from backend.database.helpers import (
    retrieve_meta_data)
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

# timestamp localizer
localizer = pytz.timezone(Config.TIMEZONE).localize

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


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def create_jwt(email, user_id, username, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "user_id": user_id, "username": username,
               "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm="HS256").decode("utf-8")


def get_invitee_list(username):
    """This is an unsustainable way to do this, but it works for now. If this app goes anywhere we will either have to
    stream values from the API, or introduce some kind of a friends feature
    """
    invitees = db.engine.execute("SELECT username FROM users WHERE username != %s;", username).fetchall()
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
    token_id = request.json.get("tokenId")
    if token_id is None:
        return make_response(TOKEN_ID_MISSING_MSG, 401)

    response = verify_google_oauth(token_id)
    if response.status_code == 200:
        decoded_json = response.json()
        user_email = decoded_json["email"]
        user = db.engine.execute("SELECT * FROM users WHERE email = %s", user_email).fetchone()
        if not user:
            db.engine.execute(
                "INSERT INTO users (name, email, profile_pic, username, created_at) VALUES (%s, %s, %s, %s, %s)",
                (decoded_json["given_name"], user_email, decoded_json["picture"], None, localizer(dt.now())))

        user_id, username = db.engine.execute("SELECT id, username FROM users WHERE email = %s", user_email).fetchone()
        session_token = create_jwt(user_email, user_id, username)
        resp = make_response()
        resp.set_cookie("session_token", session_token, httponly=True)
        return resp

    return make_response(GOOGLE_OAUTH_ERROR_MSG, response.status_code)


@routes.route("/api/home", methods=["POST"])
@authenticate
def index():
    """Return some basic information about the user's profile, games, and bets in order to
    populate the landing page"""
    decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_id = decocded_session_token["user_id"]
    user_info = db.engine.execute("SELECT * FROM users WHERE id = %s", user_id).fetchone()
    resp = jsonify({"name": user_info[1], "email": user_info[2], "profile_pic": user_info[3], "username": user_info[4]})
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

    matches = db.engine.execute("SELECT name FROM users WHERE username = %s", candidate_username).fetchone()
    if matches is None:
        db.engine.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
        user_id, username = db.engine.execute("SELECT id, username FROM users WHERE email = %s", user_email).fetchone()
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
    # Setup
    decocded_session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    metadata = retrieve_meta_data()
    game = metadata.tables["games"]
    game_invites = metadata.tables["game_invites"]
    game_status = metadata.tables["game_status"]
    users = metadata.tables["users"]

    # Update game settings database
    game_settings = request.json
    result = db.engine.execute(game.insert(), game_settings)

    # Update the invites database
    user_id = decocded_session_token["user_id"]
    game_id = result.inserted_primary_key[0]
    invitees = tuple(game_settings["invitees"])
    invitee_ids = db.engine.execute(select([users.c.id], users.c.username.in_(invitees))).fetchall()
    opened_at = localizer(dt.utcnow())
    open_until = opened_at + timedelta(hours=DEFAULT_INVITE_OPEN_WINDOW)
    for invitee_id in invitee_ids:
        invite_entry = {"creator_id": user_id, "invitee_id": invitee_id[0], "game_id": game_id, "opened_at": opened_at,
                        "open_until": open_until}
        db.engine.execute(game_invites.insert(), invite_entry)

    # add pending entry to game status database
    status_entry = {"game_id": game_id, "status": "pending", "updated_at": opened_at}
    db.engine.execute(game_status.insert(), status_entry)

    return make_response(GAME_CREATED_MSG, 200)


@routes.route("/api/update_game_states", methods=["POST"])
@authenticate
def update_game_states():
    """For now we won't invest resources on the backend in high-cost ongoing monitoring of external APIs. Rather,
    every time a user interacts with game-related resources on the website we will check and update associated games
    """
    pass
