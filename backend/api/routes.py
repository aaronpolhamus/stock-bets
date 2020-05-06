from datetime import datetime as dt, timedelta
from functools import wraps

import jwt
import requests
from flask import Blueprint, request, make_response, jsonify
from funkybob import RandomNameGenerator

from backend.database.db import db
from backend.database.models import GameModes, Benchmarks
from config import Config

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


# Frontend defaults
# -----------------
DEFAULT_GAME_DURATION = 20  # Default number of trading days that a game lasts for
DEFAULT_BUYIN = 200  # The default buyin required to play a game


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def create_jwt(email, user_id, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "user_id": user_id, "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm="HS256").decode("utf-8")


def unpack_enumerated_field_mappings(table_class):
    """This function unpacks the natural language descriptions of each enumerated field so that these can be passed
    to the frontend
    """
    return [x[1].value[1] for x in table_class.__members__.items()]


def get_participant_list():
    """This is an unsustainable way to do this, but it works for now. If this app goes anywhere we will either have to
    stream values from the API, or introduce some kind of a friends feature
    """
    return db.engine.execute("SELECT username from users;").fetchall()


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
                (decoded_json["given_name"], user_email, decoded_json["picture"], None, dt.now()))

        user_id = db.engine.execute("SELECT id FROM users WHERE email = %s", user_email).fetchone()[0]
        session_token = create_jwt(user_email, user_id)
        resp = make_response()
        resp.set_cookie("session_token", session_token, httponly=True)
        return resp

    return make_response(GOOGLE_OAUTH_ERROR_MSG, response.status_code)


@routes.route("/api/home", methods=["POST"])
@authenticate
def index():
    from flask import current_app
    current_app.logger.debug(f"*** hit this endpoint ***")

    """Return some basic information about the user's profile, games, and bets in order to
    populate the landing page"""
    decoded_request = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_id = decoded_request["user_id"]
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
    decoded_request = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_id = decoded_request["user_id"]
    candidate_username = request.json["username"]
    if candidate_username is None:
        make_response(MISSING_USERNAME_ERROR_MSG, 400)

    matches = db.engine.execute("SELECT name FROM users WHERE username = %s", candidate_username).fetchone()
    if matches is None:
        db.engine.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
        return jsonify({"status": "upated"})

    return make_response(USERNAME_TAKE_ERROR_MSG, 400)


@routes.route("/api/game_defaults", methods=["POST"])
@authenticate
def game_defaults():
    """Returns information to the MakeGame form that contains the defaults and optional values that it needs
    to render fields correctly
    """
    title_iterator = iter(RandomNameGenerator())
    default_title = next(title_iterator)  # TODO: Enforce uniqueness at some point here
    game_modes = unpack_enumerated_field_mappings(GameModes)
    benchmarks = unpack_enumerated_field_mappings(Benchmarks)
    available_participants = get_participant_list()
    resp = {
        "default_title": default_title,
        "game_modes": game_modes,
        "default_duration": DEFAULT_GAME_DURATION,
        "default_buyin": DEFAULT_BUYIN,
        "benchmarks": benchmarks,
        "available_participants": available_participants
    }
    return jsonify(resp)


@routes.route("/api/create_game", methods=["POST"])
@authenticate
def create_game():
    pass


@routes.route("/api/update_game_states", methods=["POST"])
@authenticate
def update_game_states():
    """For now we won't invest resources on the backend in high-cost ongoing monitoring of external APIs. Rather,
    every time a user interacts with game-related resources on the website we will check and update associated games
    """
    pass
