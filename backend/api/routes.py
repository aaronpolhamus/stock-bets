from functools import wraps

import jwt
from backend.config import Config
from backend.database.db import db
from backend.logic.auth import (
    decode_token,
    make_user_entry_from_google,
    make_user_entry_from_facebook,
    make_session_token_from_uuid,
    register_username_with_token,
    register_user_if_first_visit,
    check_against_whitelist,
    WhiteListException
)
from backend.logic.games import (
    add_game,
    get_game_info_for_user,
    place_order,
    cancel_order,
    get_current_game_cash_balance,
    get_current_stock_holding,
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
from logic.base import (
    get_pending_buy_order_value,
    fetch_iex_price,
    get_user_information
)
from backend.logic.visuals import (
    format_time_for_response,
    update_order_details,
    ORDER_DETAILS_PREFIX,
    BALANCES_CHART_PREFIX,
    CURRENT_BALANCES_PREFIX,
    FIELD_CHART_PREFIX,
    SIDEBAR_STATS_PREFIX,
    PAYOUTS_PREFIX,
    USD_FORMAT
)
from backend.tasks.definitions import (
    async_update_player_stats,
    async_update_play_game_visuals,
    async_compile_player_sidebar_stats,
    async_cache_price,
    async_suggest_symbols,
    async_get_user_invite_statuses_for_pending_game,
    async_serialize_order_details,
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
ADMIN_BLOCK_MSG = "This is a protected admin view. Check in with your team if you need permission to access"
ORDER_CANCELLED_MESSAGE = "Order cancelled"


# -------------- #
# Auth and login #
# -------------- #
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


def admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_email = decode_token(request, "email")
        if user_email not in ["aaron@stockbets.io"]:
            return make_response(ADMIN_BLOCK_MSG, 401)
        return f(*args, **kwargs)
    return decorated


@routes.route("/api/login", methods=["POST"])
def login():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API. token_id comes from response.tokenId where the
    response is the returned value from the React-Google-Login component.
    """
    oauth_data = request.json
    provider = oauth_data.get("provider")
    if provider not in ["google", "facebook", "twitter"]:
        return make_response(INVALID_OAUTH_PROVIDER_MSG, 411)

    if provider == "google":
        user_entry, resource_uuid, status_code = make_user_entry_from_google(oauth_data)

    if provider == "facebook":
        user_entry, resource_uuid, status_code = make_user_entry_from_facebook(oauth_data)

    if provider == "twitter":
        pass

    if status_code is not 200:
        return make_response(OAUTH_ERROR_MSG, status_code)

    if Config.CHECK_WHITE_LIST:
        try:
            check_against_whitelist(user_entry["email"])
        except WhiteListException as err:
            return make_response(str(err), 401)

    register_user_if_first_visit(user_entry)
    session_token = make_session_token_from_uuid(resource_uuid)
    resp = make_response()
    resp.set_cookie("session_token", session_token, httponly=True, samesite="None", secure=True)
    return resp


@routes.route("/api/logout", methods=["POST"])
@authenticate
def logout():
    """Log user out of the backend by blowing away their session token
    """
    resp = make_response()
    resp.set_cookie("session_token", "", httponly=True, samesite="None", secure=True, expires=0)
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

    session_token = register_username_with_token(user_id, user_email, candidate_username)
    if session_token is not None:
        resp = make_response()
        resp.set_cookie("session_token", session_token, httponly=True, samesite="None", secure=True)
        return resp

    return make_response(USERNAME_TAKE_ERROR_MSG, 400)

# --------- #
# User info #
# --------- #


@routes.route("/api/get_user_info", methods=["POST"])
@authenticate
def get_user_info():
    user_id = decode_token(request)
    return jsonify(get_user_information(user_id))


@routes.route("/api/home", methods=["POST"])
@authenticate
def home():
    """Return some basic information about the user's profile, games, and bets in order to
    populate the landing page"""
    user_id = decode_token(request)
    user_info = get_user_information(user_id)
    user_info["game_info"] = get_game_info_for_user(user_id)
    return jsonify(user_info)

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
    res = async_get_friends_details.apply(args=[user_id])
    available_invitees = [x["username"] for x in res.get()]
    resp = dict(
        title=default_title,
        mode=DEFAULT_GAME_MODE,
        game_modes=GAME_MODES,
        duration=DEFAULT_GAME_DURATION,
        buy_in=DEFAULT_BUYIN,
        n_rebuys=DEFAULT_REBUYS,
        benchmark=DEFAULT_BENCHMARK,
        side_bets_perc=DEFAULT_SIDEBET_PERCENT,
        side_bets_period=DEFAULT_SIDEBET_PERIOD,
        sidebet_periods=SIDE_BET_PERIODS,
        benchmarks=BENCHMARKS,
        available_invitees=available_invitees
    )
    return jsonify(resp)


@routes.route("/api/create_game", methods=["POST"])
@authenticate
def create_game():
    user_id = decode_token(request)
    game_settings = request.json
    n_rebuys = 0  # this is not a popular user feature, and it  adds a lot of complexity.
    add_game(
        user_id,
        game_settings["title"],
        game_settings["mode"],
        game_settings["duration"],
        game_settings["buy_in"],
        n_rebuys,
        game_settings["benchmark"],
        game_settings["side_bets_perc"],
        game_settings["side_bets_period"],
        game_settings["invitees"])
    return make_response(GAME_CREATED_MSG, 200)


@routes.route("/api/respond_to_game_invite", methods=["POST"])
@authenticate
def respond_to_game_invite():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    decision = request.json.get("decision")
    async_respond_to_game_invite.apply(args=[game_id, user_id, decision])
    return make_response(GAME_RESPONSE_MSG, 200)


@routes.route("/api/get_pending_game_info", methods=["POST"])
@authenticate
def get_pending_game_info():
    game_id = request.json.get("game_id")
    res = async_get_user_invite_statuses_for_pending_game.apply(args=[game_id])
    return jsonify(res.result)

# --------------------------- #
# Order management and prices #
# --------------------------- #


@routes.route("/api/game_info", methods=["POST"])
@authenticate
def game_info():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    return jsonify(async_get_game_info.apply(args=[game_id, user_id]).get())


@routes.route("/api/order_form_defaults", methods=["POST"])
@authenticate
def order_form_defaults():
    game_id = request.json["game_id"]
    with db.engine.connect() as conn:
        title = conn.execute("SELECT title FROM games WHERE id = %s", game_id).fetchone()[0]

    resp = dict(
        title=title,
        game_id=game_id,
        order_type_options=ORDER_TYPES,
        order_type=DEFAULT_ORDER_TYPE,
        buy_sell_options=BUY_SELL_TYPES,
        buy_or_sell=DEFAULT_BUY_SELL,
        time_in_force_options=TIME_IN_FORCE_TYPES,
        time_in_force=DEFAULT_TIME_IN_FORCE,
        quantity_type=QUANTITY_DEFAULT,
        quantity_options=QUANTITY_OPTIONS
    )
    return jsonify(resp)


@routes.route("/api/place_order", methods=["POST"])
@authenticate
def api_place_order():
    """Placing an order involves several layers of conditional logic: is this is a buy or sell order? Stop, limit, or
    market? Do we either have the adequate cash on hand, or enough of a position in the stock for this order to be
    valid? Here an order_ticket from the frontend--along with the user_id tacked on during the API call--gets decoded,
    checked for validity, and booked. Market orders are fulfilled in the same step. Stop/limit orders are monitored on
    an ongoing basis by the celery schedule and book as their requirements are satisfies
    """

    user_id = decode_token(request)
    order_ticket = request.json
    game_id = order_ticket["game_id"]
    stop_limit_price = order_ticket.get("stop_limit_price")
    if stop_limit_price:
        stop_limit_price = float(stop_limit_price)

    try:
        symbol = order_ticket["symbol"]
        market_price, _ = fetch_iex_price(symbol)
        cash_balance = get_current_game_cash_balance(user_id, game_id)
        current_holding = get_current_stock_holding(user_id, game_id, symbol)
        place_order(
            user_id,
            game_id,
            symbol,
            order_ticket["buy_or_sell"],
            cash_balance,
            current_holding,
            order_ticket["order_type"],
            order_ticket["quantity_type"],
            market_price,
            float(order_ticket["amount"]),
            order_ticket["time_in_force"],
            stop_limit_price)
    except Exception as e:
        return make_response(str(e), 400)

    async_serialize_order_details.apply(args=[game_id, user_id])  # this needs to be a single-row update
    async_serialize_current_balances.apply(args=[game_id, user_id])  # this needs to be a single-row update
    async_serialize_balances_chart.delay(game_id, user_id)
    async_compile_player_sidebar_stats.delay(game_id)
    return make_response(ORDER_PLACED_MESSAGE, 200)


@routes.route("/api/cancel_order", methods=["POST"])
@authenticate
def api_cancel_order():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    order_id = request.json.get("order_id")
    cancel_order(order_id)
    update_order_details(game_id, user_id, order_id, "remove")
    async_serialize_order_details.apply(args=[game_id, user_id])
    return make_response(ORDER_CANCELLED_MESSAGE, 200)


@routes.route("/api/fetch_price", methods=["POST"])
@authenticate
def fetch_price():
    symbol = request.json.get("symbol")
    price, timestamp = fetch_iex_price(symbol)
    async_cache_price.delay(symbol, price, timestamp)
    return jsonify({"price": price, "last_updated": format_time_for_response(timestamp)})


@routes.route("/api/suggest_symbols", methods=["POST"])
@authenticate
def api_suggest_symbols():
    text = request.json["text"]
    return jsonify(async_suggest_symbols.apply(args=[text]).result)

# ------- #
# Friends #
# ------- #


@routes.route("/api/send_friend_request", methods=["POST"])
@authenticate
def send_friend_request():
    user_id = decode_token(request)
    invited_username = request.json.get("friend_invitee")
    async_invite_friend.apply(args=[user_id, invited_username])
    return make_response(FRIEND_INVITE_SENT_MSG, 200)


@routes.route("/api/respond_to_friend_request", methods=["POST"])
@authenticate
def respond_to_friend_request():
    """Note to frontend developers working with this endpoint: the acceptable response options are 'accepted' and
    'declined'
    """
    user_id = decode_token(request)
    requester_username = request.json.get("requester_username")
    decision = request.json.get("decision")
    async_respond_to_friend_invite.apply(args=[requester_username, user_id, decision])
    return make_response(FRIEND_INVITE_RESPONSE_MSG, 200)


@routes.route("/api/get_list_of_friends", methods=["POST"])
@authenticate
def get_list_of_friends():
    user_id = decode_token(request)
    return jsonify(async_get_friends_details.apply(args=[user_id]).get())


@routes.route("/api/get_list_of_friend_invites", methods=["POST"])
@authenticate
def get_list_of_friend_invites():
    user_id = decode_token(request)
    return jsonify(async_get_friend_invites.apply(args=[user_id]).get())


@routes.route("/api/suggest_friend_invites", methods=["POST"])
@authenticate
def suggest_friend_invites():
    user_id = decode_token(request)
    text = request.json.get("text")
    return jsonify(async_suggest_friends.apply(args=[user_id, text]).get())

# ------- #
# Visuals #
# ------- #


@routes.route("/api/get_balances_chart", methods=["POST"])
@authenticate
def balances_chart():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_field_chart", methods=["POST"])
@authenticate
def field_chart():
    game_id = request.json.get("game_id")
    f"field_chart_{game_id}"
    return jsonify(unpack_redis_json(f"{FIELD_CHART_PREFIX}_{game_id}"))


@routes.route("/api/get_current_balances_table", methods=["POST"])
@authenticate
def get_current_balances_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_order_details_table", methods=["POST"])
@authenticate
def get_order_details_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{ORDER_DETAILS_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_payouts_table", methods=["POST"])
@authenticate
def get_payouts_table():
    game_id = request.json.get("game_id")
    return jsonify(unpack_redis_json(f"{PAYOUTS_PREFIX}_{game_id}"))

# ----- #
# Stats #
# ----- #


@routes.route("/api/get_sidebar_stats", methods=["POST"])
@authenticate
def get_sidebar_stats():
    game_id = request.json.get("game_id")
    return jsonify(unpack_redis_json(f"{SIDEBAR_STATS_PREFIX}_{game_id}"))


@routes.route("/api/get_cash_balances", methods=["POST"])
@authenticate
def get_cash_balances():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    outstanding_buy_order_value = get_pending_buy_order_value(user_id, game_id)
    buying_power = cash_balance - outstanding_buy_order_value
    return jsonify({"cash_balance": USD_FORMAT.format(cash_balance), "buying_power": USD_FORMAT.format(buying_power)})

# ----- #
# Admin #
# ----- #


@routes.route("/api/verify_admin", methods=["POST"])
@authenticate
@admin
def verify_admin():
    return make_response("Welcome to admin", 200)


@routes.route("/api/update_player_stats", methods=["POST"])
@authenticate
@admin
def update_player_stats():
    async_update_player_stats.delay()
    return make_response("updating stats...", 200)


@routes.route("/api/refresh_visuals", methods=["POST"])
@authenticate
@admin
def refresh_visuals():
    async_update_play_game_visuals.delay()
    return make_response("refreshing visuals...", 200)


# ------ #
# DevOps #
# ------ #


@routes.route("/healthcheck", methods=["GET"])
def healthcheck():
    return make_response(HEALTH_CHECK_RESPONSE, 200)
