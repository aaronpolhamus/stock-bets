import hashlib
import time
from functools import wraps

import jwt
from backend.bi.report_logic import (
    GAMES_PER_USER_PREFIX,
    ORDERS_PER_ACTIVE_USER_PREFIX
)
from backend.config import Config
from backend.database.db import db
from backend.database.helpers import (
    add_row,
    query_to_dict
)
from backend.logic.auth import (
    make_avatar_url,
    setup_new_user,
    verify_facebook_oauth,
    verify_google_oauth,
    decode_token,
    make_session_token_from_uuid,
    register_username_with_token,
    add_external_game_invites,
    ADMIN_USERS,
    check_against_invited_users,
    upload_image_from_url_to_s3
)
from backend.logic.base import (
    get_user_ids,
    get_game_info,
    get_pending_buy_order_value,
    fetch_price,
    get_user_information,
    standardize_email,
    USD_FORMAT
)
from backend.logic.friends import (
    get_friend_invites_list,
    suggest_friends,
    get_friend_details,
    respond_to_friend_invite,
    invite_friend,
    email_platform_invitation,
    InvalidEmailError
)
from backend.logic.games import (
    get_downloadable_transactions_table,
    get_external_invite_list_by_status,
    add_user_via_platform,
    add_user_via_email,
    leave_game,
    DEFAULT_INVITE_OPEN_WINDOW,
    respond_to_game_invite,
    get_user_invite_statuses_for_pending_game,
    get_user_invite_status_for_game,
    suggest_symbols,
    add_game,
    get_game_info_for_user,
    place_order,
    cancel_order,
    get_current_game_cash_balance,
    get_current_stock_holding,
    make_random_game_title,
    DEFAULT_GAME_DURATION,
    DEFAULT_BUYIN,
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
    QUANTITY_OPTIONS,
    DEFAULT_STAKES,
    STAKES
)
from backend.logic.payments import check_payment_profile
from backend.logic.visuals import (
    format_time_for_response,
    serialize_and_pack_order_details,
    serialize_and_pack_portfolio_details,
    PENDING_ORDERS_PREFIX,
    FULFILLED_ORDER_PREFIX,
    BALANCES_CHART_PREFIX,
    CURRENT_BALANCES_PREFIX,
    FIELD_CHART_PREFIX,
    LEADERBOARD_PREFIX,
    PAYOUTS_PREFIX,
    ORDER_PERF_CHART_PREFIX
)
from backend.tasks.definitions import (
    async_update_all_games,
    async_cache_price,
    async_calculate_key_metrics
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
INVALID_OAUTH_PROVIDER_MSG = "Not a valid OAuth provider"
MISSING_OAUTH_PROVIDER_MSG = "Please specify the provider in the requests body"
ORDER_PLACED_MESSAGE = "Order placed successfully!"
GAME_RESPONSE_MSG = "Got it, we'll the game creator know."
FRIEND_INVITE_SENT_MSG = "Friend invite sent :)"
FRIEND_INVITE_RESPONSE_MSG = "Great, we'll let them know"
ADMIN_BLOCK_MSG = "This is a protected admin view. Check in with your team if you need permission to access"
NOT_INVITED_EMAIL = "stockbets is in super-early beta, and we're whitelisting it for now. We'll open to everyone at the end of August, but email contact@stockbets.io for access before that :)"
LEAVE_GAME_MESSAGE = "You've left the game"
EMAIL_SENT_MESSAGE = "Emails sent to your friends"
INVITED_MORE_USERS_MESSAGE = "Great, we'll let your friends know about the game"
EMAIL_NOT_FOUND_MSG = "We can't find this email on file -- if this is your first time, be sure to click 'Sign Up' first. If this is an error get in touch at contact@stockbets.io"
EMAIL_ALREADY_LOGGED_MSG = "We've already registered this email. Try logging in instead? Get in touch with us at contact@stockbets.io for a password reset or if you think your account has been compromised"


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
        if user_email not in ADMIN_USERS:
            return make_response(ADMIN_BLOCK_MSG, 401)
        return f(*args, **kwargs)

    return decorated


@routes.route("/api/login", methods=["POST"])
def login():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API. token_id comes from response.tokenId where the
    response is the returned value from the React-Google-Login component.
    """
    current_time = time.time()
    login_data = request.json  # in the case of a different platform provider, this is just the oauth response
    is_sign_up = login_data.get("is_sign_up")
    provider = login_data.get("provider")
    password = login_data.get("password")
    name = login_data.get("name")
    email = login_data.get("email")
    if provider not in ["google", "facebook", "twitter", "stockbets"]:
        return make_response(INVALID_OAUTH_PROVIDER_MSG, 411)

    status_code = 400
    profile_pic = None
    resource_uuid = None
    if provider == "google":
        response = verify_google_oauth(login_data["tokenId"])
        resource_uuid = login_data.get("googleId")
        status_code = response.status_code
        if status_code == 200:
            verification_json = response.json()
            email = verification_json["email"]
            if is_sign_up:
                name = verification_json["given_name"]
                profile_pic = upload_image_from_url_to_s3(verification_json["picture"], resource_uuid)

    if provider == "facebook":
        response = verify_facebook_oauth(login_data["accessToken"])
        status_code = response.status_code
        if status_code == 200:
            resource_uuid = login_data["userID"]
            email = login_data["email"]
            if is_sign_up:
                name = login_data["name"]
                profile_pic = upload_image_from_url_to_s3(login_data["picture"]["data"]["url"], resource_uuid)

    if provider == "stockbets":
        status_code = 200
        if is_sign_up:
            resource_uuid = hashlib.sha224(bytes(email, encoding='utf-8')).hexdigest()
            url = make_avatar_url(email)
            profile_pic = upload_image_from_url_to_s3(url, resource_uuid)

    if provider == "twitter":
        pass

    if status_code is not 200:
        return make_response(OAUTH_ERROR_MSG, status_code)

    if Config.CHECK_WHITE_LIST:
        if not check_against_invited_users(email):
            return make_response(NOT_INVITED_EMAIL, 403)

    if is_sign_up:
        db_entry = query_to_dict("SELECT * FROM users WHERE LOWER(REPLACE(email, '.', '')) = %s",
                                 standardize_email(email))
        if db_entry:
            return make_response(EMAIL_ALREADY_LOGGED_MSG, 403)

        user_id = setup_new_user(name, email, profile_pic, current_time, provider, resource_uuid, password)
        add_external_game_invites(email, user_id)
    else:
        db_entry = query_to_dict("SELECT * FROM users WHERE LOWER(REPLACE(email, '.', '')) = %s",
                                 standardize_email(email))
        if not db_entry:
            return make_response(EMAIL_NOT_FOUND_MSG, 403)
        resource_uuid = db_entry[0]["resource_uuid"]

    session_token = make_session_token_from_uuid(resource_uuid)
    resp = make_response()
    resp.set_cookie("session_token", session_token, httponly=True, samesite=None, secure=True)
    return resp


@routes.route("/api/logout", methods=["POST"])
@authenticate
def logout():
    """Log user out of the backend by blowing away their session token
    """
    resp = make_response()
    resp.set_cookie("session_token", "", httponly=True, samesite=None, secure=True, expires=0)
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
        resp.set_cookie("session_token", session_token, httponly=True, samesite=None, secure=True)
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
    game_mode = request.json.get("game_mode")
    default_title = make_random_game_title()  # TODO: Enforce uniqueness at some point here
    friend_details = get_friend_details(user_id)
    available_invitees = [x["username"] for x in friend_details]
    resp = dict(
        title=default_title,
        duration=DEFAULT_GAME_DURATION,
        benchmark=DEFAULT_BENCHMARK,
        benchmarks=BENCHMARKS,
    )
    if game_mode == "multi_player":
        resp.update(dict(
            buy_in=DEFAULT_BUYIN,
            side_bets_perc=DEFAULT_SIDEBET_PERCENT,
            side_bets_period=DEFAULT_SIDEBET_PERIOD,
            sidebet_periods=SIDE_BET_PERIODS,
            available_invitees=available_invitees,
            invite_window=DEFAULT_INVITE_OPEN_WINDOW,
            stakes=DEFAULT_STAKES,
            stakes_options=STAKES
        ))
    return jsonify(resp)


@routes.route("/api/create_game", methods=["POST"])
@authenticate
def create_game():
    user_id = decode_token(request)
    game_settings = request.json
    game_id = add_game(
        user_id,
        game_settings["title"],
        game_settings["game_mode"],
        game_settings["duration"],
        game_settings["benchmark"],
        game_settings.get("stakes"),
        game_settings.get("buy_in"),
        game_settings.get("side_bets_perc"),
        game_settings.get("side_bets_period"),
        game_settings.get("invitees"),
        game_settings.get("invite_window"),
        game_settings.get("email_invitees")
    )
    return jsonify({"game_id": game_id})


@routes.route("/api/respond_to_game_invite", methods=["POST"])
@authenticate
def api_respond_to_game_invite():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    decision = request.json.get("decision")
    respond_to_game_invite(game_id, user_id, decision, time.time())
    return make_response(GAME_RESPONSE_MSG, 200)


@routes.route("/api/get_pending_game_info", methods=["POST"])
@authenticate
def get_pending_game_info():
    game_id = request.json.get("game_id")

    records = dict()
    records["platform_invites"] = get_user_invite_statuses_for_pending_game(game_id)
    records["email_invites"] = get_external_invite_list_by_status(game_id, "pending")
    return jsonify(records)


@routes.route("/api/leave_game", methods=["POST"])
@authenticate
def api_leave_game():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    leave_game(game_id, user_id)
    return make_response(LEAVE_GAME_MESSAGE, 200)


@routes.route("/api/invite_users_to_pending_game", methods=["POST"])
@authenticate
def invite_users_to_pending_game():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    invitee_emails = request.json.get("email_invitees")
    invitees = request.json.get("invitees")

    if invitees is not None:
        invited_ids = get_user_ids(invitees)
        for invited_id in invited_ids:
            add_user_via_platform(game_id, invited_id)

    if invitee_emails is not None:
        try:
            for email in invitee_emails:
                add_user_via_email(game_id, user_id, email)
        except InvalidEmailError as e:
            make_response(f"{email} : {str(e)}", 400)

    return make_response(INVITED_MORE_USERS_MESSAGE, 200)


# --------------------------- #
# Order management and prices #
# --------------------------- #


@routes.route("/api/game_info", methods=["POST"])
@authenticate
def api_game_info():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    game_info = get_game_info(game_id)
    game_info["is_host"] = game_info["creator_id"] == user_id
    game_info["user_status"] = get_user_invite_status_for_game(game_id, user_id)
    if game_info["game_status"] in ["active", "finished"]:
        game_info["leaderboard"] = unpack_redis_json(f"{LEADERBOARD_PREFIX}_{game_id}")["records"]
    return jsonify(game_info)


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
        symbol = order_ticket["symbol"].upper()  # ensure upper casing
        market_price, last_updated = fetch_price(symbol)
        async_cache_price.delay(symbol, market_price, last_updated)
        cash_balance = get_current_game_cash_balance(user_id, game_id)
        current_holding = get_current_stock_holding(user_id, game_id, symbol)
        order_id = place_order(
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

    serialize_and_pack_order_details(game_id, user_id)
    serialize_and_pack_portfolio_details(game_id, user_id)
    return make_response(ORDER_PLACED_MESSAGE, 200)


@routes.route("/api/cancel_order", methods=["POST"])
@authenticate
def api_cancel_order():
    order_id = request.json.get("order_id")
    cancel_order(order_id)
    return make_response(f"Cancelled orderId: {order_id}", 200)


@routes.route("/api/fetch_price", methods=["POST"])
@authenticate
def api_fetch_price():
    symbol = request.json.get("symbol")
    price, timestamp = fetch_price(symbol)
    async_cache_price.delay(symbol, price, timestamp)
    return jsonify({"price": price, "last_updated": format_time_for_response(timestamp)})


@routes.route("/api/suggest_symbols", methods=["POST"])
@authenticate
def api_suggest_symbols():
    user_id = decode_token(request)
    game_id = request.json["game_id"]
    text = request.json["text"]
    buy_or_sell = request.json["buy_or_sell"]
    return jsonify(suggest_symbols(game_id, user_id, text, buy_or_sell))


# ------- #
# Friends #
# ------- #


@routes.route("/api/send_friend_request", methods=["POST"])
@authenticate
def send_friend_request():
    user_id = decode_token(request)
    invited_username = request.json.get("friend_invitee")
    invited_id = get_user_ids([invited_username])[0]
    invite_friend(user_id, invited_id)
    return make_response(FRIEND_INVITE_SENT_MSG, 200)


@routes.route("/api/invite_users_by_email", methods=["POST"])
@authenticate
def invite_friend_by_email():
    user_id = decode_token(request)
    emails = request.json.get('friend_emails')
    for email in emails:
        try:
            email_platform_invitation(user_id, email)
        except InvalidEmailError as e:
            make_response(f"{email} : {str(e)}", 400)
    return make_response(EMAIL_SENT_MESSAGE, 200)


@routes.route("/api/respond_to_friend_request", methods=["POST"])
@authenticate
def respond_to_friend_request():
    """Note to frontend developers working with this endpoint: the acceptable response options are 'accepted' and
    'declined'
    """
    user_id = decode_token(request)
    requester_username = request.json.get("requester_username")
    decision = request.json.get("decision")
    respond_to_friend_invite(requester_username, user_id, decision)
    return make_response(FRIEND_INVITE_RESPONSE_MSG, 200)


@routes.route("/api/get_list_of_friends", methods=["POST"])
@authenticate
def get_list_of_friends():
    user_id = decode_token(request)
    return jsonify(get_friend_details(user_id))


@routes.route("/api/get_list_of_friend_invites", methods=["POST"])
@authenticate
def get_list_of_friend_invites():
    user_id = decode_token(request)
    return jsonify(get_friend_invites_list(user_id))


@routes.route("/api/suggest_friend_invites", methods=["POST"])
@authenticate
def suggest_friend_invites():
    user_id = decode_token(request)
    text = request.json.get("text")
    return jsonify(suggest_friends(user_id, text))


# ------- #
# Visuals #
# ------- #


@routes.route("/api/get_balances_chart", methods=["POST"])
@authenticate
def balances_chart():
    """Be default, the frontend will load with username = null for the chart selector dropdown, and we'll show them
    their own chart. When the user proactively picks a username to checkout, this will be sent in the POST request to
    this endpoint and used to pull up the appropriate chart
    """
    game_id = request.json.get("game_id")
    username = request.json.get("username")
    if username:
        user_id = get_user_ids([username])[0]
    else:
        user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{BALANCES_CHART_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_order_performance_chart", methods=["POST"])
@authenticate
def order_performance_chart():
    """This endpoints works exactly the same as balances_chart. See above for details
    """
    game_id = request.json.get("game_id")
    username = request.json.get("username")
    if username:
        user_id = get_user_ids([username])[0]
    else:
        user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{ORDER_PERF_CHART_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_field_chart", methods=["POST"])
@authenticate
def field_chart():
    game_id = request.json.get("game_id")
    return jsonify(unpack_redis_json(f"{FIELD_CHART_PREFIX}_{game_id}"))


@routes.route("/api/get_current_balances_table", methods=["POST"])
@authenticate
def get_current_balances_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{CURRENT_BALANCES_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_pending_orders_table", methods=["POST"])
@authenticate
def get_pending_orders_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{PENDING_ORDERS_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_fulfilled_orders_table", methods=["POST"])
@authenticate
def get_fulfilled_orders_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(unpack_redis_json(f"{FULFILLED_ORDER_PREFIX}_{game_id}_{user_id}"))


@routes.route("/api/get_payouts_table", methods=["POST"])
@authenticate
def get_payouts_table():
    game_id = request.json.get("game_id")
    return jsonify(unpack_redis_json(f"{PAYOUTS_PREFIX}_{game_id}"))

# ----- #
# Stats #
# ----- #


@routes.route("/api/get_leaderboard", methods=["POST"])
@authenticate
def get_leaderboard():
    game_id = request.json.get("game_id")
    return jsonify(unpack_redis_json(f"{LEADERBOARD_PREFIX}_{game_id}"))


@routes.route("/api/get_cash_balances", methods=["POST"])
@authenticate
def get_cash_balances():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    cash_balance = get_current_game_cash_balance(user_id, game_id)
    outstanding_buy_order_value = get_pending_buy_order_value(user_id, game_id)
    buying_power = cash_balance - outstanding_buy_order_value
    return jsonify({"cash_balance": USD_FORMAT.format(cash_balance), "buying_power": USD_FORMAT.format(buying_power)})


@routes.route("/api/get_transactions_table", methods=["POST"])
@authenticate
def get_transactions_table():
    game_id = request.json.get("game_id")
    user_id = decode_token(request)
    return jsonify(get_downloadable_transactions_table(game_id, user_id))


# -------- #
# Payments #
# -------- #


@routes.route("/api/process_payment", methods=["POST"])
@authenticate
def process_payment():
    user_id = decode_token(request)
    game_id = request.json.get("game_id")
    amount = request.json["amount"]
    currency = request.json["currency"]
    processor = request.json["processor"]
    payment_type = request.json["type"]
    payer_email = request.json.get("payer_email")
    uuid = request.json.get("uuid")
    winner_table_id = request.json.get("winner_table_id")

    # get payment profile id
    profile_id = check_payment_profile(user_id, processor, uuid, payer_email)

    # register payment
    add_row("payments", game_id=game_id, user_id=user_id, profile_id=profile_id, winner_table_id=winner_table_id,
            type=payment_type, amount=amount, currency=currency, direction='inflow', timestamp=time.time())

    return make_response("Payment processed", 200)

# ----- #
# Admin #
# ----- #


@routes.route("/api/verify_admin", methods=["POST"])
@authenticate
@admin
def verify_admin():
    return make_response("Welcome to admin", 200)


@routes.route("/api/refresh_game_statuses", methods=["POST"])
@authenticate
@admin
def refresh_visuals():
    async_update_all_games.delay()
    return make_response("refreshing visuals...", 200)


@routes.route("/api/refresh_metrics", methods=["POST"])
@authenticate
@admin
def refresh_metrics():
    async_calculate_key_metrics.delay()
    return make_response("refreshing metrics...", 200)


@routes.route("/api/games_per_users", methods=["POST"])
@authenticate
@admin
def api_games_per_users():
    return jsonify(unpack_redis_json(GAMES_PER_USER_PREFIX))


@routes.route("/api/orders_per_active_user", methods=["POST"])
@authenticate
@admin
def api_orders_per_active_user():
    return jsonify(unpack_redis_json(ORDERS_PER_ACTIVE_USER_PREFIX))

# ------ #
# DevOps #
# ------ #


@routes.route("/healthcheck", methods=["GET"])
def healthcheck():
    return make_response(HEALTH_CHECK_RESPONSE, 200)
