from datetime import datetime as dt, timedelta
from functools import wraps

import jwt
import requests
from backend.database.db import db
from config import Config
from flask import Blueprint, request, make_response, jsonify

routes = Blueprint("routes", __name__)


def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            return make_response("Login to receive valid session_token", 401)
        try:
            jwt.decode(session_token, Config.SECRET_KEY)
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError as err:
            resp = make_response(err, 401)
        except jwt.InvalidSignatureError as err:
            resp = make_response(err, 401)
        return resp
    return decorated


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


@routes.route("/register", methods=["POST"])
def register_user():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API. token_id comes from response.tokenId where the
    response is the returned value from the React-Google-Login component
    """
    token_id = request.json["tokenId"]
    # validate the user with Google
    response = requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})
    if response.status_code == 200:
        decoded_json = response.json()
        user_email = decoded_json["email"]
        # if the user is valid, check to see if we already have them in our DB
        user = db.engine.execute("SELECT * FROM users WHERE email = %s", user_email).fetchone()
        if not user:
            # if not, make an entry
            db.engine.execute(
                "INSERT INTO users (name, email, profile_pic, username, created_at) VALUES (%s, %s, %s, %s, %s)",
                (decoded_json["given_name"], user_email, decoded_json["picture"], None, dt.now()))

        # refresh the user's session token and return to the client for local storage and http aut
        payload = {"email": user_email, "exp": dt.utcnow() + timedelta(minutes=Config.MINUTES_PER_SESSION)}
        session_token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256").decode("utf-8")
        resp = make_response()
        resp.set_cookie("session_token", session_token, httponly=True)
        return resp

    make_response("tokenId from Google OAuth failed verification", response.status_code,
                  {'WWW-Authenticate': "Basic realm='Login Required'"})
