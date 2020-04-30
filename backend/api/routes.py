from datetime import datetime as dt, timedelta

import jwt
import requests
from backend.database.db import db
from config import Config
from flask import Blueprint, request, make_response
from flask_httpauth import HTTPTokenAuth

auth = HTTPTokenAuth(scheme="Bearer")
routes = Blueprint("routes", __name__)


@routes.route("/", methods=["POST"])
def index():
    """A user with a valid token will get a response with basic profile information to be displayed on their landing
    page. Otherwise the API will return a 401, and the front-end will redirect to the Google Login page"""
    from flask import current_app
    current_app.logger.debug(f"*** JSON cookies: {dir(request)}")
    # current_app.logger.debug(f"*** JSON cookies: {request.cookies['session_token']}")

    # auth.login_required has already validated the user

    # send back basic information for the user's landing page

    resp = make_response()
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
        resp.set_cookie("session_token", session_token, secure=True, httponly=True)
        return resp

    make_response("tokenId from Google OAuth failed verification", response.status_code,
                  {'WWW-Authenticate': "Basic realm='Login Required'"})
