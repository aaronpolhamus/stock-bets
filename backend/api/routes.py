import time
from datetime import datetime as dt, timedelta
from functools import wraps

import jwt
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
    DEFAULT_ORDER_TYPE,
    DEFAULT_BUY_SELL,
    DEFAULT_TIME_IN_FORCE,
    BUY_SELL_TYPES,
    ORDER_TYPES,
    TIME_IN_FORCE_TYPES,
    QUANTITY_DEFAULT,
    QUANTITY_OPTIONS
)
from backend.logic.stock_data import fetch_end_of_day_cache, posix_to_datetime
from backend.tasks.definitions import (
    async_get_user_info,
    async_get_game_info_for_user,
    async_fetch_price,
    async_compile_player_sidebar_stats,
    async_cache_price,
    async_suggest_symbols,
    async_place_order,
    async_add_game,
    async_serialize_open_orders,
    async_serialize_current_balances,
    async_get_game_info,
    async_invite_friend,
    async_respond_to_friend_invite,
    async_suggest_friends,
    async_get_friends_details,
    async_get_friend_invites,
    async_serialize_balances_chart,
    async_respond_to_game_invite
)
from backend.tasks.redis import unpack_redis_json
from config import Config
from flask import Blueprint, request, make_response, jsonify

routes = Blueprint("routes", __name__)

HEALTH_CHECK_RESPONSE = "Healthy, baby!"

# Error messages
# --------------
OAUTH_ERROR_MSG = "OAuth failed verification -- are you a hacker?"
INVALID_SIGNATURE_ERROR_MSG = "Couldn't decode session token -- are you a hacker?"
LOGIN_ERROR_MSG = "Login to receive valid session_token"
SESSION_EXP_ERROR_MSG = "You session token expired -- log back in"
MISSING_USERNAME_ERROR_MSG = "Didn't find 'username' in request body"
USERNAME_TAKE_ERROR_MSG = "This username is taken. Try another one?"
GAME_CREATED_MSG = "Game created! "
INVALID_OAUTH_PROVIDER_MSG = "Not a valid OAuth provider"
MISSING_OAUTH_PROVIDER_MSG = "Please specify the provider in the requests body"
ORDER_PLACED_MESSAGE = "Order placed successfully!"
GAME_RESPONSE_MSG = "Got it, we'll the game creator know."
FRIEND_INVITE_SENT_MSG = "Friend invite sent :)"
FRIEND_INVITE_RESPONSE_MSG = "Great, we'll let them know"


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def verify_facebook_oauth(access_token):
    return requests.post(Config.FACEBOOK_VALIDATION_URL, data={"access_token": access_token})


