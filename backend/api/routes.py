from datetime import datetime as dt, timedelta
from functools import wraps

import jwt
import requests
from backend.database.db import db
from config import Config
from flask import Blueprint, request, make_response, jsonify

routes = Blueprint("routes", __name__)


TOKEN_ID_MISSING_MSG = "This request is missing the 'tokenId' field -- are you a hacker?"
GOOGLE_OAUTH_ERROR_MSG = "tokenId from Google OAuth failed verification -- are you a hacker?"
INVALID_SIGNATURE_ERROR_MSG = "Couldn't decode session token -- are you a hacker?"
LOGIN_ERROR_MSG = "Login to receive valid session_token"
SESSION_EXP_ERROR_MSG = "You session token expired -- log back in"


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


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def create_jwt(email, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm="HS256").decode("utf-8")


@routes.route("/login", methods=["POST"])
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

        session_token = create_jwt(user_email)
        resp = make_response()
        resp.set_cookie("session_token", session_token, httponly=True)
        return resp

    return make_response(GOOGLE_OAUTH_ERROR_MSG, response.status_code)


@routes.route("/", methods=["POST"])
@authenticate
def index():
    """Return some basic information about the user's profile, games, and bets in order to
    populate the landing page"""
    session_token = jwt.decode(request.cookies["session_token"], Config.SECRET_KEY)
    user_email = session_token["email"]
    user_info = db.engine.execute("SELECT * FROM users WHERE email = %s", user_email).fetchone()
    resp = jsonify({"name": user_info[1], "email": user_info[2], "profile_pic": user_info[3]})
    return resp


@routes.route("/logout", methods=["POST"])
@authenticate
def logout():
    """Log user out of the backend by blowing away their session token
    """
    resp = make_response()
    resp.set_cookie("session_token", "", httponly=True, expires=0)
    return resp