def create_jwt(email, user_id, username, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "user_id": user_id, "username": username,
               "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm=Config.JWT_ENCODE_ALGORITHM).decode("utf-8")


def decode_token(req, element="user_id"):
    """Parse user information from the HTTP token that comes with each authenticated request from the frontend
    """
    decoded_session_token = jwt.decode(req.cookies["session_token"], Config.SECRET_KEY)
    return decoded_session_token[element]


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


# -------------- #
# Auth and login #
# -------------- #

@routes.route("/api/login", methods=["POST"])
def register_user():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API. token_id comes from response.tokenId where the
    response is the returned value from the React-Google-Login component.
    """
    oauth_data = request.json
    provider = oauth_data.get("provider")
    if provider not in ["google", "facebook", "twitter"]:
        return make_response(INVALID_OAUTH_PROVIDER_MSG, 411)

    if provider == "google":
        token_id = oauth_data.get("tokenId")
        response = verify_google_oauth(token_id)
        if response.status_code == 200:
            resource_uuid = oauth_data.get("googleId")
            decoded_json = response.json()
            user_entry = {
                "name": decoded_json["given_name"],
                "email": decoded_json["email"],
                "profile_pic": decoded_json["picture"],
                "username": None,
                "created_at": time.time(),
                "provider": provider,
                "resource_uuid": resource_uuid
            }
        else:
            return make_response(OAUTH_ERROR_MSG, response.status_code)

    if provider == "facebook":
        access_token = oauth_data.get("accessToken")
        response = verify_facebook_oauth(access_token)
        if response.status_code == 200:
            resource_uuid = oauth_data.get("userID")
            user_entry = {
                "name": oauth_data["name"],
                "email": oauth_data["email"],
                "profile_pic": oauth_data["picture"]["data"]["url"],
                "username": None,
                "created_at": time.time(),
                "provider": provider,
                "resource_uuid": resource_uuid
            }
        else:
            return make_response(OAUTH_ERROR_MSG, response.status_code)

    if provider == "twitter":
        pass

    with db.engine.connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE resource_uuid = %s", resource_uuid).fetchone()
        if user is None:
            metadata = retrieve_meta_data(db.engine)
            users = metadata.tables["users"]
            conn.execute(users.insert(), user_entry)

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
    user_id = decode_token(request)

    res = async_get_user_info.delay(user_id)
    while not res.ready():
        continue
    user_info = res.get()

    res = async_get_game_info_for_user.delay(user_id)
    while not res.ready():
        continue
    game_data = res.get()

    # sanitize some sensitive user info before sending back response
    del user_info["created_at"]
    del user_info["provider"]
    del user_info["resource_uuid"]

    # append game data to make reponse
    user_info["game_info"] = game_data
    return jsonify(user_info)


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
    user_id = decode_token(request)
    user_email = decode_token(request, "email")
    candidate_username = request.json["username"]
    if candidate_username is None:
        make_response(MISSING_USERNAME_ERROR_MSG, 400)

    with db.engine.connect() as conn:
        matches = conn.execute("SELECT name FROM users WHERE username = %s", candidate_username).fetchone()
        if matches is None:
            conn.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
            session_token = create_jwt(user_email, user_id, candidate_username)
            resp = make_response()
            resp.set_cookie("session_token", session_token, httponly=True)
            return resp

    return make_response(USERNAME_TAKE_ERROR_MSG, 400)


# ---------------- #
# Games management #
# ---------------- #

@routes.route("/api/game_defaults", methods=["POST"])
@authenticate
def game_defaults():
    """Returns information to the MakeGame form that contains the defaults and optional values that it needs
    to render fields correctly
    """
    user_id = decode_token(request)
    default_title = make_random_game_title()  # TODO: Enforce uniqueness at some point here
    res = async_get_friends_details.delay(user_id)
    while not res.ready():
        continue
    available_invitees = [x["username"] for x in res.get()]
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
    user_id = decode_token(request)
    game_settings = request.json
    res = async_add_game.delay(
        user_id,
        game_settings["title"],
        game_settings["mode"],
        game_settings["duration"],
        game_settings["buy_in"],
        game_settings["n_rebuys"],
        game_settings["benchmark"],
        game_settings["side_bets_perc"],
        game_settings["side_bets_period"],
        game_settings["invitees"])
    while not res.ready():
        continue
    return make_response(GAME_CREATED_MSG, 200)


@routes.route("/api/respond_to_game_invite", methods=["POST"])
@authenticate
def respond_to_game_invite():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    decision = request.json.get("decision")
    res = async_respond_to_game_invite.delay(game_id, user_id, decision)
    while not res.ready():
        continue
    return make_response(GAME_RESPONSE_MSG, 200)


# -------------------------- #
# Order management and prices#
# -------------------------- #


@routes.route("/api/game_info", methods=["POST"])
@authenticate
def game_info():
    game_id = request.json.get("game_id")
    res = async_get_game_info.delay(game_id)
    while not res.ready():
        continue
    return jsonify(res.get())


@routes.route("/api/order_form_defaults", methods=["POST"])
@authenticate
def order_form_defaults():
    game_id = request.json["game_id"]
    with db.engine.connect() as conn:
        title = conn.execute("SELECT title FROM games WHERE id = %s", game_id).fetchone()[0]

    resp = {
        "title": title,
        "game_id": game_id,
        "order_type_options": ORDER_TYPES,
        "order_type": DEFAULT_ORDER_TYPE,
        "buy_sell_options": BUY_SELL_TYPES,
        "buy_or_sell": DEFAULT_BUY_SELL,
        "time_in_force_options": TIME_IN_FORCE_TYPES,
        "time_in_force": DEFAULT_TIME_IN_FORCE,
        "quantity_type": QUANTITY_DEFAULT,
        "quantity_options": QUANTITY_OPTIONS
    }
    return jsonify(resp)


@routes.route("/api/place_order", methods=["POST"])
@authenticate
def place_order():
    user_id = decode_token(request)
    order_ticket = request.json
    game_id = order_ticket["game_id"]
    stop_limit_price = order_ticket.get("stop_limit_price")
    res = async_place_order.delay(
        user_id,
        game_id,
        order_ticket["symbol"],
        order_ticket["buy_or_sell"],
        order_ticket["order_type"],
        order_ticket["quantity_type"],
        order_ticket["market_price"],
        order_ticket["amount"],
        order_ticket["time_in_force"],
        stop_limit_price
    )
    while not res.ready():
        continue

    async_serialize_open_orders.delay(game_id, user_id)
    async_serialize_current_balances.delay(game_id, user_id)
    async_serialize_balances_chart.delay(game_id, user_id)
    async_compile_player_sidebar_stats.delay(game_id)
    return make_response(ORDER_PLACED_MESSAGE, 200)


@routes.route("/api/fetch_price", methods=["POST"])
@authenticate
def fetch_price():
    symbol = request.json.get("symbol")
    price, timestamp = fetch_end_of_day_cache(symbol)
    if price is not None:
        # If we have a valid end-of-trading day cache value, we'll use that here
        return jsonify({"price": price, "last_updated": posix_to_datetime(timestamp)})

    res = async_fetch_price.delay(symbol)
    while not res.ready():
        continue
    price, timestamp = res.get()
    async_cache_price.delay(symbol, price, timestamp)
    return jsonify({"price": price, "last_updated": posix_to_datetime(timestamp)})


@routes.route("/api/suggest_symbols", methods=["POST"])
@authenticate
def api_suggest_symbols():
    text = request.json["text"]
    res = async_suggest_symbols.delay(text)
    while not res.ready():
        continue
    return jsonify(res.get())

# ------- #
# Visuals #
# ------- #


@routes.route("/api/balances_chart", methods=["POST"])
@authenticate
def balances_chart():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"balances_chart_{game_id}_{user_id}"))


@routes.route("/api/field_chart", methods=["POST"])
@authenticate
def field_chart():
    game_id = request.json.get("game_id")
    f"field_chart_{game_id}"
    return jsonify(unpack_redis_json(f"field_chart_{game_id}"))


@routes.route("/api/get_open_orders_table", methods=["POST"])
@authenticate
def get_open_orders_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"open_orders_{game_id}_{user_id}"))


@routes.route("/api/get_current_balances_table", methods=["POST"])
@authenticate
def get_current_balances_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"current_balances_{game_id}_{user_id}"))

# ------ #
# DevOps #
# ------ #


@routes.route("/api/get_sidebar_stats", methods=["POST"])
@authenticate
def get_sidebar_stats():
    game_id = request.json.get("game_id")
    return jsonify(unpack_redis_json(f"sidebar_stats_{game_id}"))


@routes.route("/api/send_friend_request", methods=["POST"])
@authenticate
def send_friend_request():
    user_id = decode_token(request)
    invited_username = request.json.get("friend_invitee")
    res = async_invite_friend.delay(user_id, invited_username)
    while not res.ready():
        continue
    return make_response(FRIEND_INVITE_SENT_MSG, 200)


@routes.route("/api/respond_to_friend_request", methods=["POST"])
@authenticate
def respond_to_friend_request():
    """Note to frontend developers working with this endpoint: the acceptable response options are 'accepted' and
    'declined'
    """
    user_id = decode_token(request)
    requester_username = request.json.get("requester_username")
    response = request.json.get("response")
    res = async_respond_to_friend_invite.delay(requester_username, user_id, response)
    while not res.ready():
        continue
    return make_response(FRIEND_INVITE_RESPONSE_MSG, 200)


@routes.route("/api/get_list_of_friends", methods=["POST"])
@authenticate
def get_list_of_friends():
    user_id = decode_token(request)
    res = async_get_friends_details.delay(user_id)
    while not res.ready():
        continue
    return jsonify(res.get())


@routes.route("/api/get_list_of_friend_invites", methods=["POST"])
@authenticate
def get_list_of_friend_invites():
    user_id = decode_token(request)
    res = async_get_friend_invites.delay(user_id)
    while not res.ready():
        continue
    return jsonify(res.get())


@routes.route("/api/suggest_friend_invites", methods=["POST"])
@authenticate
def suggest_friend_invites():
    user_id = decode_token(request)
    text = request.json.get("text")
    res = async_suggest_friends.delay(user_id, text)
    while not res.ready():
        continue
    return jsonify(res.get())


@routes.route("/healthcheck", methods=["GET"])
def healthcheck():
    return make_response(HEALTH_CHECK_RESPONSE, 200)
